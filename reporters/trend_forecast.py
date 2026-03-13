from __future__ import annotations

import importlib
import logging
import warnings
from collections.abc import Sequence
from datetime import UTC, date, datetime, timedelta
from typing import Protocol, TypedDict, cast

from trendradar.models import TrendPoint


class ForecastPayload(TypedDict):
    history_dates: list[str]
    history_counts: list[float]
    dates: list[str]
    forecast: list[float]
    lower_80: list[float]
    upper_80: list[float]
    lower_95: list[float]
    upper_95: list[float]
    model: str


class _VectorLike(Protocol):
    def tolist(self) -> list[float]: ...


class _FrameLike(Protocol):
    def __getitem__(self, key: str) -> _VectorLike: ...


class _TableLike(_FrameLike, Protocol):
    def tail(self, count: int) -> _FrameLike: ...


class _ForecastResultLike(Protocol):
    def summary_frame(self, alpha: float = 0.05) -> _FrameLike: ...


class _ArimaFittedLike(Protocol):
    def get_forecast(self, steps: int) -> _ForecastResultLike: ...


class _ArimaModelLike(Protocol):
    def fit(self) -> _ArimaFittedLike: ...


class _ArimaFactoryLike(Protocol):
    def __call__(self, series: Sequence[float], order: tuple[int, int, int]) -> _ArimaModelLike: ...


class _ProphetModelLike(Protocol):
    def fit(self, frame: object) -> object: ...

    def make_future_dataframe(self, periods: int, freq: str, include_history: bool) -> object: ...

    def predict(self, frame: object) -> _TableLike: ...


class _ProphetFactoryLike(Protocol):
    def __call__(
        self,
        interval_width: float,
        daily_seasonality: bool,
        weekly_seasonality: bool,
        yearly_seasonality: bool,
    ) -> _ProphetModelLike: ...


class _PandasLike(Protocol):
    def to_datetime(self, values: Sequence[date]) -> object: ...

    def DataFrame(self, data: dict[str, object]) -> object: ...  # noqa: N802


logger = logging.getLogger(__name__)

FORECAST_DAYS = 7
MIN_HISTORY_DAYS = 14
ARIMA_ORDER = (5, 1, 0)
WEEKLY_SIGNAL_THRESHOLD = 0.35

ARIMAModel: _ArimaFactoryLike | None = None
ProphetModel: _ProphetFactoryLike | None = None
PandasModule: _PandasLike | None = None

_arima_lookup_done = False
_prophet_lookup_done = False
_pandas_lookup_done = False


def forecast_keyword_trends(
    trend_points: list[TrendPoint],
    top_n: int = 10,
) -> dict[str, ForecastPayload]:
    if not trend_points or top_n <= 0:
        return {}

    aggregated_daily_counts = _aggregate_daily_keyword_counts(trend_points)
    ranked_keywords = sorted(
        aggregated_daily_counts.items(),
        key=lambda item: (-sum(item[1].values()), item[0]),
    )

    forecasts: dict[str, ForecastPayload] = {}
    for keyword, daily_counts in ranked_keywords[:top_n]:
        history_dates, history_counts = _build_dense_daily_series(daily_counts)

        if len(history_dates) < MIN_HISTORY_DAYS:
            logger.info(
                "Skipping forecast for '%s': insufficient history (%d days)",
                keyword,
                len(history_dates),
            )
            continue

        selected_model = _select_forecast_model(history_dates, history_counts)
        forecast_result: (
            tuple[list[float], list[float], list[float], list[float], list[float]] | None
        )
        forecast_result = None
        model_used = selected_model

        if selected_model == "prophet":
            forecast_result = _forecast_with_prophet(history_dates, history_counts)
            if forecast_result is None:
                model_used = "arima"
                forecast_result = _forecast_with_arima(history_counts)
        else:
            forecast_result = _forecast_with_arima(history_counts)
            if (
                forecast_result is None
                and _load_prophet_model() is not None
                and len(history_dates) >= 28
            ):
                model_used = "prophet"
                forecast_result = _forecast_with_prophet(history_dates, history_counts)

        if forecast_result is None:
            logger.warning("Skipping forecast for '%s': all models failed", keyword)
            continue

        forecast, lower_80, upper_80, lower_95, upper_95 = forecast_result
        lower_80, upper_80 = _sanitize_bounds(lower_80, upper_80)
        lower_95, upper_95 = _sanitize_bounds(lower_95, upper_95)

        forecast_dates = [
            (history_dates[-1] + timedelta(days=offset)).isoformat()
            for offset in range(1, FORECAST_DAYS + 1)
        ]

        forecasts[keyword] = {
            "history_dates": [history_date.isoformat() for history_date in history_dates],
            "history_counts": _clamp_non_negative(history_counts),
            "dates": forecast_dates,
            "forecast": _clamp_non_negative(forecast),
            "lower_80": lower_80,
            "upper_80": upper_80,
            "lower_95": lower_95,
            "upper_95": upper_95,
            "model": model_used,
        }

    return forecasts


def _load_arima_model() -> _ArimaFactoryLike | None:
    global ARIMAModel, _arima_lookup_done
    if _arima_lookup_done:
        return ARIMAModel

    _arima_lookup_done = True
    try:
        module = importlib.import_module("statsmodels.tsa.arima.model")
        candidate = getattr(module, "ARIMA", None)
    except Exception:
        ARIMAModel = None
        return None

    if callable(candidate):
        ARIMAModel = cast(_ArimaFactoryLike, candidate)

    return ARIMAModel


def _load_prophet_model() -> _ProphetFactoryLike | None:
    global ProphetModel, _prophet_lookup_done
    if _prophet_lookup_done:
        return ProphetModel

    _prophet_lookup_done = True
    try:
        module = importlib.import_module("prophet")
        candidate = getattr(module, "Prophet", None)
    except Exception:
        ProphetModel = None
        return None

    if callable(candidate):
        ProphetModel = cast(_ProphetFactoryLike, candidate)

    return ProphetModel


def _load_pandas_module() -> _PandasLike | None:
    global PandasModule, _pandas_lookup_done
    if _pandas_lookup_done:
        return PandasModule

    _pandas_lookup_done = True
    try:
        module = importlib.import_module("pandas")
    except Exception:
        PandasModule = None
        return None

    PandasModule = cast(_PandasLike, cast(object, module))
    return PandasModule


def _aggregate_daily_keyword_counts(
    trend_points: list[TrendPoint],
) -> dict[str, dict[date, float]]:
    aggregated: dict[str, dict[date, float]] = {}

    for point in trend_points:
        keyword = point.keyword.strip()
        if not keyword:
            continue

        event_date = _to_utc_date(point.timestamp)
        daily_counts = aggregated.setdefault(keyword, {})
        daily_counts[event_date] = daily_counts.get(event_date, 0.0) + 1.0

    return aggregated


def _to_utc_date(timestamp: datetime) -> date:
    if timestamp.tzinfo is None:
        return timestamp.date()
    return timestamp.astimezone(UTC).date()


def _build_dense_daily_series(daily_counts: dict[date, float]) -> tuple[list[date], list[float]]:
    if not daily_counts:
        return [], []

    sorted_dates = sorted(daily_counts)
    cursor = sorted_dates[0]
    end_date = sorted_dates[-1]

    history_dates: list[date] = []
    history_counts: list[float] = []

    while cursor <= end_date:
        history_dates.append(cursor)
        history_counts.append(float(daily_counts.get(cursor, 0.0)))
        cursor += timedelta(days=1)

    return history_dates, history_counts


def _select_forecast_model(history_dates: list[date], history_counts: list[float]) -> str:
    if _load_prophet_model() is None or _load_pandas_module() is None:
        return "arima"

    if len(history_dates) < 28:
        return "arima"

    non_zero_days = sum(1 for count in history_counts if count > 0.0)
    if non_zero_days < 14:
        return "arima"

    weekly_signal = _compute_weekly_signal(history_dates, history_counts)
    if weekly_signal >= WEEKLY_SIGNAL_THRESHOLD:
        return "prophet"

    return "arima"


def _compute_weekly_signal(history_dates: list[date], history_counts: list[float]) -> float:
    weekday_buckets: dict[int, list[float]] = {index: [] for index in range(7)}

    for day, count in zip(history_dates, history_counts, strict=False):
        weekday_buckets[day.weekday()].append(count)

    weekday_means = [sum(bucket) / len(bucket) for bucket in weekday_buckets.values() if bucket]

    if len(weekday_means) < 2:
        return 0.0

    mean_count = sum(history_counts) / len(history_counts)
    if mean_count <= 0.0:
        return 0.0

    return (max(weekday_means) - min(weekday_means)) / max(mean_count, 1.0)


def _to_float_list(frame: _FrameLike, column: str) -> list[float]:
    return [float(value) for value in frame[column].tolist()]


def _forecast_with_arima(
    history_counts: list[float],
) -> tuple[list[float], list[float], list[float], list[float], list[float]] | None:
    arima_factory = _load_arima_model()
    if arima_factory is None:
        logger.warning("statsmodels is not available. ARIMA forecast skipped.")
        return None

    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            model = arima_factory(history_counts, order=ARIMA_ORDER)
            fitted_model = model.fit()

        forecast_result = fitted_model.get_forecast(steps=FORECAST_DAYS)
        summary_80 = forecast_result.summary_frame(alpha=0.20)
        summary_95 = forecast_result.summary_frame(alpha=0.05)

        forecast = _to_float_list(summary_95, "mean")
        lower_80 = _to_float_list(summary_80, "mean_ci_lower")
        upper_80 = _to_float_list(summary_80, "mean_ci_upper")
        lower_95 = _to_float_list(summary_95, "mean_ci_lower")
        upper_95 = _to_float_list(summary_95, "mean_ci_upper")

        return forecast, lower_80, upper_80, lower_95, upper_95
    except Exception as exc:
        logger.warning("ARIMA forecast failed: %s", exc)
        return None


def _forecast_with_prophet(
    history_dates: list[date],
    history_counts: list[float],
) -> tuple[list[float], list[float], list[float], list[float], list[float]] | None:
    prophet_factory = _load_prophet_model()
    pandas_module = _load_pandas_module()
    if prophet_factory is None or pandas_module is None:
        return None

    history_frame = pandas_module.DataFrame(
        {
            "ds": pandas_module.to_datetime(history_dates),
            "y": history_counts,
        }
    )

    try:
        model = prophet_factory(
            interval_width=0.95,
            daily_seasonality=False,
            weekly_seasonality=True,
            yearly_seasonality=False,
        )
        _ = model.fit(history_frame)
        future_frame = model.make_future_dataframe(
            periods=FORECAST_DAYS,
            freq="D",
            include_history=False,
        )
        forecast_table = model.predict(future_frame)
        forecast_frame = forecast_table.tail(FORECAST_DAYS)
    except Exception as exc:
        logger.warning("Prophet forecast failed: %s", exc)
        return None

    forecast = _to_float_list(forecast_frame, "yhat")
    lower_95 = _to_float_list(forecast_frame, "yhat_lower")
    upper_95 = _to_float_list(forecast_frame, "yhat_upper")

    z_95 = 1.959963984540054
    z_80 = 1.2815515655446004
    lower_80: list[float] = []
    upper_80: list[float] = []

    for mean_value, low_95, up_95 in zip(forecast, lower_95, upper_95, strict=False):
        half_width_95 = max(up_95 - mean_value, mean_value - low_95, 0.0)
        half_width_80 = (half_width_95 / z_95) * z_80
        lower_80.append(mean_value - half_width_80)
        upper_80.append(mean_value + half_width_80)

    return forecast, lower_80, upper_80, lower_95, upper_95


def _sanitize_bounds(lower: list[float], upper: list[float]) -> tuple[list[float], list[float]]:
    sanitized_lower: list[float] = []
    sanitized_upper: list[float] = []

    for low, up in zip(lower, upper, strict=False):
        low_value = max(0.0, float(low))
        upper_value = max(0.0, float(up))
        if upper_value < low_value:
            upper_value = low_value

        sanitized_lower.append(low_value)
        sanitized_upper.append(upper_value)

    return sanitized_lower, sanitized_upper


def _clamp_non_negative(values: list[float]) -> list[float]:
    return [max(0.0, float(value)) for value in values]

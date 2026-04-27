from __future__ import annotations

import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from reporters import trend_forecast  # noqa: E402
from trendradar.models import TrendPoint  # noqa: E402


pytestmark = pytest.mark.unit


def _build_points(keyword: str, days: int, daily_count: int) -> list[TrendPoint]:
    points: list[TrendPoint] = []
    start = datetime(2026, 1, 1, tzinfo=UTC)

    for day_offset in range(days):
        base_time = start + timedelta(days=day_offset)
        for hour_offset in range(daily_count):
            points.append(
                TrendPoint(
                    keyword=keyword,
                    source="google",
                    timestamp=base_time + timedelta(hours=hour_offset),
                    value=1.0,
                    metadata={},
                )
            )

    return points


def test_forecast_keyword_trends_returns_top_keyword(monkeypatch: pytest.MonkeyPatch) -> None:
    points = _build_points("ai", days=20, daily_count=3)
    points.extend(_build_points("robot", days=20, daily_count=1))

    def fake_arima(
        history_counts: list[float],
    ) -> tuple[
        list[float],
        list[float],
        list[float],
        list[float],
        list[float],
    ]:
        assert history_counts == [3.0] * 20
        return [4.0] * 7, [3.5] * 7, [4.5] * 7, [3.0] * 7, [5.0] * 7

    monkeypatch.setattr(trend_forecast, "_forecast_with_arima", fake_arima)
    monkeypatch.setattr(trend_forecast, "ProphetModel", None)

    result = trend_forecast.forecast_keyword_trends(points, top_n=1)

    assert list(result.keys()) == ["ai"]

    payload = result["ai"]
    assert payload["history_counts"] == [3.0] * 20
    assert payload["dates"] == [
        "2026-01-21",
        "2026-01-22",
        "2026-01-23",
        "2026-01-24",
        "2026-01-25",
        "2026-01-26",
        "2026-01-27",
    ]
    assert payload["forecast"] == [4.0] * 7
    assert payload["lower_80"] == [3.5] * 7
    assert payload["upper_80"] == [4.5] * 7
    assert payload["lower_95"] == [3.0] * 7
    assert payload["upper_95"] == [5.0] * 7


def test_forecast_keyword_trends_skips_sparse_history(monkeypatch: pytest.MonkeyPatch) -> None:
    points = _build_points("ai", days=10, daily_count=2)
    was_called = False

    def fake_arima(
        _: list[float],
    ) -> tuple[list[float], list[float], list[float], list[float], list[float]]:
        nonlocal was_called
        was_called = True
        return [1.0] * 7, [1.0] * 7, [1.0] * 7, [1.0] * 7, [1.0] * 7

    monkeypatch.setattr(trend_forecast, "_forecast_with_arima", fake_arima)

    result = trend_forecast.forecast_keyword_trends(points, top_n=1)

    assert result == {}
    assert was_called is False


def test_forecast_keyword_trends_handles_model_failures(monkeypatch: pytest.MonkeyPatch) -> None:
    points = _build_points("ai", days=20, daily_count=2)

    def failing_arima(
        _: list[float],
    ) -> tuple[list[float], list[float], list[float], list[float], list[float]] | None:
        return None

    monkeypatch.setattr(trend_forecast, "_forecast_with_arima", failing_arima)
    monkeypatch.setattr(trend_forecast, "ProphetModel", None)

    result = trend_forecast.forecast_keyword_trends(points, top_n=1)

    assert result == {}

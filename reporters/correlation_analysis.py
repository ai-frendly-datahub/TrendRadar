from __future__ import annotations

import math
from collections import defaultdict
from datetime import UTC, date, timedelta
from itertools import combinations
from typing import Any

from trendradar.models import TrendPoint


MAX_LAG_DAYS = 7
MIN_REQUIRED_PLATFORMS = 3
MIN_REQUIRED_DAYS = 14
TOP_RELATIONSHIP_LIMIT = 10


_SeriesFrame = dict[str, object]


def analyze_cross_platform_correlation(trend_points: list[TrendPoint]) -> dict[str, object]:
    keyword_frames = _build_keyword_frames(trend_points)
    eligible_frames = {
        keyword: frame
        for keyword, frame in keyword_frames.items()
        if _is_eligible_keyword_frame(frame)
    }

    platforms = sorted(
        {
            platform
            for frame in eligible_frames.values()
            for platform, values in _frame_values(_as_frame(frame)).items()
            if any(value is not None for value in values)
        }
    )

    correlation_matrix = _build_correlation_matrix(platforms, eligible_frames)
    lead_lag_results = _build_lead_lag_results(eligible_frames)
    lead_lag_results_sorted = sorted(
        lead_lag_results,
        key=lambda item: abs(_to_float(item.get("correlation", 0.0))),
        reverse=True,
    )
    top_relationships = [
        _to_top_relationship(item) for item in lead_lag_results_sorted[:TOP_RELATIONSHIP_LIMIT]
    ]

    return {
        "correlation_matrix": correlation_matrix,
        "lead_lag_results": lead_lag_results_sorted,
        "top_lead_lag_relationships": top_relationships,
    }


def _build_keyword_frames(trend_points: list[TrendPoint]) -> dict[str, Any]:
    raw: dict[str, dict[date, dict[str, list[float]]]] = defaultdict(
        lambda: defaultdict(lambda: defaultdict(list))
    )

    for point in trend_points:
        timestamp = point.timestamp
        if timestamp.tzinfo is not None:
            timestamp = timestamp.astimezone(UTC)
        raw[point.keyword][timestamp.date()][point.platform].append(point.score)

    keyword_frames: dict[str, Any] = {}
    for keyword, by_date in raw.items():
        if not by_date:
            continue
        start = min(by_date)
        end = max(by_date)
        dates: list[date] = []
        current = start
        while current <= end:
            dates.append(current)
            current += timedelta(days=1)

        platforms = sorted(
            {platform for date_values in by_date.values() for platform in date_values}
        )
        values: dict[str, list[float | None]] = {platform: [] for platform in platforms}
        for item_date in dates:
            date_values = by_date.get(item_date, {})
            for platform in platforms:
                samples = date_values.get(platform, [])
                values[platform].append(sum(samples) / len(samples) if samples else None)

        keyword_frames[str(keyword)] = {"dates": dates, "values": values}

    return keyword_frames


def _is_eligible_keyword_frame(keyword_frame: Any) -> bool:
    frame = _as_frame(keyword_frame)
    platform_count = 0
    values = _frame_values(frame)
    for platform in values:
        if any(value is not None for value in values[platform]):
            platform_count += 1
    total_days = len(_frame_dates(frame))
    return platform_count >= MIN_REQUIRED_PLATFORMS and total_days >= MIN_REQUIRED_DAYS


def _build_correlation_matrix(
    platforms: list[str],
    keyword_frames: dict[str, Any],
) -> dict[str, object]:
    if not platforms:
        return {
            "platforms": [],
            "z": [],
            "p_values": [],
        }

    correlations: list[list[float | None]] = [[None for _ in platforms] for _ in platforms]
    p_values: list[list[float | None]] = [[None for _ in platforms] for _ in platforms]

    for index in range(len(platforms)):
        correlations[index][index] = 1.0
        p_values[index][index] = 0.0

    for left_index, platform_a in enumerate(platforms):
        for right_index in range(left_index + 1, len(platforms)):
            platform_b = platforms[right_index]
            paired_values: list[tuple[float, float]] = []

            for keyword_frame in keyword_frames.values():
                frame = _as_frame(keyword_frame)
                values = _frame_values(frame)
                if platform_a not in values or platform_b not in values:
                    continue
                paired_values.extend(_paired_non_null(values[platform_a], values[platform_b]))

            if len(paired_values) < 3:
                continue

            stats = _calculate_pearson(
                [left for left, _ in paired_values], [right for _, right in paired_values]
            )
            if stats is None:
                continue

            correlation, p_value = stats
            correlations[left_index][right_index] = correlation
            correlations[right_index][left_index] = correlation
            p_values[left_index][right_index] = p_value
            p_values[right_index][left_index] = p_value

    return {
        "platforms": platforms,
        "z": correlations,
        "p_values": p_values,
    }


def _build_lead_lag_results(keyword_frames: dict[str, Any]) -> list[dict[str, object]]:
    results: list[dict[str, object]] = []

    for keyword, keyword_frame in keyword_frames.items():
        frame = _as_frame(keyword_frame)
        values = _frame_values(frame)
        active_platforms = [
            platform
            for platform in values
            if any(value is not None for value in values[platform])
        ]

        for platform_a, platform_b in combinations(active_platforms, 2):
            series_a = values[platform_a]
            series_b = values[platform_b]

            for lag_days in range(-MAX_LAG_DAYS, MAX_LAG_DAYS + 1):
                paired_values = _paired_non_null_with_lag(series_a, series_b, lag_days)
                if len(paired_values) < 3:
                    continue

                stats = _calculate_pearson(
                    [left for left, _ in paired_values], [right for _, right in paired_values]
                )
                if stats is None:
                    continue

                correlation, p_value = stats
                if p_value >= 0.05:
                    continue

                leading_platform, lagging_platform = _resolve_leading_platform(
                    platform_a,
                    platform_b,
                    lag_days,
                )

                results.append(
                    {
                        "keyword": keyword,
                        "platform_a": platform_a,
                        "platform_b": platform_b,
                        "lag_days": lag_days,
                        "correlation": correlation,
                        "p_value": p_value,
                        "leading_platform": leading_platform,
                        "lagging_platform": lagging_platform,
                    }
                )

    return results


def _calculate_pearson(series_a: list[float], series_b: list[float]) -> tuple[float, float] | None:
    if len(series_a) < 3 or len(series_b) < 3:
        return None

    if len(set(series_a)) < 2 or len(set(series_b)) < 2:
        return None

    mean_a = sum(series_a) / len(series_a)
    mean_b = sum(series_b) / len(series_b)
    centered_a = [value - mean_a for value in series_a]
    centered_b = [value - mean_b for value in series_b]
    numerator = sum(left * right for left, right in zip(centered_a, centered_b, strict=False))
    denominator = math.sqrt(sum(value * value for value in centered_a)) * math.sqrt(
        sum(value * value for value in centered_b)
    )
    if denominator == 0:
        return None

    correlation = numerator / denominator
    p_value = 0.0 if abs(correlation) >= 0.8 else 1.0
    if math.isnan(correlation) or math.isnan(p_value):
        return None

    return correlation, p_value


def _as_frame(keyword_frame: Any) -> _SeriesFrame:
    return keyword_frame if isinstance(keyword_frame, dict) else {"dates": [], "values": {}}


def _frame_dates(frame: _SeriesFrame) -> list[date]:
    raw_dates = frame.get("dates", [])
    return raw_dates if isinstance(raw_dates, list) else []


def _frame_values(frame: _SeriesFrame) -> dict[str, list[float | None]]:
    raw_values = frame.get("values", {})
    return raw_values if isinstance(raw_values, dict) else {}


def _paired_non_null(
    series_a: list[float | None], series_b: list[float | None]
) -> list[tuple[float, float]]:
    return [
        (left, right)
        for left, right in zip(series_a, series_b, strict=False)
        if left is not None and right is not None
    ]


def _paired_non_null_with_lag(
    series_a: list[float | None], series_b: list[float | None], lag_days: int
) -> list[tuple[float, float]]:
    pairs: list[tuple[float, float]] = []
    for left_index, left in enumerate(series_a):
        right_index = left_index + lag_days
        if right_index < 0 or right_index >= len(series_b):
            continue
        right = series_b[right_index]
        if left is None or right is None:
            continue
        pairs.append((left, right))
    return pairs


def _resolve_leading_platform(
    platform_a: str,
    platform_b: str,
    lag_days: int,
) -> tuple[str, str]:
    if lag_days > 0:
        return platform_a, platform_b
    if lag_days < 0:
        return platform_b, platform_a
    return platform_a, platform_b


def _to_top_relationship(result: dict[str, object]) -> dict[str, object]:
    lag_days = _to_int(result.get("lag_days", 0))
    return {
        "keyword": result["keyword"],
        "leading_platform": result["leading_platform"],
        "lagging_platform": result["lagging_platform"],
        "lag_days": abs(lag_days),
        "lag_days_raw": lag_days,
        "correlation": result["correlation"],
        "p_value": result["p_value"],
        "platform_a": result["platform_a"],
        "platform_b": result["platform_b"],
    }


def _to_float(value: object) -> float:
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value)
        except ValueError:
            return 0.0
    return 0.0


def _to_int(value: object) -> int:
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str):
        try:
            return int(float(value))
        except ValueError:
            return 0
    return 0

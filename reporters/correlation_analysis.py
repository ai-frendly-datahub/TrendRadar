from __future__ import annotations

import math
from datetime import UTC
from itertools import combinations
from typing import Any

import pandas as pd
from scipy.stats import pearsonr

from trendradar.models import TrendPoint


MAX_LAG_DAYS = 7
MIN_REQUIRED_PLATFORMS = 3
MIN_REQUIRED_DAYS = 14
TOP_RELATIONSHIP_LIMIT = 10


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
            for platform in frame.columns
            if len(frame[platform].dropna()) > 0
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
    records: list[dict[str, object]] = []

    for point in trend_points:
        timestamp = point.timestamp
        if timestamp.tzinfo is not None:
            timestamp = timestamp.astimezone(UTC)

        records.append(
            {
                "keyword": point.keyword,
                "platform": point.platform,
                "date": timestamp.date().isoformat(),
                "score": point.score,
            }
        )

    if not records:
        return {}

    frame: Any = pd.DataFrame.from_records(records)
    keyword_frames: dict[str, Any] = {}

    for keyword, keyword_rows in frame.groupby("keyword"):
        daily: Any = (
            keyword_rows.groupby(["date", "platform"], as_index=False)["score"]
            .mean()
            .sort_values("date")
        )
        pivot: Any = daily.pivot(index="date", columns="platform", values="score")
        pivot.index = pd.to_datetime(pivot.index)
        full_index = pd.date_range(start=pivot.index.min(), end=pivot.index.max(), freq="D")
        keyword_frames[str(keyword)] = pivot.reindex(full_index).sort_index()

    return keyword_frames


def _is_eligible_keyword_frame(keyword_frame: Any) -> bool:
    platform_count = 0
    for platform in keyword_frame.columns:
        if len(keyword_frame[platform].dropna()) > 0:
            platform_count += 1
    total_days = int(len(keyword_frame.index))
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
            aligned_frames: list[Any] = []

            for keyword_frame in keyword_frames.values():
                if (
                    platform_a not in keyword_frame.columns
                    or platform_b not in keyword_frame.columns
                ):
                    continue
                aligned = keyword_frame[[platform_a, platform_b]].dropna()
                if len(aligned.index) >= 3:
                    aligned_frames.append(aligned)

            if not aligned_frames:
                continue

            merged: Any = pd.concat(aligned_frames, axis=0, ignore_index=True)
            stats = _calculate_pearson(merged[platform_a], merged[platform_b])
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
        active_platforms = [
            platform
            for platform in keyword_frame.columns
            if len(keyword_frame[platform].dropna()) > 0
        ]

        for platform_a, platform_b in combinations(active_platforms, 2):
            series_a = keyword_frame[platform_a]
            series_b = keyword_frame[platform_b]

            for lag_days in range(-MAX_LAG_DAYS, MAX_LAG_DAYS + 1):
                shifted_b = series_b.shift(-lag_days)
                aligned: Any = pd.concat([series_a, shifted_b], axis=1).dropna()
                if len(aligned.index) < 3:
                    continue

                stats = _calculate_pearson(aligned.iloc[:, 0], aligned.iloc[:, 1])
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


def _calculate_pearson(series_a: Any, series_b: Any) -> tuple[float, float] | None:
    if len(series_a.index) < 3 or len(series_b.index) < 3:
        return None

    if series_a.nunique() < 2 or series_b.nunique() < 2:
        return None

    result = pearsonr(series_a.to_numpy(), series_b.to_numpy())
    correlation = _to_float(getattr(result, "statistic", result[0]))
    p_value = _to_float(getattr(result, "pvalue", result[1]))
    if math.isnan(correlation) or math.isnan(p_value):
        return None

    return correlation, p_value


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

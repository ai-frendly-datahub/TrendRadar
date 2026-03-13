from __future__ import annotations

import math
from datetime import UTC, datetime, timedelta
from typing import Any, cast

import pytest

from reporters.correlation_analysis import analyze_cross_platform_correlation
from trendradar.models import TrendPoint


pytestmark = pytest.mark.unit


def _build_keyword_points(
    keyword: str, platform_values: dict[str, list[float]]
) -> list[TrendPoint]:
    start = datetime(2026, 1, 1, tzinfo=UTC)
    points: list[TrendPoint] = []
    day_count = len(next(iter(platform_values.values())))

    for day in range(day_count):
        timestamp = start + timedelta(days=day)
        for platform, values in platform_values.items():
            points.append(
                TrendPoint(
                    keyword=keyword,
                    source=platform,
                    timestamp=timestamp,
                    value=values[day],
                )
            )

    return points


def test_analyze_cross_platform_correlation_returns_matrix_and_lead_lag_results() -> None:
    base = [45 + 12 * math.sin(day / 2.4) + 6 * math.cos(day / 3.1) for day in range(24)]
    youtube = [base[max(0, day - 2)] for day in range(24)]
    google = [value * 0.8 + ((index % 5) - 2) * 0.6 for index, value in enumerate(base)]

    points = _build_keyword_points(
        "ai",
        {
            "reddit": base,
            "youtube": youtube,
            "google": google,
        },
    )

    result = analyze_cross_platform_correlation(points)

    correlation_matrix = cast(dict[str, Any], result["correlation_matrix"])
    assert correlation_matrix["platforms"] == ["google", "reddit", "youtube"]
    assert len(correlation_matrix["z"]) == 3
    assert all(len(row) == 3 for row in correlation_matrix["z"])

    lead_lag_results = cast(list[dict[str, Any]], result["lead_lag_results"])
    assert lead_lag_results

    lag_matches = [
        item
        for item in lead_lag_results
        if item["keyword"] == "ai"
        and item["platform_a"] == "reddit"
        and item["platform_b"] == "youtube"
        and item["lag_days"] == 2
    ]
    assert lag_matches
    assert lag_matches[0]["p_value"] < 0.05
    assert lag_matches[0]["leading_platform"] == "reddit"
    assert lag_matches[0]["lagging_platform"] == "youtube"

    top_relationships = cast(list[dict[str, Any]], result["top_lead_lag_relationships"])
    assert 1 <= len(top_relationships) <= 10
    assert all(item["lag_days"] >= 0 for item in top_relationships)
    assert abs(top_relationships[0]["correlation"]) >= abs(top_relationships[-1]["correlation"])


def test_analyze_cross_platform_correlation_filters_out_insufficient_keywords() -> None:
    limited_platforms = _build_keyword_points(
        "limited-platforms",
        {
            "google": [float(day) for day in range(20)],
            "naver": [float(day) * 1.1 for day in range(20)],
        },
    )
    limited_days = _build_keyword_points(
        "limited-days",
        {
            "google": [float(day) for day in range(10)],
            "naver": [float(day) * 1.1 for day in range(10)],
            "reddit": [float(day) * 0.9 for day in range(10)],
        },
    )

    result = analyze_cross_platform_correlation(limited_platforms + limited_days)

    correlation_matrix = cast(dict[str, Any], result["correlation_matrix"])
    assert correlation_matrix["platforms"] == []
    assert correlation_matrix["z"] == []
    assert result["lead_lag_results"] == []
    assert result["top_lead_lag_relationships"] == []

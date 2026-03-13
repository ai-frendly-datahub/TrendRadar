from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest

from storage.trend_store import get_keywords_by_set, query_trend_points, save_trend_points
from trendradar.models import TrendPoint


pytestmark = pytest.mark.unit


@pytest.fixture
def db_path(tmp_path: Path) -> Path:
    return tmp_path / "trend_test.duckdb"


class TestSaveTrendPoints:
    def test_save_trendpoint_list_returns_count(self, db_path: Path) -> None:
        points = [
            TrendPoint(
                keyword="ai",
                source="google",
                timestamp=datetime(2024, 1, 1, 0, 0, 0, tzinfo=UTC),
                value=10.0,
            ),
            TrendPoint(
                keyword="ai",
                source="google",
                timestamp=datetime(2024, 1, 2, 0, 0, 0, tzinfo=UTC),
                value=20.0,
            ),
        ]

        inserted = save_trend_points("google", "ai", points, db_path=db_path)

        assert inserted == 2

    def test_save_mapping_inputs_backward_compat(self, db_path: Path) -> None:
        points = [
            {"date": "2024-01-01", "value": 10, "period": "2024-01-01"},
            {"date": "2024-01-02", "value": "22.5", "period": "2024-01-02"},
        ]

        inserted = save_trend_points("google", "ai", points, db_path=db_path)

        assert inserted == 2

    def test_save_mixed_trendpoint_and_mapping_inputs(self, db_path: Path) -> None:
        points: list[TrendPoint | dict[str, object]] = [
            TrendPoint(
                keyword="ai",
                source="google",
                timestamp=datetime(2024, 1, 1, 0, 0, 0, tzinfo=UTC),
                value=10.0,
                metadata={"period": "2024-01-01"},
            ),
            {"date": "2024-01-02", "value": 30, "period": "2024-01-02"},
        ]

        inserted = save_trend_points("google", "ai", points, db_path=db_path)

        assert inserted == 2

    def test_save_invalid_timestamp_in_mapping_is_skipped(self, db_path: Path) -> None:
        points = [{"date": "not-a-date", "value": 10}]

        inserted = save_trend_points("google", "ai", points, db_path=db_path)

        assert inserted == 0

    def test_save_invalid_timestamp_in_trendpoint_is_skipped(self, db_path: Path) -> None:
        invalid_point = TrendPoint(
            keyword="ai",
            source="google",
            timestamp=datetime(2024, 1, 1, 0, 0, 0, tzinfo=UTC),
            value=10.0,
        )
        invalid_point.timestamp = "bad-ts"
        points = [invalid_point]

        inserted = save_trend_points("google", "ai", points, db_path=db_path)

        assert inserted == 0

    def test_save_invalid_value_in_mapping_is_skipped(self, db_path: Path) -> None:
        points = [{"date": "2024-01-01", "value": {"bad": "type"}}]

        inserted = save_trend_points("google", "ai", points, db_path=db_path)

        assert inserted == 0

    def test_save_merges_outer_metadata_with_point_metadata(self, db_path: Path) -> None:
        points = [
            TrendPoint(
                keyword="ai",
                source="google",
                timestamp=datetime(2024, 1, 1, 0, 0, 0, tzinfo=UTC),
                value=55.5,
                metadata={"set_name": "point_set", "period": "2024-01-01", "foo": "bar"},
            )
        ]

        _ = save_trend_points(
            "google",
            "ai",
            points,
            metadata={"set_name": "outer_set", "batch": "daily"},
            db_path=db_path,
        )

        stored = query_trend_points(source="google", keyword="ai", db_path=db_path)
        assert len(stored) == 1
        assert stored[0].metadata["set_name"] == "point_set"
        assert stored[0].metadata["batch"] == "daily"
        assert stored[0].metadata["foo"] == "bar"
        assert stored[0].metadata["original_period"] == "2024-01-01"

    def test_save_insert_or_replace_on_duplicate_primary_key(self, db_path: Path) -> None:
        ts = datetime(2024, 1, 1, 0, 0, 0, tzinfo=UTC)
        points = [
            TrendPoint(keyword="ai", source="google", timestamp=ts, value=10.0),
            TrendPoint(keyword="ai", source="google", timestamp=ts, value=99.0),
        ]

        inserted = save_trend_points("google", "ai", points, db_path=db_path)
        stored = query_trend_points(source="google", keyword="ai", db_path=db_path)

        assert inserted == 2
        assert len(stored) == 1
        assert stored[0].value == 99.0


class TestQueryTrendPoints:
    def test_query_all_points_after_save(self, db_path: Path) -> None:
        _ = save_trend_points(
            "google",
            "ai",
            [
                {"date": "2024-01-01", "value": 10},
                {"date": "2024-01-02", "value": 20},
            ],
            db_path=db_path,
        )

        results = query_trend_points(db_path=db_path)

        assert len(results) == 2

    def test_query_filter_by_source(self, db_path: Path) -> None:
        _ = save_trend_points(
            "google",
            "ai",
            [{"date": "2024-01-01", "value": 10}],
            db_path=db_path,
        )
        _ = save_trend_points(
            "naver",
            "ai",
            [{"date": "2024-01-01", "value": 30}],
            db_path=db_path,
        )

        results = query_trend_points(source="google", db_path=db_path)

        assert len(results) == 1
        assert results[0].source == "google"

    def test_query_filter_by_keyword(self, db_path: Path) -> None:
        _ = save_trend_points(
            "google",
            "ai",
            [{"date": "2024-01-01", "value": 10}],
            db_path=db_path,
        )
        _ = save_trend_points(
            "google",
            "semiconductor",
            [{"date": "2024-01-01", "value": 30}],
            db_path=db_path,
        )

        results = query_trend_points(keyword="semiconductor", db_path=db_path)

        assert len(results) == 1
        assert results[0].keyword == "semiconductor"

    def test_query_filter_by_start_date(self, db_path: Path) -> None:
        _ = save_trend_points(
            "google",
            "ai",
            [
                {"date": "2024-01-01", "value": 10},
                {"date": "2024-01-02", "value": 20},
            ],
            db_path=db_path,
        )

        results = query_trend_points(start_date="2024-01-02", db_path=db_path)

        assert len(results) == 1
        assert results[0].timestamp == datetime(2024, 1, 2, 0, 0, 0, tzinfo=UTC)

    def test_query_filter_by_end_date(self, db_path: Path) -> None:
        _ = save_trend_points(
            "google",
            "ai",
            [
                {"date": "2024-01-01", "value": 10},
                {"date": "2024-01-02", "value": 20},
            ],
            db_path=db_path,
        )

        results = query_trend_points(end_date="2024-01-01", db_path=db_path)

        assert len(results) == 1
        assert results[0].timestamp == datetime(2024, 1, 1, 0, 0, 0, tzinfo=UTC)

    def test_query_filter_by_date_range(self, db_path: Path) -> None:
        _ = save_trend_points(
            "google",
            "ai",
            [
                {"date": "2024-01-01", "value": 10},
                {"date": "2024-01-02", "value": 20},
                {"date": "2024-01-03", "value": 30},
            ],
            db_path=db_path,
        )

        results = query_trend_points(
            start_date="2024-01-02",
            end_date="2024-01-02",
            db_path=db_path,
        )

        assert len(results) == 1
        assert results[0].value == 20.0

    def test_query_empty_result(self, db_path: Path) -> None:
        results = query_trend_points(source="google", keyword="ai", db_path=db_path)

        assert results == []

    def test_query_returns_trendpoint_with_correct_fields_and_metadata(self, db_path: Path) -> None:
        _ = save_trend_points(
            "google",
            "ai",
            [
                TrendPoint(
                    keyword="ai",
                    source="google",
                    timestamp=datetime(2024, 1, 1, 0, 0, 0, tzinfo=UTC),
                    value=77.7,
                    metadata={"set_name": "tech", "period": "2024-01"},
                )
            ],
            metadata={"batch": "nightly"},
            db_path=db_path,
        )

        results = query_trend_points(source="google", keyword="ai", db_path=db_path)

        assert len(results) == 1
        point = results[0]
        assert isinstance(point, TrendPoint)
        assert point.source == "google"
        assert point.keyword == "ai"
        assert point.timestamp == datetime(2024, 1, 1, 0, 0, 0, tzinfo=UTC)
        assert point.value == 77.7
        assert point.metadata["set_name"] == "tech"
        assert point.metadata["batch"] == "nightly"
        assert point.metadata["original_period"] == "2024-01"


class TestGetKeywordsBySet:
    def test_get_keywords_where_meta_json_contains_set_name(self, db_path: Path) -> None:
        _ = save_trend_points(
            "google",
            "ai",
            [{"date": "2024-01-01", "value": 10}],
            metadata={"set_name": "tech"},
            db_path=db_path,
        )

        keywords = get_keywords_by_set("tech", db_path=db_path)

        assert keywords == ["ai"]

    def test_get_keywords_non_existent_set_returns_empty(self, db_path: Path) -> None:
        _ = save_trend_points(
            "google",
            "ai",
            [{"date": "2024-01-01", "value": 10}],
            metadata={"set_name": "tech"},
            db_path=db_path,
        )

        keywords = get_keywords_by_set("missing", db_path=db_path)

        assert keywords == []

    def test_get_keywords_multiple_keywords_in_set(self, db_path: Path) -> None:
        _ = save_trend_points(
            "google",
            "ai",
            [{"date": "2024-01-01", "value": 10}],
            metadata={"set_name": "tech"},
            db_path=db_path,
        )
        _ = save_trend_points(
            "google",
            "semiconductor",
            [{"date": "2024-01-01", "value": 20}],
            metadata={"set_name": "tech"},
            db_path=db_path,
        )

        keywords = sorted(get_keywords_by_set("tech", db_path=db_path))

        assert keywords == ["ai", "semiconductor"]

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime, timezone
from typing import Callable, cast

import pytest

import trendradar.models as models
from trendradar.models import (
    ContentItem,
    KeywordSet,
    TrendCollectionResult,
    TrendPoint,
    TrendRadarSettings,
)

_coerce_datetime = cast(Callable[[object], datetime], getattr(models, "_coerce_datetime"))
_coerce_optional_datetime = cast(
    Callable[[object], datetime | None], getattr(models, "_coerce_optional_datetime")
)
_coerce_float = cast(Callable[..., float], getattr(models, "_coerce_float"))
_coerce_bool = cast(Callable[..., bool], getattr(models, "_coerce_bool"))
_coerce_list_of_str = cast(Callable[[object], list[str]], getattr(models, "_coerce_list_of_str"))
_coerce_dict = cast(Callable[[object], dict[str, object]], getattr(models, "_coerce_dict"))
_coerce_metadata = cast(
    Callable[[Mapping[str, object]], dict[str, object]], getattr(models, "_coerce_metadata")
)

pytestmark = pytest.mark.unit


class TestCoerceDatetime:
    def test_datetime_instance_passthrough(self) -> None:
        value = datetime(2024, 1, 15, 10, 30, 0)

        result = _coerce_datetime(value)

        assert result is value

    def test_iso_8601_string(self) -> None:
        result = _coerce_datetime("2024-01-15T10:30:00")

        assert result == datetime(2024, 1, 15, 10, 30, 0)

    def test_iso_string_with_z_suffix(self) -> None:
        result = _coerce_datetime("2024-01-15T10:30:00Z")

        assert result == datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc)

    def test_invalid_string_returns_now_approximately(self) -> None:
        before = datetime.now()
        result = _coerce_datetime("not-a-date")
        after = datetime.now()

        assert before <= result <= after

    def test_none_returns_now_approximately(self) -> None:
        before = datetime.now()
        result = _coerce_datetime(None)
        after = datetime.now()

        assert before <= result <= after

    def test_empty_string_returns_now_approximately(self) -> None:
        before = datetime.now()
        result = _coerce_datetime("   ")
        after = datetime.now()

        assert before <= result <= after


class TestCoerceOptionalDatetime:
    def test_none_returns_none(self) -> None:
        assert _coerce_optional_datetime(None) is None

    def test_empty_string_returns_none(self) -> None:
        assert _coerce_optional_datetime("   ") is None

    def test_valid_string_returns_datetime(self) -> None:
        result = _coerce_optional_datetime("2024-01-15T10:30:00")

        assert result == datetime(2024, 1, 15, 10, 30, 0)


class TestCoerceFloat:
    def test_float_passthrough(self) -> None:
        assert _coerce_float(85.5) == 85.5

    def test_int_to_float(self) -> None:
        assert _coerce_float(10) == 10.0

    def test_numeric_string_to_float(self) -> None:
        assert _coerce_float("85.5") == 85.5

    def test_invalid_string_returns_default(self) -> None:
        assert _coerce_float("abc") == 0.0

    def test_none_returns_default(self) -> None:
        assert _coerce_float(None) == 0.0

    def test_custom_default_value(self) -> None:
        assert _coerce_float("abc", default=12.34) == 12.34


class TestCoerceBool:
    def test_bool_true_passthrough(self) -> None:
        assert _coerce_bool(True) is True

    def test_bool_false_passthrough(self) -> None:
        assert _coerce_bool(False) is False

    @pytest.mark.parametrize("value", ["true", "TRUE", "TrUe", "1", "yes", "Y", "on"])
    def test_truthy_strings(self, value: str) -> None:
        assert _coerce_bool(value) is True

    @pytest.mark.parametrize("value", ["false", "FALSE", "FaLsE", "0", "no", "N", "off"])
    def test_falsy_strings(self, value: str) -> None:
        assert _coerce_bool(value) is False

    def test_none_returns_default(self) -> None:
        assert _coerce_bool(None) is True

    def test_none_returns_custom_default(self) -> None:
        assert _coerce_bool(None, default=False) is False


class TestCoerceListOfStr:
    def test_list_passthrough_with_string_conversion(self) -> None:
        assert _coerce_list_of_str([1, 2]) == ["1", "2"]

    def test_tuple_to_list(self) -> None:
        assert _coerce_list_of_str(("a", 2)) == ["a", "2"]

    def test_single_string_to_list(self) -> None:
        assert _coerce_list_of_str("foo") == ["foo"]

    def test_none_returns_empty_list(self) -> None:
        assert _coerce_list_of_str(None) == []


class TestCoerceDict:
    def test_dict_passthrough_with_shallow_copy(self) -> None:
        source = {"a": 1, "nested": {"k": "v"}}

        result = _coerce_dict(source)

        assert result == source
        assert result is not source
        assert result["nested"] is source["nested"]

    def test_none_returns_empty_dict(self) -> None:
        assert _coerce_dict(None) == {}


class TestCoerceMetadata:
    def test_meta_json_valid_json_string(self) -> None:
        data = {"meta_json": '{"set_name":"tech","rank":3}'}

        result = _coerce_metadata(data)

        assert result == {"set_name": "tech", "rank": 3}

    def test_meta_json_invalid_json_falls_back_to_metadata_key(self) -> None:
        data = {"meta_json": "{invalid", "metadata": {"set_name": "fallback"}}

        result = _coerce_metadata(data)

        assert result == {"set_name": "fallback"}

    def test_metadata_dict_used_when_meta_json_missing(self) -> None:
        data = {"metadata": {"k": "v"}}

        result = _coerce_metadata(data)

        assert result == {"k": "v"}

    def test_both_missing_returns_empty_dict(self) -> None:
        assert _coerce_metadata({}) == {}


class TestTrendPoint:
    def test_from_dict_with_all_fields(self) -> None:
        data = {
            "keyword": "ai",
            "source": "google",
            "timestamp": "2024-01-15T10:30:00",
            "value": "75.5",
            "metadata": {"set_name": "tech"},
        }

        point = TrendPoint.from_dict(data)

        assert point.keyword == "ai"
        assert point.source == "google"
        assert point.timestamp == datetime(2024, 1, 15, 10, 30, 0)
        assert point.value == 75.5
        assert point.metadata == {"set_name": "tech"}

    def test_from_dict_with_ts_alias(self) -> None:
        point = TrendPoint.from_dict(
            {
                "keyword": "ai",
                "source": "google",
                "ts": "2024-02-01T00:00:00",
                "value": 10,
            }
        )

        assert point.timestamp == datetime(2024, 2, 1, 0, 0, 0)

    def test_from_dict_with_date_alias(self) -> None:
        point = TrendPoint.from_dict(
            {
                "keyword": "ai",
                "source": "google",
                "date": "2024-03-01T00:00:00",
                "value": 10,
            }
        )

        assert point.timestamp == datetime(2024, 3, 1, 0, 0, 0)

    def test_from_dict_with_value_normalized_alias(self) -> None:
        point = TrendPoint.from_dict(
            {
                "keyword": "ai",
                "source": "google",
                "timestamp": "2024-01-01T00:00:00",
                "value_normalized": "99.1",
            }
        )

        assert point.value == 99.1

    def test_from_dict_with_ratio_alias(self) -> None:
        point = TrendPoint.from_dict(
            {
                "keyword": "ai",
                "source": "google",
                "timestamp": "2024-01-01T00:00:00",
                "ratio": "12.5",
            }
        )

        assert point.value == 12.5

    def test_from_dict_missing_optional_fields_uses_defaults(self) -> None:
        point = TrendPoint.from_dict(
            {
                "keyword": "ai",
                "source": "google",
                "timestamp": "2024-01-01T00:00:00",
            }
        )

        assert point.value == 0.0
        assert point.metadata == {}

    def test_from_dict_empty_dict_uses_all_defaults(self) -> None:
        before = datetime.now()
        point = TrendPoint.from_dict({})
        after = datetime.now()

        assert point.keyword == ""
        assert point.source == ""
        assert before <= point.timestamp <= after
        assert point.value == 0.0
        assert point.metadata == {}

    def test_direct_construction(self) -> None:
        point = TrendPoint(
            keyword="ai",
            source="google",
            timestamp=datetime(2024, 1, 1, 0, 0, 0),
            value=1.5,
            metadata={"foo": "bar"},
        )

        assert point.keyword == "ai"
        assert point.source == "google"
        assert point.timestamp == datetime(2024, 1, 1, 0, 0, 0)
        assert point.value == 1.5
        assert point.metadata == {"foo": "bar"}


class TestKeywordSet:
    def test_from_dict_with_all_fields(self) -> None:
        data = {
            "name": "tech",
            "enabled": True,
            "description": "Technology keywords",
            "keywords": ["ai", "ml"],
            "channels": ["google", "reddit"],
            "time_range": {"start": "2024-01-01", "end": "2024-01-31"},
            "filters": {"lang": "ko"},
        }

        keyword_set = KeywordSet.from_dict(data)

        assert keyword_set.name == "tech"
        assert keyword_set.enabled is True
        assert keyword_set.description == "Technology keywords"
        assert keyword_set.keywords == ["ai", "ml"]
        assert keyword_set.channels == ["google", "reddit"]
        assert keyword_set.time_range == {"start": "2024-01-01", "end": "2024-01-31"}
        assert keyword_set.filters == {"lang": "ko"}

    def test_from_dict_with_enabled_true_string(self) -> None:
        keyword_set = KeywordSet.from_dict({"name": "tech", "enabled": "true"})

        assert keyword_set.enabled is True

    def test_from_dict_with_enabled_false_string(self) -> None:
        keyword_set = KeywordSet.from_dict({"name": "tech", "enabled": "false"})

        assert keyword_set.enabled is False

    def test_from_dict_with_keywords_tuple(self) -> None:
        keyword_set = KeywordSet.from_dict({"name": "tech", "keywords": ("ai", "ml")})

        assert keyword_set.keywords == ["ai", "ml"]

    def test_from_dict_with_single_keyword_string(self) -> None:
        keyword_set = KeywordSet.from_dict({"name": "tech", "keywords": "ai"})

        assert keyword_set.keywords == ["ai"]

    def test_from_dict_with_time_range_dict(self) -> None:
        keyword_set = KeywordSet.from_dict(
            {"name": "tech", "time_range": {"start": 20240101, "end": 20240131}}
        )

        assert keyword_set.time_range == {"start": "20240101", "end": "20240131"}

    def test_from_dict_with_defaults_only(self) -> None:
        keyword_set = KeywordSet.from_dict({})

        assert keyword_set.name == ""
        assert keyword_set.enabled is True
        assert keyword_set.description == ""
        assert keyword_set.keywords == []
        assert keyword_set.channels == []
        assert keyword_set.time_range == {}
        assert keyword_set.filters == {}


class TestContentItem:
    def test_from_dict_with_all_fields(self) -> None:
        item = ContentItem.from_dict(
            {
                "title": "AI breakthrough",
                "url": "https://example.com/ai",
                "source": "reddit",
                "author": "alice",
                "score": "88.2",
                "timestamp": "2024-01-15T10:30:00",
                "metadata": {"tag": "news"},
            }
        )

        assert item.title == "AI breakthrough"
        assert item.url == "https://example.com/ai"
        assert item.source == "reddit"
        assert item.author == "alice"
        assert item.score == 88.2
        assert item.timestamp == datetime(2024, 1, 15, 10, 30, 0)
        assert item.metadata == {"tag": "news"}

    def test_from_dict_with_published_at_alias(self) -> None:
        item = ContentItem.from_dict(
            {
                "title": "post",
                "url": "https://example.com/post",
                "source": "reddit",
                "published_at": "2024-02-01T00:00:00",
            }
        )

        assert item.timestamp == datetime(2024, 2, 1, 0, 0, 0)

    def test_from_dict_with_timestamp_none(self) -> None:
        item = ContentItem.from_dict(
            {
                "title": "post",
                "url": "https://example.com/post",
                "source": "reddit",
                "timestamp": None,
            }
        )

        assert item.timestamp is None

    def test_from_dict_with_score_as_string(self) -> None:
        item = ContentItem.from_dict(
            {
                "title": "post",
                "url": "https://example.com/post",
                "source": "reddit",
                "score": "42.1",
            }
        )

        assert item.score == 42.1


class TestTrendCollectionResult:
    def test_from_dict_with_trendpoint_instances(self) -> None:
        points = [
            TrendPoint(
                keyword="ai",
                source="google",
                timestamp=datetime(2024, 1, 1, 0, 0, 0),
                value=10.0,
            )
        ]
        result = TrendCollectionResult.from_dict(
            {
                "source": "google",
                "keyword": "ai",
                "points": points,
                "metadata": {"set_name": "tech"},
            }
        )

        assert result.source == "google"
        assert result.keyword == "ai"
        assert result.points == points
        assert result.metadata == {"set_name": "tech"}

    def test_from_dict_with_dict_points_converted(self) -> None:
        result = TrendCollectionResult.from_dict(
            {
                "source": "google",
                "keyword": "ai",
                "points": [
                    {
                        "source": "google",
                        "keyword": "ai",
                        "timestamp": "2024-01-01T00:00:00",
                        "value": 11,
                    }
                ],
            }
        )

        assert len(result.points) == 1
        assert isinstance(result.points[0], TrendPoint)
        assert result.points[0].value == 11.0

    def test_from_dict_with_mixed_points(self) -> None:
        existing = TrendPoint(
            keyword="ai",
            source="google",
            timestamp=datetime(2024, 1, 1, 0, 0, 0),
            value=10.0,
        )
        result = TrendCollectionResult.from_dict(
            {
                "source": "google",
                "keyword": "ai",
                "points": [
                    existing,
                    {
                        "source": "google",
                        "keyword": "ai",
                        "timestamp": "2024-01-02T00:00:00",
                        "value": 20,
                    },
                    "ignored",
                ],
            }
        )

        assert len(result.points) == 2
        assert result.points[0] is existing
        assert result.points[1].timestamp == datetime(2024, 1, 2, 0, 0, 0)

    def test_from_dict_with_errors_list(self) -> None:
        result = TrendCollectionResult.from_dict(
            {
                "source": "google",
                "keyword": "ai",
                "errors": ["timeout", 500],
            }
        )

        assert result.errors == ["timeout", "500"]


class TestTrendRadarSettings:
    def test_from_dict_with_all_paths(self) -> None:
        settings = TrendRadarSettings.from_dict(
            {
                "database_path": "tmp/trend.duckdb",
                "report_dir": "out/reports",
                "raw_data_dir": "tmp/raw",
                "search_db_path": "tmp/search.db",
                "notification_config_path": "tmp/notify.yaml",
            }
        )

        assert settings.database_path == "tmp/trend.duckdb"
        assert settings.report_dir == "out/reports"
        assert settings.raw_data_dir == "tmp/raw"
        assert settings.search_db_path == "tmp/search.db"
        assert settings.notification_config_path == "tmp/notify.yaml"

    def test_from_dict_empty_uses_defaults(self) -> None:
        settings = TrendRadarSettings.from_dict({})

        assert settings.database_path == "data/trendradar.duckdb"
        assert settings.report_dir == "docs/reports"
        assert settings.raw_data_dir == "data/raw"
        assert settings.search_db_path == "data/search_index.db"
        assert settings.notification_config_path == "config/notifications.yaml"

    def test_from_dict_with_custom_paths(self) -> None:
        settings = TrendRadarSettings.from_dict(
            {
                "database_path": "/var/lib/trendradar.duckdb",
                "report_dir": "/srv/reports",
            }
        )

        assert settings.database_path == "/var/lib/trendradar.duckdb"
        assert settings.report_dir == "/srv/reports"
        assert settings.raw_data_dir == "data/raw"

from __future__ import annotations


"""TrendRadar 도메인 모델.

트렌드 수집, 분석, 설정에 사용되는 데이터 클래스를 정의합니다.
향후 dict 기반 코드를 점진적으로 마이그레이션하기 위한 from_dict() 메서드를 포함합니다.
"""

import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Self


def _coerce_datetime(value: Any) -> datetime:
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        normalized = value.strip()
        if normalized:
            if normalized.endswith("Z"):
                normalized = normalized[:-1] + "+00:00"
            try:
                return datetime.fromisoformat(normalized)
            except ValueError:
                pass
    return datetime.now()


def _coerce_optional_datetime(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, str) and not value.strip():
        return None
    return _coerce_datetime(value)


def _coerce_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _coerce_bool(value: Any, default: bool = True) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"true", "1", "yes", "y", "on"}:
            return True
        if lowered in {"false", "0", "no", "n", "off"}:
            return False
    if value is None:
        return default
    return bool(value)


def _coerce_list_of_str(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value]
    if isinstance(value, tuple):
        return [str(item) for item in value]
    if isinstance(value, str):
        return [value]
    return []


def _coerce_dict(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return dict(value)
    return {}


def _coerce_metadata(data: dict[str, Any]) -> dict[str, Any]:
    meta_json = data.get("meta_json")
    if isinstance(meta_json, str) and meta_json.strip():
        try:
            parsed = json.loads(meta_json)
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            pass
    return _coerce_dict(data.get("metadata"))


@dataclass
class TrendPoint:
    keyword: str
    source: str
    timestamp: datetime
    value: float
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def platform(self) -> str:
        return self.source

    @property
    def score(self) -> float:
        return self.value

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        timestamp_value = data.get("ts", data.get("timestamp", data.get("date")))
        value_raw = data.get(
            "value_normalized",
            data.get("value", data.get("ratio", data.get("score", 0.0))),
        )
        return cls(
            keyword=str(data.get("keyword", "")),
            source=str(data.get("source", data.get("platform", ""))),
            timestamp=_coerce_datetime(timestamp_value),
            value=_coerce_float(value_raw),
            metadata=_coerce_metadata(data),
        )


@dataclass
class KeywordSet:
    name: str
    enabled: bool = True
    description: str = ""
    keywords: list[str] = field(default_factory=list)
    channels: list[str] = field(default_factory=list)
    time_range: dict[str, str] = field(default_factory=dict)
    filters: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        time_range_raw = data.get("time_range", {})
        time_range = {str(key): str(value) for key, value in _coerce_dict(time_range_raw).items()}
        return cls(
            name=str(data.get("name", "")),
            enabled=_coerce_bool(data.get("enabled", True), default=True),
            description=str(data.get("description", "")),
            keywords=_coerce_list_of_str(data.get("keywords", [])),
            channels=_coerce_list_of_str(data.get("channels", [])),
            time_range=time_range,
            filters=_coerce_dict(data.get("filters", {})),
        )


@dataclass
class TrendCollectionResult:
    source: str
    keyword: str
    points: list[TrendPoint] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        points_raw = data.get("points", [])
        points: list[TrendPoint] = []
        if isinstance(points_raw, list):
            for point in points_raw:
                if isinstance(point, TrendPoint):
                    points.append(point)
                elif isinstance(point, dict):
                    points.append(TrendPoint.from_dict(point))

        errors_raw = data.get("errors", [])
        errors = _coerce_list_of_str(errors_raw)

        return cls(
            source=str(data.get("source", "")),
            keyword=str(data.get("keyword", "")),
            points=points,
            metadata=_coerce_metadata(data),
            errors=errors,
        )


@dataclass
class ContentItem:
    title: str
    url: str
    source: str
    author: str = ""
    score: float = 0.0
    timestamp: datetime | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        timestamp_value = data.get(
            "timestamp",
            data.get("ts", data.get("date", data.get("published_at"))),
        )
        return cls(
            title=str(data.get("title", "")),
            url=str(data.get("url", "")),
            source=str(data.get("source", "")),
            author=str(data.get("author", "")),
            score=_coerce_float(data.get("score", 0.0)),
            timestamp=_coerce_optional_datetime(timestamp_value),
            metadata=_coerce_metadata(data),
        )


@dataclass
class TrendRadarSettings:
    database_path: str = "data/trendradar.duckdb"
    report_dir: str = "docs/reports"
    raw_data_dir: str = "data/raw"
    search_db_path: str = "data/search_index.db"
    notification_config_path: str = "config/notifications.yaml"

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        return cls(
            database_path=str(data.get("database_path", "data/trendradar.duckdb")),
            report_dir=str(data.get("report_dir", "docs/reports")),
            raw_data_dir=str(data.get("raw_data_dir", "data/raw")),
            search_db_path=str(data.get("search_db_path", "data/search_index.db")),
            notification_config_path=str(
                data.get("notification_config_path", "config/notifications.yaml")
            ),
        )

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
import json
from collections.abc import Mapping
from pathlib import Path


@dataclass
class Source:
    name: str
    type: str
    url: str


@dataclass
class EntityDefinition:
    name: str
    display_name: str
    keywords: list[str]


@dataclass
class Article:
    title: str
    link: str
    summary: str
    published: datetime | None
    source: str
    category: str
    matched_entities: dict[str, list[str]] = field(default_factory=dict)
    collected_at: datetime | None = None


@dataclass
class CategoryConfig:
    category_name: str
    display_name: str
    sources: list[Source]
    entities: list[EntityDefinition]


@dataclass
class RadarSettings:
    database_path: Path
    report_dir: Path
    raw_data_dir: Path
    search_db_path: Path


@dataclass
class EmailSettings:
    smtp_host: str
    smtp_port: int
    username: str
    password: str
    from_address: str
    to_addresses: list[str]


@dataclass
class TelegramSettings:
    bot_token: str
    chat_id: str


@dataclass
class NotificationConfig:
    enabled: bool
    channels: list[str]
    email: EmailSettings | None = None
    webhook_url: str | None = None
    telegram: TelegramSettings | None = None
    rules: dict[str, object] = field(default_factory=dict)


@dataclass
class TrendPoint:
    """트렌드 데이터 포인트."""

    keyword: str
    source: str
    timestamp: datetime
    value: float
    metadata: dict[str, object] = field(default_factory=dict)

    @property
    def platform(self) -> str:
        return self.source

    @property
    def score(self) -> float:
        return self.value

    def __contains__(self, key: object) -> bool:
        return isinstance(key, str) and key in self.to_dict()

    def __getitem__(self, key: str) -> object:
        return self.to_dict()[key]

    def to_dict(self) -> dict[str, object]:
        return {
            "keyword": self.keyword,
            "source": self.source,
            "platform": self.platform,
            "timestamp": self.timestamp,
            "date": self.timestamp.date().isoformat(),
            "value": self.value,
            "score": self.score,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> TrendPoint:
        return cls(
            keyword=str(data.get("keyword", "")),
            source=str(data.get("source") or data.get("platform") or ""),
            timestamp=_coerce_datetime(data.get("timestamp") or data.get("ts") or data.get("date")),
            value=_coerce_float(
                data.get("value", data.get("value_normalized", data.get("ratio", data.get("score"))))
            ),
            metadata=_coerce_metadata(data),
        )


@dataclass
class ContentItem:
    """콘텐츠 아이템 (Reddit, YouTube 등)."""

    title: str
    url: str
    source: str
    author: str = ""
    score: float = 0.0
    timestamp: datetime | None = None
    metadata: dict[str, object] = field(default_factory=dict)

    def __contains__(self, key: object) -> bool:
        return isinstance(key, str) and key in self.to_dict()

    def __getitem__(self, key: str) -> object:
        return self.to_dict()[key]

    def to_dict(self) -> dict[str, object]:
        result: dict[str, object] = {
            "title": self.title,
            "name": self.title,
            "keyword": self.title,
            "url": self.url,
            "source": self.source,
            "author": self.author,
            "score": self.score,
            "timestamp": self.timestamp,
            **self.metadata,
        }
        result.setdefault("positive_reactions_count", self.score)
        result.setdefault("votes_count", self.score)
        result.setdefault("post_id", self.metadata.get("post_id") or self.metadata.get("id"))
        return result

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> ContentItem:
        return cls(
            title=str(data.get("title", "")),
            url=str(data.get("url", "")),
            source=str(data.get("source", "")),
            author=str(data.get("author", "")),
            score=_coerce_float(data.get("score")),
            timestamp=_coerce_optional_datetime(data.get("timestamp") or data.get("published_at")),
            metadata=_coerce_metadata(data),
        )


@dataclass
class TrendCollectionResult:
    """트렌드 수집 결과."""

    source: str
    keyword: str
    points: list[TrendPoint]
    errors: list[str] = field(default_factory=list)
    metadata: dict[str, object] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> TrendCollectionResult:
        points: list[TrendPoint] = []
        raw_points = data.get("points", [])
        if isinstance(raw_points, list):
            for item in raw_points:
                if isinstance(item, TrendPoint):
                    points.append(item)
                elif isinstance(item, dict):
                    points.append(TrendPoint.from_dict(item))

        return cls(
            source=str(data.get("source", "")),
            keyword=str(data.get("keyword", "")),
            points=points,
            errors=_coerce_list_of_str(data.get("errors")),
            metadata=_coerce_metadata(data),
        )


@dataclass
class KeywordSet:
    """키워드 세트 설정."""

    name: str
    keywords: list[str]
    channels: list[str] = field(default_factory=lambda: ["naver", "google"])
    time_range: dict[str, str] = field(default_factory=dict)
    filters: dict[str, object] = field(default_factory=dict)
    enabled: bool = True
    description: str = ""

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> KeywordSet:
        """딕셔너리로부터 KeywordSet 인스턴스를 생성합니다."""
        time_range = {
            str(key): str(value) for key, value in _coerce_dict(data.get("time_range")).items()
        }

        return cls(
            name=str(data.get("name", "")),
            keywords=_coerce_list_of_str(data.get("keywords")),
            channels=_coerce_list_of_str(data.get("channels")),
            time_range=time_range,
            filters=_coerce_dict(data.get("filters")),
            enabled=_coerce_bool(data.get("enabled"), default=True),
            description=str(data.get("description", "")),
        )


@dataclass
class TrendRadarSettings:
    """TrendRadar 설정."""

    database_path: str = "data/trendradar.duckdb"
    report_dir: str = "docs/reports"
    raw_data_dir: str = "data/raw"
    search_db_path: str = "data/search_index.db"
    notification_config_path: str = "config/notifications.yaml"

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> TrendRadarSettings:
        defaults = cls()
        return cls(
            database_path=str(data.get("database_path", defaults.database_path)),
            report_dir=str(data.get("report_dir", defaults.report_dir)),
            raw_data_dir=str(data.get("raw_data_dir", defaults.raw_data_dir)),
            search_db_path=str(data.get("search_db_path", defaults.search_db_path)),
            notification_config_path=str(
                data.get("notification_config_path", defaults.notification_config_path)
            ),
        )


def _coerce_datetime(value: object) -> datetime:
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        text = value.strip()
        if text:
            try:
                parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
                if parsed.tzinfo is None:
                    return parsed.replace(tzinfo=UTC)
                return parsed.astimezone(UTC)
            except ValueError:
                pass
    return datetime.now(UTC)


def _coerce_optional_datetime(value: object) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, str) and not value.strip():
        return None
    return _coerce_datetime(value)


def _coerce_float(value: object, default: float = 0.0) -> float:
    if isinstance(value, bool):
        return float(value)
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value)
        except ValueError:
            return default
    return default


def _coerce_bool(value: object, default: bool = True) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return default
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"true", "1", "yes", "y", "on"}:
            return True
        if normalized in {"false", "0", "no", "n", "off"}:
            return False
    return default


def _coerce_list_of_str(value: object) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, (list, tuple)):
        return [str(item) for item in value]
    return [str(value)]


def _coerce_dict(value: object) -> dict[str, object]:
    if isinstance(value, dict):
        return {str(key): item for key, item in value.items()}
    return {}


def _coerce_metadata(data: Mapping[str, object]) -> dict[str, object]:
    raw_meta_json = data.get("meta_json")
    if isinstance(raw_meta_json, str):
        try:
            parsed = json.loads(raw_meta_json)
            if isinstance(parsed, dict):
                return {str(key): value for key, value in parsed.items()}
        except json.JSONDecodeError:
            pass
    return _coerce_dict(data.get("metadata"))

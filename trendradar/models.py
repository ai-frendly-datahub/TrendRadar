from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
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

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> TrendPoint:
        """딕셔너리로부터 TrendPoint 인스턴스를 생성합니다."""
        timestamp_val = data.get("timestamp")
        if isinstance(timestamp_val, str):
            timestamp: datetime = datetime.fromisoformat(timestamp_val)
        elif isinstance(timestamp_val, datetime):
            timestamp = timestamp_val
        else:
            timestamp = datetime.now(UTC)

        metadata_val = data.get("metadata", {})
        metadata: dict[str, object] = metadata_val if isinstance(metadata_val, dict) else {}

        value_val = data.get("value", 0.0)
        try:
            value: float = float(value_val)  # type: ignore
        except (TypeError, ValueError):
            value = 0.0

        return cls(
            keyword=str(data.get("keyword", "")),
            source=str(data.get("source", "")),
            timestamp=timestamp,
            value=value,
            metadata=metadata,
        )


@dataclass
class ContentItem:
    """콘텐츠 아이템 (Reddit, YouTube 등)."""

    title: str
    url: str
    source: str
    author: str
    score: float
    metadata: dict[str, object] = field(default_factory=dict)


@dataclass
class TrendCollectionResult:
    """트렌드 수집 결과."""

    source: str
    keyword: str
    points: list[TrendPoint]
    metadata: dict[str, object] = field(default_factory=dict)


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
        keywords_val = data.get("keywords", [])
        keywords: list[str] = (
            keywords_val if isinstance(keywords_val, list) else []  # type: ignore
        )

        channels_val = data.get("channels", ["naver", "google"])
        channels: list[str] = (
            channels_val if isinstance(channels_val, list) else ["naver", "google"]  # type: ignore
        )

        time_range_val = data.get("time_range", {})
        time_range: dict[str, str] = (
            time_range_val if isinstance(time_range_val, dict) else {}  # type: ignore
        )

        filters_val = data.get("filters", {})
        filters: dict[str, object] = (
            filters_val if isinstance(filters_val, dict) else {}  # type: ignore
        )

        enabled_val = data.get("enabled", True)
        enabled: bool = (
            enabled_val if isinstance(enabled_val, bool) else True  # type: ignore
        )

        return cls(
            name=str(data.get("name", "")),
            keywords=keywords,
            channels=channels,
            time_range=time_range,
            filters=filters,
            enabled=enabled,
            description=str(data.get("description", "")),
        )


@dataclass
class TrendRadarSettings:
    """TrendRadar 설정."""

    database_path: str = "data/trendradar.duckdb"
    report_dir: str = "reports"
    raw_data_dir: str = "data/raw"
    search_db_path: str = "data/search.duckdb"
    notification_config_path: str = "config/notification.yaml"

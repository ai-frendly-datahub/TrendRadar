"""Published instants stay UTC when the crawler zone is Asia/Seoul."""

from __future__ import annotations

import time
from datetime import UTC, datetime, timedelta, timezone
from pathlib import Path

import pytest

from storage.trend_store import RadarStorage
from trendradar.collector import _extract_datetime, _extract_published
from trendradar.models import Article, Source


# 2026-10-28 15:00:00 UTC. tm_wday/tm_yday are unused by calendar.timegm.
_FIFTEEN_UTC = time.struct_time((2026, 10, 28, 15, 0, 0, 2, 301, 0))
_KST = timezone(timedelta(hours=9))


def _seoul(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TZ", "Asia/Seoul")
    time.tzset()


def _restore_tz(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.undo()
    time.tzset()


@pytest.mark.unit
def test_feedparser_struct_stores_1500_utc_under_asia_seoul(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """2026-10-28 15:00 UTC must stay 15:00 UTC when TZ=Asia/Seoul.

    time.mktime would read the UTC struct as KST and store 06:00 UTC.
    """
    _seoul(monkeypatch)
    storage = RadarStorage(tmp_path / "articles.duckdb")
    try:
        shifted = datetime.fromtimestamp(time.mktime(_FIFTEEN_UTC), tz=UTC)
        assert shifted == datetime(2026, 10, 28, 6, 0, tzinfo=UTC)

        published = _extract_datetime({"published_parsed": _FIFTEEN_UTC})
        assert published == datetime(2026, 10, 28, 15, 0, tzinfo=UTC)

        updated = _extract_datetime({"updated_parsed": _FIFTEEN_UTC})
        assert updated == datetime(2026, 10, 28, 15, 0, tzinfo=UTC)

        storage.upsert_articles(
            [
                Article(
                    title="spike",
                    link="https://example.com/spike",
                    summary="",
                    published=published,
                    source="Example",
                    category="trend",
                )
            ]
        )
        row = storage.conn.execute("SELECT published FROM articles").fetchone()
        assert row is not None
        assert row[0] == datetime(2026, 10, 28, 15, 0, tzinfo=UTC).replace(tzinfo=None)
        loaded = storage.recent_articles("trend", days=3650)
        assert loaded[0].published == datetime(2026, 10, 28, 15, 0, tzinfo=UTC)
    finally:
        storage.close()
        _restore_tz(monkeypatch)


@pytest.mark.unit
def test_offset_string_keeps_its_offset(monkeypatch: pytest.MonkeyPatch) -> None:
    _seoul(monkeypatch)
    try:
        parsed, raw = _extract_published({"published": "Thu, 29 Oct 2026 09:00:00 +0900"})
        assert raw == "Thu, 29 Oct 2026 09:00:00 +0900"
        assert parsed is not None
        assert parsed.utcoffset() == timedelta(hours=9)
        assert parsed.astimezone(UTC) == datetime(2026, 10, 29, 0, tzinfo=UTC)
    finally:
        _restore_tz(monkeypatch)


@pytest.mark.unit
def test_zoneless_kr_host_uses_seoul_and_config_default_overrides() -> None:
    korean = Source(name="인벤", type="rss", url="https://www.inven.co.kr/rss/news.xml")
    parsed, raw = _extract_published(
        {"published": "2026-10-29 18:00:00", "published_parsed": _FIFTEEN_UTC},
        korean,
    )
    assert raw == "2026-10-29 18:00:00"
    assert parsed == datetime(2026, 10, 29, 18, 0, tzinfo=_KST)
    assert parsed.astimezone(UTC) == datetime(2026, 10, 29, 9, 0, tzinfo=UTC)

    configured = Source(
        name="Example",
        type="rss",
        url="https://example.com/feed",
        config={"default_timezone": "Asia/Seoul"},
    )
    zoned, _ = _extract_published({"published": "2026-10-29 18:00:00"}, configured)
    assert zoned == datetime(2026, 10, 29, 18, 0, tzinfo=_KST)

    explicit = Source(
        name="Example",
        type="rss",
        url="https://news.example.kr/rss",
        default_timezone="UTC",
    )
    utc_parsed, _ = _extract_published({"published": "2026-10-29 18:00:00"}, explicit)
    assert utc_parsed == datetime(2026, 10, 29, 18, 0, tzinfo=UTC)

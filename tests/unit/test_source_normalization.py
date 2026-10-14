"""Compaction hook, credential skips, and keyless Google Trends RSS."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest
import requests

import main
from storage.trend_store import RadarStorage
from trendradar.date_storage import compact_duckdb_before_snapshot, snapshot_database

RSS_FIXTURE = """<?xml version="1.0" encoding="UTF-8"?>
<rss xmlns:ht="https://trends.google.com/trending/rss" version="2.0">
  <channel>
    <title>Daily Search Trends</title>
    <item>
      <title>수질오염</title>
      <ht:approx_traffic>200+</ht:approx_traffic>
      <pubDate>Tue, 13 Oct 2026 18:50:00 -0700</pubDate>
      <ht:news_item>
        <ht:news_item_url>https://example.com/water</ht:news_item_url>
      </ht:news_item>
    </item>
    <item>
      <title>Sample placeholder</title>
      <ht:approx_traffic>10K+</ht:approx_traffic>
      <pubDate>Tue, 13 Oct 2026 18:40:00 -0700</pubDate>
    </item>
  </channel>
</rss>
"""


def test_compact_failure_still_allows_snapshot(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    db_file = tmp_path / "trendradar.duckdb"
    db_file.write_text("duckdb", encoding="utf-8")

    def boom(path: Path, **_: object) -> dict[str, object]:
        raise RuntimeError("compact failed")

    import radar_core.db_compact as db_compact

    monkeypatch.setattr(db_compact, "compact_duckdb_file", boom)
    result = compact_duckdb_before_snapshot(db_file)
    assert result["reason"] == "failed"
    assert result["compacted"] is False

    snapshot = snapshot_database(db_file, snapshot_root=tmp_path / "daily")
    assert snapshot is not None
    assert snapshot.read_text(encoding="utf-8") == "duckdb"


def test_run_once_compacts_before_snapshot(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    order: list[str] = []
    db_path = tmp_path / "data" / "trendradar.duckdb"
    db_path.parent.mkdir(parents=True)
    db_path.write_text("duckdb", encoding="utf-8")

    def compact(path: Path) -> dict[str, object]:
        order.append(f"compact:{path.name}")
        return {
            "compacted": False,
            "reason": "within_limit",
            "bytes": 6,
            "bytes_before": 6,
            "rows_deleted": 0,
        }

    def snapshot(path: Path, **_: object) -> Path:
        order.append(f"snapshot:{path.name}")
        dest = path.parent / "daily" / "2026-04-12.duckdb"
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(path.read_bytes())
        return dest

    monkeypatch.setattr(main, "compact_duckdb_before_snapshot", compact)
    monkeypatch.setattr(main, "snapshot_database", snapshot)
    monkeypatch.setattr(main, "DEFAULT_RAW_DIR", tmp_path / "raw")
    monkeypatch.setattr(main, "DEFAULT_REPORT_DIR", tmp_path / "reports")
    monkeypatch.setattr(main, "DEFAULT_SEARCH_DB_PATH", tmp_path / "search.db")
    monkeypatch.setattr(
        main,
        "load_keyword_sets_config",
        lambda config_path=None: [],
    )

    # Empty keyword sets return before compaction. Use a disabled set so the
    # storage policy still runs.
    from trendradar.models import KeywordSet

    monkeypatch.setattr(
        main,
        "load_keyword_sets_config",
        lambda config_path=None: [KeywordSet(name="skip", keywords=[], enabled=False)],
    )

    main.run_once(execute_collectors=True, db_path=db_path, snapshot_db=True)
    assert order == ["compact:trendradar.duckdb", "snapshot:trendradar.duckdb"]


def test_storage_close_compacts_after_disconnect(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: list[Path] = []

    def spy(path: Path) -> dict[str, object]:
        calls.append(path)
        return {"compacted": False, "reason": "within_limit"}

    monkeypatch.setattr("trendradar.date_storage.compact_duckdb_before_snapshot", spy)
    storage = RadarStorage(tmp_path / "trend.duckdb")
    storage.close()
    assert calls == [tmp_path / "trend.duckdb"]


def test_credential_skip_is_visible_and_does_not_invent_secrets(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    for name in (
        "NAVER_CLIENT_ID",
        "NAVER_CLIENT_SECRET",
        "REDDIT_CLIENT_ID",
        "REDDIT_CLIENT_SECRET",
        "YOUTUBE_API_KEY",
    ):
        monkeypatch.delenv(name, raising=False)
    main._ANNOTATED_CREDENTIAL_SKIPS.clear()

    main._emit_credential_skip("naver", ["NAVER_CLIENT_ID", "NAVER_CLIENT_SECRET"])
    main._emit_credential_skip("youtube", ["YOUTUBE_API_KEY"])
    main._emit_credential_skip("naver", ["NAVER_CLIENT_ID", "NAVER_CLIENT_SECRET"])
    output = capsys.readouterr().out

    assert "NAVER_CLIENT_ID" in output
    assert "NAVER_CLIENT_SECRET" in output
    assert "YOUTUBE_API_KEY" in output
    assert "no keyless DataLab API" in output
    assert "no keyless most-popular chart" in output
    assert output.count("::warning title=TrendRadar source skipped::") == 2
    assert "your_client" not in output
    assert "=" not in output.split("missing env", 1)[1].split(";", 1)[0].replace(", ", "")


def test_parse_google_trends_rss_uses_public_traffic() -> None:
    from collectors.google_trends_rss_collector import parse_google_trends_rss

    parsed = parse_google_trends_rss(RSS_FIXTURE, geo="KR", top_n=10)
    assert list(parsed) == ["수질오염", "Sample placeholder"]
    assert parsed["수질오염"][0].value == 200.0
    assert parsed["수질오염"][0].metadata["news_url"] == "https://example.com/water"
    assert parsed["수질오염"][0].metadata["feed"] == "google_trends_rss"
    assert parsed["Sample placeholder"][0].value == 10_000.0
    assert parsed["수질오염"][0].source == "google_trending"


def test_reddit_request_failure_returns_empty(monkeypatch: pytest.MonkeyPatch) -> None:
    from collectors.reddit_collector import RedditCollector

    def fail(*_args: object, **_kwargs: object) -> None:
        raise requests.exceptions.ConnectionError("blocked")

    monkeypatch.setattr("collectors.reddit_collector.requests.get", fail)
    collector = RedditCollector()
    posts = collector.collect_subreddit_posts(subreddit="python", limit=5)
    popular = collector.collect_popular_posts(limit=5)
    assert posts == []
    assert popular == []


def test_long_community_title_is_truncated_and_negative_score_kept() -> None:
    errors: list[str] = []
    title = "x" * 140
    accepted = main._accept_content_keyword(
        source="devto",
        keyword=title,
        score=-3,
        errors=errors,
    )
    assert errors == []
    assert accepted is not None
    assert accepted[0] == "x" * 100
    assert accepted[1] == -3.0


def test_wikipedia_empty_recent_window_walks_back(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    class _LookbackWiki:
        calls: list[tuple[str, str]] = []

        def collect(self, **kwargs: object) -> dict[str, list[object]]:
            start_date = str(kwargs["start_date"])
            end_date = str(kwargs["end_date"])
            self.calls.append((start_date, end_date))
            if end_date == "2026-04-26":
                return {"Seoul": [{"date": end_date, "value": 12.0}]}
            return {"Seoul": []}

    class _FixedDateTime(datetime):
        @classmethod
        def now(cls, tz: object = None) -> _FixedDateTime:
            return cls(2026, 4, 29, 9, 0, tzinfo=tz or UTC)

    collector = _LookbackWiki()
    monkeypatch.setattr(main, "WikipediaPageviewsCollector", lambda: collector)
    monkeypatch.setattr(main, "datetime", _FixedDateTime)

    total_points, sources_succeeded, errors = main.collect_trends(
        {
            "name": "wiki",
            "keywords": ["Seoul"],
            "channels": ["wikipedia"],
            "time_range": {"start": "yesterday", "end": "yesterday"},
        },
        db_path=tmp_path / "trend.duckdb",
        source_filter="wikipedia",
    )

    assert collector.calls[0] == ("2026-04-28", "2026-04-28")
    assert ("2026-04-26", "2026-04-26") in collector.calls
    assert total_points == 1
    assert sources_succeeded == 1
    assert errors == []

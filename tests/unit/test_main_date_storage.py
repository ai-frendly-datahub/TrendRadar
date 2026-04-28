from __future__ import annotations

import json
from datetime import UTC, date, datetime
from pathlib import Path

import main
from storage import trend_store
import trendradar.date_storage as date_storage
from trendradar.models import KeywordSet, TrendPoint


class FixedDateTime(datetime):
    @classmethod
    def now(cls, tz=None):
        return cls(2026, 4, 12, 9, 30, tzinfo=tz or UTC)


def test_run_once_applies_date_storage_policy(tmp_path: Path, monkeypatch) -> None:
    db_path = tmp_path / "data" / "trendradar.duckdb"
    db_path.parent.mkdir(parents=True)
    db_path.write_text("duckdb", encoding="utf-8")

    raw_dir = tmp_path / "raw"
    old_raw_dir = raw_dir / "2026-01-01"
    old_raw_dir.mkdir(parents=True)
    (old_raw_dir / "google.jsonl").write_text("{}", encoding="utf-8")

    report_dir = tmp_path / "reports"
    report_dir.mkdir()
    old_report = report_dir / "trend_20260101.html"
    old_report.write_text("<html>old</html>", encoding="utf-8")

    monkeypatch.setattr(main, "DEFAULT_RAW_DIR", raw_dir)
    monkeypatch.setattr(main, "DEFAULT_SEARCH_DB_PATH", tmp_path / "search.db")
    monkeypatch.setattr(main, "DEFAULT_REPORT_DIR", report_dir)
    monkeypatch.setattr(date_storage, "datetime", FixedDateTime)
    monkeypatch.setattr(
        main,
        "load_keyword_sets_config",
        lambda config_path=None: [KeywordSet(name="skip", keywords=[], enabled=False)],
    )

    main.run_once(
        execute_collectors=True,
        db_path=db_path,
        snapshot_db=True,
        keep_raw_days=30,
        keep_report_days=30,
    )

    assert (tmp_path / "data" / "daily" / "2026-04-12.duckdb").exists()
    assert not old_raw_dir.exists()
    assert not old_report.exists()


def test_write_summary_report_uses_trend_points(tmp_path: Path) -> None:
    db_path = tmp_path / "data" / "trendradar.duckdb"
    report_dir = tmp_path / "reports"
    points = [
        TrendPoint(
            keyword="AI",
            source="google",
            timestamp=datetime(2026, 4, 12, 9, 0, tzinfo=UTC),
            value=88.0,
        ),
        TrendPoint(
            keyword="Python",
            source="hackernews",
            timestamp=datetime(2026, 4, 12, 10, 0, tzinfo=UTC),
            value=42.0,
        ),
    ]
    trend_store.save_trend_points("google", "AI", [points[0]], db_path=db_path)
    trend_store.save_trend_points("hackernews", "Python", [points[1]], db_path=db_path)

    summary_path = main._write_summary_report(
        target_date=date(2026, 4, 12),
        db_path=db_path,
        report_dir=report_dir,
    )

    assert summary_path.exists()
    payload = json.loads(summary_path.read_text(encoding="utf-8"))
    assert payload["category"] == "trend"
    assert payload["article_count"] == 2
    assert payload["source_count"] == 2
    assert payload["matched_count"] == 2
    assert {entity["name"] for entity in payload["top_entities"]} == {"AI", "Python"}
    assert payload["ontology"]["repo"] == "TrendRadar"
    assert payload["ontology"]["ontology_version"] == "0.1.0"
    assert "trend.attention_signal" in payload["ontology"]["event_model_ids"]


def test_attach_trend_event_model_payload_full_attention(tmp_path: Path) -> None:
    """Full mapping: source + keyword resolvable via metadata → 3/3 attention fields."""
    article = main._trend_summary_article(
        {
            "keyword": "위스키",
            "source": "google",
            "timestamp": datetime(2026, 4, 12, 9, 0, tzinfo=UTC),
            "value": 88.0,
        }
    )
    main._attach_trend_event_model_payload(
        article,
        event_model_key="attention_signal",
        source="google",
        keyword="위스키",
        value=88.0,
        metadata={"set_name": "위스키 시장 동향"},
    )
    payload = article.get("event_model_payload")
    assert payload == {
        "keyword_set_name": "위스키 시장 동향",
        "channel": "google",
        "normalized_value": 88.0,
    }


def test_attach_trend_event_model_payload_partial_when_keyword_unknown() -> None:
    """Partial mapping: source maps but keyword absent from metadata + yaml index."""
    article = main._trend_summary_article(
        {
            "keyword": "전혀없는키워드xyz",
            "source": "google",
            "timestamp": datetime(2026, 4, 12, 9, 0, tzinfo=UTC),
            "value": 12.0,
        }
    )
    main._attach_trend_event_model_payload(
        article,
        event_model_key="attention_signal",
        source="google",
        keyword="전혀없는키워드xyz",
        value=12.0,
        metadata=None,
    )
    payload = article.get("event_model_payload")
    assert payload is not None
    assert "keyword_set_name" not in payload  # unknown keyword drops the field
    assert payload["channel"] == "google"
    assert payload["normalized_value"] == 12.0


def test_attach_trend_event_model_payload_skips_unmappable_source() -> None:
    """Unmappable source: _resolve returns None → enrichment is skipped (graceful)."""
    article = main._trend_summary_article(
        {
            "keyword": "AI",
            "source": "foobar_unregistered",
            "timestamp": datetime(2026, 4, 12, 9, 0, tzinfo=UTC),
            "value": 1.0,
        }
    )
    assert main._resolve_trend_event_model("foobar_unregistered") is None
    main._attach_trend_event_model_payload(
        article,
        event_model_key=None,
        source="foobar_unregistered",
        keyword="AI",
        value=1.0,
        metadata=None,
    )
    assert "event_model_payload" not in article


def test_attach_trend_event_model_payload_handles_none_metadata_defensively() -> None:
    """Defensive: keyword reverse-lookup must work when metadata is None."""
    article = main._trend_summary_article(
        {
            "keyword": "AI",
            "source": "reddit",
            "timestamp": datetime(2026, 4, 12, 9, 0, tzinfo=UTC),
            "value": 7,
        }
    )
    main._attach_trend_event_model_payload(
        article,
        event_model_key="community_signal",
        source="reddit",
        keyword="AI",
        value=7,
        metadata=None,
    )
    payload = article.get("event_model_payload")
    assert payload == {
        "keyword_set_name": "글로벌 테크 커뮤니티 트렌드",
        "community": "reddit",
        "signal_value": 7,
    }


def test_sync_report_contract_artifacts_copies_custom_outputs_to_canonical_dir(tmp_path: Path) -> None:
    generated_dir = tmp_path / "reports"
    canonical_dir = tmp_path / "docs" / "reports"
    generated_dir.mkdir(parents=True)
    daily = generated_dir / "trend_20260412.html"
    latest_quality = generated_dir / "trend_quality.json"
    dated_quality = generated_dir / "trend_20260412_quality.json"
    for path in (daily, latest_quality, dated_quality):
        path.write_text(path.name, encoding="utf-8")

    synced = main._sync_report_contract_artifacts(
        generated_paths=[daily, latest_quality, dated_quality],
        canonical_dir=canonical_dir,
    )

    assert [path.name for path in synced] == [
        "trend_20260412.html",
        "trend_quality.json",
        "trend_20260412_quality.json",
    ]
    assert (canonical_dir / "trend_20260412.html").read_text(encoding="utf-8") == "trend_20260412.html"
    assert (canonical_dir / "trend_quality.json").read_text(encoding="utf-8") == "trend_quality.json"

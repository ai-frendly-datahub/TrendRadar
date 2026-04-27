from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

import main
from raw_logger import RawLogger
from storage.search_index import SearchIndex


class _DummyGoogleCollector:
    calls: list[list[str]] = []

    def collect(self, **_: object) -> dict[str, list[dict[str, object]]]:
        keywords = [str(keyword) for keyword in _.get("keywords", [])]
        self.calls.append(keywords)
        return {
            keyword: [
                {"date": "2026-03-01", "value": 88.0},
                {"date": "2026-03-02", "value": 91.0},
            ]
            for keyword in keywords[:1]
        }


@pytest.mark.unit
def test_collect_trends_logs_raw_and_syncs_search_index(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
):
    _DummyGoogleCollector.calls = []
    monkeypatch.setattr(main, "GoogleTrendsCollector", _DummyGoogleCollector)

    keyword_set = {
        "name": "AI",
        "keywords": ["인공지능", "머신러닝"],
        "channels": ["google"],
        "time_range": {"start": "2026-03-01", "end": "2026-03-02"},
        "filters": {"geo": "KR"},
    }

    db_path = tmp_path / "trend.duckdb"
    raw_logger = RawLogger(tmp_path / "raw")
    search_index = SearchIndex(tmp_path / "search.db")

    total_points, sources_succeeded, errors = main.collect_trends(
        keyword_set,
        db_path=db_path,
        source_filter="google",
        raw_logger=raw_logger,
        search_index=search_index,
    )

    assert total_points == 2
    assert sources_succeeded == 1
    assert errors == []

    raw_file = tmp_path / "raw" / datetime.now(tz=UTC).date().isoformat() / "google.jsonl"
    assert raw_file.exists()
    raw_lines = raw_file.read_text(encoding="utf-8").splitlines()
    assert len(raw_lines) == 2
    assert json.loads(raw_lines[0])["keyword"] == "인공지능"

    results = search_index.search("인공지능", limit=5)
    assert len(results) == 1
    assert results[0].platform == "google"


@pytest.mark.unit
def test_collect_trends_batches_google_keywords(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    _DummyGoogleCollector.calls = []
    monkeypatch.setattr(main, "GoogleTrendsCollector", _DummyGoogleCollector)

    keyword_set = {
        "name": "Large keyword pack",
        "keywords": ["k1", "k2", "k3", "k4", "k5", "k6"],
        "channels": ["google"],
        "time_range": {"start": "2026-03-01", "end": "2026-03-02"},
        "filters": {"geo": "KR"},
    }

    total_points, sources_succeeded, errors = main.collect_trends(
        keyword_set,
        db_path=tmp_path / "trend.duckdb",
        source_filter="google",
    )

    assert _DummyGoogleCollector.calls == [["k1", "k2", "k3", "k4", "k5"], ["k6"]]
    assert total_points == 4
    assert sources_succeeded == 1
    assert errors == []

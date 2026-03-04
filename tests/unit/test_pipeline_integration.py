from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import pytest

import main
from raw_logger import RawLogger
from storage.search_index import SearchIndex


class _DummyGoogleCollector:
    def collect(self, **_: object) -> dict[str, list[dict[str, object]]]:
        return {
            "인공지능": [
                {"date": "2026-03-01", "value": 88.0},
                {"date": "2026-03-02", "value": 91.0},
            ]
        }


@pytest.mark.unit
def test_collect_trends_logs_raw_and_syncs_search_index(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
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

    raw_file = tmp_path / "raw" / date.today().isoformat() / "google.jsonl"
    assert raw_file.exists()
    raw_lines = raw_file.read_text(encoding="utf-8").splitlines()
    assert len(raw_lines) == 2
    assert json.loads(raw_lines[0])["keyword"] == "인공지능"

    results = search_index.search("인공지능", limit=5)
    assert len(results) == 1
    assert results[0].platform == "google"

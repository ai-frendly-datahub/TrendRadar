from __future__ import annotations

from pathlib import Path

import pytest

from storage.search_index import SearchIndex


@pytest.mark.unit
def test_search_index_upsert_and_search(tmp_path: Path):
    index = SearchIndex(tmp_path / "search.db")
    index.upsert("인공지능", "google", "ai machine learning")
    index.upsert("반도체", "naver", "semiconductor memory chip")

    results = index.search("인공지능", limit=5)

    assert len(results) == 1
    assert results[0].keyword == "인공지능"
    assert results[0].platform == "google"
    assert results[0].link == "인공지능|google"


@pytest.mark.unit
def test_search_index_upsert_replaces_existing_link(tmp_path: Path):
    index = SearchIndex(tmp_path / "search.db")
    index.upsert("AI", "google", "old context")
    index.upsert("AI", "google", "new context")

    results = index.search("new", limit=5)

    assert len(results) == 1
    assert results[0].context == "new context"

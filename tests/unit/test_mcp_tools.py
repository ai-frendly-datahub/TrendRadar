from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path

import pytest

from mcp_server.tools import (
    handle_price_watch,
    handle_recent_updates,
    handle_search,
    handle_sql,
    handle_top_trends,
)
from storage.search_index import SearchIndex
from storage.trend_store import save_trend_points


@pytest.mark.unit
def test_handle_search_uses_search_index(tmp_path: Path):
    search_db = tmp_path / "search.db"
    data_db = tmp_path / "trend.duckdb"

    _ = SearchIndex(search_db)
    _.upsert("인공지능", "google", "ai machine learning")

    result = handle_search(
        search_db_path=search_db,
        db_path=data_db,
        query="최근 7일 인공지능 5개",
        limit=20,
    )

    assert "인공지능" in result
    assert "google" in result


@pytest.mark.unit
def test_handle_recent_updates_reads_duckdb(tmp_path: Path):
    db_path = tmp_path / "trend.duckdb"
    now = datetime.now()

    _ = save_trend_points(
        source="google",
        keyword="반도체",
        points=[
            {"date": (now - timedelta(days=1)).strftime("%Y-%m-%d"), "value": 45.0},
        ],
        db_path=db_path,
    )

    result = handle_recent_updates(db_path=db_path, days=7, limit=5)

    assert "반도체" in result
    assert "google" in result


@pytest.mark.unit
def test_handle_sql_blocks_non_select(tmp_path: Path):
    db_path = tmp_path / "trend.duckdb"

    result = handle_sql(db_path=db_path, query="DELETE FROM trend_points")

    assert "Only SELECT" in result


@pytest.mark.unit
def test_handle_top_trends_returns_spike_keywords(tmp_path: Path):
    db_path = tmp_path / "trend.duckdb"
    now = datetime.now()

    baseline_points = [
        {"date": (now - timedelta(days=35 - i)).strftime("%Y-%m-%d"), "value": 10.0}
        for i in range(7)
    ]
    surge_points = [
        {"date": (now - timedelta(days=6 - i)).strftime("%Y-%m-%d"), "value": 80.0}
        for i in range(7)
    ]

    _ = save_trend_points(
        source="google",
        keyword="AI",
        points=baseline_points + surge_points,
        db_path=db_path,
    )

    result = handle_top_trends(db_path=db_path, days=7, limit=5)

    assert "AI" in result


@pytest.mark.unit
def test_handle_price_watch_is_stub():
    assert handle_price_watch() == "Not available in TrendRadar"

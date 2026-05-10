from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from storage import trend_store
from trendradar.models import TrendPoint


def test_save_trend_points_replaces_existing_source_keyword_timestamp(tmp_path: Path) -> None:
    db_path = tmp_path / "trend.duckdb"
    timestamp = datetime(2026, 4, 28, tzinfo=UTC)

    trend_store.save_trend_points(
        "wikipedia",
        "Seoul",
        [
            TrendPoint(
                keyword="Seoul",
                source="wikipedia",
                timestamp=timestamp,
                value=100.0,
                metadata={"revision": "old"},
            )
        ],
        metadata={"set_name": "Wikipedia"},
        db_path=db_path,
    )
    trend_store.save_trend_points(
        "wikipedia",
        "Seoul",
        [
            TrendPoint(
                keyword="Seoul",
                source="wikipedia",
                timestamp=timestamp,
                value=120.0,
                metadata={"revision": "new"},
            )
        ],
        metadata={"set_name": "Wikipedia"},
        db_path=db_path,
    )

    rows = trend_store.query_trend_points(
        source="wikipedia",
        keyword="Seoul",
        db_path=db_path,
    )

    assert len(rows) == 1
    assert rows[0]["value"] == 120.0
    assert rows[0]["metadata"] == {"set_name": "Wikipedia", "revision": "new"}

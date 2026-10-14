from __future__ import annotations

import logging
import shutil
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

logger = logging.getLogger(__name__)


def compact_duckdb_before_snapshot(database_path: Path) -> dict[str, object]:
    """Shrink ``database_path`` before it is copied or committed.

    Compaction failure leaves the file on disk and must not block the snapshot.
    ``RADAR_DUCKDB_MAX_BYTES`` and ``RADAR_DUCKDB_COMPACT=0`` are read inside
    ``radar_core.db_compact.compact_duckdb_file``. The default budget is 90 MiB.
    """
    bytes_now = database_path.stat().st_size if database_path.exists() else 0
    fallback: dict[str, object] = {
        "compacted": False,
        "reason": "skipped",
        "bytes": bytes_now,
        "bytes_before": bytes_now,
        "rows_deleted": 0,
    }
    try:
        from radar_core.db_compact import compact_duckdb_file
    except ImportError as exc:
        logger.warning("duckdb_compact_unavailable path=%s error=%s", database_path, exc)
        fallback["reason"] = "unavailable"
        return fallback
    try:
        result = compact_duckdb_file(database_path)
    except Exception as exc:
        logger.warning("duckdb_compact_failed path=%s error=%s", database_path, exc)
        fallback["reason"] = "failed"
        fallback["bytes"] = database_path.stat().st_size if database_path.exists() else 0
        return fallback
    if isinstance(result, dict):
        return result
    fallback["reason"] = "invalid_result"
    return fallback


def snapshot_database(
    db_path: Path,
    *,
    snapshot_date: date | None = None,
    snapshot_root: Path | None = None,
) -> Path | None:
    if not db_path.exists():
        return None

    if snapshot_date is None:
        snapshot_date = datetime.now(UTC).date()
    if snapshot_root is None:
        snapshot_root = db_path.parent / "daily"

    snapshot_root.mkdir(parents=True, exist_ok=True)
    snapshot_path = snapshot_root / f"{snapshot_date.isoformat()}.duckdb"
    shutil.copy2(db_path, snapshot_path)
    return snapshot_path


def cleanup_date_directories(base_dir: Path, *, keep_days: int, today: date | None = None) -> int:
    if today is None:
        today = datetime.now(UTC).date()
    if not base_dir.exists():
        return 0

    cutoff = today - timedelta(days=keep_days)
    removed = 0
    for item in base_dir.iterdir():
        if not item.is_dir():
            continue
        try:
            stamp = date.fromisoformat(item.name)
        except ValueError:
            continue
        if stamp < cutoff:
            shutil.rmtree(item)
            removed += 1
    return removed


def cleanup_dated_reports(report_dir: Path, *, keep_days: int, today: date | None = None) -> int:
    if today is None:
        today = datetime.now(UTC).date()
    if not report_dir.exists():
        return 0

    cutoff = today - timedelta(days=keep_days)
    removed = 0
    for item in report_dir.glob("*_[0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9].html"):
        try:
            stamp = datetime.strptime(item.stem.split("_")[-1], "%Y%m%d").replace(tzinfo=UTC).date()
        except (IndexError, ValueError):
            continue
        if stamp < cutoff:
            item.unlink()
            removed += 1
    return removed

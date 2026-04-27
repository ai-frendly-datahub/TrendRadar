from __future__ import annotations

import json
from collections.abc import Iterable
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import cast

import duckdb

from exceptions import StorageError
from trendradar.models import Article, TrendPoint


def _utc_naive(dt: datetime | None) -> datetime | None:
    """Convert tz-aware datetime to UTC naive for DuckDB."""
    if dt is None:
        return None
    if dt.tzinfo:
        return dt.astimezone(UTC).replace(tzinfo=None)
    return dt


class RadarStorage:
    """DuckDB 기반 경량 스토리지."""

    def __init__(self, db_path: Path):
        self.db_path: Path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn: duckdb.DuckDBPyConnection = duckdb.connect(str(self.db_path))
        self._ensure_tables()

    def close(self) -> None:
        self.conn.close()

    def __enter__(self) -> RadarStorage:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    def _ensure_tables(self) -> None:
        _ = self.conn.execute(
            """
            CREATE SEQUENCE IF NOT EXISTS articles_id_seq START 1;
            CREATE TABLE IF NOT EXISTS articles (
                id BIGINT PRIMARY KEY DEFAULT nextval('articles_id_seq'),
                category TEXT NOT NULL,
                source TEXT NOT NULL,
                title TEXT NOT NULL,
                link TEXT NOT NULL UNIQUE,
                summary TEXT,
                published TIMESTAMP,
                collected_at TIMESTAMP NOT NULL,
                entities_json TEXT
            );
            """
        )
        _ = self.conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_articles_category_time ON articles (category, published, collected_at);"
        )

    def upsert_articles(self, articles: Iterable[Article]) -> None:
        """중복 링크는 덮어쓰고 최신 수집 시각을 기록."""
        now = _utc_naive(datetime.now(UTC))
        rows: list[tuple[object, ...]] = []
        for article in articles:
            rows.append(
                (
                    article.category,
                    article.source,
                    article.title,
                    article.link,
                    article.summary,
                    _utc_naive(article.published),
                    now,
                    json.dumps(article.matched_entities, ensure_ascii=False),
                )
            )

        if not rows:
            return

        try:
            _ = self.conn.begin()
            _ = self.conn.executemany(
                """
                INSERT INTO articles (category, source, title, link, summary, published, collected_at, entities_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(link) DO UPDATE SET
                    title = EXCLUDED.title,
                    summary = EXCLUDED.summary,
                    published = EXCLUDED.published,
                    collected_at = EXCLUDED.collected_at,
                    entities_json = EXCLUDED.entities_json
                """,
                rows,
            )
            _ = self.conn.commit()
        except Exception as exc:
            try:
                _ = self.conn.rollback()
            except duckdb.Error:
                pass
            raise StorageError("Failed to upsert articles") from exc

    def recent_articles(self, category: str, *, days: int = 7, limit: int = 200) -> list[Article]:
        """최근 N일 내 기사 반환."""
        since = _utc_naive(datetime.now(UTC) - timedelta(days=days))
        cur = self.conn.execute(
            """
            SELECT category, source, title, link, summary, published, collected_at, entities_json
            FROM articles
            WHERE category = ? AND COALESCE(published, collected_at) >= ?
            ORDER BY COALESCE(published, collected_at) DESC
            LIMIT ?
            """,
            [category, since, limit],
        )
        rows = cast(
            list[
                tuple[str, str, str, str, str | None, datetime | None, datetime | None, str | None]
            ],
            cur.fetchall(),
        )

        results: list[Article] = []
        for row in rows:
            category_value, source, title, link, summary, published, collected_at, raw_entities = (
                row
            )
            published_at = published if isinstance(published, datetime) else None
            collected = collected_at if isinstance(collected_at, datetime) else None

            entities: dict[str, list[str]] = {}
            if raw_entities:
                try:
                    parsed_entities = cast(object, json.loads(raw_entities))
                    if isinstance(parsed_entities, dict):
                        parsed_map = cast(dict[object, object], parsed_entities)
                        entities = {}
                        for name, keywords in parsed_map.items():
                            if not isinstance(name, str) or not isinstance(keywords, list):
                                continue
                            normalized_keywords: list[str] = []
                            for keyword in cast(list[object], keywords):
                                normalized_keywords.append(str(keyword))
                            entities[name] = normalized_keywords
                except json.JSONDecodeError:
                    entities = {}

            results.append(
                Article(
                    title=str(title),
                    link=str(link),
                    summary=str(summary) if summary is not None else "",
                    published=published_at,
                    source=str(source),
                    category=str(category_value),
                    matched_entities=entities,
                    collected_at=collected,
                )
            )
        return results

    def delete_older_than(self, days: int) -> int:
        """보존 기간 밖 데이터 삭제."""
        cutoff = _utc_naive(datetime.now(UTC) - timedelta(days=days))
        count_row = self.conn.execute(
            "SELECT COUNT(*) FROM articles WHERE COALESCE(published, collected_at) < ?", [cutoff]
        ).fetchone()
        to_delete = count_row[0] if count_row else 0
        _ = self.conn.execute(
            "DELETE FROM articles WHERE COALESCE(published, collected_at) < ?", [cutoff]
        )
        return to_delete

    def create_daily_snapshot(self, snapshot_dir: str | None = None) -> Path | None:
        from .date_storage import snapshot_database

        snapshot_root = Path(snapshot_dir) if snapshot_dir else self.db_path.parent / "daily"
        _ = self.conn.execute("CHECKPOINT")
        self.conn.close()
        try:
            return snapshot_database(self.db_path, snapshot_root=snapshot_root)
        finally:
            self.conn = duckdb.connect(str(self.db_path))
            self._ensure_tables()

    def cleanup_old_snapshots(self, snapshot_dir: str | None = None, keep_days: int = 90) -> int:
        from .date_storage import cleanup_date_directories

        snapshot_root = Path(snapshot_dir) if snapshot_dir else self.db_path.parent / "daily"
        return cleanup_date_directories(snapshot_root, keep_days=keep_days)


# ---------------------------------------------------------------------------
# Module-level trend_points persistence
# ---------------------------------------------------------------------------

_DEFAULT_DB_PATH = Path("data/trendradar.duckdb")


def _resolve_db_path(db_path: Path | None) -> Path:
    """Resolve db_path, falling back to the project default."""
    return db_path if db_path is not None else _DEFAULT_DB_PATH


def _ensure_trend_points_table(conn: duckdb.DuckDBPyConnection) -> None:
    """Create trend_points table and index if they don't exist."""
    _ = conn.execute(
        """
        CREATE SEQUENCE IF NOT EXISTS trend_points_id_seq START 1;
        CREATE TABLE IF NOT EXISTS trend_points (
            id BIGINT PRIMARY KEY DEFAULT nextval('trend_points_id_seq'),
            source TEXT NOT NULL,
            keyword TEXT NOT NULL,
            timestamp TIMESTAMP NOT NULL,
            value DOUBLE NOT NULL,
            metadata_json TEXT,
            created_at TIMESTAMP NOT NULL
        );
        """
    )
    _ = conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_tp_source_keyword "
        "ON trend_points (source, keyword, timestamp);"
    )


def save_trend_points(
    source: str,
    keyword: str,
    points: list[TrendPoint | dict[str, object]],
    metadata: dict[str, object] | None = None,
    db_path: Path | None = None,
) -> int:
    """Persist a list of TrendPoints (or raw dicts) to the trend_points table.

    Returns the number of rows inserted.
    """
    if not points:
        return 0

    resolved_path = _resolve_db_path(db_path)
    resolved_path.parent.mkdir(parents=True, exist_ok=True)

    now = _utc_naive(datetime.now(UTC))
    meta_str = json.dumps(metadata, ensure_ascii=False) if metadata else None

    rows: list[tuple[object, ...]] = []
    for point in points:
        if isinstance(point, TrendPoint):
            ts = _utc_naive(point.timestamp)
            val = point.value
            point_meta = point.metadata
        elif isinstance(point, dict):
            raw_ts = point.get("timestamp")
            if isinstance(raw_ts, datetime):
                ts = _utc_naive(raw_ts)
            elif isinstance(raw_ts, str):
                ts = _utc_naive(datetime.fromisoformat(raw_ts))
            else:
                ts = now
            try:
                val = float(point.get("value", 0.0))  # type: ignore[arg-type]
            except (TypeError, ValueError):
                val = 0.0
            raw_point_meta = point.get("metadata")
            point_meta = raw_point_meta if isinstance(raw_point_meta, dict) else None
        else:
            continue

        # Merge point-level metadata with call-level metadata
        merged_meta: dict[str, object] = {}
        if metadata:
            merged_meta.update(metadata)
        if point_meta:
            merged_meta.update(point_meta)
        row_meta_str = json.dumps(merged_meta, ensure_ascii=False) if merged_meta else meta_str

        rows.append((source, keyword, ts, val, row_meta_str, now))

    if not rows:
        return 0

    conn = duckdb.connect(str(resolved_path))
    try:
        _ensure_trend_points_table(conn)
        _ = conn.begin()
        _ = conn.executemany(
            """
            INSERT INTO trend_points (source, keyword, timestamp, value, metadata_json, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            rows,
        )
        _ = conn.commit()
        return len(rows)
    except Exception as exc:
        try:
            _ = conn.rollback()
        except duckdb.Error:
            pass
        raise StorageError("Failed to save trend points") from exc
    finally:
        conn.close()


def query_trend_points(
    source: str | None = None,
    keyword: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    db_path: Path | None = None,
) -> list[dict[str, object]]:
    """Query trend_points with optional filters.

    Returns a list of dicts with keys: source, keyword, timestamp, value, metadata.
    """
    resolved_path = _resolve_db_path(db_path)
    if not resolved_path.exists():
        return []

    conn = duckdb.connect(str(resolved_path))
    try:
        _ensure_trend_points_table(conn)

        conditions: list[str] = []
        params: list[object] = []

        if source is not None:
            conditions.append("source = ?")
            params.append(source)
        if keyword is not None:
            conditions.append("keyword = ?")
            params.append(keyword)
        if start_date is not None:
            conditions.append("timestamp >= ?")
            params.append(start_date)
        if end_date is not None:
            conditions.append("timestamp <= ?")
            params.append(end_date)

        where_clause = (" WHERE " + " AND ".join(conditions)) if conditions else ""
        query = (
            "SELECT source, keyword, timestamp, value, metadata_json "
            f"FROM trend_points{where_clause} "
            "ORDER BY timestamp DESC"
        )

        cur = conn.execute(query, params)
        raw_rows = cast(
            list[tuple[str, str, datetime, float, str | None]],
            cur.fetchall(),
        )

        results: list[dict[str, object]] = []
        for row_source, row_keyword, row_ts, row_value, raw_meta in raw_rows:
            meta: dict[str, object] = {}
            if raw_meta:
                try:
                    parsed = json.loads(raw_meta)
                    if isinstance(parsed, dict):
                        meta = parsed
                except json.JSONDecodeError:
                    pass
            results.append(
                {
                    "source": row_source,
                    "keyword": row_keyword,
                    "timestamp": row_ts,
                    "value": row_value,
                    "metadata": meta,
                }
            )
        return results
    except Exception as exc:
        raise StorageError("Failed to query trend points") from exc
    finally:
        conn.close()

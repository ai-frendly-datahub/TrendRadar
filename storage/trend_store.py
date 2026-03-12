# -*- coding: utf-8 -*-
"""트렌드 데이터를 DuckDB에 저장하는 모듈."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional, Any, Mapping, Sequence

import duckdb
from exceptions import StorageError
from trendradar.models import TrendPoint

logger = logging.getLogger(__name__)


def _validate_date_format(date_str: str) -> Optional[datetime]:
    """날짜 문자열을 검증하고 datetime 객체로 변환합니다.

    Args:
        date_str: 날짜 문자열 (YYYY-MM-DD 또는 YYYY-MM)

    Returns:
        datetime 객체 또는 None (파싱 실패 시)
    """
    if not date_str or not isinstance(date_str, str):
        logger.warning(f"Invalid date format: {date_str} (type: {type(date_str).__name__})")
        return None

    try:
        return datetime.fromisoformat(date_str)
    except ValueError:
        # "2024-01" 형식 (월 단위)
        if len(date_str) == 7:
            try:
                return datetime.fromisoformat(f"{date_str}-01")
            except ValueError:
                logger.warning(f"Failed to parse date: {date_str}")
                return None
        logger.warning(f"Unsupported date format: {date_str}")
        return None


def _get_db_path(db_path: Optional[Path] = None) -> Path:
    """DB 파일 경로를 반환합니다."""
    if db_path is None:
        return Path(__file__).parent.parent / "data" / "trendradar.duckdb"
    return db_path


def _ensure_table_exists(conn: duckdb.DuckDBPyConnection) -> None:
    """trend_points 테이블이 없으면 생성합니다."""
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS trend_points (
                source TEXT NOT NULL,
                keyword TEXT NOT NULL,
                ts TIMESTAMP NOT NULL,
                value_normalized FLOAT NOT NULL,
                meta_json TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (source, keyword, ts)
            )
        """)
        logger.debug("trend_points table ensured")
    except Exception as e:
        logger.error(f"Failed to ensure table exists: {e}", exc_info=True)
        raise


def save_trend_points(
    source: str,
    keyword: str,
    points: Sequence[TrendPoint | Mapping[str, object]],
    metadata: dict[str, Any] | None = None,
    db_path: Optional[Path] = None,
) -> int:
    """트렌드 포인트를 DuckDB에 저장합니다.

    Args:
        source: 데이터 소스 (google, naver)
        keyword: 키워드
        points: 트렌드 포인트 리스트
            예: [{"date": "2024-01-01", "value": 85, ...}, ...]
        metadata: 메타데이터 (set_name, filters 등)
        db_path: DuckDB 파일 경로

    Returns:
        저장된 레코드 수
    """
    db_file = _get_db_path(db_path)
    db_file.parent.mkdir(parents=True, exist_ok=True)

    conn = None
    try:
        conn = duckdb.connect(str(db_file))
        _ensure_table_exists(conn)
        conn.execute("BEGIN TRANSACTION")

        inserted = 0
        failed = 0

        for idx, item in enumerate(points):
            try:
                original_period: str = ""
                point: TrendPoint

                if isinstance(item, TrendPoint):
                    point = item
                    ts = point.timestamp
                    if not isinstance(ts, datetime):
                        logger.warning(
                            f"Skipping point {idx} for {keyword}: invalid timestamp '{point.timestamp}'"
                        )
                        failed += 1
                        continue
                    original_period = str(
                        point.metadata.get("original_period")
                        or point.metadata.get("period")
                        or ts.date().isoformat()
                    )
                elif isinstance(item, Mapping):
                    date_str = str(item.get("date", "")).strip()
                    ts = _validate_date_format(date_str)
                    if ts is None:
                        logger.warning(
                            f"Skipping point {idx} for {keyword}: invalid date '{date_str}'"
                        )
                        failed += 1
                        continue

                    value_raw = item.get("value", 0.0)
                    if not isinstance(value_raw, (int, float, str)):
                        logger.warning(
                            f"Skipping point {idx} for {keyword}: invalid value '{value_raw}'"
                        )
                        failed += 1
                        continue

                    try:
                        value = float(value_raw)
                    except (TypeError, ValueError):
                        logger.warning(
                            f"Skipping point {idx} for {keyword}: invalid value '{item.get('value')}'"
                        )
                        failed += 1
                        continue

                    point = TrendPoint(
                        keyword=keyword,
                        source=source,
                        timestamp=ts,
                        value=value,
                        metadata={
                            "period": item.get("period", date_str),
                        },
                    )
                    original_period = str(item.get("period", date_str))
                else:
                    logger.warning(
                        "Skipping point %s for %s: unsupported type '%s'",
                        idx,
                        keyword,
                        type(item).__name__,
                    )
                    failed += 1
                    continue

                # 메타데이터 JSON 생성
                meta_dict = metadata.copy() if metadata else {}
                meta_dict.update(point.metadata)
                meta_dict.update({"original_period": original_period})
                meta_json = json.dumps(meta_dict, ensure_ascii=False)

                try:
                    conn.execute(
                        """
                        INSERT INTO trend_points
                        (source, keyword, ts, value_normalized, meta_json)
                        VALUES (?, ?, ?, ?, ?)
                        ON CONFLICT (source, keyword, ts)
                        DO UPDATE SET
                            value_normalized = EXCLUDED.value_normalized,
                            meta_json = EXCLUDED.meta_json
                    """,
                        [
                            point.source or source,
                            point.keyword or keyword,
                            ts,
                            point.value,
                            meta_json,
                        ],
                    )
                    inserted += 1
                except duckdb.IntegrityError as e:
                    logger.error(f"Integrity error inserting {source}/{keyword}/{ts}: {e}")
                    failed += 1
                except Exception as e:
                    logger.error(f"Failed to insert point {idx} for {keyword}: {e}", exc_info=True)
                    failed += 1

            except Exception as e:
                logger.error(f"Unexpected error processing point {idx}: {e}", exc_info=True)
                failed += 1

        try:
            conn.commit()
            logger.info(f"Saved {inserted} points for {source}/{keyword} ({failed} failed)")
        except Exception as e:
            logger.error(f"Failed to commit transaction: {e}", exc_info=True)
            conn.rollback()
            return 0

        return inserted

    except duckdb.CatalogException as e:
        logger.error(f"Database catalog error: {e}", exc_info=True)
        raise StorageError(f"Database catalog error while saving trend points: {e}") from e
    except duckdb.IOException as e:
        logger.error(f"Database I/O error: {e}", exc_info=True)
        raise StorageError(f"Database I/O error while saving trend points: {e}") from e
    except Exception as e:
        logger.error(f"Unexpected error in save_trend_points: {e}", exc_info=True)
        raise StorageError(f"Unexpected storage error while saving trend points: {e}") from e
    finally:
        if conn is not None:
            try:
                conn.close()
            except Exception as e:
                logger.warning(f"Error closing database connection: {e}")


def query_trend_points(
    source: Optional[str] = None,
    keyword: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db_path: Optional[Path] = None,
) -> list[TrendPoint]:
    """트렌드 포인트를 조회합니다.

    Args:
        source: 데이터 소스 필터 (google, naver)
        keyword: 키워드 필터
        start_date: 시작일 (YYYY-MM-DD)
        end_date: 종료일 (YYYY-MM-DD)
        db_path: DuckDB 파일 경로

    Returns:
        트렌드 포인트 리스트
    """
    db_file = _get_db_path(db_path)

    if not db_file.exists():
        logger.debug(f"Database file not found: {db_file}")
        return []

    conn = None
    try:
        conn = duckdb.connect(str(db_file))
        _ensure_table_exists(conn)

        where_clauses = []
        params = []

        if source:
            where_clauses.append("source = ?")
            params.append(source)

        if keyword:
            where_clauses.append("keyword = ?")
            params.append(keyword)

        if start_date:
            where_clauses.append("ts >= ?")
            params.append(start_date)

        if end_date:
            where_clauses.append("ts <= ?")
            params.append(end_date)

        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

        query = f"""
            SELECT source, keyword, ts, value_normalized, meta_json
            FROM trend_points
            WHERE {where_sql}
            ORDER BY ts ASC
        """

        try:
            result = conn.execute(query, params).fetchall()
            logger.debug(f"Query returned {len(result)} rows")
        except Exception as e:
            logger.error(f"Query execution failed: {e}", exc_info=True)
            return []

        points: list[TrendPoint] = []
        for row in result:
            metadata = json.loads(row[4]) if row[4] else {}
            points.append(
                TrendPoint.from_dict(
                    {
                        "source": row[0],
                        "keyword": row[1],
                        "ts": row[2],
                        "value_normalized": round(float(row[3]), 4),
                        "metadata": metadata,
                    }
                )
            )

        return points

    except duckdb.IOException as e:
        logger.error(f"Database I/O error during query: {e}", exc_info=True)
        return []
    except Exception as e:
        logger.error(f"Unexpected error in query_trend_points: {e}", exc_info=True)
        return []
    finally:
        if conn is not None:
            try:
                conn.close()
            except Exception as e:
                logger.warning(f"Error closing database connection: {e}")


def delete_older_than(days: int, db_path: Optional[Path] = None) -> int:
    """trend_points 테이블에서 days일보다 오래된 레코드를 삭제한다.

    Args:
        days: 보존 기간 (일 단위)
        db_path: DuckDB 파일 경로

    Returns:
        삭제된 레코드 수
    """
    db_file = _get_db_path(db_path)
    if not db_file.exists():
        return 0

    cutoff = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=days)
    conn = None
    try:
        conn = duckdb.connect(str(db_file))
        _ensure_table_exists(conn)
        conn.execute("BEGIN TRANSACTION")
        count_row = conn.execute(
            "SELECT COUNT(*) FROM trend_points WHERE ts < ?", [cutoff]
        ).fetchone()
        to_delete = int(count_row[0]) if count_row else 0
        conn.execute("DELETE FROM trend_points WHERE ts < ?", [cutoff])
        conn.commit()
        logger.info(f"Deleted {to_delete} trend points older than {days} days")
        return to_delete
    except Exception as e:
        logger.error(f"Failed to delete old trend points: {e}", exc_info=True)
        raise StorageError(f"Failed to delete old trend points: {e}") from e
    finally:
        if conn is not None:
            try:
                conn.close()
            except Exception as close_err:
                logger.warning(f"Error closing connection after delete: {close_err}")


def get_keywords_by_set(
    set_name: str,
    db_path: Optional[Path] = None,
) -> list[str]:
    """특정 키워드 세트에 속한 모든 키워드를 반환합니다.

    Args:
        set_name: 키워드 세트 이름
        db_path: DuckDB 파일 경로

    Returns:
        키워드 리스트
    """
    db_file = _get_db_path(db_path)

    if not db_file.exists():
        logger.debug(f"Database file not found: {db_file}")
        return []

    conn = None
    try:
        conn = duckdb.connect(str(db_file))
        _ensure_table_exists(conn)

        try:
            result = conn.execute(
                """
                SELECT DISTINCT keyword
                FROM trend_points
                WHERE meta_json LIKE ?
            """,
                [f'%"set_name": "{set_name}"%'],
            ).fetchall()
            logger.debug(f"Found {len(result)} keywords for set '{set_name}'")
        except Exception as e:
            logger.error(f"Query failed for set '{set_name}': {e}", exc_info=True)
            return []

        return [row[0] for row in result]

    except duckdb.IOException as e:
        logger.error(f"Database I/O error: {e}", exc_info=True)
        return []
    except Exception as e:
        logger.error(f"Unexpected error in get_keywords_by_set: {e}", exc_info=True)
        return []
    finally:
        if conn is not None:
            try:
                conn.close()
            except Exception as e:
                logger.warning(f"Error closing database connection: {e}")

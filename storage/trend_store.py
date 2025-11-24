# -*- coding: utf-8 -*-
"""트렌드 데이터를 DuckDB에 저장하는 모듈."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

import duckdb


def _get_db_path(db_path: Path | None = None) -> Path:
    """DB 파일 경로를 반환합니다."""
    if db_path is None:
        return Path(__file__).parent.parent / "data" / "trendradar.duckdb"
    return db_path


def _ensure_table_exists(conn: duckdb.DuckDBPyConnection) -> None:
    """trend_points 테이블이 없으면 생성합니다."""
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


def save_trend_points(
    source: str,
    keyword: str,
    points: list[dict[str, Any]],
    metadata: dict[str, Any] | None = None,
    db_path: Path | None = None,
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

    conn = duckdb.connect(str(db_file))

    try:
        _ensure_table_exists(conn)

        inserted = 0
        for point in points:
            date_str = point.get("date")
            value = point.get("value", 0.0)

            # 날짜 파싱
            try:
                ts = datetime.fromisoformat(date_str)
            except ValueError:
                # "2024-01" 형식 (월 단위)
                if len(date_str) == 7:
                    ts = datetime.fromisoformat(f"{date_str}-01")
                else:
                    continue

            # 메타데이터 JSON 생성
            meta_dict = metadata.copy() if metadata else {}
            meta_dict.update({
                "original_period": point.get("period", date_str),
            })
            meta_json = json.dumps(meta_dict, ensure_ascii=False)

            # INSERT OR REPLACE
            conn.execute("""
                INSERT OR REPLACE INTO trend_points
                (source, keyword, ts, value_normalized, meta_json)
                VALUES (?, ?, ?, ?, ?)
            """, [source, keyword, ts, value, meta_json])

            inserted += 1

        conn.commit()
        return inserted

    finally:
        conn.close()


def query_trend_points(
    source: str | None = None,
    keyword: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    db_path: Path | None = None,
) -> list[dict[str, Any]]:
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
        return []

    conn = duckdb.connect(str(db_file))

    try:
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

        result = conn.execute(query, params).fetchall()

        return [
            {
                "source": row[0],
                "keyword": row[1],
                "ts": row[2],
                "value": row[3],
                "metadata": json.loads(row[4]) if row[4] else {},
            }
            for row in result
        ]

    finally:
        conn.close()


def get_keywords_by_set(
    set_name: str,
    db_path: Path | None = None,
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
        return []

    conn = duckdb.connect(str(db_file))

    try:
        _ensure_table_exists(conn)

        result = conn.execute("""
            SELECT DISTINCT keyword
            FROM trend_points
            WHERE meta_json LIKE ?
        """, [f'%"set_name": "{set_name}"%']).fetchall()

        return [row[0] for row in result]

    finally:
        conn.close()

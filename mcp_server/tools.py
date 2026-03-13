from __future__ import annotations

import re
from datetime import datetime, timedelta
from pathlib import Path

import duckdb

from analyzers.spike_detector import SpikeDetector, SpikeSignal
from nl_query import parse_query
from storage.search_index import SearchIndex, SearchResult


_ALLOWED_SQL = re.compile(r"^\s*(SELECT|WITH|EXPLAIN)\b", re.IGNORECASE)
_SPIKE_LABELS = {
    "surge": "sudden_spike",
    "emerging": "gradual_rise",
    "viral": "sustained_high",
}


def handle_search(*, search_db_path: Path, db_path: Path, query: str, limit: int = 20) -> str:
    parsed = parse_query(query)
    search_text = parsed.search_text or parsed.original_query
    if not search_text:
        return "No results found."

    effective_limit = parsed.limit if parsed.limit > 0 else limit
    idx = SearchIndex(search_db_path)
    results = idx.search(search_text, limit=effective_limit)

    if parsed.days is not None:
        results = _filter_results_by_days(db_path=db_path, results=results, days=parsed.days)

    if not results:
        return "No results found."

    lines = [f"Found {len(results)} result(s):"]
    for result in results:
        lines.append(f"- {result.keyword} | {result.platform}")
        lines.append(f"  Link: {result.link}")
        lines.append(f"  Context: {result.context}")
    return "\n".join(lines)


def handle_recent_updates(*, db_path: Path, days: int = 7, limit: int = 20) -> str:
    if limit <= 0:
        return "No recent updates found."

    cutoff = datetime.now() - timedelta(days=days)
    conn = duckdb.connect(str(db_path), read_only=True)
    try:
        rows = conn.execute(
            """
            SELECT keyword, source, value_normalized, ts, created_at
            FROM trend_points
            WHERE created_at >= ?
            ORDER BY created_at DESC
            LIMIT ?
            """,
            [cutoff, limit],
        ).fetchall()
    except Exception:
        return "No recent updates found."
    finally:
        conn.close()

    if not rows:
        return "No recent updates found."

    lines = [f"Recent updates ({len(rows)}):"]
    for row in rows:
        keyword = str(row[0])
        source = str(row[1])
        value = float(row[2])
        ts = str(row[3])
        created_at = str(row[4])
        lines.append(
            f"- {keyword} | {source} | value={value} | ts={ts} | collected_at={created_at}"
        )
    return "\n".join(lines)


def handle_sql(*, db_path: Path, query: str) -> str:
    if not _ALLOWED_SQL.match(query):
        return "Error: Only SELECT/WITH/EXPLAIN queries are allowed."

    conn = duckdb.connect(str(db_path), read_only=True)
    try:
        cursor = conn.execute(query)
        rows = cursor.fetchall()
        columns = [str(desc[0]) for desc in (cursor.description or [("result",)])]
        return _format_rows(columns, rows)
    except Exception as exc:  # noqa: BLE001
        return f"Error: {exc}"
    finally:
        conn.close()


def handle_top_trends(*, db_path: Path, days: int = 7, limit: int = 10) -> str:
    detector = SpikeDetector(db_path=db_path, recent_days=days, baseline_days=max(30, days * 4))
    spikes = detector.detect_all_spikes(source=None, top_n=limit)

    records: list[tuple[str, SpikeSignal]] = []
    for spike_key in ("surge", "emerging", "viral"):
        label = _SPIKE_LABELS.get(spike_key, spike_key)
        for signal in spikes.get(spike_key, []):
            records.append((label, signal))

    if not records:
        return _fallback_top_trends(db_path=db_path, days=days, limit=limit)

    lines = ["Top trend spikes:"]
    for label, signal in records[:limit]:
        lines.append(
            f"- {signal.keyword} | {signal.source} | {label} | score={signal.spike_score:.1f} | "
            + f"ratio={signal.spike_ratio:.2f}"
        )
    return "\n".join(lines)


def handle_price_watch() -> str:
    return "Not available in TrendRadar"


def _filter_results_by_days(
    *, db_path: Path, results: list[SearchResult], days: int
) -> list[SearchResult]:
    if not results:
        return []
    if not db_path.exists():
        return results

    cutoff = datetime.now() - timedelta(days=days)
    conn = duckdb.connect(str(db_path), read_only=True)
    try:
        filtered: list[SearchResult] = []
        for result in results:
            row = conn.execute(
                """
                SELECT 1
                FROM trend_points
                WHERE keyword = ? AND source = ? AND created_at >= ?
                LIMIT 1
                """,
                [result.keyword, result.platform, cutoff],
            ).fetchone()
            if row:
                filtered.append(result)
    except Exception:
        return []
    finally:
        conn.close()
    return filtered


def _format_rows(columns: list[str], rows: list[tuple[object, ...]]) -> str:
    if not rows:
        return "No rows returned."

    text_rows = [tuple("" if value is None else str(value) for value in row) for row in rows]
    widths = [len(name) for name in columns]
    for row in text_rows:
        for idx, value in enumerate(row):
            widths[idx] = max(widths[idx], len(value))

    header = " | ".join(column.ljust(widths[idx]) for idx, column in enumerate(columns))
    divider = "-+-".join("-" * widths[idx] for idx in range(len(columns)))
    body = [
        " | ".join(value.ljust(widths[idx]) for idx, value in enumerate(row)) for row in text_rows
    ]
    return "\n".join([header, divider, *body])


def _fallback_top_trends(*, db_path: Path, days: int, limit: int) -> str:
    cutoff = datetime.now() - timedelta(days=days)
    conn = duckdb.connect(str(db_path), read_only=True)
    try:
        rows = conn.execute(
            """
            SELECT keyword, source, AVG(value_normalized) AS avg_value, MAX(value_normalized) AS peak
            FROM trend_points
            WHERE created_at >= ?
            GROUP BY keyword, source
            ORDER BY peak DESC
            LIMIT ?
            """,
            [cutoff, limit],
        ).fetchall()
    except Exception:
        return "No trend data available."
    finally:
        conn.close()

    if not rows:
        return "No trend data available."

    lines = ["Top trend spikes:"]
    for row in rows:
        keyword = str(row[0])
        source = str(row[1])
        avg_value = float(row[2])
        peak = float(row[3])
        lines.append(
            f"- {keyword} | {source} | sustained_high | avg={avg_value:.2f} | peak={peak:.2f}"
        )
    return "\n".join(lines)

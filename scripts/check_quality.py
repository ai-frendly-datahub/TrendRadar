#!/usr/bin/env python3
"""Run DuckDB data quality checks."""

from __future__ import annotations

import sys
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any

import duckdb


PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from trendradar.common.quality_checks import run_all_checks  # noqa: E402
from trendradar.quality_report import (  # noqa: E402
    build_quality_report,
    load_keyword_quality_config,
    write_quality_report,
)
from storage import trend_store  # noqa: E402


def _quality_output_dir(project_root: Path, config: dict[str, Any]) -> Path:
    quality_outputs = (
        config.get("data_quality", {}).get("quality_outputs", {})
        if isinstance(config.get("data_quality"), dict)
        else {}
    )
    latest_path = Path(str(quality_outputs.get("latest", "docs/reports/trend_quality.json")))
    return latest_path.parent if latest_path.is_absolute() else project_root / latest_path.parent


def _latest_trend_point_date(db_path: Path) -> date | None:
    if not db_path.exists():
        return None
    try:
        with duckdb.connect(str(db_path), read_only=True) as con:
            row = con.execute("SELECT MAX(timestamp) FROM trend_points").fetchone()
    except duckdb.Error:
        return None
    if not row or row[0] is None:
        return None
    value = row[0]
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.date()
        return value.astimezone(UTC).date()
    if isinstance(value, date):
        return value
    if isinstance(value, str) and value.strip():
        text = value.strip()
        try:
            return datetime.fromisoformat(text.replace("Z", "+00:00")).date()
        except ValueError:
            try:
                return date.fromisoformat(text[:10])
            except ValueError:
                return None
    return None


def generate_quality_artifacts(project_root: Path = PROJECT_ROOT) -> tuple[dict[str, str], dict[str, Any]]:
    config_path = project_root / "config" / "keyword_sets.yaml"
    db_path = project_root / "data" / "trendradar.duckdb"
    quality_config = load_keyword_quality_config(config_path)
    output_dir = _quality_output_dir(project_root, quality_config)
    target_date = _latest_trend_point_date(db_path) or datetime.now(UTC).date()
    start_date = target_date.replace(day=1).isoformat()
    end_date = (target_date + timedelta(days=1)).isoformat()
    trend_points = trend_store.query_trend_points(
        start_date=start_date,
        end_date=end_date,
        db_path=db_path,
    )
    report = build_quality_report(
        quality_config,
        target_date=target_date,
        trend_points=trend_points,
    )
    paths = write_quality_report(report, output_dir, target_date=target_date)
    return paths, report


def main() -> None:
    db_path = PROJECT_ROOT / "data" / "trendradar.duckdb"
    if not db_path.exists():
        print(f"not_applicable: database not yet generated at {db_path}")
        sys.exit(0)

    with duckdb.connect(str(db_path), read_only=True) as con:
        run_all_checks(
            con,
            table_name="trend_points",
            null_conditions={
                "source": "source IS NULL OR source = ''",
                "keyword": "keyword IS NULL OR keyword = ''",
                "timestamp": "timestamp IS NULL",
                "value": "value IS NULL",
            },
            text_columns=["source", "keyword"],
            language_column=None,
            url_column=None,
            date_column="timestamp",
        )

    paths, report = generate_quality_artifacts(PROJECT_ROOT)
    summary = report["summary"]
    print(f"quality_report={paths['latest']}")
    print(f"enabled_pack_count={summary['enabled_pack_count']}")
    print(f"collected_signal_count={summary['collected_signal_count']}")
    print(f"attention_signal_count={summary['attention_signal_count']}")
    print(f"conversion_proxy_signal_count={summary['conversion_proxy_signal_count']}")
    print(f"daily_review_item_count={summary['daily_review_item_count']}")


if __name__ == "__main__":
    main()

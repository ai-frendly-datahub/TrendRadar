#!/usr/bin/env python3
"""Run DuckDB data quality checks."""

from __future__ import annotations

import sys
from pathlib import Path

import duckdb


PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from trendradar.common.quality_checks import run_all_checks  # noqa: E402


def main() -> None:
    db_path = PROJECT_ROOT / "data" / "trendradar.duckdb"
    if not db_path.exists():
        print(f"Database not found: {db_path}")
        sys.exit(1)

    with duckdb.connect(str(db_path), read_only=True) as con:
        run_all_checks(
            con,
            table_name="trend_points",
            null_conditions={
                "source": "source IS NULL OR source = ''",
                "keyword": "keyword IS NULL OR keyword = ''",
                "ts": "ts IS NULL",
                "value_normalized": "value_normalized IS NULL",
            },
            text_columns=["source", "keyword"],
            date_column="ts",
        )


if __name__ == "__main__":
    main()

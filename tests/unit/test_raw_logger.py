from __future__ import annotations

import json
from datetime import UTC, date, datetime

import pytest

from raw_logger import RawLogger


@pytest.mark.unit
def test_raw_logger_writes_jsonl_records(tmp_path):
    logger = RawLogger(tmp_path / "raw")
    records = [
        {
            "keyword": "ai",
            "platform": "google",
            "value": 82.5,
            "timestamp": "2026-03-01T00:00:00",
        },
        {
            "keyword": "llm",
            "platform": "naver",
            "value": 64.0,
            "timestamp": "2026-03-01T01:00:00",
        },
    ]

    output_path = logger.log(records, source_name="google")

    assert output_path.name == "google.jsonl"
    assert output_path.parent.name == datetime.now(tz=UTC).date().isoformat()
    assert output_path.parent.parent.name == "raw"

    lines = output_path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2
    assert json.loads(lines[0])["keyword"] == "ai"
    assert json.loads(lines[1])["platform"] == "naver"

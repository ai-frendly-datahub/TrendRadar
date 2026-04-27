from __future__ import annotations

import json
from collections.abc import Iterable
from datetime import UTC, datetime
from pathlib import Path


class RawLogger:
    raw_dir: Path

    def __init__(self, raw_dir: Path):
        self.raw_dir = raw_dir

    def log(self, records: Iterable[dict[str, object]], *, source_name: str) -> Path:
        """Log trend data dicts to JSONL."""
        target_dir = self.raw_dir / datetime.now(tz=UTC).date().isoformat()
        target_dir.mkdir(parents=True, exist_ok=True)

        safe_source_name = source_name.replace("/", "_").replace("\\", "_")
        output_path = target_dir / f"{safe_source_name}.jsonl"

        with output_path.open("a", encoding="utf-8") as fp:
            for record in records:
                _ = fp.write(json.dumps(record, ensure_ascii=False))
                _ = fp.write("\n")

        return output_path

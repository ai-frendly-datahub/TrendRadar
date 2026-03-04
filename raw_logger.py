from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any, Iterable


class RawLogger:
    def __init__(self, raw_dir: Path):
        self.raw_dir = raw_dir

    def log(self, records: Iterable[dict[str, Any]], *, source_name: str) -> Path:
        """Log trend data dicts to JSONL."""
        target_dir = self.raw_dir / date.today().isoformat()
        target_dir.mkdir(parents=True, exist_ok=True)

        safe_source_name = source_name.replace("/", "_").replace("\\", "_")
        output_path = target_dir / f"{safe_source_name}.jsonl"

        with output_path.open("w", encoding="utf-8") as fp:
            for record in records:
                fp.write(json.dumps(record, ensure_ascii=False))
                fp.write("\n")

        return output_path

from __future__ import annotations

import json
from collections.abc import Iterable
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


class RawLogger:
    raw_dir: Path

    def __init__(self, raw_dir: Path):
        self.raw_dir = raw_dir

    def log(
        self,
        records: Iterable[dict[str, object]],
        *,
        source_name: str,
        run_id: Optional[str] = None,
    ) -> Path:
        """Log trend data dicts to JSONL."""
        target_dir = self.raw_dir / datetime.now(timezone.utc).date().isoformat()
        target_dir.mkdir(parents=True, exist_ok=True)

        safe_source_name = source_name.replace("/", "_").replace("\\", "_")
        output_path = (
            target_dir / f"{safe_source_name}_{run_id}.jsonl"
            if run_id is not None
            else target_dir / f"{safe_source_name}.jsonl"
        )

        existing_links: set[str] = set()
        if run_id is not None and output_path.exists():
            try:
                with output_path.open("r", encoding="utf-8") as file_obj:
                    for line in file_obj:
                        if not line.strip():
                            continue
                        record = json.loads(line)
                        link = record.get("link") or record.get("url")
                        if isinstance(link, str) and link:
                            existing_links.add(link)
            except (json.JSONDecodeError, OSError):
                pass

        with output_path.open("a", encoding="utf-8") as fp:
            for record in records:
                link = record.get("link") or record.get("url")
                if run_id is not None and isinstance(link, str) and link in existing_links:
                    continue

                _ = fp.write(json.dumps(record, ensure_ascii=False))
                _ = fp.write("\n")

                if run_id is not None and isinstance(link, str) and link:
                    existing_links.add(link)

        return output_path

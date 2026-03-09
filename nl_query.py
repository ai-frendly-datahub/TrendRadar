from __future__ import annotations
from typing import Optional

import re
from dataclasses import dataclass


DEFAULT_LIMIT = 20


@dataclass(frozen=True)
class ParsedQuery:
    original_query: str
    search_text: str
    days: Optional[int]
    limit: int


def parse_query(query: str) -> ParsedQuery:
    normalized = " ".join(query.strip().split())
    working = normalized

    days: Optional[int] = None
    limit = DEFAULT_LIMIT

    day_match = re.search(r"(?:최근\s*(\d+)\s*일|last\s*(\d+)\s*days?)", working, re.IGNORECASE)
    if day_match:
        days = int(day_match.group(1) or day_match.group(2))
        working = _remove_match(working, day_match)

    limit_match = re.search(r"(?:\b(?:limit|top)\s*(\d+)\b|(\d+)\s*개)", working, re.IGNORECASE)
    if limit_match:
        limit = int(limit_match.group(1) or limit_match.group(2))
        working = _remove_match(working, limit_match)

    search_text = " ".join(working.split())
    return ParsedQuery(
        original_query=normalized,
        search_text=search_text,
        days=days,
        limit=limit,
    )


def _remove_match(text: str, match: re.Match[str]) -> str:
    return f"{text[:match.start()]} {text[match.end():]}"

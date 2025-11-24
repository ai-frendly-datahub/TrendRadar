# -*- coding: utf-8 -*-
"""Google Trends real-time / daily trending collector (no auth)."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from pytrends.request import TrendReq


class GoogleTrendingCollector:
    """Collect trending keywords without authentication using pytrends."""

    def __init__(self, hl: str = "ko", tz: int = 540):
        """
        Args:
            hl: Interface language for pytrends.
            tz: Timezone offset in minutes (default 540 = UTC+9).
        """
        self.pytrends = TrendReq(hl=hl, tz=tz)

    def collect(
        self,
        *,
        region: str = "south_korea",
        mode: str = "daily",
        category: str | None = None,
        top_n: int = 20,
        date_override: str | None = None,
    ) -> dict[str, list[dict[str, Any]]]:
        """Fetch trending searches.

        Args:
            region: Region code used by pytrends (e.g., 'korea', 'united_states').
            mode: 'daily' for daily trending, 'realtime' for real-time trending.
            category: Optional category for real-time (pytrends cat code, e.g., 'all', 'b', 'e').
            top_n: Limit number of returned keywords.
            date_override: Optional date (YYYY-MM-DD) to store; defaults to today UTC.

        Returns:
            Mapping keyword -> list of points [{date, value, timestamp}], where value is rank (1 = most popular).
        """
        today = datetime.now(timezone.utc).date()
        date_str = date_override or today.isoformat()

        keywords: list[str] = []

        if mode not in {"daily", "realtime"}:
            raise ValueError("mode must be 'daily' or 'realtime'")

        try:
            if mode == "daily":
                df = self.pytrends.trending_searches(pn=region)
                if df is not None and not df.empty:
                    keywords = df.iloc[:, 0].dropna().astype(str).tolist()
            elif mode == "realtime":
                cat = category or "all"
                geo = self._normalize_realtime_region(region)
                df = self.pytrends.realtime_trending_searches(pn=geo, cat=cat, count=top_n)
                if df is not None and not df.empty:
                    # pytrends returns column 'title' for realtime trending.
                    if "title" in df.columns:
                        keywords = df["title"].dropna().astype(str).tolist()
                    else:
                        keywords = df.iloc[:, 0].dropna().astype(str).tolist()
        except Exception as exc:
            logging.warning("Google trending fetch failed (%s): %s", mode, exc)
            keywords = []

        keywords = keywords[:top_n]

        results: dict[str, list[dict[str, Any]]] = {}
        timestamp = datetime.now(timezone.utc).isoformat()

        for idx, kw in enumerate(keywords, start=1):
            results[kw] = [
                {
                    "date": date_str,
                    "value": float(idx),  # rank as value (1 = highest)
                    "timestamp": timestamp,
                }
            ]

        return results

    @staticmethod
    def _normalize_realtime_region(region: str) -> str:
        """Map readable region names to geo codes expected by realtime API."""
        mapping = {
            "south_korea": "KR",
            "korea": "KR",
            "united_states": "US",
            "united_kingdom": "GB",
        }
        if len(region) == 2:
            return region.upper()
        return mapping.get(region.lower(), "US")

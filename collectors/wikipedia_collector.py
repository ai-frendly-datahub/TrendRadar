# -*- coding: utf-8 -*-
"""Wikipedia Pageviews Collector (no auth)."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any
from urllib.parse import quote

import requests


class WikipediaPageviewsCollector:
    """Collect daily pageviews for given article titles from Wikimedia REST API.

    API docs:
    https://wikitech.wikimedia.org/wiki/Analytics/AQS/Pageviews
    """

    BASE_URL = "https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article"

    def __init__(self, user_agent: str | None = None, timeout: int = 15):
        """
        Args:
            user_agent: Optional User-Agent header value. If not provided,
                a default TrendRadar UA is used.
            timeout: Request timeout in seconds.
        """
        self.user_agent = (
            user_agent
            or "TrendRadar/0.1 (wikipedia collector; https://wikimedia.org/api/rest_v1/)"
        )
        self.timeout = timeout

    @staticmethod
    def _to_api_date(date_str: str) -> str:
        """Convert YYYY-MM-DD to YYYYMMDD00 format required by the API."""
        dt = datetime.fromisoformat(date_str)
        return dt.strftime("%Y%m%d00")

    def collect(
        self,
        keywords: list[str],
        start_date: str,
        end_date: str,
        project: str = "ko.wikipedia",
        access: str = "all-access",
        agent: str = "user",
        granularity: str = "daily",
    ) -> dict[str, list[dict[str, Any]]]:
        """Fetch pageview stats for the given article titles.

        Args:
            keywords: Article titles (spaces are automatically converted to underscores).
            start_date: Start date YYYY-MM-DD.
            end_date: End date YYYY-MM-DD.
            project: Wiki project (e.g., ko.wikipedia, en.wikipedia).
            access: Access channel (all-access, desktop, mobile-web, mobile-app).
            agent: Agent type (user, spider, bot).
            granularity: daily or monthly.

        Returns:
            Mapping of keyword to list of {date, value, timestamp}.
        """
        if not start_date or not end_date:
            raise ValueError("start_date and end_date are required (YYYY-MM-DD)")

        start = self._to_api_date(start_date)
        end = self._to_api_date(end_date)

        headers = {"User-Agent": self.user_agent}

        results: dict[str, list[dict[str, Any]]] = {}

        for keyword in keywords:
            article = quote(keyword.replace(" ", "_"))
            url = (
                f"{self.BASE_URL}/{project}/{access}/{agent}/"
                f"{article}/{granularity}/{start}/{end}"
            )

            try:
                resp = requests.get(url, headers=headers, timeout=self.timeout)
                if resp.status_code == 404:
                    # Missing article or no data; treat as empty result.
                    results[keyword] = []
                    continue

                resp.raise_for_status()
                data = resp.json()

            except requests.RequestException as exc:
                logging.exception("Wikipedia API request failed: %s", exc)
                raise RuntimeError(f"Wikipedia API request failed: {exc}") from exc

            points = []
            for item in data.get("items", []):
                timestamp = item.get("timestamp")  # e.g., 2024010100
                if not timestamp or len(timestamp) < 8:
                    continue

                date_part = timestamp[:8]
                date_str = f"{date_part[:4]}-{date_part[4:6]}-{date_part[6:]}"

                points.append(
                    {
                        "date": date_str,
                        "value": int(item.get("views", 0)),
                        "timestamp": timestamp,
                    }
                )

            results[keyword] = points

        return results

from __future__ import annotations

import importlib
from datetime import UTC, datetime

from trendradar.models import ContentItem


class BrowserTrendingCollector:
    def __init__(self, timeout_ms: int = 20_000) -> None:
        self.timeout_ms = timeout_ms

    def collect(self, url: str, limit: int = 20) -> list[ContentItem]:
        try:
            browser_module = importlib.import_module("radar_core.browser_collector")
            collect_browser_sources = getattr(browser_module, "collect_browser_sources")
        except ImportError:
            return []

        source = {
            "name": "browser_trending",
            "type": "browser",
            "url": url,
            "config": {
                "timeout": self.timeout_ms,
                "wait_for": "a",
                "title_selector": "title",
                "content_selector": "main, body",
                "link_selector": "a[href]",
            },
        }

        try:
            articles, _errors = collect_browser_sources(
                [source],
                category="trend",
                timeout=self.timeout_ms,
            )
        except Exception:
            return []

        now = datetime.now(UTC)
        return [
            ContentItem(
                title=article.title,
                url=article.link,
                source="browser_trending",
                author="browser",
                score=1.0,
                metadata={
                    "collected_at": now.isoformat(),
                    "summary": article.summary,
                },
            )
            for article in articles[:limit]
            if article.link
        ]

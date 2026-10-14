"""Keyless Google Trends daily RSS collector.

The public feed ``https://trends.google.com/trending/rss?geo=KR`` does not use an
API key. It replaces the retired pytrends daily trending-searches endpoint.
"""

from __future__ import annotations

from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from xml.etree import ElementTree as ET

import requests

from trendradar.models import TrendPoint

HT_NS = "{https://trends.google.com/trending/rss}"
FEED_URL = "https://trends.google.com/trending/rss"
USER_AGENT = "TrendRadar/0.1 (google trends rss; +https://github.com/ai-frendly-datahub/TrendRadar)"


def _traffic_lower_bound(text: str) -> float:
    """Parse values such as ``200+`` or ``10K+`` into a numeric lower bound."""
    cleaned = text.strip().rstrip("+").replace(",", "").upper()
    if not cleaned:
        return 0.0
    multiplier = 1.0
    if cleaned.endswith("K"):
        multiplier = 1_000.0
        cleaned = cleaned[:-1]
    elif cleaned.endswith("M"):
        multiplier = 1_000_000.0
        cleaned = cleaned[:-1]
    try:
        return float(cleaned) * multiplier
    except ValueError:
        return 0.0


def parse_google_trends_rss(
    xml_text: str,
    *,
    geo: str,
    top_n: int = 20,
    source: str = "google_trending",
) -> dict[str, list[TrendPoint]]:
    """Parse a Google Trends RSS document into ranked trend points."""
    if top_n < 1:
        return {}

    root = ET.fromstring(xml_text)
    results: dict[str, list[TrendPoint]] = {}
    for index, item in enumerate(root.findall("./channel/item"), start=1):
        if len(results) >= top_n:
            break
        title = (item.findtext("title") or "").strip()
        if not title or title in results:
            continue

        traffic_text = (item.findtext(f"{HT_NS}approx_traffic") or "").strip()
        published_text = item.findtext("pubDate")
        timestamp = datetime.now(UTC)
        if published_text:
            try:
                parsed = parsedate_to_datetime(published_text)
                timestamp = parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)
            except (TypeError, ValueError, IndexError):
                timestamp = datetime.now(UTC)

        news_url = ""
        news = item.find(f"{HT_NS}news_item/{HT_NS}news_item_url")
        if news is not None and news.text:
            news_url = news.text.strip()

        value = _traffic_lower_bound(traffic_text)
        if value <= 0:
            value = float(index)

        results[title] = [
            TrendPoint(
                keyword=title,
                source=source,
                timestamp=timestamp,
                value=value,
                metadata={
                    "geo": geo,
                    "rank": index,
                    "approx_traffic": traffic_text,
                    "news_url": news_url,
                    "feed": "google_trends_rss",
                },
            )
        ]
    return results


class GoogleTrendsRssCollector:
    """Collect daily trending searches from the public Google Trends RSS feed."""

    def collect(self, *, geo: str = "KR", top_n: int = 20) -> dict[str, list[TrendPoint]]:
        response = requests.get(
            FEED_URL,
            params={"geo": geo},
            headers={"User-Agent": USER_AGENT, "Accept": "application/rss+xml, application/xml"},
            timeout=20,
        )
        response.raise_for_status()
        return parse_google_trends_rss(response.text, geo=geo, top_n=top_n)

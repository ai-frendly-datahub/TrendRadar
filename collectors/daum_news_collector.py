"""Daum News Realtime Search Collector."""

from __future__ import annotations

import re
import time
from datetime import datetime

import requests
from bs4 import BeautifulSoup
from tenacity import retry, stop_after_attempt, wait_exponential

from trendradar.models import ContentItem


class DaumNewsCollector:
    """Daum 뉴스의 실시간 검색어를 수집합니다.

    Daum 뉴스 페이지에서 실시간 검색어 순위를 스크래핑합니다.
    - 실시간 검색어 순위 (1-20위)
    - 검색어별 뉴스 기사 수
    - 상승/하강 추세
    """

    BASE_URL = "https://news.daum.net"
    USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

    def __init__(self, timeout: int = 30, request_delay: float = 1.0):
        """
        Args:
            timeout: HTTP 요청 타임아웃 (초)
            request_delay: 요청 간 대기 시간 (초)
        """
        self.timeout = timeout
        self.request_delay = request_delay

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
    )
    def _fetch_html(self, url: str) -> str | None:
        """HTML 페이지 가져오기"""
        headers = {
            "User-Agent": self.USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
            "Referer": self.BASE_URL,
        }

        try:
            response = requests.get(url, headers=headers, timeout=self.timeout)
            response.raise_for_status()
            response.encoding = "utf-8"
            return response.text
        except requests.exceptions.RequestException as e:
            print(f"Daum News HTML 가져오기 실패 ({url}): {e}")
            raise

    def collect_realtime_keywords(self, limit: int = 20) -> list[ContentItem]:
        """실시간 검색어를 수집합니다.

        Args:
            limit: 최대 검색어 수 (1-20)

        Returns:
            실시간 검색어 리스트
            [
                {
                    "rank": 1,
                    "keyword": "검색어",
                    "article_count": 100,
                    "trend": "up|down|new",
                    "change": 5,  # 순위 변화
                    "url": "https://news.daum.net/search?q=...",
                    "collected_at": "2024-01-01T00:00:00Z"
                }
            ]
        """
        url = f"{self.BASE_URL}/search"

        time.sleep(self.request_delay)

        try:
            html_content = self._fetch_html(url)
        except Exception as e:
            print(f"Daum News 실시간 검색어 수집 실패: {e}")
            return []

        if not html_content:
            return []

        soup = BeautifulSoup(html_content, "html.parser")
        keywords = []

        # 실시간 검색어 섹션 찾기
        search_rank_section = soup.select_one("div.rank_news, div.realtime_keywords")

        if not search_rank_section:
            # 대체 선택자 시도
            search_rank_section = soup.select_one("section.rank_news")

        if not search_rank_section:
            print("Daum News 실시간 검색어 섹션을 찾을 수 없습니다")
            return []

        # 검색어 항목 추출
        keyword_items = search_rank_section.select("li, div.item")

        for idx, item in enumerate(keyword_items[:limit], 1):
            keyword_elem = item.select_one("a.link_keyword, a.keyword, span.keyword")
            if not keyword_elem:
                continue

            keyword = keyword_elem.get_text(strip=True)
            if not keyword:
                continue

            # 순위 추출
            rank_elem = item.select_one("span.rank, em.rank")
            rank = idx
            if rank_elem:
                rank_text = rank_elem.get_text(strip=True)
                rank_match = re.search(r"(\d+)", rank_text)
                if rank_match:
                    rank = int(rank_match.group(1))

            # 기사 수 추출
            article_count_elem = item.select_one("span.count, em.count")
            article_count = 0
            if article_count_elem:
                count_text = article_count_elem.get_text(strip=True)
                count_match = re.search(r"(\d+)", count_text)
                if count_match:
                    article_count = int(count_match.group(1))

            # 추세 판단 (상승/하강/신규)
            trend = "new"
            change = 0

            trend_elem = item.select_one("span.trend, em.trend")
            if trend_elem:
                trend_text = trend_elem.get_text(strip=True)
                if "상" in trend_text or "↑" in trend_text:
                    trend = "up"
                elif "하" in trend_text or "↓" in trend_text:
                    trend = "down"

                # 순위 변화 수 추출
                change_match = re.search(r"(\d+)", trend_text)
                if change_match:
                    change = int(change_match.group(1))

            # 검색 URL
            keyword_url = f"{self.BASE_URL}/search?q={keyword}"
            href = keyword_elem.get("href")
            if isinstance(href, str) and href:
                keyword_url = href
                if not keyword_url.startswith("http"):
                    keyword_url = self.BASE_URL + keyword_url

            keywords.append(
                ContentItem(
                    title=keyword,
                    url=keyword_url,
                    source="daum_news",
                    score=float(article_count),
                    metadata={
                        "rank": rank,
                        "article_count": article_count,
                        "trend": trend,
                        "change": change,
                        "collected_at": datetime.now().isoformat(),
                    },
                )
            )

        return keywords

    def collect(self) -> list[ContentItem]:
        """기본 수집 메서드"""
        return self.collect_realtime_keywords(limit=20)

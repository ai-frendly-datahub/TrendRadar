# -*- coding: utf-8 -*-
"""HackerNews Top Stories Collector."""

from __future__ import annotations

from typing import Any, ClassVar

import requests
from tenacity import retry, stop_after_attempt, wait_exponential
from trendradar.models import ContentItem


class HackerNewsCollector:
    """HackerNews에서 인기 스토리를 수집합니다.

    공식 Firebase API를 사용하여 인증 없이 수집 가능합니다.
    Rate limit: 10,000 requests/hour
    """

    API_BASE_URL: ClassVar[str] = "https://hacker-news.firebaseio.com/v0"
    TIMEOUT: ClassVar[int] = 30
    DEFAULT_HEADERS: dict[str, str] = {
        "User-Agent": "Mozilla/5.0 (compatible; TrendRadarBot/1.0; +https://github.com/zzragida/ai-frendly-datahub)",
    }

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
    )
    def _fetch_with_retry(self, url: str) -> list[int] | dict[str, Any]:
        """HTTP 요청을 재시도 로직과 함께 실행합니다."""
        response = requests.get(url, headers=self.DEFAULT_HEADERS, timeout=self.TIMEOUT)
        response.raise_for_status()
        return response.json()

    def collect(self, limit: int = 30) -> list[ContentItem]:
        """HackerNews 상위 스토리를 수집합니다.

        Args:
            limit: 수집할 스토리 개수 (기본값: 30)

        Returns:
            스토리 정보 리스트
        """
        stories: list[ContentItem] = []

        try:
            # 상위 스토리 ID 목록 가져오기
            top_stories_url = f"{self.API_BASE_URL}/topstories.json"
            story_ids_response = self._fetch_with_retry(top_stories_url)
            if not isinstance(story_ids_response, list):
                raise RuntimeError("Expected list of story IDs")
            story_ids: list[int] = story_ids_response

            # 상위 limit개의 스토리 ID만 처리
            for story_id in story_ids[:limit]:
                try:
                    # 각 스토리의 상세 정보 가져오기
                    item_url = f"{self.API_BASE_URL}/item/{story_id}.json"
                    item_response = self._fetch_with_retry(item_url)
                    if not isinstance(item_response, dict):
                        continue
                    item_data: dict[str, Any] = item_response

                    if item_data and item_data.get("type") == "story":
                        story = ContentItem(
                            title=str(item_data.get("title", "")),
                            url=str(item_data.get("url", "")),
                            source="hackernews",
                            author=str(item_data.get("by", "")),
                            score=float(item_data.get("score", 0)),
                            metadata={
                                "id": item_data.get("id"),
                                "time": item_data.get("time", 0),
                                "descendants": item_data.get("descendants", 0),
                                "type": item_data.get("type", "story"),
                            },
                        )
                        stories.append(story)

                except requests.exceptions.RequestException as e:
                    print(f"  - HackerNews story {story_id} fetch failed: {e}")
                    continue

            return stories

        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"HackerNews API 호출 실패: {e}") from e
        except Exception as e:
            raise RuntimeError(f"HackerNews 데이터 수집 실패: {e}") from e

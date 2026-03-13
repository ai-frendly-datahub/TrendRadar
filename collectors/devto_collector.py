"""Dev.to Articles Collector."""

from __future__ import annotations

from typing import Any, ClassVar

import requests
from tenacity import retry, stop_after_attempt, wait_exponential

from trendradar.models import ContentItem


class DevtoCollector:
    """Dev.to에서 인기 기술 글을 수집합니다.

    공식 API를 사용하여 인증 없이 수집 가능합니다.
    Rate limit: 10 requests/second
    """

    API_BASE_URL: ClassVar[str] = "https://dev.to/api"
    TIMEOUT: ClassVar[int] = 30
    DEFAULT_HEADERS: dict[str, str] = {
        "User-Agent": "Mozilla/5.0 (compatible; TrendRadarBot/1.0; +https://github.com/zzragida/ai-frendly-datahub)",
    }

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
    )
    def _fetch_with_retry(
        self, url: str, params: dict[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        """HTTP 요청을 재시도 로직과 함께 실행합니다."""
        response = requests.get(
            url,
            params=params,
            headers=self.DEFAULT_HEADERS,
            timeout=self.TIMEOUT,
        )
        response.raise_for_status()
        result = response.json()
        if not isinstance(result, list):
            raise RuntimeError("Expected list response from Dev.to API")
        return result

    def collect(self, limit: int = 30, tag: str | None = None) -> list[ContentItem]:
        """Dev.to 인기 기술 글을 수집합니다.

        Args:
            limit: 수집할 글 개수 (기본값: 30)
            tag: 특정 태그로 필터링 (선택)

        Returns:
            기술 글 정보 리스트
        """
        articles: list[ContentItem] = []

        try:
            # Dev.to API 엔드포인트
            articles_url = f"{self.API_BASE_URL}/articles"

            params: dict[str, Any] = {
                "top": 1,  # 최근 1일 인기글
                "per_page": min(limit, 1000),
            }

            if tag:
                params["tag"] = tag

            articles_data = self._fetch_with_retry(articles_url, params=params)

            for article in articles_data[:limit]:
                article_info = ContentItem(
                    title=str(article.get("title", "")),
                    url=str(article.get("url", "")),
                    source="devto",
                    author=str(article.get("user", {}).get("name", "")),
                    score=float(article.get("positive_reactions_count", 0)),
                    timestamp=None,
                    metadata={
                        "id": article.get("id"),
                        "slug": article.get("slug", ""),
                        "comments_count": article.get("comments_count", 0),
                        "published_at": article.get("published_at", ""),
                        "author_username": article.get("user", {}).get("username", ""),
                        "tags": article.get("tag_list", []),
                        "reading_time_minutes": article.get("reading_time_minutes", 0),
                    },
                )
                articles.append(article_info)

            return articles

        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Dev.to API 호출 실패: {e}") from e
        except Exception as e:
            raise RuntimeError(f"Dev.to 데이터 수집 실패: {e}") from e

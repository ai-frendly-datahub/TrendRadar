# -*- coding: utf-8 -*-
"""YouTube Trending Videos Collector."""

from __future__ import annotations

from typing import Any

import requests
from trendradar.models import ContentItem


class YouTubeTrendingCollector:
    """YouTube에서 인기 급상승 영상 데이터를 수집합니다.

    YouTube Data API v3를 사용하여 지역별 인기 영상과 트렌드를 분석합니다.
    """

    API_BASE_URL = "https://www.googleapis.com/youtube/v3"
    DEFAULT_HEADERS: dict[str, str] = {
        "User-Agent": "Mozilla/5.0 (compatible; TrendRadarBot/1.0; +https://github.com/zzragida/ai-frendly-datahub)",
    }

    def __init__(self, api_key: str | None = None):
        """
        Args:
            api_key: YouTube Data API v3 키
                발급: https://console.cloud.google.com/apis/credentials
        """
        if not api_key:
            raise ValueError(
                "YOUTUBE_API_KEY 환경 변수를 설정해주세요. "
                "Google Cloud Console에서 발급받을 수 있습니다."
            )

        self.api_key = api_key

    def collect_trending_videos(
        self,
        region_code: str = "KR",
        category_id: str | None = None,
        max_results: int = 50,
    ) -> list[ContentItem]:
        """인기 급상승 영상을 수집합니다.

        Args:
            region_code: ISO 3166-1 alpha-2 국가 코드 (KR, US, JP 등)
            category_id: 카테고리 ID (선택)
                10: Music, 20: Gaming, 24: Entertainment, 25: News & Politics
            max_results: 최대 결과 수 (1-50)

        Returns:
            인기 영상 리스트
            예: [{"title": "...", "channel": "...", "views": 123456, ...}, ...]
        """
        url = f"{self.API_BASE_URL}/videos"

        params: dict[str, Any] = {
            "part": "snippet,statistics,contentDetails",
            "chart": "mostPopular",
            "regionCode": region_code,
            "maxResults": min(max_results, 50),
            "key": self.api_key,
        }

        if category_id:
            params["videoCategoryId"] = category_id

        try:
            response = requests.get(
                url,
                params=params,
                headers=self.DEFAULT_HEADERS,
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()

        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"YouTube API 호출 실패: {e}") from e

        # 응답 파싱
        videos: list[ContentItem] = []

        for item in data.get("items", []):
            snippet = item.get("snippet", {})
            statistics = item.get("statistics", {})
            content_details = item.get("contentDetails", {})

            video = ContentItem(
                title=str(snippet.get("title", "")),
                url=f"https://www.youtube.com/watch?v={item.get('id', '')}",
                source="youtube",
                author=str(snippet.get("channelTitle", "")),
                score=float(statistics.get("viewCount", 0)),
                metadata={
                    "video_id": item.get("id"),
                    "channel_id": snippet.get("channelId"),
                    "published_at": snippet.get("publishedAt"),
                    "description": str(snippet.get("description", ""))[:500],
                    "category_id": snippet.get("categoryId"),
                    "tags": snippet.get("tags", [])[:10],
                    "view_count": int(statistics.get("viewCount", 0)),
                    "like_count": int(statistics.get("likeCount", 0)),
                    "comment_count": int(statistics.get("commentCount", 0)),
                    "duration": content_details.get("duration"),
                    "thumbnail_url": snippet.get("thumbnails", {}).get("high", {}).get("url"),
                    "region_code": region_code,
                },
            )

            videos.append(video)

        return videos

    def collect_trending_keywords(
        self,
        region_code: str = "KR",
        max_results: int = 50,
    ) -> dict[str, int]:
        """인기 영상의 태그/키워드를 집계합니다.

        Args:
            region_code: ISO 3166-1 alpha-2 국가 코드
            max_results: 최대 결과 수

        Returns:
            키워드별 빈도수 딕셔너리
            예: {"K-POP": 15, "아이돌": 12, ...}
        """
        videos = self.collect_trending_videos(
            region_code=region_code,
            max_results=max_results,
        )

        # 태그 및 제목에서 키워드 추출
        keyword_counts: dict[str, int] = {}

        for video in videos:
            # 태그
            for tag in video.metadata.get("tags", []):
                keyword_counts[tag] = keyword_counts.get(tag, 0) + 1

            # 제목에서 단어 추출 (간단한 공백 기반)
            title = video.title
            for word in title.split():
                if len(word) > 1:  # 1글자 제외
                    keyword_counts[word] = keyword_counts.get(word, 0) + 1

        # 빈도순 정렬
        sorted_keywords = dict(sorted(keyword_counts.items(), key=lambda x: x[1], reverse=True))

        return sorted_keywords

    def get_video_categories(self, region_code: str = "KR") -> dict[str, str]:
        """YouTube 카테고리 목록을 조회합니다.

        Args:
            region_code: ISO 3166-1 alpha-2 국가 코드

        Returns:
            카테고리 ID: 카테고리 이름 딕셔너리
        """
        url = f"{self.API_BASE_URL}/videoCategories"

        params = {
            "part": "snippet",
            "regionCode": region_code,
            "key": self.api_key,
        }

        try:
            response = requests.get(
                url,
                params=params,
                headers=self.DEFAULT_HEADERS,
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()

        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"YouTube API 호출 실패: {e}") from e

        categories = {}
        for item in data.get("items", []):
            cat_id = item.get("id")
            cat_name = item.get("snippet", {}).get("title")
            if cat_id and cat_name:
                categories[cat_id] = cat_name

        return categories

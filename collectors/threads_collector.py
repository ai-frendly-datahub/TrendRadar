# -*- coding: utf-8 -*-
"""Threads Trending Topics Collector (Meta Threads API)."""

from __future__ import annotations
from typing import Optional

import os

import requests
from tenacity import retry, stop_after_attempt, wait_exponential
from trendradar.models import ContentItem


class ThreadsCollector:
    """Meta Threads API를 통해 트렌딩 토픽을 수집합니다.

    Threads API를 사용하여 실시간 트렌딩 토픽을 수집합니다.
    - 글로벌 트렌딩 토픽
    - 지역별 트렌딩 토픽
    - 카테고리별 트렌딩 토픽
    """

    API_BASE_URL = "https://graph.threads.net/v1.0"
    USER_AGENT = "TrendRadar/0.1.0 (Trend Analysis Bot)"

    def __init__(self, access_token: Optional[str] = None):
        """
        Args:
            access_token: Meta Threads API Access Token
                         (환경변수 THREADS_ACCESS_TOKEN에서도 읽음)
        """
        self.access_token = access_token or os.getenv("THREADS_ACCESS_TOKEN", "")
        if not self.access_token:
            raise ValueError(
                "Threads API requires access_token parameter or THREADS_ACCESS_TOKEN env var"
            )

        self.headers = {
            "User-Agent": self.USER_AGENT,
            "Authorization": f"Bearer {self.access_token}",
        }

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
    )
    def collect_trending_topics(
        self,
        region: str = "KR",
        limit: int = 50,
    ) -> list[ContentItem]:
        """트렌딩 토픽을 수집합니다.

        Args:
            region: ISO 국가 코드 (KR, US, JP 등)
            limit: 최대 토픽 수 (1-100)

        Returns:
            트렌딩 토픽 리스트
            [
                {
                    "id": "topic_id",
                    "name": "토픽명",
                    "post_count": 1000,
                    "engagement_count": 5000,
                    "rank": 1,
                    "category": "news|entertainment|sports|...",
                    "url": "https://threads.net/...",
                    "collected_at": "2024-01-01T00:00:00Z"
                }
            ]
        """
        url = f"{self.API_BASE_URL}/trending_topics"

        params = {
            "region": region,
            "limit": min(limit, 100),
            "fields": "id,name,post_count,engagement_count,rank,category,url",
        }

        try:
            response = requests.get(
                url,
                headers=self.headers,
                params=params,
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()

            topics: list[ContentItem] = []
            for item in data.get("data", []):
                topic = ContentItem(
                    title=str(item.get("name", "")),
                    url=str(item.get("url", "")),
                    source="threads",
                    score=float(item.get("engagement_count", 0)),
                    metadata={
                        "id": item.get("id"),
                        "post_count": item.get("post_count", 0),
                        "engagement_count": item.get("engagement_count", 0),
                        "rank": item.get("rank", 0),
                        "category": item.get("category", "general"),
                        "collected_at": item.get("collected_at"),
                    },
                )
                topics.append(topic)

            return topics

        except requests.exceptions.RequestException as e:
            print(f"Threads API 요청 실패: {e}")
            raise

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
    )
    def collect_trending_by_category(
        self,
        category: str = "news",
        region: str = "KR",
        limit: int = 50,
    ) -> list[ContentItem]:
        """카테고리별 트렌딩 토픽을 수집합니다.

        Args:
            category: 카테고리 (news, entertainment, sports, technology, etc.)
            region: ISO 국가 코드
            limit: 최대 토픽 수

        Returns:
            카테고리별 트렌딩 토픽 리스트
        """
        url = f"{self.API_BASE_URL}/trending_topics/by_category"

        params = {
            "category": category,
            "region": region,
            "limit": min(limit, 100),
            "fields": "id,name,post_count,engagement_count,rank,url",
        }

        try:
            response = requests.get(
                url,
                headers=self.headers,
                params=params,
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()

            topics: list[ContentItem] = []
            for item in data.get("data", []):
                topic = ContentItem(
                    title=str(item.get("name", "")),
                    url=str(item.get("url", "")),
                    source="threads",
                    score=float(item.get("engagement_count", 0)),
                    metadata={
                        "id": item.get("id"),
                        "post_count": item.get("post_count", 0),
                        "engagement_count": item.get("engagement_count", 0),
                        "rank": item.get("rank", 0),
                        "category": category,
                    },
                )
                topics.append(topic)

            return topics

        except requests.exceptions.RequestException as e:
            print(f"Threads API 카테고리 요청 실패: {e}")
            raise

    def collect(self) -> list[ContentItem]:
        """기본 수집 메서드 - 글로벌 트렌딩 토픽 수집"""
        return self.collect_trending_topics(region="KR", limit=50)

# -*- coding: utf-8 -*-
"""Reddit Trending Topics Collector."""

from __future__ import annotations

from typing import Any, Literal

import requests
from trendradar.models import ContentItem


SortType = Literal["hot", "new", "top", "rising", "controversial"]
TimeFilter = Literal["hour", "day", "week", "month", "year", "all"]


class RedditCollector:
    """Reddit에서 인기 게시글 및 트렌드를 수집합니다.

    Reddit API를 사용하여 서브레딧별 인기 게시글을 수집합니다.
    인증 없이도 사용 가능하지만, 제한적입니다 (60 req/min).
    """

    API_BASE_URL = "https://www.reddit.com"
    USER_AGENT = "TrendRadar/0.1.0 (Trend Analysis Bot)"

    def __init__(
        self,
        client_id: str | None = None,
        client_secret: str | None = None,
        user_agent: str | None = None,
    ):
        """
        Args:
            client_id: Reddit API Client ID (선택)
            client_secret: Reddit API Client Secret (선택)
            user_agent: User-Agent 문자열
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.user_agent = user_agent or self.USER_AGENT
        self.headers = {"User-Agent": self.user_agent}

        # OAuth 토큰 (인증 시)
        self.access_token: str | None = None
        if client_id and client_secret:
            self._authenticate()

    def _authenticate(self) -> None:
        """OAuth 인증으로 access token을 발급받습니다."""
        if self.client_id is None or self.client_secret is None:
            return

        auth_url = "https://www.reddit.com/api/v1/access_token"

        auth: tuple[str, str] = (self.client_id, self.client_secret)
        data = {"grant_type": "client_credentials"}

        try:
            response = requests.post(
                auth_url,
                auth=auth,
                data=data,
                headers=self.headers,
                timeout=30,
            )
            response.raise_for_status()
            token_data = response.json()
            self.access_token = token_data.get("access_token")

            # 인증 후 헤더 업데이트
            if self.access_token:
                self.headers["Authorization"] = f"Bearer {self.access_token}"

        except requests.exceptions.RequestException as e:
            print(f"Reddit 인증 실패 (인증 없이 진행): {e}")

    def collect_subreddit_posts(
        self,
        subreddit: str,
        sort: SortType = "hot",
        time_filter: TimeFilter = "day",
        limit: int = 25,
    ) -> list[ContentItem]:
        """특정 서브레딧의 게시글을 수집합니다.

        Args:
            subreddit: 서브레딧 이름 (예: "python", "worldnews")
            sort: 정렬 방식 (hot, new, top, rising, controversial)
            time_filter: 시간 필터 (top, controversial일 때만 적용)
            limit: 최대 게시글 수 (1-100)

        Returns:
            게시글 리스트
        """
        url = f"{self.API_BASE_URL}/r/{subreddit}/{sort}.json"

        params: dict[str, Any] = {
            "limit": min(limit, 100),
        }

        # top, controversial일 때만 time filter 적용
        if sort in ["top", "controversial"]:
            params["t"] = time_filter

        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()

        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Reddit API 호출 실패: {e}") from e

        # 응답 파싱
        posts: list[ContentItem] = []

        for item in data.get("data", {}).get("children", []):
            post_data = item.get("data", {})

            post = ContentItem(
                title=str(post_data.get("title", "")),
                url=str(post_data.get("url", "")),
                source="reddit",
                author=str(post_data.get("author", "")),
                score=float(post_data.get("score", 0)),
                metadata={
                    "post_id": post_data.get("id"),
                    "subreddit": post_data.get("subreddit"),
                    "created_utc": post_data.get("created_utc"),
                    "upvote_ratio": post_data.get("upvote_ratio", 0.0),
                    "num_comments": post_data.get("num_comments", 0),
                    "permalink": f"https://reddit.com{post_data.get('permalink')}",
                    "selftext": str(post_data.get("selftext", ""))[:500],
                    "is_video": post_data.get("is_video", False),
                    "domain": post_data.get("domain"),
                    "flair": post_data.get("link_flair_text"),
                },
            )

            posts.append(post)

        return posts

    def collect_popular_posts(
        self,
        time_filter: TimeFilter = "day",
        limit: int = 25,
    ) -> list[ContentItem]:
        """r/popular (전체 인기 게시글)을 수집합니다.

        Args:
            time_filter: 시간 필터
            limit: 최대 게시글 수

        Returns:
            인기 게시글 리스트
        """
        url = f"{self.API_BASE_URL}/r/popular/top.json"

        params = {
            "t": time_filter,
            "limit": min(limit, 100),
        }

        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()

        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Reddit API 호출 실패: {e}") from e

        posts: list[ContentItem] = []

        for item in data.get("data", {}).get("children", []):
            post_data = item.get("data", {})

            post = ContentItem(
                title=str(post_data.get("title", "")),
                url=str(post_data.get("url", "")),
                source="reddit",
                author=str(post_data.get("author", "")),
                score=float(post_data.get("score", 0)),
                metadata={
                    "post_id": post_data.get("id"),
                    "subreddit": post_data.get("subreddit"),
                    "created_utc": post_data.get("created_utc"),
                    "num_comments": post_data.get("num_comments", 0),
                    "permalink": f"https://reddit.com{post_data.get('permalink')}",
                },
            )

            posts.append(post)

        return posts

    def collect_trending_keywords(
        self,
        subreddits: list[str] | None = None,
        time_filter: TimeFilter = "day",
        limit: int = 25,
    ) -> dict[str, int]:
        """인기 게시글의 키워드를 집계합니다.

        Args:
            subreddits: 분석할 서브레딧 리스트 (None이면 r/popular)
            time_filter: 시간 필터
            limit: 각 서브레딧당 최대 게시글 수

        Returns:
            키워드별 빈도수 딕셔너리
        """
        keyword_counts: dict[str, int] = {}

        if subreddits is None:
            # r/popular에서 수집
            posts = self.collect_popular_posts(time_filter=time_filter, limit=limit)

            for post in posts:
                # 제목에서 단어 추출
                title = post.title
                for word in title.split():
                    if len(word) > 2:  # 2글자 이하 제외
                        word_lower = word.lower().strip(".,!?")
                        keyword_counts[word_lower] = keyword_counts.get(word_lower, 0) + 1

        else:
            # 여러 서브레딧에서 수집
            for subreddit in subreddits:
                posts = self.collect_subreddit_posts(
                    subreddit=subreddit,
                    sort="top",
                    time_filter=time_filter,
                    limit=limit,
                )

                for post in posts:
                    title = post.title
                    for word in title.split():
                        if len(word) > 2:
                            word_lower = word.lower().strip(".,!?")
                            keyword_counts[word_lower] = keyword_counts.get(word_lower, 0) + 1

        # 빈도순 정렬
        sorted_keywords = dict(sorted(keyword_counts.items(), key=lambda x: x[1], reverse=True))

        return sorted_keywords

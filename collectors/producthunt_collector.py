# -*- coding: utf-8 -*-
"""Product Hunt New Products Collector."""

from __future__ import annotations

import os
from typing import Any, ClassVar

import requests
from tenacity import retry, stop_after_attempt, wait_exponential


class ProductHuntCollector:
    """Product Hunt에서 신규 제품을 수집합니다.

    GraphQL API를 사용하여 수집합니다.
    API Key 필요: PRODUCT_HUNT_API_KEY 환경변수
    Rate limit: 500 requests/day (free tier)
    """

    API_BASE_URL: ClassVar[str] = "https://api.producthunt.com/v2/api/graphql"
    TIMEOUT: ClassVar[int] = 30

    def __init__(self, api_key: str | None = None) -> None:
        """
        Args:
            api_key: Product Hunt API Key (기본값: PRODUCT_HUNT_API_KEY 환경변수)
        """
        self.api_key: str | None = api_key or os.environ.get("PRODUCT_HUNT_API_KEY")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
    )
    def _fetch_with_retry(self, query: str, variables: dict[str, Any] | None = None) -> dict[str, Any]:
        """GraphQL 요청을 재시도 로직과 함께 실행합니다."""
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

        payload = {
            "query": query,
            "variables": variables or {},
        }

        response = requests.post(self.API_BASE_URL, json=payload, headers=headers, timeout=self.TIMEOUT)
        response.raise_for_status()
        result = response.json()
        if not isinstance(result, dict):
            raise RuntimeError("Expected dict response from Product Hunt API")
        return result

    def collect(self, limit: int = 30) -> list[dict[str, Any]]:
        """Product Hunt 신규 제품을 수집합니다.

        Args:
            limit: 수집할 제품 개수 (기본값: 30)

        Returns:
            제품 정보 리스트
        """
        products: list[dict[str, Any]] = []

        if not self.api_key:
            raise RuntimeError("PRODUCT_HUNT_API_KEY 환경변수가 설정되지 않았습니다")

        try:
            # GraphQL 쿼리
            query = """
            query GetPosts($first: Int!) {
                posts(first: $first, order: NEWEST) {
                    edges {
                        node {
                            id
                            name
                            tagline
                            description
                            url
                            votesCount
                            commentsCount
                            createdAt
                            makers {
                                name
                                username
                            }
                            thumbnail {
                                url
                            }
                        }
                    }
                }
            }
            """

            variables = {"first": min(limit, 100)}

            response_data = self._fetch_with_retry(query, variables=variables)

            if "errors" in response_data:
                errors = response_data.get("errors", [])
                error_msg = ", ".join([str(e) for e in errors])
                raise RuntimeError(f"GraphQL 에러: {error_msg}")

            posts_data = response_data.get("data", {})
            if not isinstance(posts_data, dict):
                raise RuntimeError("Invalid response structure from Product Hunt API")
            posts_edges = posts_data.get("posts", {})
            if not isinstance(posts_edges, dict):
                raise RuntimeError("Invalid posts structure from Product Hunt API")
            posts = posts_edges.get("edges", [])

            for post_edge in posts[:limit]:
                post = post_edge.get("node", {})
                makers = post.get("makers", [])

                product_info = {
                    "id": post.get("id"),
                    "name": post.get("name", ""),
                    "tagline": post.get("tagline", ""),
                    "description": post.get("description", ""),
                    "url": post.get("url", ""),
                    "votes_count": post.get("votesCount", 0),
                    "comments_count": post.get("commentsCount", 0),
                    "created_at": post.get("createdAt", ""),
                    "makers": [{"name": m.get("name"), "username": m.get("username")} for m in makers],
                    "thumbnail_url": post.get("thumbnail", {}).get("url", ""),
                }
                products.append(product_info)

            return products

        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Product Hunt API 호출 실패: {e}") from e
        except Exception as e:
            raise RuntimeError(f"Product Hunt 데이터 수집 실패: {e}") from e

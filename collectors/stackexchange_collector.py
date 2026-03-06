# -*- coding: utf-8 -*-
"""Stack Exchange Trending Questions Collector."""

from __future__ import annotations

import os
from typing import Any, ClassVar

import requests
from tenacity import retry, stop_after_attempt, wait_exponential


class StackExchangeCollector:
    """Stack Exchange에서 트렌딩 질문을 수집합니다.

    Stack Exchange API를 사용하여 수집합니다.
    API Key 필요: STACK_EXCHANGE_API_KEY 환경변수
    Rate limit: 10,000 requests/day (with key)
    """

    API_BASE_URL: ClassVar[str] = "https://api.stackexchange.com/2.3"
    TIMEOUT: ClassVar[int] = 30

    def __init__(self, api_key: str | None = None) -> None:
        """
        Args:
            api_key: Stack Exchange API Key (기본값: STACK_EXCHANGE_API_KEY 환경변수)
        """
        self.api_key: str | None = api_key or os.environ.get("STACK_EXCHANGE_API_KEY")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
    )
    def _fetch_with_retry(self, url: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        """HTTP 요청을 재시도 로직과 함께 실행합니다."""
        response = requests.get(url, params=params, timeout=self.TIMEOUT)
        response.raise_for_status()
        result = response.json()
        if not isinstance(result, dict):
            raise RuntimeError("Expected dict response from Stack Exchange API")
        return result

    def collect(self, site: str = "stackoverflow", limit: int = 30) -> list[dict[str, Any]]:
        """Stack Exchange 트렌딩 질문을 수집합니다.

        Args:
            site: Stack Exchange 사이트 (기본값: stackoverflow)
            limit: 수집할 질문 개수 (기본값: 30)

        Returns:
            질문 정보 리스트
        """
        questions: list[dict[str, Any]] = []

        try:
            # Stack Exchange API 엔드포인트
            questions_url = f"{self.API_BASE_URL}/questions"

            params: dict[str, Any] = {
                "site": site,
                "sort": "hot",  # 트렌딩 질문
                "order": "desc",
                "pagesize": min(limit, 100),
            }

            if self.api_key:
                params["key"] = self.api_key

            questions_data = self._fetch_with_retry(questions_url, params=params)

            for question in questions_data.get("items", [])[:limit]:
                question_info = {
                    "question_id": question.get("question_id"),
                    "title": question.get("title", ""),
                    "link": question.get("link", ""),
                    "score": question.get("score", 0),
                    "view_count": question.get("view_count", 0),
                    "answer_count": question.get("answer_count", 0),
                    "is_answered": question.get("is_answered", False),
                    "creation_date": question.get("creation_date", 0),
                    "last_activity_date": question.get("last_activity_date", 0),
                    "owner": question.get("owner", {}).get("display_name", ""),
                    "tags": question.get("tags", []),
                }
                questions.append(question_info)

            return questions

        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Stack Exchange API 호출 실패: {e}") from e
        except Exception as e:
            raise RuntimeError(f"Stack Exchange 데이터 수집 실패: {e}") from e

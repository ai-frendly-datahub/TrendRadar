# -*- coding: utf-8 -*-
"""네이버 쇼핑인사이트 API Collector."""

from __future__ import annotations

import json
from typing import Any, Literal

import requests


DeviceType = Literal["pc", "mo", ""]
GenderType = Literal["m", "f", ""]
AgeGroup = Literal["10", "20", "30", "40", "50", "60"]


class NaverShoppingCollector:
    """네이버 쇼핑인사이트 API를 사용하여 쇼핑 트렌드 데이터를 수집합니다.

    API 문서: https://developers.naver.com/docs/serviceapi/datalab/shopping/shopping.md
    """

    API_URL = "https://openapi.naver.com/v1/datalab/shopping/categories"
    CATEGORY_API_URL = "https://openapi.naver.com/v1/datalab/shopping/category/keywords"
    KEYWORD_API_URL = "https://openapi.naver.com/v1/datalab/shopping/category/keyword/device"

    def __init__(self, client_id: str | None = None, client_secret: str | None = None):
        """
        Args:
            client_id: 네이버 API Client ID
            client_secret: 네이버 API Client Secret
        """
        if not client_id or not client_secret:
            raise ValueError(
                "NAVER_CLIENT_ID와 NAVER_CLIENT_SECRET 환경 변수를 설정해주세요."
            )

        self.client_id = client_id
        self.client_secret = client_secret
        self.headers = {
            "X-Naver-Client-Id": self.client_id,
            "X-Naver-Client-Secret": self.client_secret,
            "Content-Type": "application/json",
        }

    def collect_category_trends(
        self,
        category: str,
        start_date: str,
        end_date: str,
        time_unit: str = "date",
        device: DeviceType = "",
        gender: GenderType = "",
        ages: list[AgeGroup] | None = None,
    ) -> list[dict[str, Any]]:
        """카테고리별 쇼핑 트렌드를 수집합니다.

        Args:
            category: 카테고리 ID (예: "50000000" - 패션의류)
            start_date: 시작일 (YYYY-MM-DD)
            end_date: 종료일 (YYYY-MM-DD)
            time_unit: 시간 단위 (date, week, month)
            device: 디바이스 (pc, mo, 빈 값이면 전체)
            gender: 성별 (m, f, 빈 값이면 전체)
            ages: 연령대 리스트 (["10", "20"] 등)

        Returns:
            트렌드 데이터 리스트
        """
        request_body: dict[str, Any] = {
            "startDate": start_date.replace("-", ""),
            "endDate": end_date.replace("-", ""),
            "timeUnit": time_unit,
            "category": [{"name": category, "param": [category]}],
        }

        # 필터 추가
        if device:
            request_body["device"] = device
        if gender:
            request_body["gender"] = gender
        if ages:
            request_body["ages"] = ages

        try:
            response = requests.post(
                self.API_URL,
                headers=self.headers,
                data=json.dumps(request_body, ensure_ascii=False).encode("utf-8"),
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()

        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"네이버 쇼핑인사이트 API 호출 실패: {e}") from e

        # 응답 파싱
        result = []

        for item in data.get("results", []):
            category_name = item.get("title", "")
            points = []

            for point in item.get("data", []):
                period = point.get("period")
                ratio = point.get("ratio", 0.0)

                date_str = period.split("~")[0] if "~" in period else period

                points.append({
                    "date": date_str,
                    "value": ratio,
                    "period": period,
                })

            result.append({
                "category": category_name,
                "points": points,
            })

        return result

    def collect_category_keywords(
        self,
        category: str,
        start_date: str,
        end_date: str,
        time_unit: str = "date",
    ) -> dict[str, list[dict[str, Any]]]:
        """카테고리의 인기 검색어를 수집합니다.

        Args:
            category: 카테고리 ID
            start_date: 시작일 (YYYY-MM-DD)
            end_date: 종료일 (YYYY-MM-DD)
            time_unit: 시간 단위 (date, week, month)

        Returns:
            검색어별 트렌드 데이터
        """
        request_body = {
            "startDate": start_date.replace("-", ""),
            "endDate": end_date.replace("-", ""),
            "timeUnit": time_unit,
            "category": category,
        }

        try:
            response = requests.post(
                self.CATEGORY_API_URL,
                headers=self.headers,
                data=json.dumps(request_body, ensure_ascii=False).encode("utf-8"),
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()

        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"네이버 쇼핑인사이트 API 호출 실패: {e}") from e

        # 응답 파싱
        result: dict[str, list[dict[str, Any]]] = {}

        for item in data.get("results", []):
            keyword = item.get("keyword", "")
            points = []

            for point in item.get("data", []):
                period = point.get("period")
                ratio = point.get("ratio", 0.0)
                date_str = period.split("~")[0] if "~" in period else period

                points.append({
                    "date": date_str,
                    "value": ratio,
                    "period": period,
                })

            result[keyword] = points

        return result

    @staticmethod
    def get_popular_categories() -> dict[str, str]:
        """자주 사용되는 네이버 쇼핑 카테고리 ID 목록을 반환합니다.

        Returns:
            카테고리 ID: 카테고리 이름 딕셔너리
        """
        return {
            "50000000": "패션의류",
            "50000001": "패션잡화",
            "50000002": "화장품/미용",
            "50000003": "디지털/가전",
            "50000004": "가구/인테리어",
            "50000005": "출산/육아",
            "50000006": "식품",
            "50000007": "스포츠/레저",
            "50000008": "생활/건강",
            "50000009": "여가/생활편의",
            "50000010": "면세점",
        }

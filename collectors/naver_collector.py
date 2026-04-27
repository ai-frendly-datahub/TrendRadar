"""네이버 데이터랩 통합 검색어 트렌드 API Collector."""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime

import requests

from trendradar.models import TrendPoint


logger = logging.getLogger(__name__)


class NaverDataLabCollector:
    """네이버 데이터랩 API 를 사용하여 검색 트렌드 데이터를 수집합니다.

    API 문서: https://developers.naver.com/docs/serviceapi/datalab/search/search.md
    """

    API_URL = "https://openapi.naver.com/v1/datalab/search"

    def __init__(self, client_id: str | None = None, client_secret: str | None = None):
        """
        Args:
            client_id: 네이버 API Client ID
            client_secret: 네이버 API Client Secret
        """
        # 환경 변수에서 값 가져오기 (인수 우선)
        self.client_id = client_id or os.environ.get("NAVER_CLIENT_ID")
        self.client_secret = client_secret or os.environ.get("NAVER_CLIENT_SECRET")

        if not self.client_id or not self.client_secret:
            raise ValueError("NAVER_CLIENT_ID 또는 NAVER_CLIENT_SECRET 환경 변수가 필요합니다")

        self.enabled = True
        self.headers = {
            "X-Naver-Client-Id": self.client_id,
            "X-Naver-Client-Secret": self.client_secret,
            "Content-Type": "application/json",
        }

    def collect(
        self,
        keywords: list[str],
        start_date: str,
        end_date: str,
        time_unit: str = "date",
        device: str | None = None,
        gender: str | None = None,
        ages: list[str] | None = None,
    ) -> dict[str, list[TrendPoint]]:
        """네이버 데이터랩에서 트렌드 데이터를 수집합니다.

        Args:
            keywords: 검색 키워드 리스트 (최대 5 개)
            start_date: 시작일 (YYYY-MM-DD)
            end_date: 종료일 (YYYY-MM-DD)
            time_unit: 시간 단위 (date, week, month)
            device: 디바이스 (pc, mo, 빈 값이면 전체)
            gender: 성별 (m, f, 빈 값이면 전체)
            ages: 연령대 리스트 (["1", "2", "3"] = 10 대, 20 대, 30 대)

        Returns:
            키워드별 트렌드 포인트 딕셔너리
            예: {"와인": [{"date": "2024-01-01", "ratio": 85.2}, ...], ...}
        """
        # API 키가 없으면 빈 결과 반환
        if not self.enabled:
            return {}

        if len(keywords) > 5:
            raise ValueError("네이버 API 는 최대 5 개 키워드만 지원합니다.")

        # API 요청 본문 생성
        keyword_groups = [{"groupName": kw, "keywords": [kw]} for kw in keywords]

        request_body: dict[str, object] = {
            "startDate": start_date.replace("-", ""),
            "endDate": end_date.replace("-", ""),
            "timeUnit": time_unit,
            "keywordGroups": keyword_groups,
        }

        # 필터 추가 (값이 있을 때만)
        if device:
            request_body["device"] = device
        if gender:
            request_body["gender"] = gender
        if ages:
            request_body["ages"] = ages

        # API 호출
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
            raise RuntimeError(f"네이버 API 호출 실패: {e}") from e

        # 응답 파싱
        result: dict[str, list[TrendPoint]] = {}

        for item in data.get("results", []):
            keyword = item.get("title", "")
            points: list[TrendPoint] = []

            for point in item.get("data", []):
                # period 를 날짜로 변환
                period = point.get("period")
                ratio = point.get("ratio", 0.0)

                # period 형식: "2024-01-01" (date), "2024-01-01~2024-01-07" (week), "2024-01" (month)
                date_str = period.split("~")[0] if "~" in period else period
                try:
                    point_timestamp = datetime.fromisoformat(
                        date_str if len(date_str) == 10 else f"{date_str}-01"
                    )
                except ValueError:
                    continue

                points.append(
                    TrendPoint(
                        keyword=keyword,
                        source="naver",
                        timestamp=point_timestamp,
                        value=float(ratio),
                        metadata={"period": period},
                    )
                )

            result[keyword] = points

        return result

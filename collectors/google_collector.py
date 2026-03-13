"""Google Trends Collector (pytrends 기반)."""

from __future__ import annotations

from pytrends.request import TrendReq

from trendradar.models import TrendPoint


class GoogleTrendsCollector:
    """Google Trends에서 트렌드 데이터를 수집합니다.

    주의: pytrends는 비공식 API이므로 rate limit이 있을 수 있습니다.
    """

    def __init__(self, hl: str = "ko", tz: int = 540):
        """
        Args:
            hl: 언어 코드 (기본값: ko)
            tz: 타임존 오프셋 (기본값: 540 = UTC+9, 한국 시간)
        """
        self.pytrends = TrendReq(hl=hl, tz=tz)

    def collect(
        self,
        keywords: list[str],
        geo: str = "KR",
        timeframe: str = "today 3-m",
    ) -> dict[str, list[TrendPoint]]:
        """Google Trends에서 트렌드 데이터를 수집합니다.

        Args:
            keywords: 검색 키워드 리스트 (최대 5개 권장)
            geo: ISO 국가 코드 (KR, US, JP 등, 빈 문자열이면 전세계)
            timeframe: 기간 설정
                - "today 3-m": 최근 3개월
                - "today 12-m": 최근 12개월
                - "YYYY-MM-DD YYYY-MM-DD": 특정 기간

        Returns:
            키워드별 트렌드 포인트 딕셔너리
            예: {"와인": [{"date": "2024-01-01", "value": 85}, ...], ...}
        """
        if len(keywords) > 5:
            raise ValueError("Google Trends는 최대 5개 키워드 권장")

        try:
            # pytrends 빌드
            self.pytrends.build_payload(
                kw_list=keywords,
                geo=geo,
                timeframe=timeframe,
            )

            # 시계열 데이터 가져오기
            interest_over_time_df = self.pytrends.interest_over_time()

            if interest_over_time_df.empty:
                return {kw: [] for kw in keywords}

            # DataFrame을 딕셔너리로 변환
            result: dict[str, list[TrendPoint]] = {}

            for keyword in keywords:
                if keyword not in interest_over_time_df.columns:
                    result[keyword] = []
                    continue

                points: list[TrendPoint] = []
                values = interest_over_time_df[keyword].tolist()
                timestamps = interest_over_time_df.index.tolist()
                for timestamp, value in zip(timestamps, values, strict=False):
                    timestamp_text = str(timestamp)
                    date_text = timestamp_text[:10]
                    points.append(
                        TrendPoint.from_dict(
                            {
                                "keyword": keyword,
                                "source": "google",
                                "timestamp": timestamp_text,
                                "date": date_text,
                                "value": float(value),
                            }
                        )
                    )

                result[keyword] = points

            return result

        except Exception as e:
            raise RuntimeError(f"Google Trends 데이터 수집 실패: {e}") from e

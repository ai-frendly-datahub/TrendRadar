# -*- coding: utf-8 -*-
"""크로스 채널 트렌드 분석 모듈.

여러 채널(Google, Naver, YouTube 등)의 트렌드를 비교 분석합니다.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from storage import trend_store


@dataclass
class ChannelGap:
    """채널 간 격차 정보."""

    keyword: str
    leading_channel: str
    lagging_channel: str
    leading_value: float
    lagging_value: float
    gap_ratio: float  # leading / lagging
    gap_score: float
    insight: str

    def __repr__(self) -> str:
        return (
            f"ChannelGap(keyword='{self.keyword}', "
            f"{self.leading_channel}>{self.lagging_channel}, "
            f"gap={self.gap_ratio:.2f}x)"
        )


@dataclass
class ChannelCorrelation:
    """채널 간 상관관계."""

    keyword: str
    channel1: str
    channel2: str
    correlation: float  # -1 to 1
    time_lag_days: int  # 시차 (일)
    strength: str  # 'strong', 'moderate', 'weak'


class CrossChannelAnalyzer:
    """크로스 채널 트렌드 분석기."""

    def __init__(self, db_path: Path | None = None):
        """
        Args:
            db_path: DuckDB 파일 경로
        """
        self.db_path = db_path

    def find_channel_gaps(
        self,
        channel1: str,
        channel2: str,
        days: int = 30,
        min_gap: float = 2.0,
    ) -> list[ChannelGap]:
        """채널 간 격차 발견.

        예: YouTube에서는 뜨는데 검색에서는 안 뜨는 키워드.

        Args:
            channel1: 첫 번째 채널 (예: 'youtube')
            channel2: 두 번째 채널 (예: 'google')
            days: 분석 기간 (일)
            min_gap: 최소 격차 비율

        Returns:
            채널 격차 리스트
        """
        now = datetime.now()
        start_date = now - timedelta(days=days)

        # 두 채널 데이터 조회
        points1 = trend_store.query_trend_points(
            source=channel1,
            start_date=start_date.strftime("%Y-%m-%d"),
            end_date=now.strftime("%Y-%m-%d"),
            db_path=self.db_path,
        )

        points2 = trend_store.query_trend_points(
            source=channel2,
            start_date=start_date.strftime("%Y-%m-%d"),
            end_date=now.strftime("%Y-%m-%d"),
            db_path=self.db_path,
        )

        # 키워드별 평균
        avg1 = self._calculate_keyword_averages(points1)
        avg2 = self._calculate_keyword_averages(points2)

        gaps = []

        # 공통 키워드에서 격차 찾기
        common_keywords = set(avg1.keys()) & set(avg2.keys())

        for keyword in common_keywords:
            val1 = avg1[keyword]
            val2 = avg2[keyword]

            # 채널1이 높은 경우
            if val1 >= val2 * min_gap and val2 > 0:
                gap_ratio = val1 / val2
                gap_score = self._calculate_gap_score(val1, val2, gap_ratio)

                insight = self._generate_gap_insight(
                    keyword, channel1, channel2, val1, val2
                )

                gaps.append(ChannelGap(
                    keyword=keyword,
                    leading_channel=channel1,
                    lagging_channel=channel2,
                    leading_value=val1,
                    lagging_value=val2,
                    gap_ratio=gap_ratio,
                    gap_score=gap_score,
                    insight=insight,
                ))

            # 채널2가 높은 경우
            elif val2 >= val1 * min_gap and val1 > 0:
                gap_ratio = val2 / val1
                gap_score = self._calculate_gap_score(val2, val1, gap_ratio)

                insight = self._generate_gap_insight(
                    keyword, channel2, channel1, val2, val1
                )

                gaps.append(ChannelGap(
                    keyword=keyword,
                    leading_channel=channel2,
                    lagging_channel=channel1,
                    leading_value=val2,
                    lagging_value=val1,
                    gap_ratio=gap_ratio,
                    gap_score=gap_score,
                    insight=insight,
                ))

        # 점수순 정렬
        gaps.sort(key=lambda x: x.gap_score, reverse=True)

        return gaps

    def find_exclusive_keywords(
        self,
        channel: str,
        exclude_channels: list[str],
        days: int = 30,
        min_value: float = 30.0,
    ) -> list[dict[str, Any]]:
        """특정 채널에만 있는 독점 키워드 찾기.

        Args:
            channel: 분석할 채널
            exclude_channels: 제외할 채널들
            days: 분석 기간
            min_value: 최소 값

        Returns:
            독점 키워드 리스트
        """
        now = datetime.now()
        start_date = now - timedelta(days=days)

        # 분석 채널 데이터
        target_points = trend_store.query_trend_points(
            source=channel,
            start_date=start_date.strftime("%Y-%m-%d"),
            end_date=now.strftime("%Y-%m-%d"),
            db_path=self.db_path,
        )

        target_keywords = self._calculate_keyword_averages(target_points)

        # 제외 채널들의 키워드 수집
        exclude_keywords = set()

        for exc_channel in exclude_channels:
            exc_points = trend_store.query_trend_points(
                source=exc_channel,
                start_date=start_date.strftime("%Y-%m-%d"),
                end_date=now.strftime("%Y-%m-%d"),
                db_path=self.db_path,
            )
            exclude_keywords.update(self._calculate_keyword_averages(exc_points).keys())

        # 독점 키워드 찾기
        exclusive = []

        for keyword, value in target_keywords.items():
            if keyword not in exclude_keywords and value >= min_value:
                exclusive.append({
                    "keyword": keyword,
                    "channel": channel,
                    "value": value,
                    "exclusivity_score": value,  # 간단한 점수
                })

        # 값 순 정렬
        exclusive.sort(key=lambda x: x["value"], reverse=True)

        return exclusive

    def compare_channels(
        self,
        channels: list[str],
        days: int = 30,
    ) -> dict[str, Any]:
        """여러 채널 종합 비교.

        Args:
            channels: 비교할 채널 리스트
            days: 분석 기간

        Returns:
            비교 결과 딕셔너리
        """
        now = datetime.now()
        start_date = now - timedelta(days=days)

        channel_data = {}

        # 각 채널 데이터 수집
        for channel in channels:
            points = trend_store.query_trend_points(
                source=channel,
                start_date=start_date.strftime("%Y-%m-%d"),
                end_date=now.strftime("%Y-%m-%d"),
                db_path=self.db_path,
            )

            keyword_avgs = self._calculate_keyword_averages(points)

            channel_data[channel] = {
                "total_keywords": len(keyword_avgs),
                "avg_value": sum(keyword_avgs.values()) / len(keyword_avgs) if keyword_avgs else 0,
                "top_keywords": sorted(
                    keyword_avgs.items(),
                    key=lambda x: x[1],
                    reverse=True
                )[:10],
                "keywords": keyword_avgs,
            }

        # 공통 & 독점 키워드 분석
        all_keywords = set()
        for data in channel_data.values():
            all_keywords.update(data["keywords"].keys())

        common_keywords = all_keywords.copy()
        for data in channel_data.values():
            common_keywords &= set(data["keywords"].keys())

        return {
            "channels": channel_data,
            "total_unique_keywords": len(all_keywords),
            "common_keywords": list(common_keywords),
            "common_count": len(common_keywords),
            "exclusive_by_channel": {
                channel: len(set(data["keywords"].keys()) - common_keywords)
                for channel, data in channel_data.items()
            },
        }

    @staticmethod
    def _calculate_keyword_averages(
        points: list[dict[str, Any]]
    ) -> dict[str, float]:
        """키워드별 평균 값 계산."""
        keyword_values: dict[str, list[float]] = {}

        for point in points:
            keyword = point.get("keyword", "")
            value = point.get("value", 0)

            if keyword not in keyword_values:
                keyword_values[keyword] = []

            keyword_values[keyword].append(value)

        return {
            kw: sum(vals) / len(vals)
            for kw, vals in keyword_values.items()
        }

    @staticmethod
    def _calculate_gap_score(
        leading_val: float,
        lagging_val: float,
        ratio: float,
    ) -> float:
        """격차 점수 계산 (0-100)."""
        # 비율 점수 (최대 50점)
        ratio_score = min(50, (ratio - 1) * 10)

        # 절대값 점수 (최대 30점)
        absolute_score = min(30, leading_val * 0.3)

        # 격차 크기 점수 (최대 20점)
        gap = leading_val - lagging_val
        gap_score = min(20, gap * 0.2)

        return ratio_score + absolute_score + gap_score

    @staticmethod
    def _generate_gap_insight(
        keyword: str,
        leading: str,
        lagging: str,
        leading_val: float,
        lagging_val: float,
    ) -> str:
        """격차에 대한 인사이트 생성."""
        ratio = leading_val / lagging_val if lagging_val > 0 else 0

        if ratio >= 3:
            strength = "매우 강하게"
        elif ratio >= 2:
            strength = "강하게"
        else:
            strength = "다소"

        return (
            f"'{keyword}'는 {leading}에서 {strength} 트렌딩 중 "
            f"({leading_val:.1f}), 하지만 {lagging}에서는 낮음 ({lagging_val:.1f}). "
            f"{lagging} 사용자들은 아직 이 트렌드를 따라잡지 못한 것으로 보입니다."
        )

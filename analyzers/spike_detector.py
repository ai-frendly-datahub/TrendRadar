"""급상승 키워드 감지 모듈.

최근 기간 대비 급격한 상승을 보이는 키워드를 탐지합니다.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, Literal

from storage import trend_store
from trendradar.models import TrendPoint


SpikeType = Literal["surge", "emerging", "sustained", "viral"]


@dataclass
class SpikeSignal:
    """급상승 신호 데이터 클래스."""

    keyword: str
    source: str
    spike_type: SpikeType
    current_value: float
    baseline_value: float
    spike_ratio: float  # 증가율 (current / baseline)
    spike_score: float  # 0-100 점수
    detected_at: datetime
    metadata: dict[str, Any]

    def __repr__(self) -> str:
        return (
            f"SpikeSignal(keyword='{self.keyword}', "
            f"type={self.spike_type}, "
            f"ratio={self.spike_ratio:.2f}x, "
            f"score={self.spike_score:.1f})"
        )


class SpikeDetector:
    """급상승 키워드 감지기.

    다양한 알고리즘으로 트렌드 급상승을 감지합니다.
    """

    def __init__(
        self,
        db_path: Path | None = None,
        recent_days: int = 7,
        baseline_days: int = 30,
    ):
        """
        Args:
            db_path: DuckDB 파일 경로
            recent_days: 최근 기간 (일)
            baseline_days: 기준 기간 (일)
        """
        self.db_path = db_path
        self.recent_days = recent_days
        self.baseline_days = baseline_days

    def detect_surge_keywords(
        self,
        source: str | None = None,
        min_ratio: float = 1.5,
        min_baseline: float = 10.0,
    ) -> list[SpikeSignal]:
        """급상승 키워드 감지 (Surge).

        최근 7일 평균이 직전 30일 평균 대비 크게 증가한 키워드.

        Args:
            source: 데이터 소스 필터 (google, naver 등)
            min_ratio: 최소 증가율 (기본 1.5배)
            min_baseline: 최소 baseline 값 (너무 작은 값 제외)

        Returns:
            급상승 신호 리스트
        """
        now = datetime.now(tz=UTC)
        recent_start = now - timedelta(days=self.recent_days)
        baseline_start = now - timedelta(days=self.baseline_days + self.recent_days)
        baseline_end = recent_start

        # 최근 기간 데이터
        recent_points = trend_store.query_trend_points(
            source=source,
            start_date=recent_start.strftime("%Y-%m-%d"),
            end_date=now.strftime("%Y-%m-%d"),
            db_path=self.db_path,
        )

        # 기준 기간 데이터
        baseline_points = trend_store.query_trend_points(
            source=source,
            start_date=baseline_start.strftime("%Y-%m-%d"),
            end_date=baseline_end.strftime("%Y-%m-%d"),
            db_path=self.db_path,
        )

        # 키워드별로 그룹화
        recent_by_keyword = self._group_by_keyword(recent_points)
        baseline_by_keyword = self._group_by_keyword(baseline_points)

        signals = []

        for keyword in recent_by_keyword:
            if keyword not in baseline_by_keyword:
                continue

            recent_avg = self._calculate_average(recent_by_keyword[keyword])
            baseline_avg = self._calculate_average(baseline_by_keyword[keyword])

            # 기준값이 너무 작으면 제외
            if baseline_avg < min_baseline:
                continue

            ratio = recent_avg / baseline_avg if baseline_avg > 0 else 0

            # 급상승 기준 충족 시
            if ratio >= min_ratio:
                spike_score = self._calculate_spike_score(
                    ratio=ratio,
                    current=recent_avg,
                    baseline=baseline_avg,
                )

                signal = SpikeSignal(
                    keyword=keyword,
                    source=recent_by_keyword[keyword][0].source,
                    spike_type="surge",
                    current_value=recent_avg,
                    baseline_value=baseline_avg,
                    spike_ratio=ratio,
                    spike_score=spike_score,
                    detected_at=now,
                    metadata={
                        "recent_days": self.recent_days,
                        "baseline_days": self.baseline_days,
                        "recent_points": len(recent_by_keyword[keyword]),
                        "baseline_points": len(baseline_by_keyword[keyword]),
                    },
                )

                signals.append(signal)

        # 점수순 정렬
        signals.sort(key=lambda x: x.spike_score, reverse=True)

        return signals

    def detect_emerging_keywords(
        self,
        source: str | None = None,
        min_current: float = 30.0,
        max_baseline: float = 5.0,
    ) -> list[SpikeSignal]:
        """신규 등장 키워드 감지 (Emerging).

        과거에는 낮았지만 최근 갑자기 나타난 키워드.

        Args:
            source: 데이터 소스 필터
            min_current: 최소 현재 값
            max_baseline: 최대 baseline 값 (이전에 낮았던 것)

        Returns:
            신규 등장 신호 리스트
        """
        now = datetime.now(tz=UTC)
        recent_start = now - timedelta(days=self.recent_days)
        baseline_start = now - timedelta(days=self.baseline_days + self.recent_days)
        baseline_end = recent_start

        recent_points = trend_store.query_trend_points(
            source=source,
            start_date=recent_start.strftime("%Y-%m-%d"),
            end_date=now.strftime("%Y-%m-%d"),
            db_path=self.db_path,
        )

        baseline_points = trend_store.query_trend_points(
            source=source,
            start_date=baseline_start.strftime("%Y-%m-%d"),
            end_date=baseline_end.strftime("%Y-%m-%d"),
            db_path=self.db_path,
        )

        recent_by_keyword = self._group_by_keyword(recent_points)
        baseline_by_keyword = self._group_by_keyword(baseline_points)

        signals = []

        for keyword in recent_by_keyword:
            recent_avg = self._calculate_average(recent_by_keyword[keyword])

            # 현재 값이 충분히 높아야 함
            if recent_avg < min_current:
                continue

            # 과거 데이터가 없거나 매우 낮았던 경우
            if keyword not in baseline_by_keyword:
                baseline_avg = 0.0
                ratio = float("inf")
            else:
                baseline_avg = self._calculate_average(baseline_by_keyword[keyword])
                if baseline_avg > max_baseline:
                    continue
                ratio = recent_avg / baseline_avg if baseline_avg > 0 else float("inf")

            spike_score = min(100, recent_avg + (ratio if ratio != float("inf") else 50))

            signal = SpikeSignal(
                keyword=keyword,
                source=recent_by_keyword[keyword][0].source,
                spike_type="emerging",
                current_value=recent_avg,
                baseline_value=baseline_avg,
                spike_ratio=ratio,
                spike_score=spike_score,
                detected_at=now,
                metadata={
                    "is_new": keyword not in baseline_by_keyword,
                },
            )

            signals.append(signal)

        signals.sort(key=lambda x: x.spike_score, reverse=True)

        return signals

    def detect_viral_keywords(
        self,
        source: str | None = None,
        window_days: int = 3,
        min_growth_rate: float = 2.0,
    ) -> list[SpikeSignal]:
        """바이럴 키워드 감지 (Viral).

        짧은 기간 동안 폭발적으로 증가하는 키워드.

        Args:
            source: 데이터 소스 필터
            window_days: 관찰 기간 (일)
            min_growth_rate: 최소 성장률 (배수/일)

        Returns:
            바이럴 신호 리스트
        """
        now = datetime.now(tz=UTC)
        start_date = now - timedelta(days=window_days * 2)

        points = trend_store.query_trend_points(
            source=source,
            start_date=start_date.strftime("%Y-%m-%d"),
            end_date=now.strftime("%Y-%m-%d"),
            db_path=self.db_path,
        )

        by_keyword = self._group_by_keyword(points)

        signals = []

        for keyword, keyword_points in by_keyword.items():
            # 시간순 정렬
            sorted_points = sorted(keyword_points, key=lambda x: x.timestamp)

            if len(sorted_points) < window_days:
                continue

            # 최근 window_days와 그 이전 비교
            mid_point = len(sorted_points) // 2
            early_points = sorted_points[:mid_point]
            recent_points = sorted_points[mid_point:]

            early_avg = self._calculate_average(early_points)
            recent_avg = self._calculate_average(recent_points)

            if early_avg < 1:
                continue

            growth_rate = recent_avg / early_avg

            if growth_rate >= min_growth_rate:
                spike_score = min(100, growth_rate * 20)

                signal = SpikeSignal(
                    keyword=keyword,
                    source=keyword_points[0].source,
                    spike_type="viral",
                    current_value=recent_avg,
                    baseline_value=early_avg,
                    spike_ratio=growth_rate,
                    spike_score=spike_score,
                    detected_at=now,
                    metadata={
                        "window_days": window_days,
                        "growth_per_day": (growth_rate - 1) / window_days,
                    },
                )

                signals.append(signal)

        signals.sort(key=lambda x: x.spike_score, reverse=True)

        return signals

    def detect_all_spikes(
        self,
        source: str | None = None,
        top_n: int = 20,
    ) -> dict[str, list[SpikeSignal]]:
        """모든 종류의 급상승 감지.

        Args:
            source: 데이터 소스 필터
            top_n: 각 타입별 상위 N개

        Returns:
            타입별 신호 딕셔너리
        """
        return {
            "surge": self.detect_surge_keywords(source=source)[:top_n],
            "emerging": self.detect_emerging_keywords(source=source)[:top_n],
            "viral": self.detect_viral_keywords(source=source)[:top_n],
        }

    @staticmethod
    def _group_by_keyword(points: list[TrendPoint]) -> dict[str, list[TrendPoint]]:
        """데이터 포인트를 키워드별로 그룹화."""
        grouped: dict[str, list[TrendPoint]] = {}

        for point in points:
            keyword = point.keyword
            if keyword not in grouped:
                grouped[keyword] = []
            grouped[keyword].append(point)

        return grouped

    @staticmethod
    def _calculate_average(points: list[TrendPoint]) -> float:
        """평균 값 계산."""
        if not points:
            return 0.0

        total = sum(p.value for p in points)
        return total / len(points)

    @staticmethod
    def _calculate_spike_score(
        ratio: float,
        current: float,
        baseline: float,
    ) -> float:
        """급상승 점수 계산 (0-100).

        Args:
            ratio: 증가율
            current: 현재 값
            baseline: 기준 값

        Returns:
            0-100 사이의 점수
        """
        # 증가율 점수 (최대 50점)
        ratio_score = min(50, (ratio - 1) * 20)

        # 절대값 점수 (최대 30점)
        absolute_score = min(30, current * 0.3)

        # 증가량 점수 (최대 20점)
        increase = current - baseline
        increase_score = min(20, increase * 0.2)

        total_score = ratio_score + absolute_score + increase_score

        return min(100, max(0, total_score))

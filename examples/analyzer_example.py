"""Analyzer 사용 예시 - 급상승 감지 및 크로스 채널 분석."""

from pathlib import Path

from analyzers.cross_channel_analyzer import CrossChannelAnalyzer
from analyzers.spike_detector import SpikeDetector


def demo_spike_detection():
    """급상승 키워드 감지 데모."""
    print("=" * 70)
    print("🔥 급상승 키워드 감지 (Spike Detection)")
    print("=" * 70)

    db_path = Path("data/trendradar.duckdb")

    if not db_path.exists():
        print("⚠️  데이터베이스 파일이 없습니다. 먼저 데이터를 수집해주세요.")
        print("   python main.py --mode once --generate-report")
        return

    detector = SpikeDetector(
        db_path=db_path,
        recent_days=7,  # 최근 7일
        baseline_days=30,  # 기준 30일
    )

    # 1. 급상승 키워드 (Surge)
    print("\n📈 1. 급상승 키워드 (Surge)")
    print("-" * 70)
    print("최근 7일 평균이 직전 30일 평균 대비 크게 증가한 키워드\n")

    surge_signals = detector.detect_surge_keywords(
        source=None,  # 모든 소스
        min_ratio=1.5,  # 1.5배 이상
        min_baseline=10.0,
    )

    if surge_signals:
        print(f"발견된 급상승 키워드: {len(surge_signals)}개\n")

        for i, signal in enumerate(surge_signals[:10], 1):
            print(f"{i}. {signal.keyword} ({signal.source})")
            print(
                f"   📊 현재: {signal.current_value:.1f} | "
                f"기준: {signal.baseline_value:.1f} | "
                f"증가율: {signal.spike_ratio:.2f}x"
            )
            print(f"   ⭐ 급상승 점수: {signal.spike_score:.1f}/100")
            print()
    else:
        print("급상승 키워드가 없습니다.\n")

    # 2. 신규 등장 키워드 (Emerging)
    print("\n🌟 2. 신규 등장 키워드 (Emerging)")
    print("-" * 70)
    print("과거에는 낮았지만 최근 갑자기 나타난 키워드\n")

    emerging_signals = detector.detect_emerging_keywords(
        source=None, min_current=30.0, max_baseline=5.0
    )

    if emerging_signals:
        print(f"발견된 신규 키워드: {len(emerging_signals)}개\n")

        for i, signal in enumerate(emerging_signals[:10], 1):
            is_new = signal.metadata.get("is_new", False)
            status = "🆕 완전히 새로운" if is_new else "📈 급부상한"

            print(f"{i}. {signal.keyword} ({signal.source}) - {status}")
            print(f"   📊 현재: {signal.current_value:.1f} | 이전: {signal.baseline_value:.1f}")
            print(f"   ⭐ 점수: {signal.spike_score:.1f}/100")
            print()
    else:
        print("신규 등장 키워드가 없습니다.\n")

    # 3. 바이럴 키워드 (Viral)
    print("\n💥 3. 바이럴 키워드 (Viral)")
    print("-" * 70)
    print("짧은 기간 동안 폭발적으로 증가하는 키워드\n")

    viral_signals = detector.detect_viral_keywords(source=None, window_days=3, min_growth_rate=2.0)

    if viral_signals:
        print(f"발견된 바이럴 키워드: {len(viral_signals)}개\n")

        for i, signal in enumerate(viral_signals[:10], 1):
            growth_per_day = signal.metadata.get("growth_per_day", 0)

            print(f"{i}. {signal.keyword} ({signal.source})")
            print(f"   📊 초기: {signal.baseline_value:.1f} → 최근: {signal.current_value:.1f}")
            print(f"   🚀 성장률: {signal.spike_ratio:.2f}x (일일 +{growth_per_day * 100:.1f}%)")
            print(f"   ⭐ 점수: {signal.spike_score:.1f}/100")
            print()
    else:
        print("바이럴 키워드가 없습니다.\n")

    # 4. 전체 통합 리포트
    print("\n📋 4. 통합 급상승 리포트")
    print("-" * 70)

    all_spikes = detector.detect_all_spikes(source=None, top_n=5)

    for spike_type, signals in all_spikes.items():
        type_names = {"surge": "급상승", "emerging": "신규 등장", "viral": "바이럴"}
        print(f"\n{type_names[spike_type]} Top 5:")

        for i, signal in enumerate(signals, 1):
            print(
                f"  {i}. {signal.keyword} ({signal.spike_ratio:.2f}x, "
                f"점수: {signal.spike_score:.1f})"
            )


def demo_cross_channel_analysis():
    """크로스 채널 분석 데모."""
    print("\n\n" + "=" * 70)
    print("🔀 크로스 채널 트렌드 분석")
    print("=" * 70)

    db_path = Path("data/trendradar.duckdb")

    if not db_path.exists():
        print("⚠️  데이터베이스 파일이 없습니다.")
        return

    analyzer = CrossChannelAnalyzer(db_path=db_path)

    # 1. 채널 간 격차 분석
    print("\n⚖️  1. 채널 간 격차 분석")
    print("-" * 70)
    print("Google vs Naver - 어느 채널에서 더 뜨는가?\n")

    gaps = analyzer.find_channel_gaps(channel1="google", channel2="naver", days=30, min_gap=2.0)

    if gaps:
        print(f"발견된 격차: {len(gaps)}개\n")

        for i, gap in enumerate(gaps[:5], 1):
            print(f"{i}. {gap.keyword}")
            print(
                f"   {gap.leading_channel}: {gap.leading_value:.1f} | "
                f"{gap.lagging_channel}: {gap.lagging_value:.1f}"
            )
            print(f"   격차: {gap.gap_ratio:.2f}x")
            print(f"   💡 {gap.insight}\n")
    else:
        print("유의미한 격차가 없습니다.\n")

    # 2. 채널 종합 비교
    print("\n📊 2. 다중 채널 종합 비교")
    print("-" * 70)

    comparison = analyzer.compare_channels(channels=["google", "naver"], days=30)

    print(f"\n전체 유니크 키워드: {comparison['total_unique_keywords']}개")
    print(f"공통 키워드: {comparison['common_count']}개\n")

    for channel, data in comparison["channels"].items():
        print(f"{channel.upper()}:")
        print(f"  • 전체 키워드: {data['total_keywords']}개")
        print(f"  • 평균 관심도: {data['avg_value']:.1f}")
        print(f"  • 독점 키워드: {comparison['exclusive_by_channel'][channel]}개")

        print("\n  Top 5 키워드:")
        for kw, val in data["top_keywords"][:5]:
            print(f"    - {kw}: {val:.1f}")
        print()


def main():
    """메인 실행 함수."""
    print("\n🎯 TrendRadar Analyzer 데모")
    print("=" * 70)

    # 급상승 감지 데모
    demo_spike_detection()

    # 크로스 채널 분석 데모
    demo_cross_channel_analysis()

    print("\n" + "=" * 70)
    print("✅ 데모 완료!")
    print("=" * 70)
    print("\n💡 TIP:")
    print("  • 더 많은 데이터를 수집하면 분석 정확도가 높아집니다")
    print("  • python main.py --mode scheduler 로 정기 수집 설정하세요")
    print("=" * 70)


if __name__ == "__main__":
    main()

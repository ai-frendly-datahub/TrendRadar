"""기본 기능 테스트 스크립트."""

import io
import sys
from datetime import datetime, timedelta
from pathlib import Path


# Windows 인코딩 문제 해결
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

print("=" * 70)
print("TrendRadar 기본 기능 테스트")
print("=" * 70)

# 1. Import 테스트
print("\n[1/5] Import 테스트...")
try:
    from analyzers.cross_channel_analyzer import CrossChannelAnalyzer
    from analyzers.spike_detector import SpikeDetector
    from collectors.google_collector import GoogleTrendsCollector
    from collectors.naver_collector import NaverDataLabCollector
    from storage import trend_store

    print("✓ 모든 모듈 import 성공")
except ImportError as e:
    print(f"✗ Import 실패: {e}")
    sys.exit(1)

# 2. 저장소 테스트
print("\n[2/5] 저장소 테스트...")
try:
    test_db = Path("data/test_trendradar.duckdb")
    test_db.parent.mkdir(exist_ok=True)

    # 테스트 데이터 저장
    test_points = [
        {"date": (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d"), "value": 50 + i * 5}
        for i in range(40)
    ]

    count = trend_store.save_trend_points(
        source="test",
        keyword="테스트키워드",
        points=test_points,
        metadata={"test": True},
        db_path=test_db,
    )
    print(f"✓ 테스트 데이터 저장 성공: {count}개")

    # 데이터 조회
    saved_points = trend_store.query_trend_points(
        source="test", keyword="테스트키워드", db_path=test_db
    )
    print(f"✓ 데이터 조회 성공: {len(saved_points)}개")

except Exception as e:
    print(f"✗ 저장소 테스트 실패: {e}")
    sys.exit(1)

# 3. Spike Detector 테스트
print("\n[3/5] Spike Detector 테스트...")
try:
    detector = SpikeDetector(db_path=test_db, recent_days=7, baseline_days=30)

    # 급상승 감지 (데이터가 인위적이므로 결과가 없을 수 있음)
    surge = detector.detect_surge_keywords(source="test", min_baseline=1.0)
    emerging = detector.detect_emerging_keywords(source="test")
    viral = detector.detect_viral_keywords(source="test")

    print(f"✓ Surge 감지: {len(surge)}개")
    print(f"✓ Emerging 감지: {len(emerging)}개")
    print(f"✓ Viral 감지: {len(viral)}개")

except Exception as e:
    print(f"✗ Spike Detector 실패: {e}")
    import traceback

    traceback.print_exc()

# 4. Cross-Channel Analyzer 테스트
print("\n[4/5] Cross-Channel Analyzer 테스트...")
try:
    # 다른 채널 데이터 추가
    test_points2 = [
        {"date": (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d"), "value": 30 + i * 2}
        for i in range(40)
    ]

    test_points3 = [
        {"date": (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d"), "value": 70 + i * 3}
        for i in range(40)
    ]

    trend_store.save_trend_points("test2", "공통키워드", test_points2, db_path=test_db)
    trend_store.save_trend_points("test", "공통키워드", test_points3, db_path=test_db)

    analyzer = CrossChannelAnalyzer(db_path=test_db)

    gaps = analyzer.find_channel_gaps(channel1="test", channel2="test2", days=30, min_gap=1.5)

    print(f"✓ 채널 격차 감지: {len(gaps)}개")

    comparison = analyzer.compare_channels(channels=["test", "test2"], days=30)

    print("✓ 다중 채널 비교 완료")
    print(f"  - 전체 키워드: {comparison['total_unique_keywords']}개")
    print(f"  - 공통 키워드: {comparison['common_count']}개")

except Exception as e:
    print(f"✗ Cross-Channel Analyzer 실패: {e}")
    import traceback

    traceback.print_exc()

# 5. 리포트 생성 테스트
print("\n[5/5] 리포트 생성 테스트...")
try:
    from reporters.spike_reporter import generate_spike_report

    report_dir = Path("docs/reports")
    report_dir.mkdir(parents=True, exist_ok=True)

    generate_spike_report(target_date=datetime.now().date(), db_path=test_db, output_dir=report_dir)

    report_file = report_dir / f"spike_{datetime.now().date().isoformat()}.html"
    if report_file.exists():
        print(f"✓ 급상승 리포트 생성 성공: {report_file}")
    else:
        print("⚠ 리포트 파일이 생성되지 않음")

except Exception as e:
    print(f"✗ 리포트 생성 실패: {e}")
    import traceback

    traceback.print_exc()

# 정리
print("\n" + "=" * 70)
print("테스트 완료!")
print("=" * 70)
print(f"\n테스트 데이터베이스: {test_db}")
print(f"리포트 디렉토리: {report_dir}")
print("\n다음 명령으로 테스트 데이터 정리:")
print(f"  del {test_db}")

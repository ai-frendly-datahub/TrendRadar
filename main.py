# -*- coding: utf-8 -*-
"""TrendRadar 메인 실행 스크립트."""

from __future__ import annotations

import argparse
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from collectors.google_collector import GoogleTrendsCollector
from collectors.google_trending_collector import GoogleTrendingCollector
from collectors.naver_collector import NaverDataLabCollector
from collectors.wikipedia_collector import WikipediaPageviewsCollector
from storage import trend_store
from reporters.html_reporter import generate_daily_report
from analyzers.spike_detector import SpikeDetector
from reporters.spike_reporter import generate_spike_report

CONFIG_ENV_VAR = "TRENDRADAR_CONFIG_PATH"
PROJECT_ROOT = Path(__file__).resolve().parent
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "config" / "keyword_sets.yaml"
DEFAULT_REPORT_DIR = PROJECT_ROOT / "docs" / "reports"


def load_keyword_sets_config(path: Path | None = None) -> dict[str, Any]:
    """keyword_sets.yaml 로드."""
    config_path = Path(path or os.environ.get(CONFIG_ENV_VAR, DEFAULT_CONFIG_PATH))
    with config_path.open(encoding="utf-8") as fp:
        return yaml.safe_load(fp)


def collect_trends(
    keyword_set: dict[str, Any],
    *,
    db_path: Path | None = None,
    source_filter: str | None = None,
) -> tuple[int, int, list[str]]:
    """Collect trend data from configured sources and persist them."""
    total_points = 0
    sources_succeeded = 0
    errors: list[str] = []

    keywords = keyword_set.get("keywords", [])
    channels = keyword_set.get("channels", ["naver", "google"])
    time_range = keyword_set.get("time_range", {})
    filters = keyword_set.get("filters", {})

    # Naver DataLab
    if "naver" in channels and (source_filter is None or source_filter == "naver"):
        try:
            naver_collector = NaverDataLabCollector(
                client_id=os.environ.get("NAVER_CLIENT_ID"),
                client_secret=os.environ.get("NAVER_CLIENT_SECRET"),
            )

            naver_data = naver_collector.collect(
                keywords=keywords,
                start_date=time_range.get("start"),
                end_date=time_range.get("end"),
                time_unit=filters.get("time_unit", "date"),
                device=filters.get("device"),
                gender=filters.get("gender"),
                ages=filters.get("ages"),
            )

            for keyword, points in naver_data.items():
                trend_store.save_trend_points(
                    source="naver",
                    keyword=keyword,
                    points=points,
                    metadata={
                        "set_name": keyword_set.get("name"),
                        "filters": filters,
                    },
                    db_path=db_path,
                )
                total_points += len(points)

            sources_succeeded += 1
            print(f"  - Naver DataLab: {len(naver_data)} keywords, {total_points} points")

        except Exception as e:
            errors.append(f"Naver DataLab: {str(e)[:100]}")
            print(f"  - Naver DataLab failed: {e}")

    # Google Trends
    if "google" in channels and (source_filter is None or source_filter == "google"):
        try:
            google_collector = GoogleTrendsCollector()

            google_data = google_collector.collect(
                keywords=keywords,
                geo=filters.get("geo", "KR"),
                timeframe=f"{time_range.get('start')} {time_range.get('end')}",
            )

            google_points = 0
            for keyword, points in google_data.items():
                trend_store.save_trend_points(
                    source="google",
                    keyword=keyword,
                    points=points,
                    metadata={
                        "set_name": keyword_set.get("name"),
                        "geo": filters.get("geo", "KR"),
                    },
                    db_path=db_path,
                )
                google_points += len(points)

            total_points += google_points
            sources_succeeded += 1
            print(f"  - Google Trends: {len(google_data)} keywords, {google_points} points")

        except Exception as e:
            errors.append(f"Google Trends: {str(e)[:100]}")
            print(f"  - Google Trends failed: {e}")

    # Google Trending (daily/realtime)
    if "google_trending" in channels and (source_filter is None or source_filter == "google_trending"):
        try:
            trending_collector = GoogleTrendingCollector()
            trending_data = trending_collector.collect(
                region=filters.get("google_trending_region", "south_korea"),
                mode=filters.get("google_trending_mode", "daily"),
                category=filters.get("google_trending_category"),
                top_n=filters.get("google_trending_top_n", 20),
                date_override=time_range.get("end") or time_range.get("start"),
            )

            trending_points = 0
            for keyword, points in trending_data.items():
                trend_store.save_trend_points(
                    source="google_trending",
                    keyword=keyword,
                    points=points,
                    metadata={
                        "set_name": keyword_set.get("name"),
                        "region": filters.get("google_trending_region", "south_korea"),
                        "mode": filters.get("google_trending_mode", "daily"),
                        "category": filters.get("google_trending_category"),
                    },
                    db_path=db_path,
                )
                trending_points += len(points)

            total_points += trending_points
            sources_succeeded += 1
            print(f"  - Google Trending: {len(trending_data)} keywords, {trending_points} points")

        except Exception as e:
            errors.append(f"Google Trending: {str(e)[:100]}")
            print(f"  - Google Trending failed: {e}")

    # Wikipedia Pageviews
    if "wikipedia" in channels and (source_filter is None or source_filter == "wikipedia"):
        try:
            wiki_collector = WikipediaPageviewsCollector()
            wiki_data = wiki_collector.collect(
                keywords=keywords,
                start_date=time_range.get("start"),
                end_date=time_range.get("end"),
                project=filters.get("wikipedia_project", "ko.wikipedia"),
                access=filters.get("wikipedia_access", "all-access"),
                agent=filters.get("wikipedia_agent", "user"),
                granularity=filters.get("wikipedia_granularity", "daily"),
            )

            wiki_points = 0
            for keyword, points in wiki_data.items():
                trend_store.save_trend_points(
                    source="wikipedia",
                    keyword=keyword,
                    points=points,
                    metadata={
                        "set_name": keyword_set.get("name"),
                        "project": filters.get("wikipedia_project", "ko.wikipedia"),
                        "access": filters.get("wikipedia_access", "all-access"),
                        "agent": filters.get("wikipedia_agent", "user"),
                        "granularity": filters.get("wikipedia_granularity", "daily"),
                    },
                    db_path=db_path,
                )
                wiki_points += len(points)

            total_points += wiki_points
            sources_succeeded += 1
            print(f"  - Wikipedia Pageviews: {len(wiki_data)} keywords, {wiki_points} points")

        except Exception as e:
            errors.append(f"Wikipedia Pageviews: {str(e)[:100]}")
            print(f"  - Wikipedia Pageviews failed: {e}")

    return total_points, sources_succeeded, errors

def run_once(
    execute_collectors: bool = False,
    *,
    config_path: Path | None = None,
    db_path: Path | None = None,
    generate_report: bool = False,
    report_output_dir: Path | None = None,
    source_filter: str | None = None,
) -> None:
    """트렌드 수집을 한 번 실행합니다."""
    start_time = time.time()
    now = datetime.now(timezone.utc)

    print(f"[{now.isoformat()}] TrendRadar run_once 시작")

    if not execute_collectors:
        print("  - 실행 모드: dry-run (collectors 미실행)")
        return

    # 키워드 세트 설정 로드
    config = load_keyword_sets_config(config_path)
    keyword_sets = config.get("keyword_sets", [])

    if not keyword_sets:
        print("  - 경고: keyword_sets.yaml에 키워드 세트가 없습니다.")
        return

    print(f"  - 로드된 키워드 세트: {len(keyword_sets)}개")

    # 각 키워드 세트별로 수집
    total_points = 0
    total_sources_succeeded = 0
    all_errors = []

    for kw_set in keyword_sets:
        if not kw_set.get("enabled", True):
            continue

        set_name = kw_set.get("name", "Unknown")
        print(f"\n  [{set_name}] 수집 시작...")

        points, sources, errors = collect_trends(
            kw_set,
            db_path=db_path,
            source_filter=source_filter,
        )

        total_points += points
        total_sources_succeeded += sources
        all_errors.extend(errors)

    print(f"\n  - 총 수집 데이터 포인트: {total_points}개")
    print(f"  - 성공한 소스: {total_sources_succeeded}개")

    # HTML 리포트 생성
    if generate_report:
        print("\n  - HTML 리포트 생성 중...")
        try:
            report_dir = report_output_dir or DEFAULT_REPORT_DIR
            report_dir.mkdir(parents=True, exist_ok=True)

            generate_daily_report(
                target_date=now.date(),
                keyword_sets=keyword_sets,
                db_path=db_path,
                output_dir=report_dir,
            )
            print(f"  ✓ 리포트 저장: {report_dir}")
        except Exception as e:
            print(f"  ✗ 리포트 생성 실패: {e}")
            all_errors.append(f"Report generation: {str(e)[:100]}")

        # 급상승 키워드 감지 및 리포트 생성
        print("\n  - 급상승 키워드 감지 중...")
        try:
            detector = SpikeDetector(
                db_path=db_path,
                recent_days=7,
                baseline_days=30
            )
            all_spikes = detector.detect_all_spikes(source=None, top_n=10)

            total_spikes = sum(len(v) for v in all_spikes.values())
            if total_spikes > 0:
                print(f"  ✓ 급상승 신호 {total_spikes}개 감지")
                print(f"    - Surge: {len(all_spikes['surge'])}개")
                print(f"    - Emerging: {len(all_spikes['emerging'])}개")
                print(f"    - Viral: {len(all_spikes['viral'])}개")

                report_dir = report_output_dir or DEFAULT_REPORT_DIR
                generate_spike_report(
                    target_date=now.date(),
                    db_path=db_path,
                    output_dir=report_dir,
                )
                print(f"  ✓ 급상승 리포트 저장: {report_dir}")
            else:
                print("  ℹ️  급상승 신호 없음 (데이터 부족 가능)")
        except Exception as e:
            print(f"  ✗ 급상승 감지 실패: {e}")
            all_errors.append(f"Spike detection: {str(e)[:100]}")

        # 인덱스 페이지 생성
        print("\n  - 리포트 인덱스 페이지 생성 중...")
        try:
            from reporters.index_generator import generate_index_page
            report_dir = report_output_dir or DEFAULT_REPORT_DIR
            generate_index_page(report_dir)
            print(f"  ✓ 인덱스 페이지 생성 완료")
        except Exception as e:
            print(f"  ✗ 인덱스 페이지 생성 실패: {e}")

    runtime_seconds = time.time() - start_time
    print(f"\n  - 실행 시간: {runtime_seconds:.1f}초")

    if all_errors:
        print(f"  - 오류 {len(all_errors)}건:")
        for err in all_errors[:5]:  # 최대 5개만 표시
            print(f"    - {err}")


def run_scheduler(
    interval_hours: int = 24,
    *,
    config_path: Path | None = None,
    db_path: Path | None = None,
) -> None:
    """정기적으로 트렌드 데이터를 수집하는 스케줄러.

    Args:
        interval_hours: 수집 간격 (시간 단위, 기본 24시간)
        config_path: keyword_sets.yaml 경로
        db_path: DuckDB 파일 경로
    """
    print(f"TrendRadar 스케줄러 시작 (수집 간격: {interval_hours}시간)")
    print(f"중단하려면 Ctrl+C를 누르세요")

    while True:
        try:
            run_once(
                execute_collectors=True,
                config_path=config_path,
                db_path=db_path,
                generate_report=True,
            )
            print(f"\n다음 수집까지 {interval_hours}시간 대기 중...")
            time.sleep(interval_hours * 3600)

        except KeyboardInterrupt:
            print("\n스케줄러 종료")
            break
        except Exception as e:
            print(f"오류 발생: {e}")
            print(f"10분 후 재시도...")
            time.sleep(600)  # 10분 대기 후 재시도


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="TrendRadar 트렌드 데이터 수집")
    parser.add_argument(
        "--mode",
        choices=["once", "scheduler"],
        default="once",
        help="실행 모드: once (1회 실행) 또는 scheduler (정기 실행)",
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=24,
        help="스케줄러 모드에서 수집 간격 (시간 단위, 기본 24)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Dry-run 모드 (수집 없이 설정만 확인)",
    )
    parser.add_argument(
        "--generate-report",
        action="store_true",
        help="HTML 리포트 생성 (기본값: False)",
    )
    parser.add_argument(
        "--report-dir",
        type=Path,
        default=DEFAULT_REPORT_DIR,
        help=f"리포트 출력 디렉토리 (기본값: {DEFAULT_REPORT_DIR})",
    )
    parser.add_argument(
        "--source",
        choices=["naver", "google", "google_trending", "wikipedia"],
        default=None,
        help="특정 소스만 수집 (기본값: 모두)",
    )
    parser.add_argument(
        "--db-path",
        type=Path,
        default=PROJECT_ROOT / "data" / "trendradar.duckdb",
        help="DuckDB 파일 경로",
    )

    args = parser.parse_args()

    if args.mode == "once":
        run_once(
            execute_collectors=not args.dry_run,
            generate_report=args.generate_report,
            report_output_dir=args.report_dir,
            source_filter=args.source,
            db_path=args.db_path,
        )
    else:
        if args.dry_run:
            print("스케줄러 모드에서는 dry-run이 지원되지 않습니다")
        else:
            run_scheduler(
                interval_hours=args.interval,
                db_path=args.db_path,
            )

# -*- coding: utf-8 -*-
"""네이버 쇼핑인사이트 Collector 사용 예시."""

import os
from datetime import datetime, timedelta
from collectors.naver_shopping_collector import NaverShoppingCollector


def main():
    """네이버 쇼핑 트렌드 수집 예시."""
    # API 키 설정 필요
    client_id = os.environ.get("NAVER_CLIENT_ID")
    client_secret = os.environ.get("NAVER_CLIENT_SECRET")

    if not client_id or not client_secret:
        print("❌ NAVER_CLIENT_ID/SECRET 환경 변수를 설정해주세요.")
        return

    collector = NaverShoppingCollector(
        client_id=client_id,
        client_secret=client_secret
    )

    # 1. 인기 카테고리 목록
    print("📂 네이버 쇼핑 인기 카테고리")
    print("=" * 60)

    categories = NaverShoppingCollector.get_popular_categories()

    for cat_id, cat_name in categories.items():
        print(f"  • {cat_name} ({cat_id})")

    # 2. 패션의류 카테고리 트렌드 (최근 3개월)
    print("\n\n👗 패션의류 카테고리 트렌드 (최근 3개월)")
    print("=" * 60)

    end_date = datetime.now()
    start_date = end_date - timedelta(days=90)

    fashion_trends = collector.collect_category_trends(
        category="50000000",  # 패션의류
        start_date=start_date.strftime("%Y-%m-%d"),
        end_date=end_date.strftime("%Y-%m-%d"),
        time_unit="week"
    )

    if fashion_trends:
        points = fashion_trends[0]['points']
        print(f"수집된 데이터 포인트: {len(points)}개\n")

        # 최근 5주 데이터
        print("최근 5주 트렌드:")
        for point in points[-5:]:
            print(f"  {point['date']}: {point['value']:.1f}")

    # 3. 패션의류 인기 검색어 (최근 1개월)
    print("\n\n🔍 패션의류 인기 검색어 (최근 1개월)")
    print("=" * 60)

    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)

    fashion_keywords = collector.collect_category_keywords(
        category="50000000",
        start_date=start_date.strftime("%Y-%m-%d"),
        end_date=end_date.strftime("%Y-%m-%d"),
        time_unit="date"
    )

    for i, (keyword, points) in enumerate(list(fashion_keywords.items())[:10], 1):
        if points:
            latest = points[-1]
            avg_value = sum(p['value'] for p in points) / len(points)
            print(f"{i:2d}. {keyword:15s} - 최근: {latest['value']:5.1f}, "
                  f"평균: {avg_value:5.1f}")

    # 4. 여성 20-30대 모바일 패션 트렌드
    print("\n\n👩 여성 20-30대 모바일 패션 트렌드")
    print("=" * 60)

    end_date = datetime.now()
    start_date = end_date - timedelta(days=60)

    target_trends = collector.collect_category_trends(
        category="50000000",
        start_date=start_date.strftime("%Y-%m-%d"),
        end_date=end_date.strftime("%Y-%m-%d"),
        time_unit="week",
        device="mo",  # 모바일
        gender="f",   # 여성
        ages=["2", "3"]  # 20대, 30대
    )

    if target_trends:
        points = target_trends[0]['points']
        print(f"수집된 데이터 포인트: {len(points)}개\n")

        print("최근 4주 트렌드:")
        for point in points[-4:]:
            print(f"  {point['date']}: {point['value']:.1f}")

    # 5. 화장품/미용 카테고리 트렌드
    print("\n\n💄 화장품/미용 카테고리 트렌드")
    print("=" * 60)

    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)

    beauty_trends = collector.collect_category_trends(
        category="50000002",  # 화장품/미용
        start_date=start_date.strftime("%Y-%m-%d"),
        end_date=end_date.strftime("%Y-%m-%d"),
        time_unit="week"
    )

    if beauty_trends:
        points = beauty_trends[0]['points']

        print("최근 트렌드:")
        for point in points:
            print(f"  {point['date']}: {point['value']:.1f}")


if __name__ == "__main__":
    main()

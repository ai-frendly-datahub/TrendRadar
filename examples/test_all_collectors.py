# -*- coding: utf-8 -*-
"""모든 Collector 통합 테스트 스크립트.

실제 API를 호출하여 각 Collector가 제대로 작동하는지 확인합니다.
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta


def test_google_trends():
    """Google Trends Collector 테스트."""
    print("\n" + "="*60)
    print("🔍 Google Trends Collector 테스트")
    print("="*60)

    from collectors.google_collector import GoogleTrendsCollector

    try:
        collector = GoogleTrendsCollector(hl="ko", tz=540)

        print("📊 키워드: 파이썬, 자바스크립트")
        print("📅 기간: 최근 3개월")

        data = collector.collect(
            keywords=["파이썬", "자바스크립트"],
            geo="KR",
            timeframe="today 3-m"
        )

        for keyword, points in data.items():
            if points:
                latest = points[-1]
                print(f"  ✅ {keyword}: {len(points)}개 데이터 포인트")
                print(f"     최신 값: {latest['value']} ({latest['date']})")
            else:
                print(f"  ⚠️  {keyword}: 데이터 없음")

        print("✅ Google Trends 테스트 성공!")
        return True

    except Exception as e:
        print(f"❌ Google Trends 테스트 실패: {e}")
        return False


def test_naver_datalab():
    """네이버 데이터랩 Collector 테스트."""
    print("\n" + "="*60)
    print("🔍 네이버 데이터랩 Collector 테스트")
    print("="*60)

    client_id = os.environ.get("NAVER_CLIENT_ID")
    client_secret = os.environ.get("NAVER_CLIENT_SECRET")

    if not client_id or not client_secret:
        print("⚠️  NAVER_CLIENT_ID/SECRET 환경 변수가 설정되지 않았습니다.")
        print("   테스트를 건너뜁니다.")
        return None

    from collectors.naver_collector import NaverDataLabCollector

    try:
        collector = NaverDataLabCollector(
            client_id=client_id,
            client_secret=client_secret
        )

        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)

        print(f"📊 키워드: 파이썬, 자바스크립트")
        print(f"📅 기간: {start_date.date()} ~ {end_date.date()}")

        data = collector.collect(
            keywords=["파이썬", "자바스크립트"],
            start_date=start_date.strftime("%Y-%m-%d"),
            end_date=end_date.strftime("%Y-%m-%d"),
            time_unit="date"
        )

        for keyword, points in data.items():
            if points:
                latest = points[-1]
                print(f"  ✅ {keyword}: {len(points)}개 데이터 포인트")
                print(f"     최신 값: {latest['value']} ({latest['date']})")
            else:
                print(f"  ⚠️  {keyword}: 데이터 없음")

        print("✅ 네이버 데이터랩 테스트 성공!")
        return True

    except Exception as e:
        print(f"❌ 네이버 데이터랩 테스트 실패: {e}")
        return False


def test_youtube_trending():
    """YouTube Trending Collector 테스트."""
    print("\n" + "="*60)
    print("🎥 YouTube Trending Collector 테스트")
    print("="*60)

    api_key = os.environ.get("YOUTUBE_API_KEY")

    if not api_key:
        print("⚠️  YOUTUBE_API_KEY 환경 변수가 설정되지 않았습니다.")
        print("   테스트를 건너뜁니다.")
        return None

    from collectors.youtube_collector import YouTubeTrendingCollector

    try:
        collector = YouTubeTrendingCollector(api_key=api_key)

        print("📊 지역: 한국 (KR)")
        print("📅 카테고리: Music (10)")

        videos = collector.collect_trending_videos(
            region_code="KR",
            category_id="10",  # Music
            max_results=10
        )

        print(f"  ✅ 수집된 영상: {len(videos)}개")

        if videos:
            print("\n  🔥 Top 5 트렌딩 영상:")
            for i, video in enumerate(videos[:5], 1):
                print(f"     {i}. {video['title'][:50]}")
                print(f"        👁 {video['view_count']:,} views | "
                      f"👍 {video['like_count']:,} likes")

        # 키워드 집계
        keywords = collector.collect_trending_keywords(
            region_code="KR",
            max_results=10
        )

        if keywords:
            print("\n  🏷️  Top 10 트렌딩 키워드:")
            for i, (keyword, count) in enumerate(list(keywords.items())[:10], 1):
                print(f"     {i}. {keyword} ({count}회)")

        print("✅ YouTube Trending 테스트 성공!")
        return True

    except Exception as e:
        print(f"❌ YouTube Trending 테스트 실패: {e}")
        return False


def test_reddit():
    """Reddit Collector 테스트."""
    print("\n" + "="*60)
    print("💬 Reddit Collector 테스트")
    print("="*60)

    from collectors.reddit_collector import RedditCollector

    try:
        # 인증 없이 테스트
        collector = RedditCollector()

        print("📊 서브레딧: python")
        print("📅 정렬: hot")

        posts = collector.collect_subreddit_posts(
            subreddit="python",
            sort="hot",
            limit=10
        )

        print(f"  ✅ 수집된 게시글: {len(posts)}개")

        if posts:
            print("\n  🔥 Top 5 인기 게시글:")
            for i, post in enumerate(posts[:5], 1):
                print(f"     {i}. {post['title'][:60]}")
                print(f"        ⬆️  {post['score']} points | "
                      f"💬 {post['num_comments']} comments")

        # 키워드 집계
        keywords = collector.collect_trending_keywords(
            subreddits=["python", "learnpython"],
            time_filter="day",
            limit=10
        )

        if keywords:
            print("\n  🏷️  Top 10 트렌딩 키워드:")
            for i, (keyword, count) in enumerate(list(keywords.items())[:10], 1):
                print(f"     {i}. {keyword} ({count}회)")

        print("✅ Reddit 테스트 성공!")
        return True

    except Exception as e:
        print(f"❌ Reddit 테스트 실패: {e}")
        return False


def test_naver_shopping():
    """네이버 쇼핑인사이트 Collector 테스트."""
    print("\n" + "="*60)
    print("🛒 네이버 쇼핑인사이트 Collector 테스트")
    print("="*60)

    client_id = os.environ.get("NAVER_CLIENT_ID")
    client_secret = os.environ.get("NAVER_CLIENT_SECRET")

    if not client_id or not client_secret:
        print("⚠️  NAVER_CLIENT_ID/SECRET 환경 변수가 설정되지 않았습니다.")
        print("   테스트를 건너뜁니다.")
        return None

    from collectors.naver_shopping_collector import NaverShoppingCollector

    try:
        collector = NaverShoppingCollector(
            client_id=client_id,
            client_secret=client_secret
        )

        # 카테고리 목록
        categories = NaverShoppingCollector.get_popular_categories()
        print("📊 인기 카테고리:")
        for cat_id, cat_name in list(categories.items())[:5]:
            print(f"  • {cat_name} ({cat_id})")

        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)

        print(f"\n📅 기간: {start_date.date()} ~ {end_date.date()}")
        print("📊 카테고리: 패션의류 (50000000)")

        trends = collector.collect_category_trends(
            category="50000000",  # 패션의류
            start_date=start_date.strftime("%Y-%m-%d"),
            end_date=end_date.strftime("%Y-%m-%d"),
            time_unit="week"
        )

        if trends:
            print(f"  ✅ 수집된 트렌드 데이터: {len(trends[0]['points'])}개 포인트")
            if trends[0]['points']:
                latest = trends[0]['points'][-1]
                print(f"     최신 값: {latest['value']} ({latest['date']})")

        print("✅ 네이버 쇼핑인사이트 테스트 성공!")
        return True

    except Exception as e:
        print(f"❌ 네이버 쇼핑인사이트 테스트 실패: {e}")
        return False


def main():
    """모든 Collector 테스트 실행."""
    print("\n" + "🎯 TrendRadar Collectors 통합 테스트")
    print("=" * 60)

    results = {
        "Google Trends": test_google_trends(),
        "네이버 데이터랩": test_naver_datalab(),
        "YouTube Trending": test_youtube_trending(),
        "Reddit": test_reddit(),
        "네이버 쇼핑": test_naver_shopping(),
    }

    # 결과 요약
    print("\n" + "="*60)
    print("📊 테스트 결과 요약")
    print("="*60)

    for name, result in results.items():
        if result is True:
            status = "✅ 성공"
        elif result is False:
            status = "❌ 실패"
        else:
            status = "⚠️  건너뜀 (API 키 없음)"

        print(f"  {name}: {status}")

    # 통계
    success_count = sum(1 for r in results.values() if r is True)
    fail_count = sum(1 for r in results.values() if r is False)
    skip_count = sum(1 for r in results.values() if r is None)

    print(f"\n  총 {len(results)}개 중:")
    print(f"  • 성공: {success_count}개")
    print(f"  • 실패: {fail_count}개")
    print(f"  • 건너뜀: {skip_count}개")

    print("\n" + "="*60)
    print("💡 API 키 설정 방법:")
    print("   export NAVER_CLIENT_ID=your_id")
    print("   export NAVER_CLIENT_SECRET=your_secret")
    print("   export YOUTUBE_API_KEY=your_key")
    print("="*60)


if __name__ == "__main__":
    main()

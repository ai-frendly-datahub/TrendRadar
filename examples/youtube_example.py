"""YouTube Trending Collector 사용 예시."""

import os

from collectors.youtube_collector import YouTubeTrendingCollector


def main():
    """YouTube 트렌딩 영상 및 키워드 수집 예시."""
    # API 키 설정 필요
    api_key = os.environ.get("YOUTUBE_API_KEY")

    if not api_key:
        print("❌ YOUTUBE_API_KEY 환경 변수를 설정해주세요.")
        print("   export YOUTUBE_API_KEY=your_api_key")
        return

    collector = YouTubeTrendingCollector(api_key=api_key)

    # 1. 한국 인기 급상승 영상 (음악 카테고리)
    print("🎵 한국 인기 Music 영상 Top 10")
    print("=" * 60)

    music_videos = collector.collect_trending_videos(
        region_code="KR",
        category_id="10",  # Music
        max_results=10,
    )

    for i, video in enumerate(music_videos, 1):
        print(f"\n{i}. {video['title']}")
        print(f"   📺 {video['channel_title']}")
        print(f"   👁  {video['view_count']:,} views")
        print(f"   👍 {video['like_count']:,} likes")
        print(f"   💬 {video['comment_count']:,} comments")
        print(f"   🔗 https://youtube.com/watch?v={video['video_id']}")

    # 2. 전체 인기 영상 (카테고리 무관)
    print("\n\n🔥 한국 전체 인기 영상 Top 10")
    print("=" * 60)

    all_videos = collector.collect_trending_videos(region_code="KR", max_results=10)

    for i, video in enumerate(all_videos, 1):
        print(f"{i}. {video['title'][:60]}")
        print(f"   {video['view_count']:,} views | {video['channel_title']}")

    # 3. 트렌딩 키워드 분석
    print("\n\n🏷️  트렌딩 키워드 Top 20")
    print("=" * 60)

    keywords = collector.collect_trending_keywords(region_code="KR", max_results=50)

    for i, (keyword, count) in enumerate(list(keywords.items())[:20], 1):
        print(f"{i:2d}. {keyword[:30]:30s} - {count:3d}회")

    # 4. 카테고리 목록 조회
    print("\n\n📂 YouTube 카테고리 목록")
    print("=" * 60)

    categories = collector.get_video_categories(region_code="KR")

    for cat_id, cat_name in sorted(categories.items(), key=lambda x: int(x[0]))[:10]:
        print(f"  {cat_id:2s}. {cat_name}")


if __name__ == "__main__":
    main()

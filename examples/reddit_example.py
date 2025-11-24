# -*- coding: utf-8 -*-
"""Reddit Collector 사용 예시."""

from collectors.reddit_collector import RedditCollector


def main():
    """Reddit 인기 게시글 및 트렌드 수집 예시."""
    # 인증 없이 사용 가능 (제한적)
    collector = RedditCollector()

    # 1. r/python 인기 게시글
    print("🐍 r/python 인기 게시글 Top 10")
    print("=" * 60)

    python_posts = collector.collect_subreddit_posts(
        subreddit="python",
        sort="hot",
        limit=10
    )

    for i, post in enumerate(python_posts, 1):
        print(f"\n{i}. {post['title']}")
        print(f"   👤 u/{post['author']}")
        print(f"   ⬆️  {post['score']:,} points")
        print(f"   💬 {post['num_comments']:,} comments")
        print(f"   🔗 {post['permalink']}")

    # 2. r/popular 전체 인기 게시글
    print("\n\n🔥 r/popular 인기 게시글 Top 10")
    print("=" * 60)

    popular_posts = collector.collect_popular_posts(
        time_filter="day",
        limit=10
    )

    for i, post in enumerate(popular_posts, 1):
        print(f"{i}. [{post['subreddit']}] {post['title'][:60]}")
        print(f"   {post['score']:,} points | {post['num_comments']:,} comments")

    # 3. 여러 서브레딧의 트렌딩 키워드
    print("\n\n🏷️  Python 관련 서브레딧 트렌딩 키워드 Top 20")
    print("=" * 60)

    keywords = collector.collect_trending_keywords(
        subreddits=["python", "learnpython", "django", "flask"],
        time_filter="day",
        limit=25
    )

    for i, (keyword, count) in enumerate(list(keywords.items())[:20], 1):
        print(f"{i:2d}. {keyword[:30]:30s} - {count:3d}회")

    # 4. 특정 서브레딧의 Top 게시글 (지난 주)
    print("\n\n📅 r/programming 지난 주 Top 게시글")
    print("=" * 60)

    top_posts = collector.collect_subreddit_posts(
        subreddit="programming",
        sort="top",
        time_filter="week",
        limit=5
    )

    for i, post in enumerate(top_posts, 1):
        print(f"\n{i}. {post['title']}")
        print(f"   ⬆️  {post['score']:,} points | 💬 {post['num_comments']:,} comments")
        print(f"   🔗 {post['url']}")


if __name__ == "__main__":
    main()

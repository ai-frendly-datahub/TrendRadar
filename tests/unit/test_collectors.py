"""Collector 단위 테스트."""

from __future__ import annotations

import os
from datetime import UTC, datetime, timedelta

import pytest


# Google Trends Collector Tests
class TestGoogleTrendsCollector:
    """Google Trends Collector 테스트."""

    def test_collector_initialization(self):
        """Collector 초기화 테스트."""
        from collectors.google_collector import GoogleTrendsCollector

        collector = GoogleTrendsCollector(hl="ko", tz=540)
        assert collector.pytrends is not None

    @pytest.mark.integration
    def test_collect_basic(self):
        """기본 수집 테스트 (실제 API 호출)."""
        from collectors.google_collector import GoogleTrendsCollector

        collector = GoogleTrendsCollector()

        # 최근 3개월 데이터
        data = collector.collect(keywords=["python"], geo="KR", timeframe="today 3-m")

        assert "python" in data
        assert len(data["python"]) > 0
        assert "date" in data["python"][0]
        assert "value" in data["python"][0]


# Naver DataLab Collector Tests
class TestNaverDataLabCollector:
    """네이버 데이터랩 Collector 테스트."""

    def test_collector_requires_credentials(self):
        """인증 정보 없이 초기화 시 에러."""
        from collectors.naver_collector import NaverDataLabCollector

        with pytest.raises(ValueError, match="NAVER_CLIENT_ID"):
            NaverDataLabCollector(client_id=None, client_secret=None)

    def test_collector_initialization(self):
        """Collector 초기화 테스트."""
        from collectors.naver_collector import NaverDataLabCollector

        # 더미 키로 초기화만 테스트
        collector = NaverDataLabCollector(client_id="dummy_id", client_secret="dummy_secret")
        assert collector.client_id == "dummy_id"
        assert collector.client_secret == "dummy_secret"

    @pytest.mark.integration
    @pytest.mark.skipif(not os.environ.get("NAVER_CLIENT_ID"), reason="NAVER_CLIENT_ID not set")
    def test_collect_basic(self):
        """기본 수집 테스트 (실제 API 호출)."""
        from collectors.naver_collector import NaverDataLabCollector

        collector = NaverDataLabCollector(
            client_id=os.environ["NAVER_CLIENT_ID"], client_secret=os.environ["NAVER_CLIENT_SECRET"]
        )

        end_date = datetime.now(tz=UTC)
        start_date = end_date - timedelta(days=30)

        data = collector.collect(
            keywords=["파이썬"],
            start_date=start_date.strftime("%Y-%m-%d"),
            end_date=end_date.strftime("%Y-%m-%d"),
            time_unit="date",
        )

        assert "파이썬" in data
        assert len(data["파이썬"]) > 0


# YouTube Trending Collector Tests
class TestYouTubeTrendingCollector:
    """YouTube Trending Collector 테스트."""

    def test_collector_requires_api_key(self):
        """API 키 없이 초기화 시 에러."""
        from collectors.youtube_collector import YouTubeTrendingCollector

        with pytest.raises(ValueError, match="YOUTUBE_API_KEY"):
            YouTubeTrendingCollector(api_key=None)

    def test_collector_initialization(self):
        """Collector 초기화 테스트."""
        from collectors.youtube_collector import YouTubeTrendingCollector

        collector = YouTubeTrendingCollector(api_key="dummy_key")
        assert collector.api_key == "dummy_key"

    @pytest.mark.integration
    @pytest.mark.skipif(not os.environ.get("YOUTUBE_API_KEY"), reason="YOUTUBE_API_KEY not set")
    def test_collect_trending_videos(self):
        """인기 영상 수집 테스트 (실제 API 호출)."""
        from collectors.youtube_collector import YouTubeTrendingCollector

        collector = YouTubeTrendingCollector(api_key=os.environ["YOUTUBE_API_KEY"])

        videos = collector.collect_trending_videos(region_code="KR", max_results=10)

        assert len(videos) > 0
        assert "video_id" in videos[0]
        assert "title" in videos[0]
        assert "view_count" in videos[0]

    @pytest.mark.integration
    @pytest.mark.skipif(not os.environ.get("YOUTUBE_API_KEY"), reason="YOUTUBE_API_KEY not set")
    def test_collect_trending_keywords(self):
        """트렌딩 키워드 집계 테스트."""
        from collectors.youtube_collector import YouTubeTrendingCollector

        collector = YouTubeTrendingCollector(api_key=os.environ["YOUTUBE_API_KEY"])

        keywords = collector.collect_trending_keywords(region_code="KR", max_results=10)

        assert isinstance(keywords, dict)
        assert len(keywords) > 0


# Reddit Collector Tests
class TestRedditCollector:
    """Reddit Collector 테스트."""

    def test_collector_initialization_without_auth(self):
        """인증 없이 초기화."""
        from collectors.reddit_collector import RedditCollector

        collector = RedditCollector()
        assert collector.user_agent is not None
        assert collector.access_token is None

    def test_collector_initialization_with_auth(self):
        """인증 정보로 초기화."""
        from collectors.reddit_collector import RedditCollector

        collector = RedditCollector(client_id="dummy_id", client_secret="dummy_secret")
        assert collector.client_id == "dummy_id"

    @pytest.mark.integration
    def test_collect_subreddit_posts(self):
        """서브레딧 게시글 수집 (실제 API 호출)."""
        from collectors.reddit_collector import RedditCollector

        collector = RedditCollector()

        posts = collector.collect_subreddit_posts(subreddit="python", sort="hot", limit=10)

        assert len(posts) > 0
        assert "post_id" in posts[0]
        assert "title" in posts[0]
        assert "score" in posts[0]

    @pytest.mark.integration
    def test_collect_popular_posts(self):
        """r/popular 수집 테스트."""
        from collectors.reddit_collector import RedditCollector

        collector = RedditCollector()

        posts = collector.collect_popular_posts(time_filter="day", limit=10)

        assert len(posts) > 0
        assert "subreddit" in posts[0]


# Naver Shopping Collector Tests
class TestNaverShoppingCollector:
    """네이버 쇼핑인사이트 Collector 테스트."""

    def test_collector_requires_credentials(self):
        """인증 정보 없이 초기화 시 에러."""
        from collectors.naver_shopping_collector import NaverShoppingCollector

        with pytest.raises(ValueError, match="NAVER_CLIENT_ID"):
            NaverShoppingCollector(client_id=None, client_secret=None)

    def test_get_popular_categories(self):
        """인기 카테고리 목록 테스트."""
        from collectors.naver_shopping_collector import NaverShoppingCollector

        categories = NaverShoppingCollector.get_popular_categories()

        assert isinstance(categories, dict)
        assert "50000000" in categories  # 패션의류
        assert categories["50000000"] == "패션의류"

    @pytest.mark.integration
    @pytest.mark.skipif(not os.environ.get("NAVER_CLIENT_ID"), reason="NAVER_CLIENT_ID not set")
    def test_collect_category_trends(self):
        """카테고리 트렌드 수집 (실제 API 호출)."""
        from collectors.naver_shopping_collector import NaverShoppingCollector

        collector = NaverShoppingCollector(
            client_id=os.environ["NAVER_CLIENT_ID"], client_secret=os.environ["NAVER_CLIENT_SECRET"]
        )

        end_date = datetime.now(tz=UTC)
        start_date = end_date - timedelta(days=30)

        trends = collector.collect_category_trends(
            category="50000000",  # 패션의류
            start_date=start_date.strftime("%Y-%m-%d"),
            end_date=end_date.strftime("%Y-%m-%d"),
            time_unit="week",
        )

        assert len(trends) > 0
        assert "category" in trends[0]
        assert "points" in trends[0]

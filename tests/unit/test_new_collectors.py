"""New Collectors Unit Tests (HackerNews, Dev.to, Stack Exchange, Product Hunt)."""

from __future__ import annotations

import os
from unittest.mock import MagicMock, patch

import pytest


# HackerNews Collector Tests
class TestHackerNewsCollector:
    """HackerNews Collector 테스트."""

    def test_collector_initialization(self) -> None:
        """Collector 초기화 테스트."""
        from collectors.hackernews_collector import HackerNewsCollector

        collector = HackerNewsCollector()
        assert collector.API_BASE_URL == "https://hacker-news.firebaseio.com/v0"
        assert collector.TIMEOUT == 30

    @patch("collectors.hackernews_collector.requests.get")
    def test_collect_with_mocked_api(self, mock_get: MagicMock) -> None:
        """Mocked API를 사용한 수집 테스트."""
        from collectors.hackernews_collector import HackerNewsCollector

        # Mock top stories response
        mock_response_stories = MagicMock()
        mock_response_stories.json.return_value = [1, 2, 3]
        mock_response_stories.raise_for_status.return_value = None

        # Mock item responses
        mock_response_item = MagicMock()
        mock_response_item.json.return_value = {
            "id": 1,
            "title": "Test Story",
            "url": "https://example.com",
            "score": 100,
            "by": "testuser",
            "time": 1234567890,
            "descendants": 10,
            "type": "story",
        }
        mock_response_item.raise_for_status.return_value = None

        # Configure mock to return different responses
        mock_get.side_effect = [
            mock_response_stories,
            mock_response_item,
            mock_response_item,
            mock_response_item,
        ]

        collector = HackerNewsCollector()
        stories = collector.collect(limit=3)

        assert len(stories) == 3
        assert stories[0]["title"] == "Test Story"
        assert stories[0]["score"] == 100

    @patch("collectors.hackernews_collector.requests.get")
    def test_collect_handles_errors(self, mock_get: MagicMock) -> None:
        """API 에러 처리 테스트."""
        import requests

        from collectors.hackernews_collector import HackerNewsCollector

        mock_get.side_effect = requests.exceptions.RequestException("API Error")

        collector = HackerNewsCollector()
        with pytest.raises(RuntimeError, match="HackerNews"):
            collector.collect()


# Dev.to Collector Tests
class TestDevtoCollector:
    """Dev.to Collector 테스트."""

    def test_collector_initialization(self) -> None:
        """Collector 초기화 테스트."""
        from collectors.devto_collector import DevtoCollector

        collector = DevtoCollector()
        assert collector.API_BASE_URL == "https://dev.to/api"
        assert collector.TIMEOUT == 30

    @patch("collectors.devto_collector.requests.get")
    def test_collect_with_mocked_api(self, mock_get: MagicMock) -> None:
        """Mocked API를 사용한 수집 테스트."""
        from collectors.devto_collector import DevtoCollector

        mock_response = MagicMock()
        mock_response.json.return_value = [
            {
                "id": 1,
                "title": "Test Article",
                "url": "https://dev.to/test",
                "slug": "test-article",
                "positive_reactions_count": 50,
                "comments_count": 5,
                "published_at": "2024-01-01T00:00:00Z",
                "user": {"name": "Test Author", "username": "testauthor"},
                "tag_list": ["python", "testing"],
                "reading_time_minutes": 5,
            }
        ]
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        collector = DevtoCollector()
        articles = collector.collect(limit=1)

        assert len(articles) == 1
        assert articles[0]["title"] == "Test Article"
        assert articles[0]["positive_reactions_count"] == 50

    @patch("collectors.devto_collector.requests.get")
    def test_collect_handles_errors(self, mock_get: MagicMock) -> None:
        """API 에러 처리 테스트."""
        import requests

        from collectors.devto_collector import DevtoCollector

        mock_get.side_effect = requests.exceptions.RequestException("API Error")

        collector = DevtoCollector()
        with pytest.raises(RuntimeError, match="Dev.to"):
            collector.collect()


# Stack Exchange Collector Tests
class TestStackExchangeCollector:
    """Stack Exchange Collector 테스트."""

    def test_collector_initialization(self) -> None:
        """Collector 초기화 테스트."""
        from collectors.stackexchange_collector import StackExchangeCollector

        collector = StackExchangeCollector(api_key="test_key")
        assert collector.API_BASE_URL == "https://api.stackexchange.com/2.3"
        assert collector.TIMEOUT == 30
        assert collector.api_key == "test_key"

    def test_collector_initialization_from_env(self) -> None:
        """환경변수에서 API 키 로드 테스트."""
        from collectors.stackexchange_collector import StackExchangeCollector

        with patch.dict(os.environ, {"STACK_EXCHANGE_API_KEY": "env_key"}):
            collector = StackExchangeCollector()
            assert collector.api_key == "env_key"

    @patch("collectors.stackexchange_collector.requests.get")
    def test_collect_with_mocked_api(self, mock_get: MagicMock) -> None:
        """Mocked API를 사용한 수집 테스트."""
        from collectors.stackexchange_collector import StackExchangeCollector

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "items": [
                {
                    "question_id": 1,
                    "title": "Test Question",
                    "link": "https://stackoverflow.com/q/1",
                    "score": 100,
                    "view_count": 1000,
                    "answer_count": 5,
                    "is_answered": True,
                    "creation_date": 1234567890,
                    "last_activity_date": 1234567890,
                    "owner": {"display_name": "Test User"},
                    "tags": ["python", "testing"],
                }
            ]
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        collector = StackExchangeCollector(api_key="test_key")
        questions = collector.collect(limit=1)

        assert len(questions) == 1
        assert questions[0]["title"] == "Test Question"
        assert questions[0]["score"] == 100

    @patch("collectors.stackexchange_collector.requests.get")
    def test_collect_handles_errors(self, mock_get: MagicMock) -> None:
        """API 에러 처리 테스트."""
        import requests

        from collectors.stackexchange_collector import StackExchangeCollector

        mock_get.side_effect = requests.exceptions.RequestException("API Error")

        collector = StackExchangeCollector(api_key="test_key")
        with pytest.raises(RuntimeError, match="Stack Exchange"):
            collector.collect()


# Product Hunt Collector Tests
class TestProductHuntCollector:
    """Product Hunt Collector 테스트."""

    def test_collector_initialization(self) -> None:
        """Collector 초기화 테스트."""
        from collectors.producthunt_collector import ProductHuntCollector

        collector = ProductHuntCollector(api_key="test_key")
        assert collector.API_BASE_URL == "https://api.producthunt.com/v2/api/graphql"
        assert collector.TIMEOUT == 30
        assert collector.api_key == "test_key"

    def test_collector_initialization_from_env(self) -> None:
        """환경변수에서 API 키 로드 테스트."""
        from collectors.producthunt_collector import ProductHuntCollector

        with patch.dict(os.environ, {"PRODUCT_HUNT_API_KEY": "env_key"}):
            collector = ProductHuntCollector()
            assert collector.api_key == "env_key"

    def test_collect_requires_api_key(self) -> None:
        """API 키 없이 수집 시 에러."""
        from collectors.producthunt_collector import ProductHuntCollector

        collector = ProductHuntCollector(api_key=None)
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(RuntimeError, match="PRODUCT_HUNT_API_KEY"):
                collector.collect()

    @patch("collectors.producthunt_collector.requests.post")
    def test_collect_with_mocked_api(self, mock_post: MagicMock) -> None:
        """Mocked GraphQL API를 사용한 수집 테스트."""
        from collectors.producthunt_collector import ProductHuntCollector

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "data": {
                "posts": {
                    "edges": [
                        {
                            "node": {
                                "id": "1",
                                "name": "Test Product",
                                "tagline": "A test product",
                                "description": "Test description",
                                "url": "https://producthunt.com/posts/test",
                                "votesCount": 100,
                                "commentsCount": 10,
                                "createdAt": "2024-01-01T00:00:00Z",
                                "makers": [{"name": "Test Maker", "username": "testmaker"}],
                                "thumbnail": {"url": "https://example.com/thumb.jpg"},
                            }
                        }
                    ]
                }
            }
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        collector = ProductHuntCollector(api_key="test_key")
        products = collector.collect(limit=1)

        assert len(products) == 1
        assert products[0]["name"] == "Test Product"
        assert products[0]["votes_count"] == 100

    @patch("collectors.producthunt_collector.requests.post")
    def test_collect_handles_graphql_errors(self, mock_post: MagicMock) -> None:
        """GraphQL 에러 처리 테스트."""
        from collectors.producthunt_collector import ProductHuntCollector

        mock_response = MagicMock()
        mock_response.json.return_value = {"errors": [{"message": "Invalid query"}]}
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        collector = ProductHuntCollector(api_key="test_key")
        with pytest.raises(RuntimeError, match="GraphQL"):
            collector.collect()

    @patch("collectors.producthunt_collector.requests.post")
    def test_collect_handles_request_errors(self, mock_post: MagicMock) -> None:
        """HTTP 요청 에러 처리 테스트."""
        import requests

        from collectors.producthunt_collector import ProductHuntCollector

        mock_post.side_effect = requests.exceptions.RequestException("API Error")

        collector = ProductHuntCollector(api_key="test_key")
        with pytest.raises(RuntimeError, match="Product Hunt"):
            collector.collect()

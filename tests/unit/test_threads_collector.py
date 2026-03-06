"""Unit tests for ThreadsCollector."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from collectors.threads_collector import ThreadsCollector


@pytest.mark.unit
def test_threads_collector_initializes_with_token() -> None:
    """ThreadsCollector는 액세스 토큰으로 초기화된다"""
    with patch.dict("os.environ", {"THREADS_ACCESS_TOKEN": "test_token"}):
        collector = ThreadsCollector(access_token="test_token")
        assert collector.access_token == "test_token"


@pytest.mark.unit
def test_threads_collector_requires_access_token() -> None:
    """ThreadsCollector는 액세스 토큰이 필요하다"""
    with patch.dict("os.environ", {}, clear=True):
        with pytest.raises(ValueError, match="access_token"):
            ThreadsCollector()


@pytest.mark.unit
@patch("collectors.threads_collector.requests.get")
def test_threads_collector_collects_trending_topics(mock_get: MagicMock) -> None:
    """ThreadsCollector는 트렌딩 토픽을 수집한다"""
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "data": [
            {
                "id": "topic_1",
                "name": "Python",
                "post_count": 1000,
                "engagement_count": 5000,
                "rank": 1,
                "category": "technology",
                "url": "https://threads.net/topic/python",
                "collected_at": "2024-01-01T00:00:00Z",
            },
            {
                "id": "topic_2",
                "name": "AI",
                "post_count": 800,
                "engagement_count": 4000,
                "rank": 2,
                "category": "technology",
                "url": "https://threads.net/topic/ai",
                "collected_at": "2024-01-01T00:00:00Z",
            },
        ]
    }
    mock_get.return_value = mock_response

    collector = ThreadsCollector(access_token="test_token")
    topics = collector.collect_trending_topics(region="KR", limit=50)

    assert len(topics) == 2
    assert topics[0]["name"] == "Python"
    assert topics[0]["rank"] == 1
    assert topics[1]["name"] == "AI"
    assert topics[1]["rank"] == 2


@pytest.mark.unit
@patch("collectors.threads_collector.requests.get")
def test_threads_collector_collects_by_category(mock_get: MagicMock) -> None:
    """ThreadsCollector는 카테고리별 토픽을 수집한다"""
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "data": [
            {
                "id": "topic_1",
                "name": "Breaking News",
                "post_count": 2000,
                "engagement_count": 10000,
                "rank": 1,
                "url": "https://threads.net/topic/news",
            }
        ]
    }
    mock_get.return_value = mock_response

    collector = ThreadsCollector(access_token="test_token")
    topics = collector.collect_trending_by_category(category="news", region="KR", limit=50)

    assert len(topics) == 1
    assert topics[0]["category"] == "news"


@pytest.mark.unit
@patch("collectors.threads_collector.requests.get")
def test_threads_collector_retries_on_failure(mock_get: MagicMock) -> None:
    """ThreadsCollector는 실패 시 재시도한다"""
    mock_get.side_effect = Exception("Network error")

    collector = ThreadsCollector(access_token="test_token")

    with pytest.raises(Exception):
        collector.collect_trending_topics()

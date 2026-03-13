# pyright: reportPrivateUsage=false, reportAny=false
from __future__ import annotations

from unittest.mock import Mock, patch

import pytest
import requests
from tenacity import RetryError

from collectors.devto_collector import DevtoCollector
from collectors.hackernews_collector import HackerNewsCollector
from collectors.stackexchange_collector import StackExchangeCollector


pytestmark = pytest.mark.unit


def _mock_json_response(payload: object) -> Mock:
    response = Mock()
    response.raise_for_status = Mock()
    response.json.return_value = payload
    return response


def _http_500_error() -> requests.exceptions.HTTPError:
    return requests.exceptions.HTTPError("500 server error")


class TestDevtoCollectorRetry:
    def test_retry_on_timeout(self) -> None:
        collector = DevtoCollector()
        with patch("collectors.devto_collector.requests.get") as mock_get:
            mock_get.side_effect = [
                requests.exceptions.Timeout("timeout"),
                requests.exceptions.Timeout("timeout"),
                _mock_json_response([{"id": 1, "title": "Test Article"}]),
            ]

            result = collector._fetch_with_retry("https://dev.to/api/articles")

            assert isinstance(result, list)
            assert result[0]["id"] == 1
            assert mock_get.call_count == 3

    def test_retry_on_5xx(self) -> None:
        collector = DevtoCollector()
        with patch("collectors.devto_collector.requests.get") as mock_get:
            mock_get.side_effect = [
                _http_500_error(),
                _http_500_error(),
                _mock_json_response([{"id": 1, "title": "Test Article"}]),
            ]

            result = collector._fetch_with_retry("https://dev.to/api/articles")

            assert isinstance(result, list)
            assert result[0]["title"] == "Test Article"
            assert mock_get.call_count == 3

    def test_max_retries_exceeded(self) -> None:
        collector = DevtoCollector()
        with patch("collectors.devto_collector.requests.get") as mock_get:
            mock_get.side_effect = [
                requests.exceptions.Timeout("timeout"),
                requests.exceptions.Timeout("timeout"),
                requests.exceptions.Timeout("timeout"),
            ]

            with pytest.raises(RetryError):
                _ = collector._fetch_with_retry("https://dev.to/api/articles")

            assert mock_get.call_count == 3

    def test_connection_error_retry(self) -> None:
        collector = DevtoCollector()
        with patch("collectors.devto_collector.requests.get") as mock_get:
            mock_get.side_effect = [
                requests.exceptions.ConnectionError("connection error"),
                _mock_json_response([{"id": 1, "title": "Test Article"}]),
            ]

            result = collector._fetch_with_retry("https://dev.to/api/articles")

            assert isinstance(result, list)
            assert len(result) == 1
            assert mock_get.call_count == 2


class TestHackerNewsCollectorRetry:
    def test_retry_on_timeout(self) -> None:
        collector = HackerNewsCollector()
        with patch("collectors.hackernews_collector.requests.get") as mock_get:
            mock_get.side_effect = [
                requests.exceptions.Timeout("timeout"),
                requests.exceptions.Timeout("timeout"),
                _mock_json_response([1, 2, 3]),
            ]

            result = collector._fetch_with_retry(
                "https://hacker-news.firebaseio.com/v0/topstories.json"
            )

            assert isinstance(result, list)
            assert result == [1, 2, 3]
            assert mock_get.call_count == 3

    def test_retry_on_5xx(self) -> None:
        collector = HackerNewsCollector()
        with patch("collectors.hackernews_collector.requests.get") as mock_get:
            mock_get.side_effect = [
                _http_500_error(),
                _http_500_error(),
                _mock_json_response({"id": 1, "title": "HN Story"}),
            ]

            result = collector._fetch_with_retry(
                "https://hacker-news.firebaseio.com/v0/item/1.json"
            )

            assert isinstance(result, dict)
            assert result["id"] == 1
            assert mock_get.call_count == 3

    def test_max_retries_exceeded(self) -> None:
        collector = HackerNewsCollector()
        with patch("collectors.hackernews_collector.requests.get") as mock_get:
            mock_get.side_effect = [
                requests.exceptions.Timeout("timeout"),
                requests.exceptions.Timeout("timeout"),
                requests.exceptions.Timeout("timeout"),
            ]

            with pytest.raises(RetryError):
                _ = collector._fetch_with_retry(
                    "https://hacker-news.firebaseio.com/v0/topstories.json"
                )

            assert mock_get.call_count == 3

    def test_connection_error_retry(self) -> None:
        collector = HackerNewsCollector()
        with patch("collectors.hackernews_collector.requests.get") as mock_get:
            mock_get.side_effect = [
                requests.exceptions.ConnectionError("connection error"),
                _mock_json_response([1]),
            ]

            result = collector._fetch_with_retry(
                "https://hacker-news.firebaseio.com/v0/topstories.json"
            )

            assert isinstance(result, list)
            assert result == [1]
            assert mock_get.call_count == 2


class TestStackExchangeCollectorRetry:
    def test_retry_on_timeout(self) -> None:
        collector = StackExchangeCollector(api_key="test")
        with patch("collectors.stackexchange_collector.requests.get") as mock_get:
            mock_get.side_effect = [
                requests.exceptions.Timeout("timeout"),
                requests.exceptions.Timeout("timeout"),
                _mock_json_response({"items": [{"question_id": 1, "title": "Q1"}]}),
            ]

            result = collector._fetch_with_retry("https://api.stackexchange.com/2.3/questions")

            assert isinstance(result, dict)
            assert "items" in result
            assert mock_get.call_count == 3

    def test_retry_on_5xx(self) -> None:
        collector = StackExchangeCollector(api_key="test")
        with patch("collectors.stackexchange_collector.requests.get") as mock_get:
            mock_get.side_effect = [
                _http_500_error(),
                _http_500_error(),
                _mock_json_response({"items": [{"question_id": 1, "title": "Q1"}]}),
            ]

            result = collector._fetch_with_retry("https://api.stackexchange.com/2.3/questions")

            assert isinstance(result, dict)
            assert result["items"][0]["question_id"] == 1
            assert mock_get.call_count == 3

    def test_max_retries_exceeded(self) -> None:
        collector = StackExchangeCollector(api_key="test")
        with patch("collectors.stackexchange_collector.requests.get") as mock_get:
            mock_get.side_effect = [
                requests.exceptions.Timeout("timeout"),
                requests.exceptions.Timeout("timeout"),
                requests.exceptions.Timeout("timeout"),
            ]

            with pytest.raises(RetryError):
                _ = collector._fetch_with_retry("https://api.stackexchange.com/2.3/questions")

            assert mock_get.call_count == 3

    def test_connection_error_retry(self) -> None:
        collector = StackExchangeCollector(api_key="test")
        with patch("collectors.stackexchange_collector.requests.get") as mock_get:
            mock_get.side_effect = [
                requests.exceptions.ConnectionError("connection error"),
                _mock_json_response({"items": []}),
            ]

            result = collector._fetch_with_retry("https://api.stackexchange.com/2.3/questions")

            assert isinstance(result, dict)
            assert result["items"] == []
            assert mock_get.call_count == 2

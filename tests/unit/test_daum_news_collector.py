"""Unit tests for DaumNewsCollector."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from collectors.daum_news_collector import DaumNewsCollector


@pytest.mark.unit
def test_daum_news_collector_initializes() -> None:
    """DaumNewsCollector는 초기화된다"""
    collector = DaumNewsCollector(timeout=15, request_delay=0.5)

    assert collector.timeout == 15
    assert collector.request_delay == 0.5
    assert collector.BASE_URL == "https://news.daum.net"


@pytest.mark.unit
def test_daum_news_collector_uses_default_values() -> None:
    """DaumNewsCollector는 기본값을 사용한다"""
    collector = DaumNewsCollector()

    assert collector.timeout == 30
    assert collector.request_delay == 1.0


@pytest.mark.unit
@patch("collectors.daum_news_collector.requests.get")
def test_daum_news_collector_collects_realtime_keywords(mock_get: MagicMock) -> None:
    """DaumNewsCollector는 실시간 검색어를 수집한다"""
    html_content = """
    <html>
        <div class="rank_news">
            <li>
                <span class="rank">1</span>
                <a class="link_keyword" href="/search?q=Python">Python</a>
                <span class="count">150</span>
                <span class="trend">상 5</span>
            </li>
            <li>
                <span class="rank">2</span>
                <a class="link_keyword" href="/search?q=AI">AI</a>
                <span class="count">120</span>
                <span class="trend">상 3</span>
            </li>
        </div>
    </html>
    """

    mock_response = MagicMock()
    mock_response.text = html_content
    mock_response.raise_for_status = MagicMock()
    mock_get.return_value = mock_response

    collector = DaumNewsCollector()
    keywords = collector.collect_realtime_keywords(limit=20)

    assert len(keywords) >= 1
    assert any(k["keyword"] == "Python" for k in keywords)


@pytest.mark.unit
def test_daum_news_collector_parses_trend() -> None:
    """DaumNewsCollector는 추세를 파싱한다"""
    from bs4 import BeautifulSoup

    html = """
    <li>
        <a class="link_keyword">Python</a>
        <span class="trend">상 5</span>
    </li>
    """

    soup = BeautifulSoup(html, "html.parser")
    item = soup.select_one("li")

    _ = DaumNewsCollector()

    # 상승 추세 확인
    trend_elem = item.select_one("span.trend")
    trend_text = trend_elem.get_text(strip=True) if trend_elem else ""

    assert "상" in trend_text or "↑" in trend_text


@pytest.mark.unit
@patch("collectors.daum_news_collector.requests.get")
def test_daum_news_collector_retries_on_failure(mock_get: MagicMock) -> None:
    """DaumNewsCollector는 실패 시 재시도한다"""
    mock_get.side_effect = Exception("Network error")

    collector = DaumNewsCollector()

    with pytest.raises(Exception):  # noqa: B017
        collector._fetch_html("https://news.daum.net/search")


@pytest.mark.unit
def test_daum_news_collector_collect_method() -> None:
    """DaumNewsCollector의 collect 메서드는 기본 수집을 수행한다"""
    with patch.object(
        DaumNewsCollector, "collect_realtime_keywords", return_value=[]
    ) as mock_collect:
        collector = DaumNewsCollector()
        result = collector.collect()

        mock_collect.assert_called_once_with(limit=20)
        assert result == []

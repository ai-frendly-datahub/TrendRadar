"""Playwright Browser Collector for JS-heavy trend sources.

Playwright를 사용하여 JavaScript 렌더링이 필요한 웹사이트에서
트렌드/뉴스 콘텐츠를 수집합니다. 한국 사이트 EUC-KR 인코딩,
쿠키 배너 닫기, Naver iframe 처리 등을 지원합니다.
"""

from __future__ import annotations

import importlib
import logging
from datetime import UTC, datetime
from typing import Any

from trendradar.models import ContentItem

logger = logging.getLogger(__name__)


def _check_playwright_available() -> bool:
    """Playwright 설치 여부를 확인합니다."""
    try:
        importlib.import_module("playwright.sync_api")
        return True
    except ImportError:
        return False


class BrowserCollector:
    """JS가 필요한 웹사이트에서 트렌드 콘텐츠를 수집합니다.

    radar_core.browser_collector를 활용하여 Playwright 기반의
    브라우저 렌더링 수집을 수행합니다. 수집 결과는 ContentItem
    리스트로 반환됩니다.

    Attributes:
        timeout_ms: 페이지 로드 타임아웃 (밀리초)
        rate_limit: 요청 간 최소 대기 시간 (초)
    """

    def __init__(
        self,
        timeout_ms: int = 20_000,
        rate_limit: float = 3.0,
    ) -> None:
        """
        Args:
            timeout_ms: Playwright 페이지 로드 타임아웃 (밀리초, 기본 20초)
            rate_limit: 소스 간 최소 대기 시간 (초, 기본 3초 — 한국 사이트 예절)
        """
        self.timeout_ms = timeout_ms
        self.rate_limit = rate_limit
        self._playwright_available = _check_playwright_available()

    def collect(
        self,
        sources: list[dict[str, Any]] | None = None,
        *,
        limit: int = 30,
    ) -> list[ContentItem]:
        """Playwright를 사용하여 JS 렌더링 페이지에서 콘텐츠를 수집합니다.

        Args:
            sources: 수집 대상 소스 목록. 각 소스는 dict로:
                - name (str): 소스 식별 이름
                - type (str): "browser" | "js" | "web"
                - url (str): 수집 URL
                - config (dict, optional): Playwright 설정
                    - wait_for (str): CSS 선택자 (페이지 로드 대기)
                    - timeout (int): 개별 타임아웃 (ms)
                    - title_selector (str): 제목 선택자
                    - content_selector (str): 본문 선택자
                    - link_selector (str): 링크 선택자
            limit: 최대 수집 아이템 수 (기본 30)

        Returns:
            수집된 ContentItem 리스트. Playwright 미설치 시 빈 리스트.
        """
        if not self._playwright_available:
            logger.warning(
                "Playwright not installed, skipping browser collection. "
                "Install with: pip install 'radar-core[browser]'"
            )
            return []

        target_sources = sources or []
        if not target_sources:
            logger.debug("No browser sources configured, skipping")
            return []

        try:
            browser_module = importlib.import_module("radar_core.browser_collector")
            collect_fn = getattr(browser_module, "collect_browser_sources")
        except (ImportError, AttributeError) as exc:
            logger.error("Failed to import radar_core.browser_collector: %s", exc)
            return []

        try:
            articles, errors = collect_fn(
                target_sources,
                category="trend",
                timeout=self.timeout_ms,
            )
        except Exception as exc:
            logger.error("Browser collection failed: %s", exc)
            return []

        for err in errors:
            logger.warning("Browser source error: %s", err)

        now = datetime.now(UTC)
        items: list[ContentItem] = []

        for article in articles[:limit]:
            if not article.link:
                continue

            items.append(
                ContentItem(
                    title=article.title,
                    url=article.link,
                    source="browser",
                    author="browser",
                    score=1.0,
                    metadata={
                        "collected_at": now.isoformat(),
                        "summary": getattr(article, "summary", ""),
                        "original_source": getattr(article, "source", "browser"),
                        "category": getattr(article, "category", "trend"),
                    },
                )
            )

        logger.info("Browser collector: %d items from %d sources", len(items), len(target_sources))
        return items

    def collect_from_urls(
        self,
        urls: list[str],
        *,
        wait_for: str = "body",
        link_selector: str = "a[href]",
        limit: int = 30,
    ) -> list[ContentItem]:
        """단축 메서드: URL 목록에서 간단하게 수집합니다.

        Args:
            urls: 수집할 URL 목록
            wait_for: 페이지 로드 대기 CSS 선택자
            link_selector: 링크 추출 선택자
            limit: 최대 수집 아이템 수

        Returns:
            수집된 ContentItem 리스트
        """
        sources = [
            {
                "name": f"browser_{idx}",
                "type": "browser",
                "url": url,
                "config": {
                    "timeout": self.timeout_ms,
                    "wait_for": wait_for,
                    "link_selector": link_selector,
                },
            }
            for idx, url in enumerate(urls)
        ]
        return self.collect(sources, limit=limit)

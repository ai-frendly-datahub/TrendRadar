from __future__ import annotations

import logging
import os
import threading
import time
from abc import ABC, abstractmethod
from typing import Any
from urllib.parse import urlparse

import requests
from pybreaker import CircuitBreakerError
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from resilience import SourceCircuitBreakerManager


logger = logging.getLogger(__name__)
_DEFAULT_HEALTH_DB_PATH = "data/radar_data.duckdb"


def _load_adaptive_controls() -> tuple[type[Any], type[Any]]:
    module = __import__("radar_core", fromlist=["AdaptiveThrottler", "CrawlHealthStore"])
    return module.AdaptiveThrottler, module.CrawlHealthStore


_patch_lock = threading.Lock()
_patched = False
_original_session_request = requests.sessions.Session.request
_global_breaker_manager = SourceCircuitBreakerManager()


class BaseCollector(ABC):
    def __init__(self, source_name: str, timeout: float = 30.0, rate_limit: float = 1.0) -> None:
        self.source_name = source_name
        self.timeout = timeout
        self.rate_limit = rate_limit
        self._last_request: float = 0.0
        self._lock: threading.Lock = threading.Lock()
        self.breaker_manager = SourceCircuitBreakerManager()
        self._session = self._create_session()
        throttler_cls, health_store_cls = _load_adaptive_controls()
        self._throttler = throttler_cls(min_delay=max(0.001, float(rate_limit)))
        self._health_store = health_store_cls(
            os.environ.get("RADAR_CRAWL_HEALTH_DB_PATH", _DEFAULT_HEALTH_DB_PATH)
        )

    def _create_session(self) -> requests.Session:
        """Create a session with retry logic for transient errors."""
        session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[408, 429, 500, 502, 503, 504, 522, 524],
            allowed_methods=frozenset(["GET", "POST"]),
            raise_on_status=False,
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        return session

    def _apply_rate_limit(self) -> None:
        """Apply rate limiting between requests."""
        with self._lock:
            elapsed = time.monotonic() - self._last_request
            if elapsed < self.rate_limit:
                time.sleep(self.rate_limit - elapsed)
            self._last_request = time.monotonic()

    def _fetch_with_retry(self, url: str) -> requests.Response:
        max_attempts = 3
        source_name = self._resolve_source_name()
        retryable_errors = (
            requests.exceptions.Timeout,
            requests.exceptions.ConnectionError,
            requests.exceptions.HTTPError,
        )

        for attempt in range(max_attempts):
            self._apply_rate_limit()
            self._throttler.acquire(source_name)

            try:
                response = self._session.get(url, timeout=self.timeout)
                if response.status_code in (408, 429, 500, 502, 503, 504, 522, 524):
                    logger.warning(
                        "Retryable HTTP status %s for %s, will retry",
                        response.status_code,
                        url,
                    )
                    response.raise_for_status()
                response.raise_for_status()

                self._throttler.record_success(source_name)
                delay = self._throttler.get_current_delay(source_name)
                self._health_store.record_success(source_name, delay)
                return response
            except retryable_errors as exc:
                retry_after: int | str | None = None
                if isinstance(exc, requests.exceptions.HTTPError):
                    response = exc.response
                    if response is not None and response.status_code == 429:
                        retry_after = _parse_retry_after(response.headers.get("Retry-After"))

                self._throttler.record_failure(source_name, retry_after=retry_after)
                delay = self._throttler.get_current_delay(source_name)
                self._health_store.record_failure(source_name, str(exc), delay)

                if attempt == max_attempts - 1:
                    raise

        raise RuntimeError("Retry loop exited unexpectedly")

    def _resolve_source_name(self) -> str:
        return self.source_name

    def _fetch(self, url: str) -> requests.Response:
        source_name = self._resolve_source_name()
        breaker = self.breaker_manager.get_breaker(source_name)

        return breaker.call(
            lambda source=source_name: self._fetch_with_retry(url),
            source=source_name,
        )

    def _fetch_html(self, url: str) -> str | None:
        source_name = self._resolve_source_name()
        breaker = self.breaker_manager.get_breaker(source_name)

        def _fetch_html_impl() -> str | None:
            response = self._fetch_with_retry(url)
            response.encoding = response.apparent_encoding or "utf-8"
            return response.text

        return breaker.call(
            lambda source=source_name: _fetch_html_impl(),
            source=source_name,
        )

    def _fetch_json(self, url: str) -> dict[str, Any] | list[Any]:
        source_name = self._resolve_source_name()
        breaker = self.breaker_manager.get_breaker(source_name)

        def _fetch_json_impl() -> dict[str, Any] | list[Any]:
            response = self._fetch_with_retry(url)
            return response.json()

        return breaker.call(
            lambda source=source_name: _fetch_json_impl(),
            source=source_name,
        )

    def __del__(self) -> None:
        self._session.close()
        self._health_store.close()

    @abstractmethod
    def collect(self) -> list[Any]:
        pass


def _session_request_with_circuit_breaker(
    self: requests.sessions.Session,
    method: str | bytes,
    url: str | bytes,
    *args: Any,
    **kwargs: Any,
) -> requests.Response:
    resolved_url = url.decode("utf-8", errors="ignore") if isinstance(url, bytes) else url
    source_name = urlparse(resolved_url).netloc or "unknown_source"
    breaker = _global_breaker_manager.get_breaker(source_name)

    try:
        return breaker.call(_original_session_request, self, method, url, *args, **kwargs)
    except CircuitBreakerError as exc:
        raise requests.exceptions.RequestException(
            f"Circuit breaker open for source '{source_name}'"
        ) from exc


def install_requests_circuit_breaker() -> None:
    global _patched
    if _patched:
        return

    with _patch_lock:
        if _patched:
            return

        requests.sessions.Session.request = _session_request_with_circuit_breaker
        _patched = True


def _parse_retry_after(value: str | None) -> int | str | None:
    if value is None:
        return None

    stripped = value.strip()
    if not stripped:
        return None

    if stripped.isdigit():
        return int(stripped)

    return stripped

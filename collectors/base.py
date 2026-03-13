from __future__ import annotations

import logging
import threading
import time
from abc import ABC, abstractmethod
from typing import Any
from urllib.parse import urlparse

import requests
from pybreaker import CircuitBreakerError
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from resilience import SourceCircuitBreakerManager


logger = logging.getLogger(__name__)


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

    def _apply_rate_limit(self) -> None:
        """Apply rate limiting between requests."""
        with self._lock:
            elapsed = time.monotonic() - self._last_request
            if elapsed < self.rate_limit:
                time.sleep(self.rate_limit - elapsed)
            self._last_request = time.monotonic()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type(
            (requests.exceptions.Timeout, requests.exceptions.ConnectionError)
        ),
        reraise=True,
    )
    def _fetch(self, url: str) -> requests.Response:
        self._apply_rate_limit()
        breaker = self.breaker_manager.get_breaker(self.source_name)

        def _fetch_impl() -> requests.Response:
            try:
                response = requests.get(url, timeout=self.timeout)
                response.raise_for_status()
                return response
            except requests.exceptions.RequestException as exc:
                logger.error(f"Fetch error for {self.source_name} at {url}: {exc}")
                raise

        return breaker.call(
            lambda source=self.source_name: _fetch_impl(),
            source=self.source_name,
        )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type(
            (requests.exceptions.Timeout, requests.exceptions.ConnectionError)
        ),
        reraise=True,
    )
    def _fetch_html(self, url: str) -> str | None:
        self._apply_rate_limit()
        breaker = self.breaker_manager.get_breaker(self.source_name)

        def _fetch_html_impl() -> str | None:
            try:
                response = requests.get(url, timeout=self.timeout)
                response.raise_for_status()
                response.encoding = response.apparent_encoding or "utf-8"
                return response.text
            except requests.exceptions.RequestException as exc:
                logger.error(f"HTML fetch error for {self.source_name} at {url}: {exc}")
                raise

        return breaker.call(
            lambda source=self.source_name: _fetch_html_impl(),
            source=self.source_name,
        )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type(
            (requests.exceptions.Timeout, requests.exceptions.ConnectionError)
        ),
        reraise=True,
    )
    def _fetch_json(self, url: str) -> dict[str, Any] | list[Any]:
        self._apply_rate_limit()
        breaker = self.breaker_manager.get_breaker(self.source_name)

        def _fetch_json_impl() -> dict[str, Any] | list[Any]:
            try:
                response = requests.get(url, timeout=self.timeout)
                response.raise_for_status()
                return response.json()
            except requests.exceptions.RequestException as exc:
                logger.error(f"JSON fetch error for {self.source_name} at {url}: {exc}")
                raise
            except ValueError as exc:
                logger.error(f"JSON decode error for {self.source_name} at {url}: {exc}")
                raise

        return breaker.call(
            lambda source=self.source_name: _fetch_json_impl(),
            source=self.source_name,
        )

    @abstractmethod
    def collect(self) -> list[Any]:
        pass


def _session_request_with_circuit_breaker(
    session: requests.sessions.Session,
    method: str,
    url: str,
    *args: Any,
    **kwargs: Any,
) -> requests.Response:
    source_name = urlparse(url).netloc or "unknown_source"
    breaker = _global_breaker_manager.get_breaker(source_name)

    try:
        return breaker.call(_original_session_request, session, method, url, *args, **kwargs)
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

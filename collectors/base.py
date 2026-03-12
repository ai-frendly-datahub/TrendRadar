from __future__ import annotations

from abc import ABC, abstractmethod
import os
import threading
import time
from typing import Optional, Any
from urllib.parse import urlparse

import requests
from pybreaker import CircuitBreakerError
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from resilience import SourceCircuitBreakerManager


_patch_lock = threading.Lock()
_patched = False
_http_patched = False
_original_session_request = requests.sessions.Session.request
_original_get = requests.get
_original_post = requests.post
_global_breaker_manager = SourceCircuitBreakerManager()
_rate_limiters: dict[str, "RateLimiter"] = {}
_shared_session: requests.Session | None = None


class BaseCollector(ABC):
    def __init__(self, source_name: str, timeout: float = 30.0) -> None:
        self.source_name = source_name
        self.timeout = timeout
        self.breaker_manager = SourceCircuitBreakerManager()
        self._session = _create_session()
        self._collector_limiters: dict[str, RateLimiter] = {}

    def _request(self, method: str, url: str, **kwargs: Any) -> requests.Response:
        breaker = self.breaker_manager.get_breaker(self.source_name)
        timeout = kwargs.pop("timeout", self.timeout)
        host = urlparse(url).netloc.lower() or self.source_name
        limiter = self._collector_limiters.setdefault(host, RateLimiter(0.5))

        def _request_impl() -> requests.Response:
            limiter.acquire()
            response = self._session.request(method, url, timeout=timeout, **kwargs)
            response.raise_for_status()
            return response

        return breaker.call(
            lambda source=self.source_name: _request_impl(),
            source=self.source_name,
        )

    def _fetch(self, url: str) -> requests.Response:
        return self._request("GET", url)

    def _fetch_html(self, url: str) -> Optional[str]:
        response = self._request("GET", url)
        response.encoding = response.apparent_encoding or "utf-8"
        return response.text

    def _fetch_json(self, url: str) -> dict[str, Any] | list[Any]:
        response = self._request("GET", url)
        return response.json()

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

        setattr(requests.sessions.Session, "request", _session_request_with_circuit_breaker)
        _patched = True


class RateLimiter:
    def __init__(self, min_interval: float = 0.5):
        self._min_interval = min_interval
        self._last_request = 0.0
        self._lock = threading.Lock()

    def acquire(self) -> None:
        with self._lock:
            now = time.monotonic()
            elapsed = now - self._last_request
            if elapsed < self._min_interval:
                time.sleep(self._min_interval - elapsed)
            self._last_request = time.monotonic()


def resolve_max_workers(max_workers: Optional[int] = None) -> int:
    if max_workers is None:
        raw_value = os.environ.get("RADAR_MAX_WORKERS", "5")
        try:
            parsed = int(raw_value)
        except ValueError:
            parsed = 5
    else:
        parsed = max_workers

    return max(1, min(parsed, 10))


def _create_session() -> requests.Session:
    session = requests.Session()
    retry_strategy = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=frozenset(["GET", "POST"]),
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session


def _get_shared_session() -> requests.Session:
    global _shared_session
    if _shared_session is None:
        _shared_session = _create_session()
    return _shared_session


def _rate_limited_request(method: str, url: str, **kwargs: Any) -> requests.Response:
    timeout = kwargs.pop("timeout", 30)
    host = urlparse(url).netloc.lower() or "unknown_source"
    limiter = _rate_limiters.setdefault(host, RateLimiter(0.5))
    limiter.acquire()
    session = _get_shared_session()
    response = session.request(method, url, timeout=timeout, **kwargs)
    return response


def install_requests_http_controls() -> None:
    global _http_patched
    if _http_patched:
        return

    with _patch_lock:
        if _http_patched:
            return

        def _patched_get(url: str, *args: Any, **kwargs: Any) -> requests.Response:
            if args:
                kwargs["params"] = args[0]
            return _rate_limited_request("GET", url, **kwargs)

        def _patched_post(url: str, *args: Any, **kwargs: Any) -> requests.Response:
            if args:
                kwargs["data"] = args[0]
            return _rate_limited_request("POST", url, **kwargs)

        requests.get = _patched_get
        requests.post = _patched_post
        _http_patched = True

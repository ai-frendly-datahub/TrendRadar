"""트렌드 데이터 수집 모듈."""

from .base import install_requests_circuit_breaker, install_requests_http_controls


install_requests_circuit_breaker()
install_requests_http_controls()

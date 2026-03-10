# Canonical Notifier implementation for AI-Friendly DataHub
# Synced from: Radar-Template/radar/notifier.py
# DO NOT MODIFY core classes (Notifier, NotificationPayload, EmailNotifier, WebhookNotifier, CompositeNotifier)
# Domain-specific detection functions (detect_trend_notifications) preserved below

from __future__ import annotations

import smtplib
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from email.mime.text import MIMEText
from pathlib import Path
from typing import Optional, Any, Protocol

import duckdb
import requests
import structlog

logger = structlog.get_logger(__name__)


@dataclass
class NotificationPayload:
    """Payload for notification delivery."""

    category_name: str
    sources_count: int
    collected_count: int
    matched_count: int
    errors_count: int
    timestamp: datetime
    report_url: Optional[str] = None

    def to_dict(self) -> dict[str, object]:
        """Convert payload to dictionary for JSON serialization."""
        return {
            "category_name": self.category_name,
            "sources_count": self.sources_count,
            "collected_count": self.collected_count,
            "matched_count": self.matched_count,
            "errors_count": self.errors_count,
            "timestamp": self.timestamp.isoformat(),
            "report_url": self.report_url,
        }


class Notifier(Protocol):
    """Protocol for notification delivery."""

    def send(self, payload: NotificationPayload) -> bool:
        """Send notification. Return True if successful, False otherwise."""
        ...


class EmailNotifier:
    """Send notifications via email using SMTP."""

    def __init__(
        self,
        smtp_host: str,
        smtp_port: int,
        smtp_user: str,
        smtp_password: str,
        from_addr: str,
        to_addrs: list[str],
    ) -> None:
        """Initialize email notifier.

        Args:
            smtp_host: SMTP server hostname
            smtp_port: SMTP server port
            smtp_user: SMTP username
            smtp_password: SMTP password
            from_addr: Sender email address
            to_addrs: List of recipient email addresses
        """
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.smtp_user = smtp_user
        self.smtp_password = smtp_password
        self.from_addr = from_addr
        self.to_addrs = to_addrs

    def send(self, payload: NotificationPayload) -> bool:
        """Send email notification.

        Args:
            payload: Notification payload

        Returns:
            True if successful, False otherwise
        """
        try:
            subject = f"Radar Pipeline Complete: {payload.category_name}"
            body = self._build_email_body(payload)

            msg = MIMEText(body, "plain")
            msg["Subject"] = subject
            msg["From"] = self.from_addr
            msg["To"] = ", ".join(self.to_addrs)

            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)

            logger.info("email_notification_sent", category=payload.category_name)
            return True
        except Exception as e:
            logger.error(
                "email_notification_failed",
                category=payload.category_name,
                error=str(e),
            )
            return False

    def _build_email_body(self, payload: NotificationPayload) -> str:
        """Build email body from payload."""
        lines = [
            f"Radar Pipeline Completion Report",
            f"================================",
            f"",
            f"Category: {payload.category_name}",
            f"Timestamp: {payload.timestamp.isoformat()}",
            f"",
            f"Statistics:",
            f"  Sources: {payload.sources_count}",
            f"  Collected: {payload.collected_count}",
            f"  Matched: {payload.matched_count}",
            f"  Errors: {payload.errors_count}",
        ]
        if payload.report_url:
            lines.append(f"")
            lines.append(f"Report: {payload.report_url}")
        return "\n".join(lines)


class WebhookNotifier:
    """Send notifications via HTTP webhook."""

    def __init__(
        self,
        url: str,
        method: str = "POST",
        headers: dict[str, str] | None = None,
    ) -> None:
        """Initialize webhook notifier.

        Args:
            url: Webhook URL
            method: HTTP method (POST or GET)
            headers: Optional HTTP headers
        """
        self.url = url
        self.method = method.upper()
        self.headers = headers or {}

    def send(self, payload: NotificationPayload) -> bool:
        """Send webhook notification.

        Args:
            payload: Notification payload

        Returns:
            True if successful, False otherwise
        """
        try:
            if self.method == "POST":
                response = requests.post(
                    self.url,
                    json=payload.to_dict(),
                    headers=self.headers,
                    timeout=10,
                )
            elif self.method == "GET":
                response = requests.get(
                    self.url,
                    headers=self.headers,
                    timeout=10,
                )
            else:
                logger.error(
                    "webhook_invalid_method",
                    method=self.method,
                    url=self.url,
                )
                return False

            if response.status_code >= 400:
                logger.error(
                    "webhook_notification_failed",
                    url=self.url,
                    status_code=response.status_code,
                )
                return False

            logger.info("webhook_notification_sent", url=self.url)
            return True
        except Exception as e:
            logger.error(
                "webhook_notification_failed",
                url=self.url,
                error=str(e),
            )
            return False


class CompositeNotifier:
    """Send notifications to multiple notifiers."""

    def __init__(self, notifiers: list[object]) -> None:
        """Initialize composite notifier.

        Args:
            notifiers: List of notifiers to send to
        """
        self.notifiers = notifiers

    def send(self, payload: NotificationPayload) -> bool:
        """Send notification to all notifiers.

        Args:
            payload: Notification payload

        Returns:
            True if all notifiers succeeded, False if any failed
        """
        if not self.notifiers:
            return True

        results = []
        for notifier in self.notifiers:
            try:
                result = getattr(notifier, "send")(payload)
                results.append(result)
            except Exception:
                results.append(False)
        return all(results) if results else True


# Domain-specific configuration and event classes (preserved from original)
@dataclass
class NotificationConfig:
    enabled: bool
    channels: list[str]
    email_settings: dict[str, Any] = field(default_factory=dict)
    webhook_url: str = ""
    telegram_config: dict[str, str] = field(default_factory=dict)
    rules: dict[str, Any] = field(default_factory=dict)


@dataclass
class NotificationEvent:
    title: str
    message: str
    priority: str
    event_type: str
    metadata: dict[str, Any] = field(default_factory=dict)


def detect_trend_notifications(db_path: Path, rules: dict[str, Any]) -> list[NotificationEvent]:
    """Detect trend-specific notification events (spike detection, cross-channel spread).

    Args:
        db_path: Path to DuckDB database with trend_points table
        rules: Notification rules from config/notifications.yaml

    Returns:
        List of notification events to send
    """
    if not db_path.exists():
        return []

    spike_multiplier = float(rules.get("spike_multiplier", 2.0))
    spread_min_channels = int(rules.get("spread_min_channels", 3))

    with duckdb.connect(str(db_path)) as conn:
        latest_row = conn.execute("SELECT CAST(MAX(ts) AS DATE) FROM trend_points").fetchone()
        if not latest_row or latest_row[0] is None:
            return []
        latest_date = latest_row[0]

        spikes = conn.execute(
            """
            WITH latest AS (
                SELECT source, keyword, AVG(value_normalized) AS value_latest
                FROM trend_points
                WHERE CAST(ts AS DATE) = ?
                GROUP BY source, keyword
            ),
            prev AS (
                SELECT source, keyword, AVG(value_normalized) AS value_prev
                FROM trend_points
                WHERE CAST(ts AS DATE) = ?::DATE - INTERVAL 1 DAY
                GROUP BY source, keyword
            )
            SELECT latest.source, latest.keyword, latest.value_latest, prev.value_prev
            FROM latest
            JOIN prev ON latest.source = prev.source AND latest.keyword = prev.keyword
            WHERE prev.value_prev > 0 AND latest.value_latest >= prev.value_prev * ?
            """,
            [latest_date, latest_date, spike_multiplier],
        ).fetchall()

        new_keywords = conn.execute(
            """
            SELECT latest.source, latest.keyword, latest.value_latest
            FROM (
                SELECT source, keyword, AVG(value_normalized) AS value_latest
                FROM trend_points
                WHERE CAST(ts AS DATE) = ?
                GROUP BY source, keyword
            ) latest
            WHERE NOT EXISTS (
                SELECT 1
                FROM trend_points older
                WHERE older.source = latest.source
                  AND older.keyword = latest.keyword
                  AND CAST(older.ts AS DATE) < ?
            )
            """,
            [latest_date, latest_date],
        ).fetchall()

        spreads = conn.execute(
            """
            SELECT keyword, COUNT(DISTINCT source) AS channel_count
            FROM trend_points
            WHERE CAST(ts AS DATE) = ?
            GROUP BY keyword
            HAVING COUNT(DISTINCT source) >= ?
            """,
            [latest_date, spread_min_channels],
        ).fetchall()

    events: list[NotificationEvent] = []
    for source, keyword, latest_value, previous_value in spikes:
        ratio = float(latest_value) / float(previous_value)
        events.append(
            NotificationEvent(
                title=f"[TrendRadar] 스파이크 감지: {keyword}",
                message=(
                    f"채널: {source}\n"
                    f"전일 대비 {ratio:.2f}배 상승 ({float(previous_value):.1f} -> {float(latest_value):.1f})"
                ),
                priority="high",
                event_type="spike",
                metadata={"source": source, "keyword": keyword, "ratio": ratio},
            )
        )

    for source, keyword, latest_value in new_keywords:
        events.append(
            NotificationEvent(
                title=f"[TrendRadar] 신규 트렌드 등장: {keyword}",
                message=f"채널: {source}\n지표: {float(latest_value):.1f}",
                priority="normal",
                event_type="new_trend",
                metadata={"source": source, "keyword": keyword},
            )
        )

    for keyword, channel_count in spreads:
        events.append(
            NotificationEvent(
                title=f"[TrendRadar] 채널 확산 감지: {keyword}",
                message=f"동시 등장 채널 수: {int(channel_count)}",
                priority="high" if int(channel_count) >= spread_min_channels + 1 else "normal",
                event_type="cross_channel_spread",
                metadata={"keyword": keyword, "channels": int(channel_count)},
            )
        )

    return events


class PipelineNotifier:
    """Concrete notifier that wraps NotificationConfig and delegates to channel notifiers."""

    def __init__(self, config: "NotificationConfig") -> None:
        self.config = config
        self._notifiers: list[object] = []
        if not config.enabled:
            return
        if "email" in config.channels and config.email_settings:
            es = config.email_settings
            self._notifiers.append(
                EmailNotifier(
                    smtp_host=es.get("smtp_host", ""),
                    smtp_port=int(es.get("smtp_port", 587)),
                    smtp_user=es.get("smtp_user", ""),
                    smtp_password=es.get("smtp_password", ""),
                    from_addr=es.get("from_addr", ""),
                    to_addrs=es.get("to_addrs", []),
                )
            )
        if "webhook" in config.channels and config.webhook_url:
            self._notifiers.append(WebhookNotifier(url=config.webhook_url))

    def send(
        self,
        *,
        title: str,
        message: str,
        priority: str = "normal",
        metadata: Optional[dict[str, Any]] = None,
    ) -> bool:
        if not self.config.enabled or not self._notifiers:
            return True
        payload = NotificationPayload(
            category_name=title,
            sources_count=0,
            collected_count=0,
            matched_count=0,
            errors_count=0,
            timestamp=datetime.now(),
        )
        composite = CompositeNotifier(self._notifiers)
        return composite.send(payload)


def create_notifier(config: "NotificationConfig") -> "PipelineNotifier":
    """Factory function to create a PipelineNotifier from NotificationConfig."""
    return PipelineNotifier(config)

from __future__ import annotations

import smtplib
from dataclasses import dataclass, field
from email.mime.text import MIMEText
from pathlib import Path
from typing import Any

import duckdb
import requests


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


class Notifier:
    def __init__(self, config: NotificationConfig):
        self.config = config

    def send(
        self,
        title: str,
        message: str,
        priority: str = "normal",
        metadata: dict[str, Any] | None = None,
    ) -> None:
        if not self.config.enabled:
            return

        payload = {
            "title": title,
            "message": message,
            "priority": priority,
            "metadata": metadata or {},
        }
        channels = {channel.strip().lower() for channel in self.config.channels}

        if "email" in channels:
            self._send_email(payload)
        if "webhook" in channels:
            self._send_webhook(payload)
        if "telegram" in channels:
            self._send_telegram(payload)

    def _send_email(self, payload: dict[str, Any]) -> None:
        settings = self.config.email_settings
        smtp_host = str(settings.get("smtp_host", "")).strip()
        smtp_port = int(settings.get("smtp_port", 587) or 587)
        from_address = str(settings.get("from_address", "")).strip()
        to_addresses = settings.get("to_addresses", [])
        username = str(settings.get("username", "")).strip()
        password = str(settings.get("password", "")).strip()

        if (
            not smtp_host
            or not from_address
            or not isinstance(to_addresses, list)
            or not to_addresses
        ):
            return

        msg = MIMEText(str(payload["message"]), "plain", "utf-8")
        msg["Subject"] = str(payload["title"])
        msg["From"] = from_address
        msg["To"] = ", ".join(str(addr) for addr in to_addresses)

        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            if username and password:
                server.login(username, password)
            server.send_message(msg)

    def _send_webhook(self, payload: dict[str, Any]) -> None:
        if not self.config.webhook_url:
            return
        requests.post(self.config.webhook_url, json=payload, timeout=10)

    def _send_telegram(self, payload: dict[str, Any]) -> None:
        token = self.config.telegram_config.get("bot_token", "")
        chat_id = self.config.telegram_config.get("chat_id", "")
        if not token or not chat_id:
            return

        text = f"[{payload['priority'].upper()}] {payload['title']}\n{payload['message']}"
        requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={"chat_id": chat_id, "text": text},
            timeout=10,
        )


def detect_trend_notifications(db_path: Path, rules: dict[str, Any]) -> list[NotificationEvent]:
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

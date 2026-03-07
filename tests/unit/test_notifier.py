from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch

import duckdb
import pytest

from config_loader import load_notification_config
from notifier import NotificationConfig, Notifier, detect_trend_notifications


@pytest.mark.unit
def test_notifier_sends_email_channel() -> None:
    notifier = Notifier(
        NotificationConfig(
            enabled=True,
            channels=["email"],
            email_settings={
                "smtp_host": "smtp.example.com",
                "smtp_port": 587,
                "from_address": "from@example.com",
                "to_addresses": ["to@example.com"],
            },
        )
    )

    with patch("notifier.smtplib.SMTP") as mock_smtp:
        notifier.send("title", "message", "normal")

    mock_smtp.assert_called_once()


@pytest.mark.unit
def test_notifier_sends_webhook_channel() -> None:
    notifier = Notifier(
        NotificationConfig(enabled=True, channels=["webhook"], webhook_url="https://hooks.example")
    )

    with patch("notifier.requests.post") as mock_post:
        notifier.send("title", "message", "normal")

    mock_post.assert_called_once()


@pytest.mark.unit
def test_notifier_sends_telegram_channel() -> None:
    notifier = Notifier(
        NotificationConfig(
            enabled=True,
            channels=["telegram"],
            telegram_config={"bot_token": "token", "chat_id": "chat"},
        )
    )

    with patch("notifier.requests.post") as mock_post:
        notifier.send("title", "message", "high")

    mock_post.assert_called_once()


@pytest.mark.unit
def test_load_notification_config_resolves_env(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("WEBHOOK_URL", "https://hooks.example")
    config_file = tmp_path / "notifications.yaml"
    config_file.write_text(
        """
notifications:
  enabled: true
  channels: [webhook]
  webhook_url: "${WEBHOOK_URL}"
  rules:
    spike_multiplier: 2.0
""".strip(),
        encoding="utf-8",
    )

    config = load_notification_config(config_file)
    assert config.enabled is True
    assert config.webhook_url == "https://hooks.example"


@pytest.mark.unit
def test_detect_trend_notifications_detects_priority_and_types(tmp_path: Path) -> None:
    db_path = tmp_path / "trend.duckdb"
    with duckdb.connect(str(db_path)) as conn:
        conn.execute(
            """
            CREATE TABLE trend_points (
                source TEXT,
                keyword TEXT,
                ts TIMESTAMP,
                value_normalized FLOAT,
                meta_json TEXT
            )
            """
        )
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        yesterday = today - timedelta(days=1)

        conn.execute(
            "INSERT INTO trend_points VALUES (?, ?, ?, ?, ?)",
            ["google", "ai", yesterday, 10.0, "{}"],
        )
        conn.execute(
            "INSERT INTO trend_points VALUES (?, ?, ?, ?, ?)",
            ["google", "ai", today, 25.0, "{}"],
        )
        conn.execute(
            "INSERT INTO trend_points VALUES (?, ?, ?, ?, ?)",
            ["naver", "ai", today, 13.0, "{}"],
        )
        conn.execute(
            "INSERT INTO trend_points VALUES (?, ?, ?, ?, ?)",
            ["youtube", "ai", today, 14.0, "{}"],
        )
        conn.execute(
            "INSERT INTO trend_points VALUES (?, ?, ?, ?, ?)",
            ["reddit", "new-keyword", today, 6.0, "{}"],
        )

    events = detect_trend_notifications(
        db_path,
        {"spike_multiplier": 2.0, "spread_min_channels": 3},
    )

    event_types = {event.event_type for event in events}
    assert "spike" in event_types
    assert "new_trend" in event_types
    assert "cross_channel_spread" in event_types
    assert any(event.priority == "high" for event in events)

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from analyzers import spike_detector
from analyzers.spike_detector import SpikeDetector


pytestmark = pytest.mark.unit


def test_spike_detector_accepts_dict_rows_from_trend_store(monkeypatch: pytest.MonkeyPatch) -> None:
    timestamp = datetime(2026, 4, 12, tzinfo=UTC)
    calls = 0

    def fake_query_trend_points(**kwargs: object) -> list[dict[str, object]]:
        nonlocal calls
        calls += 1
        if calls == 1:
            return [
                {
                    "keyword": "ai",
                    "source": "google",
                    "timestamp": timestamp,
                    "value": 42.0,
                    "metadata": {"set_name": "test"},
                }
            ]
        return []

    monkeypatch.setattr(
        spike_detector.trend_store,
        "query_trend_points",
        fake_query_trend_points,
    )

    signals = SpikeDetector(recent_days=7, baseline_days=30).detect_emerging_keywords()

    assert len(signals) == 1
    assert signals[0].keyword == "ai"
    assert signals[0].source == "google"

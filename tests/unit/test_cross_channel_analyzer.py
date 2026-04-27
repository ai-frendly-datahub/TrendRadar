from __future__ import annotations

import pytest

from analyzers.cross_channel_analyzer import CrossChannelAnalyzer


pytestmark = pytest.mark.unit


def test_calculate_keyword_averages_accepts_dict_rows() -> None:
    averages = CrossChannelAnalyzer._calculate_keyword_averages(
        [
            {
                "keyword": "ai",
                "source": "google",
                "timestamp": "2026-04-12T00:00:00+00:00",
                "value": 30.0,
            },
            {
                "keyword": "ai",
                "source": "google",
                "timestamp": "2026-04-13T00:00:00+00:00",
                "value": 60.0,
            },
        ]
    )

    assert averages == {"ai": 45.0}

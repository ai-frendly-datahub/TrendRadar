from __future__ import annotations

from datetime import UTC, date, datetime

from trendradar.quality_report import build_quality_report, write_quality_report


def test_build_quality_report_tracks_pack_version_taxonomy_and_signal_layers() -> None:
    config = {
        "data_quality": {
            "priority": "P1",
            "primary_motion": "attention",
            "signal_layers": {
                "attention": ["naver", "google", "wikipedia"],
                "conversion_proxy": ["naver_shopping"],
                "community": ["reddit", "hackernews"],
            },
            "score_axes": {
                "attention": {"output_field": "attention_score"},
                "conversion_proxy": {"output_field": "conversion_proxy_score"},
            },
            "normalization": {"policy": "normalize to 0-100 by platform"},
            "next_actions": ["visualize attention and conversion separately"],
        },
        "keyword_sets": [
            {
                "name": "Fashion",
                "enabled": True,
                "version": "2026.04",
                "taxonomy": {"vertical": "commerce_fashion", "intent": "conversion_proxy"},
                "keywords": ["패션", "쇼핑"],
                "channels": ["naver", "naver_shopping"],
            },
            {
                "name": "Tech",
                "enabled": True,
                "version": "2026.04",
                "taxonomy": {"vertical": "technology", "intent": "community_attention"},
                "keywords": ["AI"],
                "channels": ["reddit", "hackernews"],
            },
        ],
    }

    report = build_quality_report(
        config,
        generated_at=datetime(2026, 4, 12, tzinfo=UTC),
        target_date=date(2026, 4, 12),
    )

    assert report["repo"] == "TrendRadar"
    assert report["target_date"] == "2026-04-12"
    assert report["summary"]["enabled_pack_count"] == 2
    assert report["summary"]["versioned_pack_coverage"] == 1.0
    assert report["summary"]["taxonomy_coverage"] == 1.0
    assert report["summary"]["attention_pack_coverage"] == 0.5
    assert report["summary"]["conversion_proxy_pack_coverage"] == 0.5
    assert report["summary"]["community_pack_coverage"] == 0.5
    assert report["summary"]["separated_score_axes"] is True
    assert report["summary"]["collected_signal_count"] == 0
    assert report["summary"]["missing_required_components"] == []


def test_build_quality_report_separates_observed_signal_axes() -> None:
    config = {
        "data_quality": {
            "priority": "P1",
            "primary_motion": "attention",
            "signal_layers": {
                "attention": ["google"],
                "conversion_proxy": ["naver_shopping"],
                "community": ["reddit"],
            },
            "score_axes": {
                "attention": {"output_field": "attention_score"},
                "conversion_proxy": {"output_field": "conversion_proxy_score"},
            },
            "normalization": {"policy": "normalize to 0-100 by platform"},
            "event_models": {
                "attention_signal": {
                    "required_fields": [
                        "keyword_set_name",
                        "channel",
                        "raw_value",
                        "normalized_value",
                    ],
                },
                "conversion_proxy_signal": {
                    "required_fields": ["keyword_set_name", "proxy_type", "source"],
                },
                "community_signal": {
                    "required_fields": ["keyword_set_name", "community", "signal_value"],
                },
            },
            "freshness_sla": {
                "attention_signal_days": 1,
                "conversion_proxy_signal_days": 7,
                "community_signal_days": 3,
            },
        },
        "keyword_sets": [
            {
                "name": "Fashion",
                "enabled": True,
                "version": "2026.04",
                "taxonomy": {"vertical": "commerce_fashion", "intent": "conversion_proxy"},
                "keywords": ["fashion"],
                "channels": ["google", "naver_shopping", "reddit"],
            },
        ],
    }
    trend_points = [
        {
            "keyword": "fashion",
            "source": "google",
            "timestamp": datetime(2026, 4, 12, 8, 0, tzinfo=UTC),
            "value": 50.0,
            "metadata": {"set_name": "Fashion"},
        },
        {
            "keyword": "fashion",
            "source": "naver_shopping",
            "timestamp": datetime(2026, 4, 12, 9, 0, tzinfo=UTC),
            "value": 20.0,
            "metadata": {"set_name": "Fashion"},
        },
        {
            "keyword": "fashion",
            "source": "reddit",
            "timestamp": datetime(2026, 4, 11, 9, 0, tzinfo=UTC),
            "value": 5.0,
            "metadata": {"set_name": "Fashion"},
        },
    ]

    report = build_quality_report(
        config,
        generated_at=datetime(2026, 4, 12, tzinfo=UTC),
        target_date=date(2026, 4, 12),
        trend_points=trend_points,
    )

    summary = report["summary"]
    assert summary["collected_signal_count"] == 3
    assert summary["attention_signal_count"] == 1
    assert summary["conversion_proxy_signal_count"] == 1
    assert summary["community_signal_count"] == 1
    assert summary["score_axis_contamination_count"] == 0
    assert summary["signal_required_field_gap_count"] == 0

    events_by_model = {event["event_model"]: event for event in report["events"]}
    attention = events_by_model["attention_signal"]
    conversion = events_by_model["conversion_proxy_signal"]
    community = events_by_model["community_signal"]

    assert attention["attention_score"] == 100.0
    assert attention["conversion_proxy_score"] is None
    assert conversion["conversion_proxy_score"] == 100.0
    assert conversion["attention_score"] is None
    assert conversion["proxy_type"] == "shopping_interest"
    assert community["community_score"] == 100.0
    assert community["community"] == "reddit"
    assert report["daily_review_items"] == []


def test_build_quality_report_flags_missing_conversion_proxy_observation() -> None:
    config = {
        "data_quality": {
            "signal_layers": {
                "attention": ["google"],
                "conversion_proxy": ["naver_shopping"],
                "community": [],
            },
            "score_axes": {
                "attention": {"output_field": "attention_score"},
                "conversion_proxy": {"output_field": "conversion_proxy_score"},
            },
            "normalization": {"policy": "normalize to 0-100 by platform"},
        },
        "keyword_sets": [
            {
                "name": "Fashion",
                "enabled": True,
                "version": "2026.04",
                "taxonomy": {"vertical": "commerce_fashion", "intent": "conversion_proxy"},
                "keywords": ["fashion"],
                "channels": ["google", "naver_shopping"],
            },
        ],
    }

    report = build_quality_report(
        config,
        generated_at=datetime(2026, 4, 12, tzinfo=UTC),
        target_date=date(2026, 4, 12),
        trend_points=[
            {
                "keyword": "fashion",
                "source": "google",
                "timestamp": datetime(2026, 4, 12, tzinfo=UTC),
                "value": 50.0,
                "metadata": {"set_name": "Fashion"},
            },
        ],
    )

    assert report["summary"]["conversion_proxy_signal_count"] == 0
    assert any(
        item["reason"] == "conversion_proxy_no_observed_signal"
        for item in report["daily_review_items"]
    )


def test_write_quality_report_writes_latest_and_dated_paths(tmp_path) -> None:
    report = {
        "target_date": "2026-04-12",
        "summary": {},
    }

    paths = write_quality_report(report, tmp_path, target_date=date(2026, 4, 12))

    assert sorted(paths) == ["dated", "latest"]
    assert (tmp_path / "trend_quality.json").exists()
    assert (tmp_path / "trend_20260412_quality.json").exists()

from __future__ import annotations

from datetime import date

from reporters.html_reporter import generate_daily_report, generate_index_html


def test_generate_daily_report_includes_trend_quality_panel(tmp_path) -> None:
    quality_report = {
        "generated_at": "2026-04-12T00:00:00+00:00",
        "summary": {
            "collected_signal_count": 2,
            "attention_signal_count": 1,
            "conversion_proxy_signal_count": 1,
            "community_signal_count": 0,
            "signal_required_field_gap_count": 0,
            "daily_review_item_count": 1,
        },
        "events": [
            {
                "event_model": "attention_signal",
                "keyword_set_name": "Fashion",
                "channel": "google",
                "keyword": "fashion",
                "score_axis": "attention",
                "normalized_value": 100.0,
            },
            {
                "event_model": "conversion_proxy_signal",
                "keyword_set_name": "Fashion",
                "channel": "naver_shopping",
                "keyword": "fashion",
                "score_axis": "conversion_proxy",
                "normalized_value": 80.0,
            },
        ],
        "daily_review_items": [
            {
                "reason": "conversion_proxy_no_observed_signal",
                "event_model": "conversion_proxy_signal",
                "detail": "example",
            }
        ],
    }

    generate_daily_report(
        target_date=date(2026, 4, 12),
        keyword_sets=[],
        output_dir=tmp_path,
        quality_report=quality_report,
    )

    html = (tmp_path / "trend_20260412.html").read_text(encoding="utf-8")
    assert 'data-visual-system="radar-unified-v2"' in html
    assert 'data-visual-surface="report"' in html
    assert "Trend Quality" in html
    assert "attention_signal" in html
    assert "conversion_proxy_signal" in html
    assert "naver_shopping" in html


def test_generate_index_html_uses_unified_surface_markers(tmp_path) -> None:
    report_dir = tmp_path / "reports"
    report_dir.mkdir(parents=True)
    (report_dir / "trend_20260412.html").write_text("sample", encoding="utf-8")

    index_path = generate_index_html(report_dir)
    html = index_path.read_text(encoding="utf-8")

    assert 'data-visual-system="radar-unified-v2"' in html
    assert 'data-visual-surface="report"' in html
    assert 'data-visual-page="index"' in html

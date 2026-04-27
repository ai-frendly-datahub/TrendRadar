from __future__ import annotations

from pathlib import Path


def test_spike_report_template_uses_unified_visual_marker() -> None:
    template = Path(__file__).resolve().parents[2] / "reporters" / "templates" / "spike_report.html"
    html = template.read_text(encoding="utf-8")

    assert 'data-visual-system="radar-unified-v2"' in html
    assert 'data-visual-surface="report"' in html
    assert 'data-visual-page="spike-report"' in html

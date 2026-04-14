"""HTML 리포트 생성 모듈."""

from __future__ import annotations

import json
from collections.abc import Mapping
from datetime import UTC, date
from html import escape
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape

from reporters.correlation_analysis import analyze_cross_platform_correlation
from reporters.trend_forecast import forecast_keyword_trends
from trendradar.models import KeywordSet, TrendPoint


def _build_7x24_heatmap_data(points: list[TrendPoint]) -> dict[str, object]:
    matrix = [[0 for _ in range(24)] for _ in range(7)]

    for point in points:
        timestamp = point.timestamp
        if timestamp.tzinfo is not None:
            timestamp = timestamp.astimezone(UTC)

        matrix[timestamp.weekday()][timestamp.hour] += 1

    max_count = max((max(row) for row in matrix), default=0)

    return {
        "x": [f"{hour:02d}:00" for hour in range(24)],
        "y": ["월", "화", "수", "목", "금", "토", "일"],
        "z": matrix,
        "max_count": max_count,
        "total_points": len(points),
    }


def generate_daily_report(
    target_date: date,
    keyword_sets: list[KeywordSet],
    db_path: Path | None = None,
    output_dir: Path | None = None,
    quality_report: Mapping[str, Any] | None = None,
) -> None:
    """일일 트렌드 리포트를 생성합니다.

    Args:
        target_date: 리포트 날짜
        keyword_sets: 키워드 세트 리스트
        db_path: DuckDB 파일 경로
        output_dir: 리포트 출력 디렉토리
    """
    from storage import trend_store

    if output_dir is None:
        output_dir = Path(__file__).parent.parent / "reports"

    output_dir.mkdir(parents=True, exist_ok=True)

    # 각 키워드 세트별로 데이터 조회
    sections: list[dict[str, object]] = []
    heatmap_points: list[TrendPoint] = []
    forecast_points: list[TrendPoint] = []
    total_keywords = 0

    for kw_set in keyword_sets:
        if not kw_set.enabled:
            continue

        set_name = kw_set.name or "Unknown"
        keywords = kw_set.keywords

        # 데이터 조회 (최근 30일)
        start_date = str(target_date.replace(day=1))  # 월초부터
        end_date = str(target_date)

        trend_data: list[dict[str, object]] = []
        for keyword in keywords:
            raw_points = trend_store.query_trend_points(
                keyword=keyword,
                start_date=start_date,
                end_date=end_date,
                db_path=db_path,
            )
            points = [
                TrendPoint.from_dict(point) for point in raw_points if isinstance(point, dict)
            ]
            heatmap_points.extend(points)
            forecast_points.extend(points)
            total_keywords += 1
            trend_data.append(
                {
                    "keyword": keyword,
                    "points": points,
                    "latest_value": points[-1].value if points else 0,
                }
            )

        sections.append(
            {
                "name": set_name,
                "description": kw_set.description,
                "trend_data": trend_data,
            }
        )

    # 템플릿 렌더링
    template_dir = Path(__file__).parent / "templates"
    template_dir.mkdir(exist_ok=True)

    # 간단한 템플릿 파일 생성 (실제로는 별도 파일로 관리)
    _create_default_template(template_dir)

    env = Environment(
        loader=FileSystemLoader(str(template_dir)),
        autoescape=select_autoescape(["html", "xml"]),
    )

    template = env.get_template("daily_report.html")
    heatmap_data = _build_7x24_heatmap_data(heatmap_points)
    heatmap_total_points = len(heatmap_points)
    forecast_data = forecast_keyword_trends(forecast_points, top_n=10)
    correlation_analysis = analyze_cross_platform_correlation(heatmap_points)

    html_content = template.render(
        report_date=target_date.isoformat(),
        sections=sections,
        total_keywords=total_keywords,
        heatmap_total_points=heatmap_total_points,
        heatmap_data_json=json.dumps(heatmap_data, ensure_ascii=False),
        forecast_keyword_count=len(forecast_data),
        forecast_data_json=json.dumps(forecast_data, ensure_ascii=False),
        correlation_analysis_json=json.dumps(correlation_analysis, ensure_ascii=False),
        top_lead_lag_relationships=correlation_analysis["top_lead_lag_relationships"],
    )

    # 파일 저장
    output_file = output_dir / f"trend_{target_date.strftime('%Y%m%d')}.html"
    _ = output_file.write_text(html_content, encoding="utf-8")
    if quality_report:
        _inject_trend_quality_panel(output_file, quality_report)

    print(f"리포트 생성 완료: {output_file}")


def _inject_trend_quality_panel(
    output_file: Path,
    quality_report: Mapping[str, Any],
) -> None:
    panel = _render_trend_quality_panel(quality_report)
    html = output_file.read_text(encoding="utf-8")
    if 'id="trend-quality"' in html:
        return

    marker = '<script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>'
    if marker in html:
        html = html.replace(marker, f"{panel}\n\n    {marker}", 1)
    else:
        html = html.replace("</body>", f"{panel}\n</body>", 1)
    output_file.write_text(html, encoding="utf-8")


def _render_trend_quality_panel(quality_report: Mapping[str, Any]) -> str:
    summary = _mapping(quality_report.get("summary"))
    events = _list_of_mappings(quality_report.get("events"))[:8]
    review_items = _list_of_mappings(quality_report.get("daily_review_items"))[:8]
    chips = [
        ("signals", summary.get("collected_signal_count", 0)),
        ("attention", summary.get("attention_signal_count", 0)),
        ("conversion", summary.get("conversion_proxy_signal_count", 0)),
        ("community", summary.get("community_signal_count", 0)),
        ("field gaps", summary.get("signal_required_field_gap_count", 0)),
        ("review", summary.get("daily_review_item_count", 0)),
    ]
    chip_html = "\n            ".join(
        f'<span class="metric-chip">{escape(label)}: {escape(str(value))}</span>'
        for label, value in chips
    )
    event_html = _render_quality_events(events)
    review_html = _render_quality_review_items(review_items)
    generated_at = escape(str(quality_report.get("generated_at", "")))
    return f"""    <div class="section" id="trend-quality">
        <h2>Trend Quality</h2>
        <p class="section-desc">attention, conversion proxy, and community signals are scored as separate axes. Generated at {generated_at}</p>
        <div class="trend-quality-chips">
            {chip_html}
        </div>
        <h3>Quality Signals</h3>
        {event_html}
        <h3>Daily Review</h3>
        {review_html}
    </div>"""


def _render_quality_events(events: list[Mapping[str, Any]]) -> str:
    if not events:
        return '<p class="no-data">No quality signals observed for this report window.</p>'
    rows = []
    for event in events:
        rows.append(
            "<tr>"
            f"<td>{escape(str(event.get('event_model') or ''))}</td>"
            f"<td>{escape(str(event.get('keyword_set_name') or ''))}</td>"
            f"<td>{escape(str(event.get('channel') or ''))}</td>"
            f"<td>{escape(str(event.get('keyword') or ''))}</td>"
            f"<td>{escape(str(event.get('score_axis') or ''))}</td>"
            f"<td>{escape(str(event.get('normalized_value') or ''))}</td>"
            "</tr>"
        )
    body = "\n                ".join(rows)
    return f"""<div class="table-wrap">
            <table class="lead-lag-table">
                <thead>
                    <tr><th>Model</th><th>Pack</th><th>Channel</th><th>Keyword</th><th>Axis</th><th>Score</th></tr>
                </thead>
                <tbody>
                {body}
                </tbody>
            </table>
        </div>"""


def _render_quality_review_items(items: list[Mapping[str, Any]]) -> str:
    if not items:
        return '<p class="no-data">No quality review items.</p>'
    rows = []
    for item in items:
        rows.append(
            "<tr>"
            f"<td>{escape(str(item.get('reason') or ''))}</td>"
            f"<td>{escape(str(item.get('event_model') or ''))}</td>"
            f"<td>{escape(str(item.get('keyword_set_name') or ''))}</td>"
            f"<td>{escape(str(item.get('channel') or item.get('detail') or ''))}</td>"
            "</tr>"
        )
    body = "\n                ".join(rows)
    return f"""<div class="table-wrap">
            <table class="lead-lag-table">
                <thead>
                    <tr><th>Reason</th><th>Model</th><th>Pack</th><th>Detail</th></tr>
                </thead>
                <tbody>
                {body}
                </tbody>
            </table>
        </div>"""


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _list_of_mappings(value: Any) -> list[Mapping[str, Any]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, Mapping)]


def _create_default_template(template_dir: Path) -> None:
    """기본 템플릿을 생성합니다."""
    template_file = template_dir / "daily_report.html"

    if template_file.exists():
        return

    template_content = """<!DOCTYPE html>
<html lang="ko" data-visual-system="radar-unified-v2" data-visual-surface="report">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="color-scheme" content="dark">
    <link rel="preconnect" href="https://cdn.jsdelivr.net">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/pretendard@1.3.9/dist/web/variable/pretendardvariable-dynamic-subset.css">
    <title>TrendRadar 일일 리포트 - {{ report_date }}</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }
        h1 {
            color: #333;
            border-bottom: 3px solid #4CAF50;
            padding-bottom: 10px;
        }
        .section {
            background: white;
            border-radius: 8px;
            padding: 20px;
            margin: 20px 0;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .section h2 {
            color: #4CAF50;
            margin-top: 0;
        }
        .keyword-card {
            border-left: 4px solid #2196F3;
            padding: 10px 15px;
            margin: 10px 0;
            background-color: #f9f9f9;
        }
        .keyword-name {
            font-weight: bold;
            font-size: 1.1em;
        }
        .keyword-value {
            color: #666;
            font-size: 0.9em;
        }
        .stats {
            display: flex;
            gap: 20px;
            margin: 20px 0;
        }
        .stat-box {
            flex: 1;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
        }
        .stat-number {
            font-size: 2em;
            font-weight: bold;
        }
        .stat-label {
            font-size: 0.9em;
            opacity: 0.9;
        }
        :root {
            --radar-bg:#11100f;
            --radar-bg2:#171613;
            --radar-panel:rgba(29, 33, 31, .88);
            --radar-line:rgba(215, 201, 123, .22);
            --radar-text:#f4f2ea;
            --radar-muted:rgba(244, 242, 234, .68);
            --radar-brand:#37d7bd;
            --radar-accent:#f2c14e;
        }
        body {
            font-family: "Pretendard Variable", "Pretendard", -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(180deg, var(--radar-bg), var(--radar-bg2) 55%, #0e0d0b);
            color: var(--radar-text);
        }
        h1 {
            color: var(--radar-text);
            border-bottom-color: var(--radar-brand);
        }
        .section {
            background: var(--radar-panel);
            border: 1px solid var(--radar-line);
            box-shadow: 0 14px 42px rgba(0,0,0,0.28);
        }
        .section h2 {
            color: var(--radar-brand);
        }
        .keyword-card {
            background-color: rgba(244, 242, 234, .06);
            border-left-color: var(--radar-brand);
        }
        .keyword-value {
            color: var(--radar-muted);
        }
        .stat-box {
            background: linear-gradient(135deg, rgba(55,215,189,.24), rgba(242,193,78,.18));
            border: 1px solid var(--radar-line);
            color: var(--radar-text);
        }
        p[style*="color: #666"],
        footer[style*="color: #999"] {
            color: var(--radar-muted) !important;
        }
    </style>
</head>
<body>
    <h1>🎯 TrendRadar 일일 리포트</h1>
    <p style="color: #666;">리포트 날짜: {{ report_date }}</p>

    <div class="stats">
        <div class="stat-box">
            <div class="stat-number">{{ sections|length }}</div>
            <div class="stat-label">키워드 세트</div>
        </div>
        <div class="stat-box">
            <div class="stat-number">{{ total_keywords }}</div>
            <div class="stat-label">총 키워드</div>
        </div>
    </div>

    {% for section in sections %}
    <div class="section">
        <h2>{{ section.name }}</h2>
        <p style="color: #666;">{{ section.description }}</p>

        {% for item in section.trend_data %}
        <div class="keyword-card">
            <div class="keyword-name">{{ item.keyword }}</div>
            <div class="keyword-value">
                최근 관심도: {{ "%.1f"|format(item.latest_value) }} / 데이터 포인트: {{ item.points|length }}개
            </div>
        </div>
        {% endfor %}
    </div>
    {% endfor %}

    <footer style="text-align: center; margin-top: 40px; color: #999; font-size: 0.9em;">
        <p>Generated by TrendRadar</p>
    </footer>
</body>
</html>
"""
    _ = template_file.write_text(template_content, encoding="utf-8")


def generate_index_html(report_dir: Path) -> Path:
    """Generate an index.html that lists all available report files."""
    from datetime import datetime

    report_dir.mkdir(parents=True, exist_ok=True)

    html_files = sorted(
        [f for f in report_dir.glob("*.html") if f.name != "index.html"],
        key=lambda p: p.name,
    )

    reports: list[dict[str, str]] = []
    for html_file in html_files:
        name = html_file.stem
        display_name = name.replace("_report", "").replace("_", " ").title()
        reports.append({"filename": html_file.name, "display_name": display_name})

    generated_at = datetime.now(UTC).isoformat()

    if reports:
        cards_html = "\n    ".join(
            f'<div class="card"><a href="{r["filename"]}"><strong>{r["display_name"]}</strong></a></div>'
            for r in reports
        )
        body_content = f'<div class="reports">\n    {cards_html}\n  </div>'
    else:
        body_content = '<div class="empty">No reports available yet.</div>'

    html_content = f"""<!doctype html>
<html lang="en" data-visual-system="radar-unified-v2" data-visual-surface="index">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta name="color-scheme" content="dark">
  <title>Radar Reports</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; margin: 0; padding: 24px; background: linear-gradient(180deg, #11100f, #171613 55%, #0e0d0b); color: #f4f2ea; }}
    h1 {{ margin: 0 0 8px 0; }}
    .muted {{ color: rgba(244, 242, 234, .68); font-size: 13px; margin-bottom: 24px; }}
    .reports {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 12px; }}
    .card {{ background: rgba(29, 33, 31, .88); border: 1px solid rgba(215, 201, 123, .22); border-radius: 8px; padding: 16px; box-shadow: 0 14px 42px rgba(0,0,0,0.28); transition: box-shadow 0.2s; }}
    .card:hover {{ box-shadow: 0 4px 6px rgba(0,0,0,0.08); }}
    a {{ color: #f4f2ea; text-decoration: none; }}
    a:hover {{ text-decoration: underline; }}
    .empty {{ text-align: center; color: rgba(244, 242, 234, .68); padding: 48px; }}
  </style>
</head>
<body>
  <h1>Radar Reports</h1>
  <div class="muted">Generated at {generated_at} (UTC)</div>

  {body_content}
</body>
</html>"""

    index_path = report_dir / "index.html"
    _ = index_path.write_text(html_content, encoding="utf-8")
    return index_path

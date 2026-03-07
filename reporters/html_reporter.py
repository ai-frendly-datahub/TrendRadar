# -*- coding: utf-8 -*-
"""HTML 리포트 생성 모듈."""

from __future__ import annotations

from datetime import date
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape
from trendradar.models import KeywordSet


def generate_daily_report(
    target_date: date,
    keyword_sets: list[KeywordSet],
    db_path: Path | None = None,
    output_dir: Path | None = None,
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
        output_dir = Path(__file__).parent.parent / "docs" / "reports"

    output_dir.mkdir(parents=True, exist_ok=True)

    # 각 키워드 세트별로 데이터 조회
    sections = []

    for kw_set in keyword_sets:
        if not kw_set.enabled:
            continue

        set_name = kw_set.name or "Unknown"
        keywords = kw_set.keywords

        # 데이터 조회 (최근 30일)
        start_date = str(target_date.replace(day=1))  # 월초부터
        end_date = str(target_date)

        trend_data = []
        for keyword in keywords:
            points = trend_store.query_trend_points(
                keyword=keyword,
                start_date=start_date,
                end_date=end_date,
                db_path=db_path,
            )
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

    html_content = template.render(
        report_date=target_date.isoformat(),
        sections=sections,
        total_keywords=sum(len(s["trend_data"]) for s in sections),
    )

    # 파일 저장
    output_file = output_dir / f"{target_date.isoformat()}.html"
    output_file.write_text(html_content, encoding="utf-8")

    print(f"리포트 생성 완료: {output_file}")


def _create_default_template(template_dir: Path) -> None:
    """기본 템플릿을 생성합니다."""
    template_file = template_dir / "daily_report.html"

    if template_file.exists():
        return

    template_content = """<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
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
    template_file.write_text(template_content, encoding="utf-8")

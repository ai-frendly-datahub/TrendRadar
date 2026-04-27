"""리포트 인덱스 페이지 생성 모듈."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path


def generate_index_page(reports_dir: Path) -> None:
    """리포트 목록 인덱스 페이지를 생성합니다.

    Args:
        reports_dir: 리포트 디렉토리 경로
    """
    # HTML 리포트 파일 찾기
    trend_reports = sorted(reports_dir.glob("trend_*.html"), reverse=True)
    spike_reports = sorted(reports_dir.glob("spike_*.html"), reverse=True)

    # 날짜별로 그룹화
    reports_by_date = {}

    for report in trend_reports:
        date_str = report.stem.replace("trend_", "")
        if date_str not in reports_by_date:
            reports_by_date[date_str] = {}
        reports_by_date[date_str]["trend"] = report.name

    for report in spike_reports:
        date_str = report.stem.replace("spike_", "")
        if date_str not in reports_by_date:
            reports_by_date[date_str] = {}
        reports_by_date[date_str]["spike"] = report.name

    # 날짜순 정렬 (최신순)
    sorted_dates = sorted(reports_by_date.keys(), reverse=True)

    # 통계 계산
    total_reports = len(trend_reports) + len(spike_reports)
    trend_count = len(trend_reports)
    spike_count = len(spike_reports)

    # HTML 생성
    html_content = f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>TrendRadar 리포트 목록</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }}
        .container {{
            background: white;
            border-radius: 12px;
            padding: 40px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
        }}
        h1 {{
            color: #667eea;
            border-bottom: 3px solid #667eea;
            padding-bottom: 15px;
            margin-bottom: 30px;
            display: flex;
            align-items: center;
            gap: 15px;
        }}
        .subtitle {{
            color: #666;
            font-size: 1.1em;
            margin-bottom: 30px;
        }}
        .stats {{
            display: flex;
            gap: 20px;
            margin-bottom: 30px;
            flex-wrap: wrap;
        }}
        .stat-card {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 10px;
            flex: 1;
            min-width: 200px;
        }}
        .stat-number {{
            font-size: 2.5em;
            font-weight: bold;
            margin: 10px 0;
        }}
        .stat-label {{
            font-size: 0.9em;
            opacity: 0.9;
        }}
        .report-list {{
            margin-top: 30px;
        }}
        .report-date {{
            font-size: 1.3em;
            font-weight: bold;
            color: #333;
            margin: 30px 0 15px 0;
            padding-bottom: 10px;
            border-bottom: 2px solid #eee;
        }}
        .report-links {{
            display: flex;
            gap: 15px;
            flex-wrap: wrap;
            margin-bottom: 10px;
        }}
        .report-link {{
            display: inline-flex;
            align-items: center;
            gap: 8px;
            background: #f8f9fa;
            padding: 12px 20px;
            border-radius: 8px;
            text-decoration: none;
            color: #333;
            transition: all 0.3s;
            border: 2px solid transparent;
        }}
        .report-link:hover {{
            background: #667eea;
            color: white;
            border-color: #667eea;
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
        }}
        .report-link.trend {{
            border-left: 4px solid #4CAF50;
        }}
        .report-link.spike {{
            border-left: 4px solid #f5576c;
        }}
        .icon {{
            font-size: 1.2em;
        }}
        .no-reports {{
            text-align: center;
            padding: 60px 20px;
            color: #999;
        }}
        .footer {{
            margin-top: 50px;
            padding-top: 20px;
            border-top: 1px solid #eee;
            text-align: center;
            color: #999;
            font-size: 0.9em;
        }}
        .github-link {{
            display: inline-flex;
            align-items: center;
            gap: 8px;
            margin-top: 10px;
            color: #667eea;
            text-decoration: none;
        }}
        .github-link:hover {{
            text-decoration: underline;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>
            <span>🎯</span>
            <span>TrendRadar 리포트</span>
        </h1>

        <div class="subtitle">
            트렌드를 레이더처럼 계속 보여주는 도구 - 급상승 키워드 자동 감지
        </div>

        <div class="stats">
            <div class="stat-card">
                <div class="stat-label">전체 리포트</div>
                <div class="stat-number">{total_reports}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">일일 트렌드</div>
                <div class="stat-number">{trend_count}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">급상승 분석</div>
                <div class="stat-number">{spike_count}</div>
            </div>
        </div>

        <div class="report-list">
"""

    if not sorted_dates:
        html_content += """
            <div class="no-reports">
                <h2>📭 아직 생성된 리포트가 없습니다</h2>
                <p>GitHub Actions 워크플로를 실행하여 첫 리포트를 생성하세요!</p>
            </div>
"""
    else:
        for date_str in sorted_dates:
            reports = reports_by_date[date_str]

            # 날짜 포맷팅
            try:
                date_obj = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=UTC)
                formatted_date = date_obj.strftime("%Y년 %m월 %d일")
                weekday = ["월", "화", "수", "목", "금", "토", "일"][date_obj.weekday()]
                formatted_date += f" ({weekday})"
            except Exception:
                formatted_date = date_str

            html_content += f"""
            <div class="report-date">📅 {formatted_date}</div>
            <div class="report-links">
"""

            if "trend" in reports:
                html_content += f"""
                <a href="{reports["trend"]}" class="report-link trend">
                    <span class="icon">📈</span>
                    <span>일일 트렌드 리포트</span>
                </a>
"""

            if "spike" in reports:
                html_content += f"""
                <a href="{reports["spike"]}" class="report-link spike">
                    <span class="icon">🔥</span>
                    <span>급상승 키워드 리포트</span>
                </a>
"""

            html_content += """
            </div>
"""

    html_content += """
        </div>

        <div class="footer">
            <p>Generated by TrendRadar</p>
            <a href="https://github.com/zzragida/TrendRadar" class="github-link" target="_blank">
                <span>🔗</span>
                <span>GitHub Repository</span>
            </a>
        </div>
    </div>
</body>
</html>
"""

    # index.html 저장
    index_file = reports_dir / "index.html"
    index_file.write_text(html_content, encoding="utf-8")
    print(f"인덱스 페이지 생성 완료: {index_file}")


if __name__ == "__main__":
    reports_dir = Path(__file__).parent.parent / "docs" / "reports"
    generate_index_page(reports_dir)

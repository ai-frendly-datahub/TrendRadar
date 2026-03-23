"""급상승 키워드 리포트 생성 모듈."""

from __future__ import annotations

import logging
from datetime import date
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from analyzers.cross_channel_analyzer import CrossChannelAnalyzer
from analyzers.spike_detector import SpikeDetector


logger = logging.getLogger(__name__)


def generate_spike_report(
    target_date: date,
    db_path: Path | None = None,
    output_dir: Path | None = None,
) -> None:
    """급상승 키워드 리포트를 생성합니다.

    Args:
        target_date: 리포트 날짜
        db_path: DuckDB 파일 경로
        output_dir: 리포트 출력 디렉토리
    """
    if output_dir is None:
        output_dir = Path(__file__).parent.parent / "reports"

    output_dir.mkdir(parents=True, exist_ok=True)

    # Spike Detector로 급상승 감지
    detector = SpikeDetector(
        db_path=db_path,
        recent_days=7,
        baseline_days=30,
    )

    all_spikes = detector.detect_all_spikes(source=None, top_n=10)

    # Cross-Channel Analyzer로 채널 격차 분석
    analyzer = CrossChannelAnalyzer(db_path=db_path)

    channel_gaps = []
    try:
        gaps = analyzer.find_channel_gaps(
            channel1="google",
            channel2="naver",
            days=30,
            min_gap=1.5,
        )
        channel_gaps = gaps[:10]
    except KeyError as e:
        logger.warning(f"Missing data for cross-channel analysis: {e}")
    except Exception as e:
        logger.error(f"Cross-channel analysis failed: {e}", exc_info=True)

    # 템플릿 렌더링
    template_dir = Path(__file__).parent / "templates"
    template_dir.mkdir(exist_ok=True)

    _create_spike_template(template_dir)

    env = Environment(
        loader=FileSystemLoader(str(template_dir)),
        autoescape=select_autoescape(["html", "xml"]),
    )

    template = env.get_template("spike_report.html")

    html_content = template.render(
        report_date=target_date.isoformat(),
        surge_spikes=all_spikes.get("surge", []),
        emerging_spikes=all_spikes.get("emerging", []),
        viral_spikes=all_spikes.get("viral", []),
        channel_gaps=channel_gaps,
        total_spikes=sum(len(v) for v in all_spikes.values()),
    )

    # 파일 저장
    output_file = output_dir / f"spike_{target_date.strftime('%Y%m%d')}.html"
    output_file.write_text(html_content, encoding="utf-8")

    logger.info(f"Spike report generated: {output_file}")
    print(f"급상승 리포트 생성 완료: {output_file}")


def _create_spike_template(template_dir: Path) -> None:
    """급상승 리포트 템플릿을 생성합니다."""
    template_file = template_dir / "spike_report.html"

    if template_file.exists():
        return

    template_content = """<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>TrendRadar 급상승 리포트 - {{ report_date }}</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #333;
        }
        .container {
            background: white;
            border-radius: 12px;
            padding: 30px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
        }
        h1 {
            color: #667eea;
            border-bottom: 3px solid #667eea;
            padding-bottom: 15px;
            margin-bottom: 30px;
        }
        .alert-box {
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            color: white;
            padding: 20px;
            border-radius: 10px;
            margin: 20px 0;
            font-size: 1.1em;
            text-align: center;
        }
        .section {
            margin: 30px 0;
        }
        .section-title {
            font-size: 1.5em;
            color: #667eea;
            margin-bottom: 15px;
            display: flex;
            align-items: center;
        }
        .section-title .icon {
            font-size: 1.3em;
            margin-right: 10px;
        }
        .spike-card {
            background: #f8f9fa;
            border-left: 5px solid #f5576c;
            padding: 15px;
            margin: 10px 0;
            border-radius: 5px;
            transition: all 0.3s;
        }
        .spike-card:hover {
            transform: translateX(5px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        }
        .keyword-name {
            font-size: 1.2em;
            font-weight: bold;
            color: #333;
            margin-bottom: 8px;
        }
        .spike-stats {
            display: flex;
            gap: 15px;
            flex-wrap: wrap;
            margin: 8px 0;
        }
        .stat {
            background: white;
            padding: 5px 12px;
            border-radius: 20px;
            font-size: 0.9em;
        }
        .score-badge {
            display: inline-block;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 5px 15px;
            border-radius: 20px;
            font-weight: bold;
        }
        .gap-card {
            background: #e3f2fd;
            border-left: 5px solid #2196F3;
            padding: 15px;
            margin: 10px 0;
            border-radius: 5px;
        }
        .insight {
            background: #fff3cd;
            border-left: 4px solid #ffc107;
            padding: 10px;
            margin-top: 10px;
            font-style: italic;
        }
        .no-data {
            text-align: center;
            padding: 40px;
            color: #999;
            font-size: 1.1em;
        }
        .footer {
            margin-top: 40px;
            text-align: center;
            color: #999;
            font-size: 0.9em;
            padding-top: 20px;
            border-top: 1px solid #eee;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎯 TrendRadar 급상승 리포트</h1>
        <p style="color: #666; font-size: 1.1em;">리포트 날짜: {{ report_date }}</p>

        {% if total_spikes > 0 %}
        <div class="alert-box">
            🔥 총 {{ total_spikes }}개의 급상승 신호가 감지되었습니다!
        </div>
        {% endif %}

        <!-- 급상승 키워드 (Surge) -->
        <div class="section">
            <div class="section-title">
                <span class="icon">📈</span>
                <span>급상승 키워드 (Surge)</span>
            </div>
            <p style="color: #666;">최근 7일 평균이 직전 30일 평균 대비 크게 증가한 키워드</p>

            {% if surge_spikes %}
                {% for spike in surge_spikes %}
                <div class="spike-card">
                    <div class="keyword-name">{{ spike.keyword }}</div>
                    <div class="spike-stats">
                        <span class="stat">📊 현재: {{ "%.1f"|format(spike.current_value) }}</span>
                        <span class="stat">📉 기준: {{ "%.1f"|format(spike.baseline_value) }}</span>
                        <span class="stat">🚀 증가율: {{ "%.2f"|format(spike.spike_ratio) }}x</span>
                        <span class="stat">📡 소스: {{ spike.source }}</span>
                    </div>
                    <div style="margin-top: 10px;">
                        <span class="score-badge">⭐ 급상승 점수: {{ "%.1f"|format(spike.spike_score) }}/100</span>
                    </div>
                </div>
                {% endfor %}
            {% else %}
                <div class="no-data">급상승 키워드가 없습니다.</div>
            {% endif %}
        </div>

        <!-- 신규 등장 키워드 (Emerging) -->
        <div class="section">
            <div class="section-title">
                <span class="icon">🌟</span>
                <span>신규 등장 키워드 (Emerging)</span>
            </div>
            <p style="color: #666;">과거에는 낮았지만 최근 갑자기 나타난 키워드</p>

            {% if emerging_spikes %}
                {% for spike in emerging_spikes %}
                <div class="spike-card">
                    <div class="keyword-name">
                        {{ spike.keyword }}
                        {% if spike.metadata.get('is_new', False) %}
                        <span style="background: #4CAF50; color: white; padding: 3px 10px; border-radius: 15px; font-size: 0.7em;">NEW</span>
                        {% endif %}
                    </div>
                    <div class="spike-stats">
                        <span class="stat">📊 현재: {{ "%.1f"|format(spike.current_value) }}</span>
                        <span class="stat">📉 이전: {{ "%.1f"|format(spike.baseline_value) }}</span>
                        <span class="stat">📡 소스: {{ spike.source }}</span>
                    </div>
                    <div style="margin-top: 10px;">
                        <span class="score-badge">⭐ 점수: {{ "%.1f"|format(spike.spike_score) }}/100</span>
                    </div>
                </div>
                {% endfor %}
            {% else %}
                <div class="no-data">신규 등장 키워드가 없습니다.</div>
            {% endif %}
        </div>

        <!-- 바이럴 키워드 (Viral) -->
        <div class="section">
            <div class="section-title">
                <span class="icon">💥</span>
                <span>바이럴 키워드 (Viral)</span>
            </div>
            <p style="color: #666;">짧은 기간 동안 폭발적으로 증가하는 키워드</p>

            {% if viral_spikes %}
                {% for spike in viral_spikes %}
                <div class="spike-card">
                    <div class="keyword-name">{{ spike.keyword }}</div>
                    <div class="spike-stats">
                        <span class="stat">📊 초기: {{ "%.1f"|format(spike.baseline_value) }}</span>
                        <span class="stat">🔥 최근: {{ "%.1f"|format(spike.current_value) }}</span>
                        <span class="stat">🚀 성장률: {{ "%.2f"|format(spike.spike_ratio) }}x</span>
                        <span class="stat">📡 소스: {{ spike.source }}</span>
                    </div>
                    <div style="margin-top: 10px;">
                        <span class="score-badge">⭐ 점수: {{ "%.1f"|format(spike.spike_score) }}/100</span>
                    </div>
                </div>
                {% endfor %}
            {% else %}
                <div class="no-data">바이럴 키워드가 없습니다.</div>
            {% endif %}
        </div>

        <!-- 채널 간 격차 -->
        {% if channel_gaps %}
        <div class="section">
            <div class="section-title">
                <span class="icon">🔀</span>
                <span>채널 간 격차 분석</span>
            </div>
            <p style="color: #666;">채널별로 트렌드 강도가 다른 키워드</p>

            {% for gap in channel_gaps %}
            <div class="gap-card">
                <div class="keyword-name">{{ gap.keyword }}</div>
                <div class="spike-stats">
                    <span class="stat">🥇 {{ gap.leading_channel }}: {{ "%.1f"|format(gap.leading_value) }}</span>
                    <span class="stat">📉 {{ gap.lagging_channel }}: {{ "%.1f"|format(gap.lagging_value) }}</span>
                    <span class="stat">⚖️ 격차: {{ "%.2f"|format(gap.gap_ratio) }}x</span>
                </div>
                <div class="insight">
                    💡 {{ gap.insight }}
                </div>
            </div>
            {% endfor %}
        </div>
        {% endif %}

        <div class="footer">
            <p>Generated by TrendRadar Spike Detector</p>
            <p>데이터 기간: 최근 7일 vs 직전 30일</p>
        </div>
    </div>
</body>
</html>
"""
    template_file.write_text(template_content, encoding="utf-8")

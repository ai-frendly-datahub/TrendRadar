"""Plotly trend heatmap plugin for TrendRadar unified template."""

from __future__ import annotations

from typing import Any


def get_chart_config(store: Any = None, articles: Any = None) -> dict | None:
    """Generate Plotly 7x24 heatmap chart config for plugin slot.

    Args:
        store: Unused (kept for API compatibility).
        articles: List of TrendPoint objects to build heatmap from.

    Returns:
        Plugin chart config dict with id, title, config_json, or None on failure.
    """
    try:
        if not articles:
            return None

        from datetime import UTC

        # Build 7x24 heatmap matrix (weekday x hour)
        matrix = [[0 for _ in range(24)] for _ in range(7)]

        for point in articles:
            try:
                timestamp = getattr(point, "timestamp", None)
                if timestamp is None:
                    continue
                if hasattr(timestamp, "tzinfo") and timestamp.tzinfo is not None:
                    timestamp = timestamp.astimezone(UTC)
                matrix[timestamp.weekday()][timestamp.hour] += 1
            except Exception:
                continue

        max_count = max((max(row) for row in matrix), default=0)
        if max_count == 0:
            return None

        import plotly.graph_objects as go

        x_labels = [f"{hour:02d}:00" for hour in range(24)]
        y_labels = ["월", "화", "수", "목", "금", "토", "일"]

        fig = go.Figure(
            data=go.Heatmap(
                z=matrix,
                x=x_labels,
                y=y_labels,
                colorscale="Blues",
                showscale=True,
                hovertemplate="요일: %{y}<br>시간: %{x}<br>수집: %{z}건<extra></extra>",
            )
        )

        fig.update_layout(
            height=320,
            margin={"l": 60, "r": 20, "t": 24, "b": 40},
            paper_bgcolor="rgba(10,14,23,0)",
            plot_bgcolor="rgba(14,22,42,0.5)",
            font={"color": "#e9eefb"},
            xaxis={
                "title": "시간 (UTC)",
                "color": "#e9eefb",
                "gridcolor": "rgba(233,238,251,0.1)",
            },
            yaxis={
                "title": "요일",
                "color": "#e9eefb",
                "gridcolor": "rgba(233,238,251,0.1)",
            },
        )

        import plotly.io as pio

        config_json = pio.to_html(fig, full_html=False, include_plotlyjs="cdn")

        return {
            "id": "trend_heatmap",
            "title": "트렌드 수집 히트맵 (요일 × 시간)",
            "config_json": config_json,
        }

    except Exception:
        return None

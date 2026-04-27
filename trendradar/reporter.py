from __future__ import annotations

from collections.abc import Iterable
from dataclasses import replace
from importlib import import_module
from pathlib import Path

from radar_core.ontology import build_summary_ontology_metadata

from .models import Article, CategoryConfig


def generate_report(
    *,
    category: CategoryConfig,
    articles: Iterable[Article],
    output_path: Path,
    stats: dict[str, int],
    errors: list[str] | None = None,
    store=None,
) -> Path:
    """Render HTML report using radar-core unified template."""
    normalized_category = category
    if not category.category_name.strip() or not category.display_name.strip():
        category_name = category.category_name.strip() or category.display_name.strip() or "daily"
        display_name = category.display_name.strip() or category_name
        normalized_category = replace(
            category,
            category_name=category_name,
            display_name=display_name,
        )

    articles_list = list(articles)
    report_utils = import_module("radar_core.report_utils")
    core_generate_report = report_utils.generate_report
    plugin_charts = []
    if articles_list:
        try:
            from trendradar.plugins.trend_heatmap import get_chart_config

            chart = get_chart_config(articles=articles_list)
            if chart is not None:
                plugin_charts.append(chart)
        except Exception:
            pass

    # --- Universal plugins (entity heatmap + source reliability) ---
    try:
        entity_heatmap = import_module("radar_core.plugins.entity_heatmap")
        _heatmap = entity_heatmap.get_chart_config(articles=articles_list)
        if _heatmap is not None:
            plugin_charts.append(_heatmap)
    except Exception:
        pass
    try:
        source_reliability = import_module("radar_core.plugins.source_reliability")
        _reliability = source_reliability.get_chart_config(store=store)
        if _reliability is not None:
            plugin_charts.append(_reliability)
    except Exception:
        pass

    return core_generate_report(
        category=normalized_category,
        articles=articles_list,
        output_path=output_path,
        stats=stats,
        errors=errors,
        plugin_charts=plugin_charts if plugin_charts else None,
        ontology_metadata=build_summary_ontology_metadata(
            "TrendRadar",
            category_name=normalized_category.category_name,
            search_from=Path(__file__).resolve(),
        ),
    )


def generate_index_html(report_dir: Path, summaries_dir: Path | None = None) -> Path:
    """Generate index.html using radar-core unified template."""
    report_utils = import_module("radar_core.report_utils")
    core_generate_index_html = report_utils.generate_index_html
    return core_generate_index_html(report_dir, "TrendRadar")

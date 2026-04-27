from __future__ import annotations

import importlib.util
from datetime import UTC, datetime
from pathlib import Path

import yaml

from storage import trend_store
from trendradar.models import TrendPoint


def _load_script_module():
    script_path = Path(__file__).resolve().parents[2] / "scripts" / "check_quality.py"
    spec = importlib.util.spec_from_file_location("trendradar_check_quality_script", script_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_generate_quality_artifacts_writes_trend_quality_json(
    tmp_path: Path,
    capsys,
) -> None:
    project_root = tmp_path
    (project_root / "config").mkdir(parents=True)

    (project_root / "config" / "keyword_sets.yaml").write_text(
        yaml.safe_dump(
            {
                "data_quality": {
                    "priority": "P1",
                    "primary_motion": "attention",
                    "quality_outputs": {
                        "latest": "docs/reports/trend_quality.json",
                        "dated_pattern": "docs/reports/trend_YYYYMMDD_quality.json",
                    },
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
                },
                "keyword_sets": [
                    {
                        "name": "Fashion",
                        "enabled": True,
                        "version": "2026.04",
                        "taxonomy": {
                            "vertical": "commerce_fashion",
                            "intent": "conversion_proxy",
                        },
                        "keywords": ["fashion"],
                        "channels": ["google", "naver_shopping"],
                    }
                ],
            },
            allow_unicode=True,
            sort_keys=False,
        ),
        encoding="utf-8",
    )

    db_path = project_root / "data" / "trendradar.duckdb"
    trend_store.save_trend_points(
        "google",
        "fashion",
        [
            TrendPoint(
                keyword="fashion",
                source="google",
                timestamp=datetime(2026, 4, 15, 8, 0, tzinfo=UTC),
                value=55.0,
                metadata={"set_name": "Fashion"},
            )
        ],
        metadata={"set_name": "Fashion"},
        db_path=db_path,
    )
    trend_store.save_trend_points(
        "naver_shopping",
        "fashion",
        [
            TrendPoint(
                keyword="fashion",
                source="naver_shopping",
                timestamp=datetime(2026, 4, 15, 9, 0, tzinfo=UTC),
                value=21.0,
                metadata={"set_name": "Fashion"},
            )
        ],
        metadata={"set_name": "Fashion"},
        db_path=db_path,
    )

    module = _load_script_module()
    paths, report = module.generate_quality_artifacts(project_root)

    assert Path(paths["latest"]).exists()
    assert Path(paths["dated"]).exists()
    assert report["target_date"] == "2026-04-15"
    assert report["summary"]["collected_signal_count"] == 2
    assert report["summary"]["conversion_proxy_signal_count"] == 1

    module.PROJECT_ROOT = project_root
    module.main()
    captured = capsys.readouterr()
    assert "quality_report=" in captured.out
    assert "collected_signal_count=" in captured.out

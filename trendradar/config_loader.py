from __future__ import annotations

from pathlib import Path
from typing import Any, cast

import yaml

from config_loader import load_notification_config
from trendradar.models import RadarSettings, TrendRadarSettings


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def load_settings(config_path: Path | None = None) -> RadarSettings:
    if config_path is None:
        return _resolve_settings(TrendRadarSettings())

    loaded = cast(object, yaml.safe_load(config_path.read_text(encoding="utf-8")))
    data = cast(dict[str, Any], loaded if isinstance(loaded, dict) else {})
    return _resolve_settings(TrendRadarSettings.from_dict(data))


def _resolve_settings(settings: TrendRadarSettings) -> RadarSettings:
    return RadarSettings(
        database_path=_resolve_path(settings.database_path),
        report_dir=_resolve_path(settings.report_dir),
        raw_data_dir=_resolve_path(settings.raw_data_dir),
        search_db_path=_resolve_path(settings.search_db_path),
    )


def _resolve_path(value: str) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path.resolve()
    return (PROJECT_ROOT / path).resolve()


__all__ = ["load_notification_config", "load_settings"]

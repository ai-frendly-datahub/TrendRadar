from __future__ import annotations

import importlib
import sys


_ALIASES = {
    "analyzer": "trendradar.analyzer",
    "collector": "trendradar.collector",
    "exceptions": "trendradar.exceptions",
    "models": "trendradar.models",
    "nl_query": "radar_core.nl_query",
    "reporter": "trendradar.reporter",
    "search_index": "trendradar.search_index",
    "storage": "trendradar.storage",
}


for _name, _target in _ALIASES.items():
    sys.modules[f"{__name__}.{_name}"] = importlib.import_module(_target)


__all__ = sorted(_ALIASES)

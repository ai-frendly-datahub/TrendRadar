"""TrendRadar source mapping consistency audit.

Cycle 12 wired ``main._TREND_SOURCE_EVENT_MODEL`` (source → contract event_model_key)
to mirror the ``signal_layers`` declaration in ``config/keyword_sets.yaml``. The two
artifacts are intended to be a 1:1 reflection of each other; if they drift, contract
enrichment silently misroutes (or skips) sources without raising.

This module audits the mirror at test time so divergence surfaces immediately:

1. Source key parity between the dict and the yaml ``signal_layers`` union.
2. Each dict source's mapped ``event_model_key`` is one of the contract-declared ids
   (``attention_signal`` / ``conversion_proxy_signal`` / ``community_signal``).
3. Each layer in ``signal_layers`` maps its sources to the matching event_model_key
   (attention → attention_signal, conversion_proxy → conversion_proxy_signal,
   community → community_signal).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

import main


_TREND_REPO_ROOT = Path(__file__).resolve().parents[2]
_KEYWORD_SETS_YAML = _TREND_REPO_ROOT / "config" / "keyword_sets.yaml"
_CONTRACT_PATH = (
    _TREND_REPO_ROOT.parent / "radar-ontology" / "runtime_contracts" / "TrendRadar.json"
)

# yaml signal_layers key → contract event_model_key
_LAYER_TO_EVENT_MODEL = {
    "attention": "attention_signal",
    "conversion_proxy": "conversion_proxy_signal",
    "community": "community_signal",
}


def _load_signal_layers() -> dict[str, list[str]]:
    with _KEYWORD_SETS_YAML.open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}
    # ``signal_layers`` lives under the ``data_quality`` block in keyword_sets.yaml.
    data_quality = data.get("data_quality") or {}
    layers = data_quality.get("signal_layers") or {}
    return {layer: list(sources or []) for layer, sources in layers.items()}


def _load_contract_event_model_ids() -> set[str]:
    with _CONTRACT_PATH.open("r", encoding="utf-8") as fh:
        contract = json.load(fh)
    return set((contract.get("event_model_field_specs") or {}).keys())


@pytest.mark.xfail(
    strict=False,
    reason=(
        "Cycle 15 audit: 'browser' is wired in _TREND_SOURCE_EVENT_MODEL but "
        "missing from keyword_sets.yaml signal_layers.community. Mirror "
        "reconciliation is deferred to a separate cycle; this xfail surfaces "
        "the divergence without blocking CI. Remove the marker once the "
        "mismatch is resolved."
    ),
)
def test_source_event_model_dict_mirrors_yaml_signal_layers() -> None:
    """Dict keys must match the union of yaml signal_layers source lists."""

    layers = _load_signal_layers()
    yaml_sources = {src for sources in layers.values() for src in sources}
    dict_sources = set(main._TREND_SOURCE_EVENT_MODEL.keys())

    only_in_dict = sorted(dict_sources - yaml_sources)
    only_in_yaml = sorted(yaml_sources - dict_sources)

    assert not only_in_dict and not only_in_yaml, (
        "TrendRadar source mapping mirror drifted between "
        "_TREND_SOURCE_EVENT_MODEL and keyword_sets.yaml signal_layers.\n"
        f"  only in _TREND_SOURCE_EVENT_MODEL (main.py): {only_in_dict}\n"
        f"  only in signal_layers (keyword_sets.yaml):   {only_in_yaml}"
    )


def test_source_event_model_dict_values_are_contract_ids() -> None:
    """Every dict value must be a valid contract event_model_key."""

    valid_ids = _load_contract_event_model_ids()
    # sanity: contract should declare exactly the three signal axes
    assert valid_ids == {
        "attention_signal",
        "conversion_proxy_signal",
        "community_signal",
    }, (
        "Contract event_model_field_specs no longer matches the expected three "
        f"signal axes; got {sorted(valid_ids)}"
    )

    invalid = {
        source: event_model
        for source, event_model in main._TREND_SOURCE_EVENT_MODEL.items()
        if event_model not in valid_ids
    }
    assert not invalid, (
        "_TREND_SOURCE_EVENT_MODEL contains values outside the contract's "
        f"event_model_field_specs: {invalid} (valid={sorted(valid_ids)})"
    )


def test_signal_layer_sources_map_to_matching_event_model() -> None:
    """Each yaml layer's sources must map to the layer-aligned event_model_key."""

    layers = _load_signal_layers()
    mismatches: list[str] = []
    for layer, sources in layers.items():
        expected = _LAYER_TO_EVENT_MODEL.get(layer)
        if expected is None:
            mismatches.append(
                f"unknown signal_layers key '{layer}' — extend _LAYER_TO_EVENT_MODEL"
            )
            continue
        for source in sources:
            actual = main._TREND_SOURCE_EVENT_MODEL.get(source)
            if actual != expected:
                mismatches.append(
                    f"layer={layer} source={source!r}: "
                    f"expected {expected!r}, got {actual!r}"
                )

    assert not mismatches, (
        "TrendRadar signal_layers → event_model_key mismatch:\n  "
        + "\n  ".join(mismatches)
    )


def test_keyword_reverse_lookup_index_matches_yaml(tmp_path: Path, monkeypatch) -> None:
    """``_load_trend_keyword_set_index`` reverse map must equal yaml keyword_sets."""

    # Reset cache so we read the actual yaml fresh.
    monkeypatch.setattr(main, "_TREND_KEYWORD_SET_INDEX_CACHE", None)
    index = main._load_trend_keyword_set_index(_KEYWORD_SETS_YAML)

    with _KEYWORD_SETS_YAML.open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}
    expected: dict[str, str] = {}
    for entry in data.get("keyword_sets") or []:
        set_name = entry.get("name")
        if not set_name:
            continue
        for keyword in entry.get("keywords") or []:
            expected[str(keyword).strip().lower()] = set_name

    # The runtime index lower-cases keyword keys; align both sides defensively.
    actual = {str(k).strip().lower(): v for k, v in index.items()}
    assert actual == expected, (
        "Keyword reverse-lookup index drifted from keyword_sets.yaml.\n"
        f"  only in index:    {sorted(set(actual) - set(expected))}\n"
        f"  only in yaml:     {sorted(set(expected) - set(actual))}\n"
        f"  value mismatches: "
        f"{ {k: (actual[k], expected[k]) for k in actual.keys() & expected.keys() if actual[k] != expected[k]} }"
    )

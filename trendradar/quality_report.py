from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections.abc import Iterable, Mapping
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

import yaml


DEFAULT_REPORT_NAME = "trend_quality.json"
DEFAULT_EVENT_LIMIT = 200
SCORE_FIELD_BY_EVENT_MODEL = {
    "attention_signal": "attention_score",
    "conversion_proxy_signal": "conversion_proxy_score",
    "community_signal": "community_score",
}


def load_keyword_quality_config(path: Path) -> dict[str, Any]:
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return raw if isinstance(raw, dict) else {}


def build_quality_report(
    keyword_config: dict[str, Any],
    *,
    generated_at: datetime | None = None,
    target_date: date | None = None,
    trend_points: Iterable[Mapping[str, Any]] | None = None,
    event_limit: int = DEFAULT_EVENT_LIMIT,
) -> dict[str, Any]:
    generated_at = generated_at or datetime.now(UTC)
    target_date = target_date or generated_at.date()
    data_quality = _dict_value(keyword_config.get("data_quality"))
    keyword_sets = [
        item for item in keyword_config.get("keyword_sets", []) if isinstance(item, dict)
    ]
    enabled_packs = [item for item in keyword_sets if item.get("enabled", True) is not False]
    signal_layers = _dict_value(data_quality.get("signal_layers"))
    attention_channels = set(_list_of_str(signal_layers.get("attention")))
    conversion_channels = set(_list_of_str(signal_layers.get("conversion_proxy")))
    community_channels = set(_list_of_str(signal_layers.get("community")))
    trend_points_provided = trend_points is not None
    point_rows = [_coerce_point_row(point) for point in (trend_points or [])]
    source_max_values = _source_max_values(point_rows)
    event_contracts = _event_contracts(data_quality)

    base_pack_status = [
        _pack_status(
            pack,
            attention_channels=attention_channels,
            conversion_channels=conversion_channels,
            community_channels=community_channels,
        )
        for pack in keyword_sets
    ]
    pack_lookup = _pack_lookup(enabled_packs)
    keyword_lookup = _keyword_pack_lookup(enabled_packs)
    raw_event_rows = [
        event
        for point in point_rows
        if (
            event := _signal_event(
                point,
                target_date=target_date,
                data_quality=data_quality,
                attention_channels=attention_channels,
                conversion_channels=conversion_channels,
                community_channels=community_channels,
                source_max_values=source_max_values,
                event_contracts=event_contracts,
                pack_lookup=pack_lookup,
                keyword_lookup=keyword_lookup,
            )
        )
    ]
    event_rows = _dedupe_event_rows(raw_event_rows)
    event_rows = sorted(
        event_rows,
        key=lambda row: (
            str(row.get("signal_date") or ""),
            float(row.get("raw_value") or 0.0),
            str(row.get("keyword") or ""),
        ),
        reverse=True,
    )
    limited_events = event_rows[: max(event_limit, 0)]
    pack_status = _attach_pack_event_stats(base_pack_status, event_rows)
    quality_gates = _quality_gates(data_quality, [row for row in pack_status if row["enabled"]])
    daily_review_items = _daily_review_items(
        event_rows=event_rows,
        summary_pack_status=pack_status,
        trend_points_provided=trend_points_provided,
    )

    summary = {
        "priority": data_quality.get("priority", "P1"),
        "primary_motion": data_quality.get("primary_motion", "attention"),
        "configured_pack_count": len(pack_status),
        "enabled_pack_count": len([row for row in pack_status if row["enabled"]]),
        "versioned_pack_coverage": _coverage(
            [row for row in pack_status if row["enabled"]], "has_version"
        ),
        "taxonomy_coverage": _coverage(
            [row for row in pack_status if row["enabled"]], "has_taxonomy"
        ),
        "attention_pack_coverage": _coverage(
            [row for row in pack_status if row["enabled"]], "has_attention_signal"
        ),
        "conversion_proxy_pack_coverage": _coverage(
            [row for row in pack_status if row["enabled"]], "has_conversion_proxy"
        ),
        "community_pack_coverage": _coverage(
            [row for row in pack_status if row["enabled"]], "has_community_signal"
        ),
        "separated_score_axes": _has_separated_score_axes(data_quality),
        "raw_signal_point_count": len(raw_event_rows),
        "collected_signal_count": len(event_rows),
        "attention_signal_count": _count_events(event_rows, "attention_signal"),
        "conversion_proxy_signal_count": _count_events(event_rows, "conversion_proxy_signal"),
        "community_signal_count": _count_events(event_rows, "community_signal"),
        "fresh_signal_count": _count_by_status(event_rows, "fresh"),
        "stale_signal_count": _count_by_status(event_rows, "stale"),
        "undated_signal_count": _count_by_status(event_rows, "undated"),
        "distinct_signal_channel_count": len(
            {str(row.get("channel") or "") for row in event_rows if row.get("channel")}
        ),
        "distinct_keyword_pack_event_count": len(
            {
                str(row.get("keyword_set_name") or "")
                for row in event_rows
                if row.get("keyword_set_name")
            }
        ),
        "unique_signal_key_count": len(
            {str(row.get("signal_key") or "") for row in event_rows if row.get("signal_key")}
        ),
        "signal_required_field_gap_count": sum(
            len(_list_value(row.get("required_field_gaps"))) for row in event_rows
        ),
        "score_axis_contamination_count": _score_axis_contamination_count(event_rows),
        "daily_review_item_count": len(daily_review_items),
        "events_truncated": max(len(event_rows) - len(limited_events), 0),
        "missing_required_components": [
            gate["name"] for gate in quality_gates if gate["status"] == "attention"
        ],
    }

    return {
        "generated_at": generated_at.isoformat(),
        "target_date": target_date.isoformat(),
        "repo": "TrendRadar",
        "summary": summary,
        "signal_layers": data_quality.get("signal_layers", {}),
        "score_axes": data_quality.get("score_axes", {}),
        "normalization": data_quality.get("normalization", {}),
        "pack_status": pack_status,
        "events": limited_events,
        "daily_review_items": daily_review_items,
        "source_backlog": data_quality.get("source_backlog", []),
        "quality_gates": quality_gates,
        "recommendations": _recommendations(summary, data_quality),
    }


def write_quality_report(
    report: dict[str, Any],
    output_dir: Path,
    *,
    target_date: date | None = None,
) -> dict[str, str]:
    target_date = target_date or date.fromisoformat(str(report["target_date"]))
    output_dir.mkdir(parents=True, exist_ok=True)
    latest_path = output_dir / DEFAULT_REPORT_NAME
    dated_path = output_dir / f"trend_{target_date.strftime('%Y%m%d')}_quality.json"
    content = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    latest_path.write_text(content, encoding="utf-8")
    dated_path.write_text(content, encoding="utf-8")
    return {"latest": str(latest_path), "dated": str(dated_path)}


def _pack_status(
    pack: dict[str, Any],
    *,
    attention_channels: set[str],
    conversion_channels: set[str],
    community_channels: set[str],
) -> dict[str, Any]:
    channels = set(_list_of_str(pack.get("channels")))
    taxonomy = _dict_value(pack.get("taxonomy"))
    return {
        "name": str(pack.get("name") or "unknown"),
        "enabled": pack.get("enabled", True) is not False,
        "version": pack.get("version"),
        "taxonomy": taxonomy,
        "keyword_count": len(_list_of_str(pack.get("keywords"))),
        "channels": sorted(channels),
        "attention_channels": sorted(channels & attention_channels),
        "conversion_proxy_channels": sorted(channels & conversion_channels),
        "community_channels": sorted(channels & community_channels),
        "has_version": bool(pack.get("version")),
        "has_taxonomy": bool(taxonomy.get("vertical")) and bool(taxonomy.get("intent")),
        "has_attention_signal": bool(channels & attention_channels),
        "has_conversion_proxy": bool(channels & conversion_channels),
        "has_community_signal": bool(channels & community_channels),
    }


def _quality_gates(
    data_quality: dict[str, Any],
    enabled_status: list[dict[str, Any]],
) -> list[dict[str, str]]:
    gates = [
        (
            "keyword_pack_versioning",
            "enabled keyword packs carry an explicit version",
            bool(enabled_status) and all(row["has_version"] for row in enabled_status),
        ),
        (
            "keyword_pack_taxonomy",
            "enabled keyword packs carry vertical and intent taxonomy",
            bool(enabled_status) and all(row["has_taxonomy"] for row in enabled_status),
        ),
        (
            "attention_layer",
            "at least one enabled pack contains attention-layer channels",
            any(row["has_attention_signal"] for row in enabled_status),
        ),
        (
            "conversion_proxy_layer",
            "at least one enabled pack contains a conversion proxy channel",
            any(row["has_conversion_proxy"] for row in enabled_status),
        ),
        (
            "score_axis_separation",
            "attention and conversion proxy scores are configured as separate axes",
            _has_separated_score_axes(data_quality),
        ),
        (
            "platform_scale_normalization",
            "platform scale normalization policy is documented",
            bool(_dict_value(data_quality.get("normalization"))),
        ),
    ]
    configured_gates = _list_of_str(data_quality.get("quality_gates"))
    results = [
        {
            "name": name,
            "status": "ok" if passed else "attention",
            "description": description,
        }
        for name, description, passed in gates
    ]
    for gate in configured_gates:
        results.append({"name": gate, "status": "documented", "description": gate})
    return results


def _recommendations(summary: dict[str, Any], data_quality: dict[str, Any]) -> list[str]:
    recommendations: list[str] = []
    if summary["versioned_pack_coverage"] < 1.0:
        recommendations.append("Add a version to every enabled keyword pack.")
    if summary["taxonomy_coverage"] < 1.0:
        recommendations.append("Add vertical and intent taxonomy to every enabled keyword pack.")
    if summary["conversion_proxy_pack_coverage"] <= 0.0:
        recommendations.append("Add a shopping, signup, visit, or catalog-interest proxy source.")
    if summary.get("conversion_proxy_signal_count", 0) <= 0:
        recommendations.append("Validate a live conversion proxy source before mixing it with attention.")
    if summary.get("score_axis_contamination_count", 0) > 0:
        recommendations.append("Keep attention, conversion proxy, and community scores on separate axes.")
    if not summary["separated_score_axes"]:
        recommendations.append("Output attention_score and conversion_proxy_score as separate fields.")
    recommendations.extend(str(item) for item in _list_value(data_quality.get("next_actions")))
    return list(dict.fromkeys(recommendations))


def _has_separated_score_axes(data_quality: dict[str, Any]) -> bool:
    score_axes = _dict_value(data_quality.get("score_axes"))
    return bool(score_axes.get("attention")) and bool(score_axes.get("conversion_proxy"))


def _coverage(rows: list[dict[str, Any]], key: str) -> float:
    if not rows:
        return 0.0
    return round(sum(1 for row in rows if row.get(key)) / len(rows), 3)


def _coerce_point_row(point: Mapping[str, Any]) -> dict[str, Any]:
    if isinstance(point, dict):
        return point
    if hasattr(point, "to_dict"):
        raw = point.to_dict()
        return raw if isinstance(raw, dict) else {}
    return dict(point)


def _source_max_values(rows: list[dict[str, Any]]) -> dict[str, float]:
    max_values: dict[str, float] = {}
    for row in rows:
        source = _text(row.get("source") or row.get("platform"))
        value = _float_value(row.get("value") or row.get("score"))
        if not source or value is None:
            continue
        max_values[source] = max(max_values.get(source, 0.0), value)
    return max_values


def _pack_lookup(packs: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {str(pack.get("name") or ""): pack for pack in packs if pack.get("name")}


def _keyword_pack_lookup(packs: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    lookup: dict[str, dict[str, Any]] = {}
    for pack in packs:
        for keyword in _list_of_str(pack.get("keywords")):
            lookup.setdefault(keyword, pack)
    return lookup


def _signal_event(
    point: dict[str, Any],
    *,
    target_date: date,
    data_quality: dict[str, Any],
    attention_channels: set[str],
    conversion_channels: set[str],
    community_channels: set[str],
    source_max_values: dict[str, float],
    event_contracts: dict[str, dict[str, Any]],
    pack_lookup: dict[str, dict[str, Any]],
    keyword_lookup: dict[str, dict[str, Any]],
) -> dict[str, Any] | None:
    channel = _text(point.get("source") or point.get("platform"))
    if not channel:
        return None
    if channel in attention_channels:
        event_model = "attention_signal"
        score_axis = "attention"
    elif channel in conversion_channels:
        event_model = "conversion_proxy_signal"
        score_axis = "conversion_proxy"
    elif channel in community_channels:
        event_model = "community_signal"
        score_axis = "community"
    else:
        return None

    keyword = _text(point.get("keyword"))
    metadata = _dict_value(point.get("metadata"))
    pack_name = _text(metadata.get("set_name"))
    pack = pack_lookup.get(pack_name) or keyword_lookup.get(keyword) or {}
    if not pack_name:
        pack_name = _text(pack.get("name"))
    taxonomy = _dict_value(pack.get("taxonomy"))
    raw_value = _float_value(point.get("value") if "value" in point else point.get("score"))
    normalized_value = _normalized_value(raw_value, source_max_values.get(channel))
    signal_date = _point_date(point)
    freshness_sla = _freshness_sla(data_quality, event_model)
    age_days = (target_date - signal_date).days if signal_date is not None else None
    score_value = normalized_value if normalized_value is not None else raw_value

    row: dict[str, Any] = {
        "event_model": event_model,
        "signal_key": _signal_key(event_model, pack_name, channel, keyword, signal_date),
        "keyword_set_name": pack_name,
        "keyword_pack_version": pack.get("version"),
        "taxonomy": taxonomy,
        "taxonomy_vertical": taxonomy.get("vertical"),
        "taxonomy_intent": taxonomy.get("intent"),
        "keyword": keyword,
        "channel": channel,
        "source": channel,
        "signal_date": signal_date.isoformat() if signal_date is not None else None,
        "raw_value": raw_value,
        "normalized_value": normalized_value,
        "score_axis": score_axis,
        "freshness_sla_days": freshness_sla,
        "age_days": age_days,
        "freshness_status": _freshness_status(age_days, freshness_sla),
        "proxy_type": _proxy_type(channel) if event_model == "conversion_proxy_signal" else None,
        "community": channel if event_model == "community_signal" else None,
        "signal_value": raw_value if event_model == "community_signal" else None,
        "attention_score": score_value if event_model == "attention_signal" else None,
        "conversion_proxy_score": score_value
        if event_model == "conversion_proxy_signal"
        else None,
        "community_score": score_value if event_model == "community_signal" else None,
    }
    row["required_field_gaps"] = _required_field_gaps(row, event_contracts.get(event_model, {}))
    return row


def _event_contracts(data_quality: dict[str, Any]) -> dict[str, dict[str, Any]]:
    event_models = _dict_value(data_quality.get("event_models"))
    return {
        str(name): _dict_value(contract)
        for name, contract in event_models.items()
        if isinstance(contract, dict)
    }


def _required_field_gaps(row: Mapping[str, Any], contract: Mapping[str, Any]) -> list[str]:
    gaps: list[str] = []
    for field_name in _list_of_str(contract.get("required_fields")):
        value = row.get(field_name)
        if value is None or value == "":
            gaps.append(field_name)
    return gaps


def _attach_pack_event_stats(
    pack_status: list[dict[str, Any]],
    event_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    stats_by_pack: dict[str, dict[str, Any]] = {}
    for event in event_rows:
        pack_name = _text(event.get("keyword_set_name"))
        if not pack_name:
            continue
        stats = stats_by_pack.setdefault(
            pack_name,
            {
                "attention_signal_count": 0,
                "conversion_proxy_signal_count": 0,
                "community_signal_count": 0,
                "latest_signal_date": None,
            },
        )
        event_model = _text(event.get("event_model"))
        if event_model in SCORE_FIELD_BY_EVENT_MODEL:
            stats[f"{event_model}_count"] += 1
        signal_date = event.get("signal_date")
        if signal_date and (
            stats["latest_signal_date"] is None or str(signal_date) > str(stats["latest_signal_date"])
        ):
            stats["latest_signal_date"] = signal_date

    enriched: list[dict[str, Any]] = []
    for pack in pack_status:
        stats = stats_by_pack.get(str(pack.get("name") or ""), {})
        enriched.append(
            {
                **pack,
                "attention_signal_count": int(stats.get("attention_signal_count", 0)),
                "conversion_proxy_signal_count": int(
                    stats.get("conversion_proxy_signal_count", 0)
                ),
                "community_signal_count": int(stats.get("community_signal_count", 0)),
                "latest_signal_date": stats.get("latest_signal_date"),
            }
        )
    return enriched


def _dedupe_event_rows(event_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    deduped: dict[str, dict[str, Any]] = {}
    for event in event_rows:
        key = _text(event.get("signal_key"))
        if not key:
            continue
        existing = deduped.get(key)
        if existing is None:
            deduped[key] = {**event, "observation_count": 1}
            continue

        observation_count = int(existing.get("observation_count", 1)) + 1
        current_value = _float_value(event.get("raw_value")) or 0.0
        existing_value = _float_value(existing.get("raw_value")) or 0.0
        if current_value > existing_value:
            deduped[key] = {**event, "observation_count": observation_count}
        else:
            existing["observation_count"] = observation_count
    return list(deduped.values())


def _daily_review_items(
    *,
    event_rows: list[dict[str, Any]],
    summary_pack_status: list[dict[str, Any]],
    trend_points_provided: bool,
) -> list[dict[str, Any]]:
    review_items: list[dict[str, Any]] = []
    for event in event_rows:
        gaps = _list_value(event.get("required_field_gaps"))
        if gaps:
            review_items.append(
                {
                    "reason": "missing_required_fields",
                    "event_model": event.get("event_model"),
                    "signal_key": event.get("signal_key"),
                    "keyword_set_name": event.get("keyword_set_name"),
                    "keyword": event.get("keyword"),
                    "channel": event.get("channel"),
                    "required_field_gaps": gaps,
                }
            )
        if event.get("freshness_status") == "stale":
            review_items.append(
                {
                    "reason": "stale_signal",
                    "event_model": event.get("event_model"),
                    "signal_key": event.get("signal_key"),
                    "keyword_set_name": event.get("keyword_set_name"),
                    "channel": event.get("channel"),
                    "age_days": event.get("age_days"),
                    "freshness_sla_days": event.get("freshness_sla_days"),
                }
            )

    if trend_points_provided and not event_rows:
        review_items.append(
            {
                "reason": "no_quality_signals_observed",
                "event_model": None,
                "detail": "No trend points matched configured attention, conversion, or community layers.",
            }
        )

    has_configured_conversion = any(row.get("has_conversion_proxy") for row in summary_pack_status)
    has_observed_conversion = any(
        row.get("event_model") == "conversion_proxy_signal" for row in event_rows
    )
    if trend_points_provided and has_configured_conversion and not has_observed_conversion:
        review_items.append(
            {
                "reason": "conversion_proxy_no_observed_signal",
                "event_model": "conversion_proxy_signal",
                "detail": "Conversion proxy is configured but no live proxy rows were observed.",
            }
        )

    return review_items[:50]


def _count_events(rows: list[dict[str, Any]], event_model: str) -> int:
    return sum(1 for row in rows if row.get("event_model") == event_model)


def _count_by_status(rows: list[dict[str, Any]], status: str) -> int:
    return sum(1 for row in rows if row.get("freshness_status") == status)


def _score_axis_contamination_count(rows: list[dict[str, Any]]) -> int:
    score_fields = tuple(SCORE_FIELD_BY_EVENT_MODEL.values())
    return sum(1 for row in rows if sum(row.get(field) is not None for field in score_fields) > 1)


def _point_date(point: Mapping[str, Any]) -> date | None:
    timestamp = point.get("timestamp") or point.get("date")
    if isinstance(timestamp, datetime):
        return timestamp.astimezone(UTC).date() if timestamp.tzinfo else timestamp.date()
    if isinstance(timestamp, date):
        return timestamp
    if isinstance(timestamp, str):
        text = timestamp.strip()
        if not text:
            return None
        try:
            return datetime.fromisoformat(text.replace("Z", "+00:00")).date()
        except ValueError:
            try:
                return date.fromisoformat(text[:10])
            except ValueError:
                return None
    return None


def _freshness_sla(data_quality: dict[str, Any], event_model: str) -> int:
    freshness_sla = _dict_value(data_quality.get("freshness_sla"))
    raw = freshness_sla.get(f"{event_model}_days")
    try:
        return int(raw)
    except (TypeError, ValueError):
        return 7


def _freshness_status(age_days: int | None, sla_days: int) -> str:
    if age_days is None:
        return "undated"
    if age_days <= sla_days:
        return "fresh"
    return "stale"


def _normalized_value(value: float | None, source_max: float | None) -> float | None:
    if value is None or not source_max or source_max <= 0:
        return None
    return round((value / source_max) * 100.0, 3)


def _proxy_type(channel: str) -> str:
    if "shopping" in channel:
        return "shopping_interest"
    if "signup" in channel:
        return "signup_interest"
    if "visit" in channel:
        return "visit_interest"
    return "conversion_proxy"


def _signal_key(
    event_model: str,
    pack_name: str,
    channel: str,
    keyword: str,
    signal_date: date | None,
) -> str:
    return ":".join(
        [
            event_model,
            _slug(pack_name or "unknown-pack"),
            _slug(channel or "unknown-channel"),
            _slug(keyword or "unknown-keyword"),
            signal_date.isoformat() if signal_date else "undated",
        ]
    )


def _slug(value: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "-", value.lower())
    slug = normalized.strip("-")
    if slug:
        return slug
    digest = hashlib.sha1(value.encode("utf-8")).hexdigest()[:12]
    return f"u-{digest}"


def _float_value(value: Any) -> float | None:
    if isinstance(value, bool):
        return float(value)
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value)
        except ValueError:
            return None
    return None


def _text(value: Any) -> str:
    return str(value).strip() if value is not None else ""


def _dict_value(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _list_value(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _list_of_str(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value]


def _query_trend_points_for_cli(db_path: Path, target_date: date) -> list[Mapping[str, Any]]:
    try:
        from storage import trend_store

        start_date = target_date.replace(day=1).isoformat()
        end_date = target_date.isoformat()
        return trend_store.query_trend_points(
            start_date=start_date,
            end_date=end_date,
            db_path=db_path,
        )
    except Exception:
        return []


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Generate TrendRadar data quality report")
    parser.add_argument("--config", type=Path, default=Path("config/keyword_sets.yaml"))
    parser.add_argument("--output-dir", type=Path, default=Path("docs/reports"))
    parser.add_argument("--date", dest="target_date", default=None, help="YYYY-MM-DD")
    parser.add_argument("--db-path", type=Path, default=None)
    args = parser.parse_args(argv)

    target_date = date.fromisoformat(args.target_date) if args.target_date else None
    config = load_keyword_quality_config(args.config)
    trend_points = (
        _query_trend_points_for_cli(args.db_path, target_date or datetime.now(UTC).date())
        if args.db_path is not None
        else None
    )
    report = build_quality_report(config, target_date=target_date, trend_points=trend_points)
    paths = write_quality_report(report, args.output_dir, target_date=target_date)
    print(json.dumps(paths, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()

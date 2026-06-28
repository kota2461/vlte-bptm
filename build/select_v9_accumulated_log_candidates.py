"""Select usable V9 candidates from accumulated non-sealed debate logs.

This is a selection/indexing step only. Raw LLM debate text remains evidence,
not training data. Selected rows must be rewritten into short self-contained
non-sealed samples and human-reviewed before any fixture or gate use.
"""

import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SOURCE_PRIORITY = ROOT / "build" / "v8_recovery_debate_candidate_priority_selection_v1.json"
V8_MEASUREMENT = ROOT / "build" / "pattern_language_sealed_v8_measurement_report.json"
OUTPUT = ROOT / "build" / "v9_accumulated_log_candidate_selection_v1.json"
WORKSHEET = ROOT / "build" / "v9_accumulated_log_candidate_selection_v1.md"

POLICY = {
    "sealed_fixtures_used_as_sources": False,
    "sealed_text_used": False,
    "sealed_labels_used": False,
    "raw_debate_logs_direct_training_allowed": False,
    "llm_turn_text_direct_training_allowed": False,
    "selection_is_training_data": False,
    "human_rewrite_required_before_fixture_adoption": True,
    "human_review_required_before_gate": True,
    "same_cycle_gate_use_allowed": False,
}

PRIMARY_QUOTAS = {
    "current_search_split": 5,
    "multiple_intents": 5,
    "operation_terminal": 5,
    "constraints": 5,
    "risk_ladder": 5,
    "missing_info": 3,
    "unverified_claim": 2,
    "false_positive": 2,
    "mixed_language": 1,
    "paraphrase": 1,
}

CATEGORY_WEIGHTS = {
    "current_search_split": 48,
    "multiple_intents": 44,
    "operation_terminal": 42,
    "constraints": 40,
    "risk_ladder": 40,
    "missing_info": 30,
    "unverified_claim": 24,
    "false_positive": 22,
    "mixed_language": 14,
    "paraphrase": 14,
}

V8_ERROR_FIELD_TO_CATEGORIES = {
    "information_state": {"current_search_split", "multiple_intents", "missing_info", "unverified_claim"},
    "operations": {"operation_terminal", "multiple_intents", "current_search_split", "unverified_claim"},
    "constraints": {"constraints", "operation_terminal", "false_positive"},
    "risk": {"risk_ladder", "false_positive", "current_search_split", "unverified_claim"},
    "primary_intent": {"multiple_intents", "paraphrase", "mixed_language"},
}

CRITICAL_SIGNAL_WEIGHTS = {
    "requires_current_information": {"current_search_split": 18},
    "multiple_intents": {"multiple_intents": 14, "operation_terminal": 4},
    "missing_required_information": {"missing_info": 4},
    "contains_unverified_claims": {"unverified_claim": 4},
}

CATEGORY_NOTES = {
    "current_search_split": "V8 critical recall was weakest for requires_current_information; keep local/current vs web-current minimal pairs.",
    "multiple_intents": "V8 still missed one multiple-intent signal; preserve vertical order and terminal action.",
    "operation_terminal": "Operation exact match remains below target; focus on final action and operation ordering.",
    "constraints": "Constraint exact match remains below target; preserve short/no-table/neutrality style controls.",
    "risk_ladder": "Risk exact match remains below target; calibrate low/medium/high without overfiring.",
    "missing_info": "Information-state errors remain; keep ask-first boundaries but avoid over-clarifying.",
    "unverified_claim": "Critical recall passed, but information/risk/operation mismatches still benefit from examples.",
    "false_positive": "Useful for low-risk sensitive-word contrast so risk/verify does not overfire.",
    "mixed_language": "Lower priority now; keep as robustness reserve.",
    "paraphrase": "Lower priority now; keep as surface-variant reserve.",
}

REFERENCE_LOGS = [
    {
        "source": "build/v7_router_debate_candidate_selection_v1.json",
        "recommended_use": "reference_only_or_backfill",
        "reason": "already used as V7/V8 repair context; do not duplicate before reviewing overlap",
    },
    {
        "source": "build/v6_structural_build_30_candidate_queue_v1.json",
        "recommended_use": "reference_only",
        "reason": "structural build set has already been adopted into earlier non-sealed repair lanes",
    },
    {
        "source": "build/v6_boundary_debate_candidate_queue_v1.json",
        "recommended_use": "reference_only_or_negative_contrast_backfill",
        "reason": "older boundary queue is useful for taxonomy examples but likely overlaps adopted V6 material",
    },
]


def _load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def _category(record: dict[str, Any]) -> str:
    return str(record.get("category", "unknown"))


def _v8_error_field_counts(measurement: dict[str, Any]) -> Counter[str]:
    counts: Counter[str] = Counter()
    for error in measurement["measurements"].get("errors", []):
        counts.update(error.get("fields", []))
    return counts


def _critical_miss_counts(measurement: dict[str, Any]) -> dict[str, int]:
    signals = measurement["measurements"].get("critical_signals", {})
    return {
        name: int(round(float(data.get("support", 0)) * (1.0 - float(data.get("recall", 0.0)))))
        for name, data in signals.items()
    }


def _category_error_boost(category: str, field_counts: Counter[str], critical_misses: dict[str, int]) -> int:
    boost = 0
    for field, count in field_counts.items():
        if category in V8_ERROR_FIELD_TO_CATEGORIES.get(field, set()):
            boost += int(count) * 3
    for signal, categories in CRITICAL_SIGNAL_WEIGHTS.items():
        miss_count = critical_misses.get(signal, 0)
        boost += int(categories.get(category, 0)) * miss_count
    return boost


def _selection_score(record: dict[str, Any], field_counts: Counter[str], critical_misses: dict[str, int]) -> int:
    category = _category(record)
    base = int(record.get("selection_score", 0))
    score = base + CATEGORY_WEIGHTS.get(category, 0)
    score += _category_error_boost(category, field_counts, critical_misses)
    if record.get("length_finish"):
        score -= 12
    return score


def _compact(record: dict[str, Any], bucket: str, rank: int | None, field_counts: Counter[str], critical_misses: dict[str, int]) -> dict[str, Any]:
    category = _category(record)
    return {
        "id": record["id"],
        "selection_bucket": bucket,
        "priority_rank": rank,
        "source_topic_id": record.get("source_topic_id", ""),
        "category": category,
        "v9_selection_score": _selection_score(record, field_counts, critical_misses),
        "source_selection_score": record.get("selection_score", 0),
        "source_review_bucket": record.get("review_bucket", ""),
        "theme": record.get("theme", ""),
        "axis_ids": record.get("axis_ids", []),
        "completed_rounds": record.get("completed_rounds", 0),
        "content_chars": record.get("content_chars", 0),
        "length_finish": bool(record.get("length_finish")),
        "length_finish_details": record.get("length_finish_details", []),
        "router_packet_hint": record.get("router_packet_hint", {}),
        "desired_discussion": record.get("desired_discussion", []),
        "v9_use_note": CATEGORY_NOTES.get(category, "Use only after human rewrite and review."),
        "rewrite_instruction": "Rewrite into a short self-contained non-sealed sample; do not copy raw LLM prose.",
        "training_status": "not_training_data",
        "allowed_use": "human_review_and_rewrite_only",
    }


def build_selection() -> dict[str, Any]:
    priority = _load(SOURCE_PRIORITY)
    measurement = _load(V8_MEASUREMENT)
    field_counts = _v8_error_field_counts(measurement)
    critical_misses = _critical_miss_counts(measurement)

    already_used = list(priority.get("priority_review", []))
    ready_pool = list(priority.get("reserve_review", []))
    rerun_pool = list(priority.get("hold_for_rerun", []))

    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in ready_pool:
        grouped[_category(record)].append(record)

    primary_raw: list[dict[str, Any]] = []
    primary_ids: set[str] = set()
    deficits: dict[str, int] = {}
    for category, quota in PRIMARY_QUOTAS.items():
        ordered = sorted(
            grouped.get(category, []),
            key=lambda item: (-_selection_score(item, field_counts, critical_misses), str(item.get("source_topic_id", ""))),
        )
        selected = ordered[:quota]
        deficits[category] = max(0, quota - len(selected))
        for item in selected:
            primary_ids.add(item["id"])
            primary_raw.append(item)

    primary_raw.sort(key=lambda item: (-_selection_score(item, field_counts, critical_misses), _category(item), str(item.get("source_topic_id", ""))))
    primary_review = [
        _compact(record, "primary_review", index, field_counts, critical_misses)
        for index, record in enumerate(primary_raw, start=1)
    ]

    reserve_raw = [record for record in ready_pool if record["id"] not in primary_ids]
    reserve_raw.sort(key=lambda item: (-_selection_score(item, field_counts, critical_misses), _category(item), str(item.get("source_topic_id", ""))))
    reserve_review = [_compact(record, "reserve_review", None, field_counts, critical_misses) for record in reserve_raw]

    rerun_pool.sort(key=lambda item: (-_selection_score(item, field_counts, critical_misses), _category(item), str(item.get("source_topic_id", ""))))
    rerun_before_use = [_compact(record, "rerun_before_use", None, field_counts, critical_misses) for record in rerun_pool]

    already_used_records = [
        {
            "id": record["id"],
            "source_topic_id": record.get("source_topic_id", ""),
            "category": _category(record),
            "reason": "already used in V8 priority review/adoption path; do not reselect as fresh V9 material",
        }
        for record in already_used
    ]

    summary = {
        "source_candidate_count": priority["summary"]["source_candidate_count"],
        "already_used_v8_priority_count": len(already_used_records),
        "ready_pool_count": len(ready_pool),
        "primary_review_count": len(primary_review),
        "rerun_before_use_count": len(rerun_before_use),
        "reserve_review_count": len(reserve_review),
        "field_error_counts_from_v8": dict(sorted(field_counts.items())),
        "critical_miss_counts_from_v8": dict(sorted(critical_misses.items())),
        "primary_category_counts": dict(sorted(Counter(item["category"] for item in primary_review).items())),
        "rerun_category_counts": dict(sorted(Counter(item["category"] for item in rerun_before_use).items())),
        "reserve_category_counts": dict(sorted(Counter(item["category"] for item in reserve_review).items())),
        "category_deficits": {key: value for key, value in sorted(deficits.items()) if value},
    }

    return {
        "schema_version": "v9-accumulated-log-candidate-selection.v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": "accumulated_log_candidates_selected_for_v9_review",
        "sources": {
            "source_priority_selection": "build/v8_recovery_debate_candidate_priority_selection_v1.json",
            "source_debate_log": priority.get("source_log", ""),
            "v8_measurement_report": "build/pattern_language_sealed_v8_measurement_report.json",
        },
        "policy": POLICY,
        "selection_rules": {
            "exclude_already_used_v8_priority_review": True,
            "primary_quotas": PRIMARY_QUOTAS,
            "category_weights": CATEGORY_WEIGHTS,
            "rerun_length_finish_before_use": True,
            "raw_llm_text_is_training_data": False,
            "human_rewrite_required": True,
        },
        "summary": summary,
        "reference_logs": REFERENCE_LOGS,
        "primary_review": primary_review,
        "rerun_before_use": rerun_before_use,
        "reserve_review": reserve_review,
        "already_used_excluded": already_used_records,
    }


def write_worksheet(selection: dict[str, Any]) -> None:
    lines = [
        "# V9 Accumulated Log Candidate Selection v1",
        "",
        "Raw debate logs are not training data. The rows below are review targets for human rewrite into short non-sealed samples.",
        "",
        "## Summary",
        "",
    ]
    for key, value in selection["summary"].items():
        lines.append(f"- {key}: {value}")

    lines.extend([
        "",
        "## Primary Review",
        "",
        "| rank | id | category | v9 score | source topic | source bucket | length finish | note |",
        "|---:|---|---|---:|---|---|---|---|",
    ])
    for row in selection["primary_review"]:
        note = row["v9_use_note"].replace("|", "&#124;")
        lines.append(
            f"| {row['priority_rank']} | {row['id']} | {row['category']} | {row['v9_selection_score']} | "
            f"{row['source_topic_id']} | {row['source_review_bucket']} | {row['length_finish']} | {note} |"
        )

    lines.extend([
        "",
        "## Rerun Before Use",
        "",
        "These were usable but had length-finish turns. Rerun or manually inspect before rewrite.",
        "",
        "| id | category | v9 score | source topic | length turns |",
        "|---|---|---:|---|---|",
    ])
    for row in selection["rerun_before_use"]:
        length_turns = ", ".join(f"{item.get('role', '')}@{item.get('turn_index', '')}" for item in row["length_finish_details"])
        lines.append(f"| {row['id']} | {row['category']} | {row['v9_selection_score']} | {row['source_topic_id']} | {length_turns} |")

    lines.extend([
        "",
        "## Reserve Review",
        "",
        "Reserve rows are usable but lower priority for the V9 recovery target.",
        "",
        "| id | category | v9 score | source topic |",
        "|---|---|---:|---|",
    ])
    for row in selection["reserve_review"][:40]:
        lines.append(f"| {row['id']} | {row['category']} | {row['v9_selection_score']} | {row['source_topic_id']} |")
    if len(selection["reserve_review"]) > 40:
        lines.append(f"| ... | ... | ... | {len(selection['reserve_review']) - 40} more reserve rows in JSON |")

    lines.extend([
        "",
        "## Reference Logs",
        "",
        "| source | use | reason |",
        "|---|---|---|",
    ])
    for row in selection["reference_logs"]:
        lines.append(f"| {row['source']} | {row['recommended_use']} | {row['reason']} |")

    lines.extend([
        "",
        "## Review Instructions",
        "",
        "- Rewrite selected material into short self-contained non-sealed samples; do not copy raw LLM prose.",
        "- Keep positive/negative contrast pairs when the source topic is about false positives, risk ladders, or current/search split.",
        "- Prioritize fields that failed V8: information_state, operations, constraints, and risk.",
        "- Do not use this selection as a gate until human approval creates a fixture from it.",
    ])
    WORKSHEET.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def main() -> None:
    selection = build_selection()
    _write_json(OUTPUT, selection)
    write_worksheet(selection)
    print(json.dumps({
        "status": selection["status"],
        "output": str(OUTPUT.relative_to(ROOT)),
        "worksheet": str(WORKSHEET.relative_to(ROOT)),
        "summary": selection["summary"],
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

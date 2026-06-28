"""Prepare V4 failure-memory adoption inputs from non-sealed sources."""

import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SUSPECT_REVIEW = ROOT / "build" / "intent_corpus_suspect_review_v1.json"
SUSPECT_PROBE = ROOT / "build" / "probe_without_suspect_corpus_v1.json"
CRITICAL_CANDIDATES = ROOT / "build" / "critical_constraints_candidates_v1.json"
V3_MEASUREMENT = ROOT / "build" / "pattern_language_sealed_v3_measurement_report.json"
OUTPUT_JSON = ROOT / "build" / "v4_failure_memory_adoption_v1.json"
OUTPUT_WORKSHEET = ROOT / "build" / "v4_failure_memory_review_worksheet_v1.md"


def _load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def _suspect_item(raw: dict[str, Any], lane: str) -> dict[str, Any]:
    return {
        "source": "intent_corpus_suspect_review",
        "source_path": _rel(SUSPECT_REVIEW),
        "source_index": raw.get("corpus_index", raw.get("harvest_index")),
        "old_intent": raw.get("intent"),
        "flags": raw.get("flags", []),
        "recommendation": raw.get("recommendation"),
        "lane": lane,
        "allowed_use": "failure_memory_or_negative_calibration",
        "review_status": "pending",
        "input": raw.get("input"),
    }


def _miss_item(raw: dict[str, Any]) -> dict[str, Any]:
    actual = raw["actual"]
    expected = raw["expected"]
    return {
        "source": "suspect_ablation_accumulation_miss",
        "source_path": _rel(SUSPECT_PROBE),
        "case_id": raw["id"],
        "category": raw["category"],
        "expected_intent": expected["intent"],
        "actual_intent": actual["intent"],
        "expected_processing_class": expected["processing_class"],
        "actual_processing_class": actual["processing_class"],
        "expected_core_mode": expected["core_mode"],
        "actual_core_mode": actual["core_mode"],
        "lane": "nonsealed_regression",
        "allowed_use": "regression_replay_and_failure_memory",
        "review_status": "pending",
    }


def _critical_ref(raw: dict[str, Any]) -> dict[str, Any]:
    return {
        "source": "critical_constraints_candidates",
        "source_path": _rel(CRITICAL_CANDIDATES),
        "id": raw["id"],
        "priority": raw["priority"],
        "score": raw["score"],
        "review_focus": raw["review_focus"],
        "reason_tags": raw["reason_tags"],
        "draft_intent": raw["draft_expected"]["primary_intent"],
        "lane": "critical_constraints_review",
        "allowed_use": "human_review_then_failure_memory_or_relabel_candidate",
        "review_status": raw["review_status"],
    }


def _v3_error_ref(raw: dict[str, Any]) -> dict[str, Any]:
    return {
        "source": "v3_sealed_measurement_error_taxonomy",
        "source_path": _rel(V3_MEASUREMENT),
        "id": raw["id"],
        "expected_intent": raw["expected_intent"],
        "predicted_intent": raw["predicted_intent"],
        "fields": raw["fields"],
        "allowed_use": "error_taxonomy_only_no_sealed_text_for_training",
    }


def _lane_for_suspect(raw: dict[str, Any]) -> str:
    recommendation = raw.get("recommendation")
    flags = set(raw.get("flags", []))
    if recommendation == "exclude_or_negative":
        return "negative_calibration"
    if recommendation == "exclude_or_relabel_clarify":
        return "clarify_relabel_guard"
    if "very_short_le_8" in flags:
        return "low_confidence_short_text"
    if "weak_question_suffix" in flags:
        return "weak_question_suffix_guard"
    if "path_or_url" in flags or "bare_path_or_url" in flags:
        return "path_url_guard"
    return "manual_review"


def main() -> None:
    suspect = _load(SUSPECT_REVIEW)
    probe = _load(SUSPECT_PROBE)
    critical = _load(CRITICAL_CANDIDATES)
    v3 = _load(V3_MEASUREMENT)

    suspect_items = [
        _suspect_item(item, _lane_for_suspect(item))
        for item in suspect["high_priority_review"]
    ]
    suspect_items.extend(
        _suspect_item(item, "excluded_reference")
        for item in suspect["excluded_reference_rows"]
    )
    ablation_misses = [
        _miss_item(item)
        for item in probe["accumulation_route_eval"]["misses"]
    ]
    critical_ab = [
        item
        for item in critical["candidates"]
        if item["priority"] in {"A", "B"}
    ]
    critical_refs = [_critical_ref(item) for item in critical_ab[:60]]
    v3_errors = [_v3_error_ref(item) for item in v3["measurements"]["errors"]]

    lane_counts = Counter(item["lane"] for item in suspect_items)
    lane_counts.update(item["lane"] for item in ablation_misses)
    lane_counts.update(item["lane"] for item in critical_refs)

    v3_field_counts = Counter()
    for item in v3_errors:
        v3_field_counts.update(item["fields"])

    payload = {
        "schema_version": "v4-failure-memory-adoption.v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": "draft_for_human_review",
        "policy": {
            "sealed_fixtures_used_as_sources": False,
            "v3_sealed_text_used_for_training": False,
            "v3_sealed_errors_used_as_taxonomy_only": True,
            "success_pattern_lane_write_allowed": False,
            "requires_human_review_before_training": True,
            "same_cycle_promotion_allowed": False,
        },
        "v4_targets": {
            "intent_accuracy_min": 0.90,
            "intent_accuracy_stretch": 0.93,
            "critical_signal_recall_min": 0.85,
            "critical_signal_recall_stretch": 0.90,
            "operation_exact_match_min": 0.90,
            "constraint_exact_match_min": 0.92,
            "risk_exact_match_min": 0.95,
            "sealed_error_count_max": 4,
            "critical_underprocessing_max": 0,
        },
        "sources": [
            {
                "name": "intent_corpus_suspect_review",
                "path": _rel(SUSPECT_REVIEW),
                "sealed": False,
                "total_suspects": suspect["summary"]["suspect_count"],
                "high_priority_review_count": suspect["summary"]["high_priority_review_count"],
                "by_recommendation": suspect["summary"]["by_recommendation"],
                "by_flag": suspect["summary"]["by_flag"],
            },
            {
                "name": "suspect_ablation_probe",
                "path": _rel(SUSPECT_PROBE),
                "sealed": False,
                "miss_count": len(ablation_misses),
                "critical_underprocessing": probe["accumulation_route_eval"]["critical_underprocessing"],
            },
            {
                "name": "critical_constraints_candidates",
                "path": _rel(CRITICAL_CANDIDATES),
                "sealed": False,
                "candidate_count": critical["summary"]["candidate_count"],
                "review_candidate_count": critical["summary"]["review_candidate_count"],
                "priority_a": critical["summary"]["by_priority"].get("A", 0),
                "priority_b": critical["summary"]["by_priority"].get("B", 0),
                "selected_refs_in_this_file": len(critical_refs),
            },
            {
                "name": "v3_sealed_measurement_error_taxonomy",
                "path": _rel(V3_MEASUREMENT),
                "sealed": True,
                "used_as_source": False,
                "taxonomy_only": True,
                "error_count": len(v3_errors),
                "error_field_counts": dict(sorted(v3_field_counts.items())),
            },
        ],
        "adoption_lanes": {
            "negative_calibration": {
                "purpose": "teach what not to reinforce as success patterns",
                "write_target": "failure_memory",
            },
            "clarify_relabel_guard": {
                "purpose": "catch path/url, missing-target, and underspecified cases before respond fallback",
                "write_target": "failure_memory_or_relabel_candidate",
            },
            "low_confidence_short_text": {
                "purpose": "avoid overlearning ambiguous short utterances",
                "write_target": "confidence_guard",
            },
            "weak_question_suffix_guard": {
                "purpose": "route weak '??????' style prompts by context instead of suffix alone",
                "write_target": "failure_memory",
            },
            "critical_constraints_review": {
                "purpose": "improve critical signals, operations, constraints, and risk without sealed text",
                "write_target": "review_then_candidate_fixture",
            },
            "nonsealed_regression": {
                "purpose": "keep old accumulation misses as regression targets",
                "write_target": "regression_replay",
            },
            "puzzle_failure_memory": {
                "purpose": "record puzzle solve failures as guard actions, not success labels",
                "write_target": "puzzle_failure_memory_v1",
            },
        },
        "summary": {
            "suspect_review_items": len(suspect_items),
            "ablation_miss_items": len(ablation_misses),
            "critical_candidate_refs": len(critical_refs),
            "v3_error_taxonomy_items": len(v3_errors),
            "lane_counts": dict(sorted(lane_counts.items())),
        },
        "items": {
            "suspect_review": suspect_items,
            "ablation_misses": ablation_misses,
            "critical_candidate_refs": critical_refs,
            "v3_error_taxonomy": v3_errors,
        },
        "sequence": [
            {
                "step": 1,
                "name": "adoption_registry_and_roadmap",
                "status": "completed_by_this_script",
            },
            {
                "step": 2,
                "name": "human_review_failure_memory_candidates",
                "status": "next",
            },
            {
                "step": 3,
                "name": "create_failure_memory_fixture_v1",
                "status": "pending",
            },
            {
                "step": 4,
                "name": "nonsealed_route_replay",
                "status": "pending",
            },
            {
                "step": 5,
                "name": "implement_guard_or_relabel_changes",
                "status": "pending",
            },
            {
                "step": 6,
                "name": "puzzle_task_schema_and_seed_set",
                "status": "pending",
            },
            {
                "step": 7,
                "name": "puzzle_solver_trace_and_failure_memory",
                "status": "pending",
            },
            {
                "step": 8,
                "name": "v4_candidate_eval_and_sealed_rotation",
                "status": "pending",
            },
        ],
    }
    OUTPUT_JSON.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    worksheet_lines = [
        "# V4 Failure Memory Review Worksheet",
        "",
        "Policy: non-sealed sources only. V3 sealed report is taxonomy-only; do not copy sealed text into training.",
        "",
        "## Review Order",
        "",
        "1. High-priority suspect rows: decide negative / clarify relabel / keep-out.",
        "2. Ablation misses: decide regression target and guard action.",
        "3. Critical A/B refs: approve only after human review of expected packet.",
        "4. Puzzle failure lane: add after schema is created; keep failures separate from success patterns.",
        "",
        "## Summary",
        "",
        f"- suspect review items: {len(suspect_items)}",
        f"- ablation misses: {len(ablation_misses)}",
        f"- critical candidate refs included: {len(critical_refs)} / {len(critical_ab)} A+B",
        f"- V3 error taxonomy items: {len(v3_errors)}",
        "",
        "## V3 Error Taxonomy (No Sealed Text)",
        "",
    ]
    for item in v3_errors:
        worksheet_lines.append(
            f"- {item['id']}: {item['expected_intent']} -> {item['predicted_intent']} / {', '.join(item['fields'])}"
        )
    worksheet_lines.extend(["", "## High Priority Suspect Items", ""])
    for item in suspect_items:
        worksheet_lines.append(
            f"- source_index={item['source_index']} lane={item['lane']} old_intent={item['old_intent']} recommendation={item['recommendation']} flags={','.join(item['flags'])}"
        )
    worksheet_lines.extend(["", "## Ablation Misses", ""])
    for item in ablation_misses:
        worksheet_lines.append(
            f"- {item['case_id']} {item['expected_intent']} -> {item['actual_intent']} / {item['expected_processing_class']} -> {item['actual_processing_class']}"
        )
    worksheet_lines.extend(["", "## Critical Candidate Refs (First 60 A/B)", ""])
    for item in critical_refs:
        worksheet_lines.append(
            f"- {item['id']} priority={item['priority']} score={item['score']} intent={item['draft_intent']} focus={','.join(item['review_focus'])}"
        )
    OUTPUT_WORKSHEET.write_text("\n".join(worksheet_lines) + "\n", encoding="utf-8")

    print(json.dumps({
        "json": _rel(OUTPUT_JSON),
        "worksheet": _rel(OUTPUT_WORKSHEET),
        "summary": payload["summary"],
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

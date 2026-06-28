"""Create the V5 non-sealed curriculum plan.

This is Step 2 of the PLM V5 roadmap. It uses the sealed-v4 measurement only
through the already-sanitized taxonomy in build/v5_targets_and_roadmap_v1.json;
no sealed input text or labels are copied into curriculum data.
"""

import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List


ROOT = Path(__file__).resolve().parents[1]
TARGETS_PATH = ROOT / "build" / "v5_targets_and_roadmap_v1.json"
CANDIDATES_PATH = ROOT / "build" / "critical_constraints_candidates_v1.json"
FAILURE_MEMORY_PATH = ROOT / "tests" / "fixtures" / "v4_failure_memory_fixture_v1.json"
PUZZLE_FAILURE_PATH = ROOT / "tests" / "fixtures" / "v4_puzzle_failure_memory_v1.json"
QUARANTINE_PATH = ROOT / "data" / "intent_training_corpus_quarantine_v1.json"
OUT_JSON = ROOT / "build" / "v5_nonsealed_curriculum_plan_v1.json"
OUT_MD = ROOT / "build" / "v5_nonsealed_curriculum_plan_v1.md"


AXES = [
    {
        "id": "v5-axis-01",
        "name": "multiple_intent_preservation",
        "priority": 1,
        "sealed_v4_taxonomy_fields": ["information_state", "operations"],
        "target_signals": ["multiple_intents"],
        "target_operations": ["verify", "search", "compare", "calculate", "build", "summarize"],
        "review_requirements": [
            "preserve every independent user deliverable",
            "emit operations in execution order",
            "do not collapse verify_then_build or verify_then_summarize into respond",
        ],
        "min_fixture_cases": 12,
        "gate_expectations": {
            "critical_signal_recall": 0.95,
            "operation_exact_match": 0.95,
        },
    },
    {
        "id": "v5-axis-02",
        "name": "missing_info_and_clarify_boundary",
        "priority": 2,
        "sealed_v4_taxonomy_fields": ["primary_intent", "information_state", "constraints", "operations"],
        "target_signals": ["missing_required_information"],
        "target_operations": ["clarify"],
        "review_requirements": [
            "route underspecified requests to clarify",
            "preserve ask_first when the user requests a question before action",
            "separate lightweight chit-chat from genuine missing artifact/context",
        ],
        "min_fixture_cases": 10,
        "gate_expectations": {
            "critical_signal_recall": 0.95,
            "intent_accuracy": 0.95,
        },
    },
    {
        "id": "v5-axis-03",
        "name": "current_unverified_verification",
        "priority": 3,
        "sealed_v4_taxonomy_fields": ["information_state", "operations", "risk"],
        "target_signals": ["contains_unverified_claims", "requires_current_information"],
        "target_operations": ["verify", "search"],
        "review_requirements": [
            "distinguish local/current-context wording from external freshness requirements",
            "require search only for external current facts",
            "mark unverified claims without turning all ordinary questions into verify",
        ],
        "min_fixture_cases": 10,
        "gate_expectations": {
            "critical_signal_recall": 0.95,
            "risk_exact_match": 0.95,
        },
    },
    {
        "id": "v5-axis-04",
        "name": "constraint_preservation",
        "priority": 4,
        "sealed_v4_taxonomy_fields": ["constraints"],
        "target_signals": [],
        "target_operations": ["respond", "summarize", "build", "clarify"],
        "review_requirements": [
            "preserve response_length, format, must, and must_not fields",
            "test short/json/bullets/no_table/ask_first independently and in combinations",
            "constraints must not be dropped when intent is otherwise correct",
        ],
        "min_fixture_cases": 12,
        "gate_expectations": {
            "constraint_exact_match": 0.95,
        },
    },
    {
        "id": "v5-axis-05",
        "name": "operation_sequence_exactness",
        "priority": 5,
        "sealed_v4_taxonomy_fields": ["operations"],
        "target_signals": ["multiple_intents"],
        "target_operations": ["clarify", "calculate", "verify", "search", "compare", "explore"],
        "review_requirements": [
            "operations must include required helper actions without adding unrelated ones",
            "calculate must fire for arithmetic, not dates/paths/issue numbers",
            "explore/compare should remain distinct from plain explain/respond",
        ],
        "min_fixture_cases": 16,
        "gate_expectations": {
            "operation_exact_match": 0.95,
        },
    },
    {
        "id": "v5-axis-06",
        "name": "intent_boundary_repair",
        "priority": 6,
        "sealed_v4_taxonomy_fields": ["primary_intent", "operations"],
        "target_signals": [],
        "target_operations": ["respond", "explain", "clarify", "verify"],
        "review_requirements": [
            "cover clarify->respond and explain->respond leakage with non-sealed paraphrases",
            "keep simple respond anchors so cleanup does not hollow out everyday responses",
            "use quarantine rows only as negative/guard context, never success-pattern examples",
        ],
        "min_fixture_cases": 8,
        "gate_expectations": {
            "intent_accuracy": 0.95,
        },
    },
    {
        "id": "v5-axis-07",
        "name": "risk_flag_completion",
        "priority": 7,
        "sealed_v4_taxonomy_fields": ["risk", "information_state"],
        "target_signals": ["contains_unverified_claims", "requires_current_information"],
        "target_operations": ["verify", "search"],
        "review_requirements": [
            "complete medium-risk flags for current/legal/medical/unverified combinations",
            "do not raise risk for ordinary local status or conversational today wording",
            "risk flags must agree with operations and information_state",
        ],
        "min_fixture_cases": 8,
        "gate_expectations": {
            "risk_exact_match": 0.95,
        },
    },
]


def _load(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _count_failure_memory_guards(payload: Dict[str, Any]) -> Dict[str, int]:
    counts: Counter[str] = Counter()
    for item in payload.get("items", []):
        counts.update(item.get("guard_action", []))
    return dict(sorted(counts.items()))


def _count_failure_conditions(payload: Dict[str, Any]) -> Dict[str, int]:
    counts: Counter[str] = Counter()
    for item in payload.get("items", []):
        counts.update(item.get("failure_condition", []))
    return dict(sorted(counts.items()))


def _candidate_pool_summary(payload: Dict[str, Any]) -> Dict[str, Any]:
    priority_a = [c for c in payload["candidates"] if c["priority"] == "A"]
    priority_b = [c for c in payload["candidates"] if c["priority"] == "B"]
    focus_counts = Counter(
        focus
        for candidate in payload["candidates"]
        for focus in candidate["review_focus"]
    )
    return {
        "source_path": str(CANDIDATES_PATH.relative_to(ROOT)),
        "sealed_source": False,
        "candidate_count": payload["summary"]["candidate_count"],
        "review_candidate_count": payload["summary"]["review_candidate_count"],
        "priority_a_count": len(priority_a),
        "priority_b_count": len(priority_b),
        "by_focus": dict(sorted(focus_counts.items())),
        "by_draft_intent": payload["summary"]["by_draft_intent"],
    }


def _axis_pool(axis: Dict[str, Any], candidate_summary: Dict[str, Any], fm: Dict[str, Any]) -> Dict[str, Any]:
    focus_counts = candidate_summary["by_focus"]
    guards = fm["guard_action_counts"]
    conditions = fm["failure_condition_counts"]
    signal_pool = {
        signal: focus_counts.get(f"critical_signal:{signal}", 0)
        for signal in axis["target_signals"]
    }
    operation_pool = focus_counts.get("operations", 0)
    constraint_pool = focus_counts.get("constraints", 0)
    risk_pool = focus_counts.get("risk", 0)
    guard_pool = {
        guard: guards.get(guard, 0)
        for guard in (
            "ask_first",
            "clarify_up",
            "preserve_constraints",
            "preserve_multi_intent",
            "split_or_sequence_operations",
            "verify_up",
            "search_up",
            "risk_check_up",
            "avoid_overclaim",
        )
        if guards.get(guard, 0)
    }
    condition_pool = {
        condition: conditions.get(condition, 0)
        for condition in axis["target_signals"] + axis["sealed_v4_taxonomy_fields"]
        if conditions.get(condition, 0)
    }
    return {
        "candidate_focus_counts": {
            **signal_pool,
            "operations": operation_pool,
            "constraints": constraint_pool,
            "risk": risk_pool,
        },
        "failure_memory_guard_counts": guard_pool,
        "failure_memory_condition_counts": condition_pool,
    }


def _write_markdown(report: Dict[str, Any]) -> None:
    lines = [
        "# V5 Non-Sealed Curriculum Plan v1",
        "",
        "Diagnostic/design artifact only. It uses sealed v4 measurement taxonomy "
        "without sealed input text or sealed labels.",
        "",
        "## Summary",
        "",
        f"- status: {report['status']}",
        f"- minimum challenge cases: {report['fixture_blueprint']['case_count_min']}",
        f"- review required: {report['fixture_blueprint']['human_review_required']}",
        f"- sealed text used: {report['policy']['sealed_v4_text_used']}",
        f"- quarantine overlay active: {report['data_hygiene']['quarantine_overlay']['status']}",
        "",
        "## Curriculum Axes",
        "",
        "| axis | priority | min cases | target signals | target operations |",
        "| --- | ---: | ---: | --- | --- |",
    ]
    for axis in report["curriculum_axes"]:
        lines.append(
            "| "
            f"{axis['name']} | "
            f"{axis['priority']} | "
            f"{axis['min_fixture_cases']} | "
            f"{', '.join(axis['target_signals']) or '-'} | "
            f"{', '.join(axis['target_operations']) or '-'} |"
        )
    lines.extend([
        "",
        "## Step 3 Fixture Rule",
        "",
        "- Build only from non-sealed sources listed in `source_pools`.",
        "- Every case must be human-reviewed before use in gates.",
        "- Quarantined corpus rows may be used only as negative/guard references.",
        "- Sealed v4 text overlap must remain 0 before sealed v5 rotation.",
        "",
    ])
    OUT_MD.write_text("\n".join(lines), encoding="utf-8", newline="\n")


def main() -> None:
    targets = _load(TARGETS_PATH)
    candidates = _load(CANDIDATES_PATH)
    failure_memory = _load(FAILURE_MEMORY_PATH)
    puzzle_failure = _load(PUZZLE_FAILURE_PATH)
    quarantine = _load(QUARANTINE_PATH)

    candidate_summary = _candidate_pool_summary(candidates)
    fm_summary = {
        "source_path": str(FAILURE_MEMORY_PATH.relative_to(ROOT)),
        "sealed_source": False,
        "item_count": failure_memory["summary"]["item_count"],
        "guard_action_counts": _count_failure_memory_guards(failure_memory),
        "failure_condition_counts": _count_failure_conditions(failure_memory),
    }
    axes = []
    for axis in AXES:
        axes.append({**axis, "source_pool_evidence": _axis_pool(axis, candidate_summary, fm_summary)})

    report = {
        "schema_version": "v5-nonsealed-curriculum-plan.v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": "designed",
        "policy": {
            "sealed_v4_fixture_status": targets["policy"]["sealed_v4_fixture_status"],
            "sealed_v4_text_used": False,
            "sealed_v4_labels_used_for_tuning": False,
            "sealed_v4_measurement_used_as_taxonomy_only": True,
            "sealed_fixture_opened_by_this_step": False,
            "success_pattern_lane_write_from_failures_allowed": False,
            "same_cycle_promotion_allowed": False,
        },
        "taxonomy_source": {
            "path": str(TARGETS_PATH.relative_to(ROOT)),
            "allowed_use": "sealed_v4_error_taxonomy_only_no_text_for_training",
            "error_field_counts": targets["baseline"]["error_field_counts"],
            "critical_signals": targets["baseline"]["critical_signals"],
            "target_minimums": targets["targets"]["minimum"],
        },
        "data_hygiene": {
            "quarantine_overlay": {
                "path": str(QUARANTINE_PATH.relative_to(ROOT)),
                "status": quarantine["status"],
                "entry_count": quarantine["summary"]["entry_count"],
                "active_approved_count_after_quarantine": quarantine["restore"]["active_approved_count_after_quarantine"],
                "allowed_use": "negative_or_guard_reference_only",
            }
        },
        "source_pools": {
            "critical_constraints_candidates": candidate_summary,
            "v4_failure_memory": fm_summary,
            "v4_puzzle_failure_memory": {
                "source_path": str(PUZZLE_FAILURE_PATH.relative_to(ROOT)),
                "sealed_source": False,
                "failure_count": puzzle_failure["summary"]["failure_count"],
                "source_failed_task_ids": puzzle_failure["summary"]["source_failed_task_ids"],
            },
        },
        "curriculum_axes": axes,
        "fixture_blueprint": {
            "output": "tests\\fixtures\\v5_critical_operations_fixture_v1.json",
            "case_count_min": 48,
            "human_review_required": True,
            "review_status_before_gate": "human_reviewed",
            "min_cases_by_axis": {axis["name"]: axis["min_fixture_cases"] for axis in axes},
            "case_overlap_between_axes_allowed": True,
            "sealed_text_overlap_count_required": 0,
            "must_include": [
                "multiple_intents + operation sequencing",
                "missing_required_information + clarify boundary",
                "current/unverified verify/search distinction",
                "constraint preservation under correct intent",
                "risk flags aligned with operations",
                "puzzle ambiguity and over-inference guards",
            ],
        },
        "pre_step3_gates": {
            "candidate_sources_nonsealed": True,
            "quarantine_overlay_active": quarantine["status"] == "active",
            "failure_memory_available": failure_memory["summary"]["item_count"] >= 38,
            "puzzle_failure_memory_available": puzzle_failure["summary"]["failure_count"] >= 2,
            "critical_candidate_review_pool_min": candidates["summary"]["review_candidate_count"] >= 200,
        },
        "next_step": {
            "step": 3,
            "name": "critical_signal_and_operations_fixture",
            "output": "tests\\fixtures\\v5_critical_operations_fixture_v1.json",
        },
    }
    OUT_JSON.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    _write_markdown(report)
    print(f"wrote {OUT_JSON.relative_to(ROOT)}")
    print(f"wrote {OUT_MD.relative_to(ROOT)}")
    print(
        json.dumps(
            {
                "status": report["status"],
                "axes": len(report["curriculum_axes"]),
                "case_count_min": report["fixture_blueprint"]["case_count_min"],
                "next_step": report["next_step"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
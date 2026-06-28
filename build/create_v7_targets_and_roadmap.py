"""Create post-v6 measurement taxonomy and the V7 roadmap.

The sealed v6 fixture is consumed. This script derives only aggregate taxonomy,
metric targets, and next-step planning from the measurement report. It does not
copy sealed input text or sealed expected labels into a training fixture.
"""

import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
MEASUREMENT_PATH = ROOT / "build" / "pattern_language_sealed_v6_measurement_report.json"
READINESS_PATH = ROOT / "build" / "plm_measurement_readiness_review.json"
REGISTRY_PATH = ROOT / "tests" / "fixtures" / "pattern_language_fixture_registry.json"
OUTPUT_JSON = ROOT / "build" / "v7_targets_and_roadmap_v1.json"
OUTPUT_MD = ROOT / "docs" / "PLM_V7_ROADMAP.md"
V6_ROADMAP_PATH = ROOT / "docs" / "PLM_V6_ROADMAP.md"
MAIN_ROADMAP_PATH = ROOT / "docs" / "PATTERN_LANGUAGE_MODEL_roadmap.md"


def _rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def _metric_targets() -> dict[str, Any]:
    return {
        "minimum": {
            "intent_accuracy": 0.892857,
            "critical_signal_recall": 0.75,
            "operation_exact_match": 0.821429,
            "constraint_exact_match": 0.821429,
            "risk_exact_match": 0.892857,
            "sealed_error_count_max": 10,
            "critical_signal_miss_count_max": 4,
        },
        "stretch": {
            "intent_accuracy": 0.928571,
            "critical_signal_recall": 0.875,
            "operation_exact_match": 0.892857,
            "constraint_exact_match": 0.892857,
            "risk_exact_match": 0.928571,
            "sealed_error_count_max": 6,
            "critical_signal_miss_count_max": 2,
        },
        "granularity": {
            "case_metric_step": 0.035714,
            "critical_signal_step": 0.071429,
        },
    }


def _taxonomy(measurement: dict[str, Any]) -> dict[str, Any]:
    metrics = measurement["measurements"]
    errors = metrics["errors"]
    field_counts: Counter[str] = Counter()
    by_expected_intent: dict[str, Counter[str]] = defaultdict(Counter)
    by_predicted_intent: dict[str, Counter[str]] = defaultdict(Counter)
    transitions: Counter[str] = Counter()
    for error in errors:
        for field in error["fields"]:
            field_counts[field] += 1
        expected = error["expected_intent"]
        predicted = error["predicted_intent"]
        by_expected_intent[expected].update(error["fields"])
        by_predicted_intent[predicted].update(error["fields"])
        if expected != predicted:
            transitions[f"{expected}->{predicted}"] += 1

    critical_signals = metrics["critical_signals"]
    support = sum(signal["support"] for signal in critical_signals.values())
    misses = {
        name: round(signal["support"] * (1.0 - signal["recall"]))
        for name, signal in critical_signals.items()
    }

    focus_areas = [
        {
            "id": "constraint_preservation",
            "priority": 1,
            "evidence": {
                "field": "constraints",
                "count": field_counts["constraints"],
                "metric": metrics["constraint_exact_match"],
            },
            "generalized_issue": (
                "response length, format, neutrality, cite-sources, no-table, "
                "and guard constraints are not retained consistently"
            ),
            "allowed_use": "nonsealed_constraint_curriculum_only",
        },
        {
            "id": "operation_sequence_repair",
            "priority": 1,
            "evidence": {
                "field": "operations",
                "count": field_counts["operations"],
                "metric": metrics["operation_exact_match"],
            },
            "generalized_issue": (
                "multi-step routes such as clarify+build, verify+search, "
                "explore+compare, and build+verify collapse to a single action"
            ),
            "allowed_use": "nonsealed_operation_curriculum_only",
        },
        {
            "id": "critical_signal_recovery",
            "priority": 1,
            "evidence": {
                "metric": metrics["critical_signal_recall"],
                "misses": misses,
                "support": support,
            },
            "generalized_issue": (
                "unverified claims and multiple intent signals are under-detected"
            ),
            "allowed_use": "nonsealed_critical_signal_curriculum_only",
        },
        {
            "id": "clarify_boundary_repair",
            "priority": 2,
            "evidence": {
                "clarify_recall": metrics["per_intent"]["clarify"]["recall"],
                "clarify_errors": dict(by_expected_intent["clarify"]),
            },
            "generalized_issue": (
                "missing information and ask-first cases are redirected to "
                "respond, build, or verify too quickly"
            ),
            "allowed_use": "nonsealed_clarify_boundary_curriculum_only",
        },
        {
            "id": "risk_ladder_calibration",
            "priority": 2,
            "evidence": {
                "field": "risk",
                "count": field_counts["risk"],
                "metric": metrics["risk_exact_match"],
            },
            "generalized_issue": (
                "low-risk contrast, medium current/license, and high medical/legal "
                "cases need steadier severity separation"
            ),
            "allowed_use": "nonsealed_risk_ladder_curriculum_only",
        },
        {
            "id": "intent_boundary_stability",
            "priority": 2,
            "evidence": {
                "intent_accuracy": metrics["intent_accuracy"],
                "transitions": dict(transitions),
            },
            "generalized_issue": (
                "respond/build, explain/build, clarify/respond, clarify/build, "
                "build/verify, and explore/respond boundaries remain fragile"
            ),
            "allowed_use": "nonsealed_intent_boundary_curriculum_only",
        },
    ]

    return {
        "field_error_counts": dict(sorted(field_counts.items())),
        "critical_signal_miss_counts": misses,
        "intent_boundary_transitions": dict(sorted(transitions.items())),
        "by_expected_intent": {
            intent: dict(counter)
            for intent, counter in sorted(by_expected_intent.items())
        },
        "by_predicted_intent": {
            intent: dict(counter)
            for intent, counter in sorted(by_predicted_intent.items())
        },
        "focus_areas": focus_areas,
    }


def _roadmap(report: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "step": 1,
            "name": "post_v6_measurement_taxonomy",
            "output": "build\\v7_targets_and_roadmap_v1.json",
            "status": "completed",
        },
        {
            "step": 2,
            "name": "v7_nonsealed_curriculum_design",
            "output": "build\\v7_nonsealed_curriculum_plan_v1.json",
            "status": "next",
        },
        {
            "step": 3,
            "name": "v7_nonsealed_fixture_and_candidate_replay",
            "output": "tests\\fixtures\\v7_router_repair_fixture_v1.json",
            "status": "pending",
        },
        {
            "step": 4,
            "name": "v7_router_generalization_changes",
            "output": "build\\v7_router_generalization_report_v1.json",
            "status": "pending",
        },
        {
            "step": 5,
            "name": "v7_nonsealed_replay_gate",
            "output": "build\\v7_nonsealed_replay_gate_report_v1.json",
            "status": "pending",
        },
        {
            "step": 6,
            "name": "sealed_v7_rotation_review",
            "output": "build\\v7_sealed_rotation_review_v1.json",
            "status": "pending",
        },
        {
            "step": 7,
            "name": "sealed_v7_rotation",
            "output": "tests\\fixtures\\pattern_language_sealed_v7.json",
            "status": "pending",
        },
        {
            "step": 8,
            "name": "sealed_v7_one_time_measurement",
            "output": "build\\pattern_language_sealed_v7_measurement_report.json",
            "status": "pending",
        },
    ]


def build_payload() -> dict[str, Any]:
    measurement = _load_json(MEASUREMENT_PATH)
    readiness = _load_json(READINESS_PATH)
    registry = _load_json(REGISTRY_PATH)
    metrics = measurement["measurements"]
    taxonomy = _taxonomy(measurement)
    targets = _metric_targets()
    fixture_name = measurement["fixture"]["registry_name"]
    registry_entry = registry["fixtures"][fixture_name]

    policy = {
        "sealed_v6_consumed": registry_entry["status"] == "consumed",
        "sealed_v6_labels_used_for_tuning": measurement[
            "sealed_labels_used_for_tuning"
        ],
        "sealed_v6_text_used_for_training": False,
        "sealed_v6_measurement_used_as_taxonomy_only": True,
        "same_cycle_promotion_allowed": False,
        "fresh_sealed_successor_required_before_measurement": True,
        "nonsealed_curriculum_required_before_rotation": True,
    }
    return {
        "schema_version": "v7-targets-and-roadmap.v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": "post_v6_taxonomy_created_v7_curriculum_next",
        "sources": {
            "sealed_v6_measurement": _rel(MEASUREMENT_PATH),
            "readiness_review": _rel(READINESS_PATH),
            "fixture_registry": _rel(REGISTRY_PATH),
        },
        "policy": policy,
        "baseline": {
            "fixture": fixture_name,
            "case_count": metrics["case_count"],
            "intent_accuracy": metrics["intent_accuracy"],
            "critical_signal_recall": metrics["critical_signal_recall"],
            "operation_exact_match": metrics["operation_exact_match"],
            "constraint_exact_match": metrics["constraint_exact_match"],
            "risk_exact_match": metrics["risk_exact_match"],
            "sealed_error_count": len(metrics["errors"]),
            "readiness_decision_after_measurement": readiness["decision"],
            "blocked_reasons": readiness["blocked_reasons"],
        },
        "targets": targets,
        "taxonomy": taxonomy,
        "nonsealed_curriculum_requirements": {
            "minimum_case_count": 72,
            "recommended_case_count": 96,
            "must_include_axes": [
                "constraint_preservation",
                "operation_sequence_repair",
                "critical_signal_recovery",
                "clarify_boundary_repair",
                "risk_ladder_calibration",
                "intent_boundary_stability",
            ],
            "review_required": True,
            "draft_lanes_are_diagnostic_only": True,
            "sealed_text_or_label_copy_allowed": False,
        },
        "pre_rotation_gates": {
            "visible_plm_exact_required": True,
            "v6_required_nonsealed_lanes_exact_required": True,
            "v7_curriculum_exact_minimum": 0.95,
            "v7_critical_signal_recall_minimum": 0.9,
            "v7_constraint_exact_match_minimum": 0.9,
            "v7_risk_exact_match_minimum": 0.9,
            "sealed_overlap_count_required": 0,
        },
        "roadmap": _roadmap({}),
        "next_action": "roadmap_v7_step2_nonsealed_curriculum_design",
    }


def _write_markdown(payload: dict[str, Any]) -> None:
    baseline = payload["baseline"]
    targets = payload["targets"]
    taxonomy = payload["taxonomy"]
    lines = [
        "# PLM V7 Roadmap: Constraint And Critical Signal Recovery",
        "",
        "Updated: 2026-06-24",
        "",
        "## Contract",
        "",
        "- Sealed v6 is consumed and may be used only as measurement taxonomy.",
        "- Sealed v6 text and labels must not be copied into training, review, or non-sealed fixtures.",
        "- V7 work must use non-sealed curriculum and human-reviewed replay surfaces.",
        "- Same-cycle promotion remains disallowed.",
        "- A fresh sealed v7 fixture is required before the next adjudicating measurement.",
        "",
        "## Baseline And Targets",
        "",
        "| Metric | V6 sealed | V7 minimum | V7 stretch |",
        "|---|---:|---:|---:|",
        f"| intent_accuracy | {baseline['intent_accuracy']:.6f} | {targets['minimum']['intent_accuracy']:.6f} | {targets['stretch']['intent_accuracy']:.6f} |",
        f"| critical_signal_recall | {baseline['critical_signal_recall']:.6f} | {targets['minimum']['critical_signal_recall']:.6f} | {targets['stretch']['critical_signal_recall']:.6f} |",
        f"| operation_exact_match | {baseline['operation_exact_match']:.6f} | {targets['minimum']['operation_exact_match']:.6f} | {targets['stretch']['operation_exact_match']:.6f} |",
        f"| constraint_exact_match | {baseline['constraint_exact_match']:.6f} | {targets['minimum']['constraint_exact_match']:.6f} | {targets['stretch']['constraint_exact_match']:.6f} |",
        f"| risk_exact_match | {baseline['risk_exact_match']:.6f} | {targets['minimum']['risk_exact_match']:.6f} | {targets['stretch']['risk_exact_match']:.6f} |",
        f"| sealed_error_count | {baseline['sealed_error_count']} | <= {targets['minimum']['sealed_error_count_max']} | <= {targets['stretch']['sealed_error_count_max']} |",
        "",
        "## Error Taxonomy",
        "",
        "| Field | Count |",
        "|---|---:|",
    ]
    for field, count in taxonomy["field_error_counts"].items():
        lines.append(f"| {field} | {count} |")
    lines.extend(
        [
            "",
            "## Focus Areas",
            "",
        ]
    )
    for item in taxonomy["focus_areas"]:
        lines.append(
            f"{item['priority']}. {item['id']}: {item['generalized_issue']}"
        )
    lines.extend(
        [
            "",
            "## Roadmap",
            "",
            "| Step | Name | Output | Status |",
            "|---:|---|---|---|",
        ]
    )
    for step in payload["roadmap"]:
        lines.append(
            f"| {step['step']} | {step['name']} | `{step['output']}` | {step['status']} |"
        )
    OUTPUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def _update_v6_roadmap() -> None:
    roadmap = V6_ROADMAP_PATH.read_text(encoding="utf-8")
    roadmap = roadmap.replace(
        "| 7 | post_v6_measurement_taxonomy | `build\\v7_targets_and_roadmap_v1.json` | next |",
        "| 7 | post_v6_measurement_taxonomy | `build\\v7_targets_and_roadmap_v1.json` | completed |",
    )
    section = (
        "## Step 7 Output\n\n"
        "`build\\v7_targets_and_roadmap_v1.json` and `docs\\PLM_V7_ROADMAP.md` "
        "convert the consumed sealed v6 result into aggregate taxonomy, V7 "
        "targets, non-sealed curriculum requirements, and the fresh sealed v7 "
        "rotation plan. Sealed v6 text and labels remain excluded from training."
    )
    if "## Step 7 Output" in roadmap:
        head, _ = roadmap.split("## Step 7 Output", 1)
        roadmap = head.rstrip() + "\n\n" + section + "\n"
    else:
        roadmap = roadmap.rstrip() + "\n\n" + section + "\n"
    V6_ROADMAP_PATH.write_text(roadmap, encoding="utf-8", newline="\n")


def _update_main_roadmap(payload: dict[str, Any]) -> None:
    marker = "## PLM V7: Constraint And Critical Signal Recovery"
    baseline = payload["baseline"]
    main = MAIN_ROADMAP_PATH.read_text(encoding="utf-8")
    section = f"""
{marker}

Status: V7 Step 1 post-v6 taxonomy completed; Step 2 non-sealed curriculum design next.

Primary roadmap: `docs/PLM_V7_ROADMAP.md`
Targets and taxonomy: `build/v7_targets_and_roadmap_v1.json`
Baseline sealed v6 measurement: `build/pattern_language_sealed_v6_measurement_report.json`

V7 uses sealed v6 measurement only as aggregate taxonomy. Sealed v6 text and labels are not training data. V6 measured intent_accuracy {baseline['intent_accuracy']:.6f}, critical_signal_recall {baseline['critical_signal_recall']:.6f}, operation_exact_match {baseline['operation_exact_match']:.6f}, constraint_exact_match {baseline['constraint_exact_match']:.6f}, risk_exact_match {baseline['risk_exact_match']:.6f}, errors {baseline['sealed_error_count']}. The immediate priority is a reviewed non-sealed curriculum for constraint preservation, operation sequencing, critical signal recovery, clarify boundaries, risk ladder calibration, and intent boundary stability before sealed v7 rotation.
""".strip()
    if marker in main:
        head, _ = main.split(marker, 1)
        main = head.rstrip() + "\n\n" + section + "\n"
    else:
        main = main.rstrip() + "\n\n" + section + "\n"
    MAIN_ROADMAP_PATH.write_text(main, encoding="utf-8", newline="\n")


def main() -> None:
    payload = build_payload()
    _write_json(OUTPUT_JSON, payload)
    _write_markdown(payload)
    _update_v6_roadmap()
    _update_main_roadmap(payload)
    print(
        json.dumps(
            {
                "status": payload["status"],
                "output": _rel(OUTPUT_JSON),
                "roadmap": _rel(OUTPUT_MD),
                "next_action": payload["next_action"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()

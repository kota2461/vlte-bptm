"""Create PLM V5 targets and roadmap from sealed V4 measurement taxonomy.

The output may use sealed V4 measurement metrics and error ids/field names as
taxonomy. It must not copy sealed V4 input text into training or review lanes.
"""

import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
V4_MEASUREMENT = ROOT / "build" / "pattern_language_sealed_v4_measurement_report.json"
OUTPUT_JSON = ROOT / "build" / "v5_targets_and_roadmap_v1.json"
OUTPUT_MD = ROOT / "docs" / "PLM_V5_ROADMAP.md"


V5_MINIMUM_TARGETS = {
    "intent_accuracy": 0.928571,
    "critical_signal_recall": 0.875,
    "operation_exact_match": 0.892857,
    "constraint_exact_match": 0.928571,
    "risk_exact_match": 0.964286,
    "sealed_error_count_max": 6,
    "critical_signal_miss_count_max": 2,
    "critical_underprocessing_max": 0,
}

V5_STRETCH_TARGETS = {
    "intent_accuracy": 0.964286,
    "critical_signal_recall": 1.0,
    "operation_exact_match": 0.928571,
    "constraint_exact_match": 0.964286,
    "risk_exact_match": 1.0,
    "sealed_error_count_max": 3,
    "critical_signal_miss_count_max": 0,
    "critical_underprocessing_max": 0,
}

BY_SIGNAL_TARGETS = {
    "missing_required_information": {"minimum": 0.75, "stretch": 1.0},
    "contains_unverified_claims": {"minimum": 1.0, "stretch": 1.0},
    "requires_current_information": {"minimum": 1.0, "stretch": 1.0},
    "multiple_intents": {"minimum": 0.75, "stretch": 1.0},
}

ROADMAP = [
    {
        "step": 1,
        "name": "targets_and_taxonomy",
        "status": "completed",
        "output": "build\\v5_targets_and_roadmap_v1.json",
        "purpose": "Freeze V5 goals and V4 sealed measurement taxonomy without sealed text reuse.",
    },
    {
        "step": 2,
        "name": "nonsealed_error_curriculum_design",
        "status": "next",
        "output": "build\\v5_nonsealed_curriculum_plan_v1.json",
        "purpose": "Map V4 error taxonomy to non-sealed challenge categories and review requirements.",
    },
    {
        "step": 3,
        "name": "critical_signal_and_operations_fixture",
        "status": "pending",
        "output": "tests\\fixtures\\v5_critical_operations_fixture_v1.json",
        "purpose": "Build human-reviewable non-sealed cases for multiple-intent, missing-info, current-info, operations, and constraints.",
    },
    {
        "step": 4,
        "name": "router_generalization_changes",
        "status": "pending",
        "output": "build\\v5_router_generalization_report.json",
        "purpose": "Improve critical signal, operation, constraint, and risk generalization without copying sealed labels.",
    },
    {
        "step": 5,
        "name": "nonsealed_replay_gate",
        "status": "pending",
        "output": "build\\v5_nonsealed_replay_gate_report.json",
        "purpose": "Pass visible PLM, V4 Failure Memory, Puzzle Failure Memory, and V5 non-sealed challenge gates before sealed rotation.",
    },
    {
        "step": 6,
        "name": "sealed_v5_rotation",
        "status": "pending",
        "output": "tests\\fixtures\\pattern_language_sealed_v5.json",
        "purpose": "Create a fresh unopened sealed V5 fixture and register it active only after non-sealed gates pass.",
    },
    {
        "step": 7,
        "name": "sealed_v5_one_time_measurement",
        "status": "pending",
        "output": "build\\pattern_language_sealed_v5_measurement_report.json",
        "purpose": "Measure sealed V5 once, consume it, and rotate before any tuning based on the result.",
    },
]


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _critical_signal_counts(critical: dict[str, Any]) -> dict[str, dict[str, int | float]]:
    result: dict[str, dict[str, int | float]] = {}
    for signal, metrics in critical.items():
        support = int(metrics["support"])
        tp = int(round(float(metrics["recall"]) * support))
        result[signal] = {
            "support": support,
            "true_positive": tp,
            "miss": support - tp,
            "recall": float(metrics["recall"]),
        }
    return result


def _taxonomy(errors: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "id": error["id"],
            "kind": error["kind"],
            "fields": list(error.get("fields", [])),
            "expected_intent": error.get("expected_intent"),
            "predicted_intent": error.get("predicted_intent"),
            "allowed_use": "sealed_v4_error_taxonomy_only_no_text_for_training",
        }
        for error in errors
    ]


def build_payload() -> dict[str, Any]:
    report = _load(V4_MEASUREMENT)
    measurements = report["measurements"]
    errors = measurements["errors"]
    field_counts = Counter(field for error in errors for field in error.get("fields", []))
    intent_pairs = Counter(
        f"{error.get('expected_intent')}->{error.get('predicted_intent')}"
        for error in errors
    )
    critical_counts = _critical_signal_counts(measurements["critical_signals"])
    critical_support = sum(item["support"] for item in critical_counts.values())
    critical_miss = sum(item["miss"] for item in critical_counts.values())
    payload = {
        "schema_version": "v5-targets-and-roadmap.v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": "targets_defined",
        "policy": {
            "sealed_v4_fixture_status": "consumed",
            "sealed_v4_text_used_for_training": False,
            "sealed_v4_labels_used_for_tuning": False,
            "sealed_v4_measurement_used_as_taxonomy_only": True,
            "requires_sealed_v5_rotation_before_adjudication": True,
            "same_cycle_promotion_allowed": False,
        },
        "baseline": {
            "source_report": "build\\pattern_language_sealed_v4_measurement_report.json",
            "fixture": report["fixture"],
            "metrics": {
                "case_count": measurements["case_count"],
                "intent_accuracy": measurements["intent_accuracy"],
                "intent_macro_f1": measurements["intent_macro_f1"],
                "critical_signal_recall": measurements["critical_signal_recall"],
                "operation_exact_match": measurements["operation_exact_match"],
                "constraint_exact_match": measurements["constraint_exact_match"],
                "risk_exact_match": measurements["risk_exact_match"],
                "evidence_offset_validity": measurements["evidence_offset_validity"],
                "sealed_error_count": len(errors),
                "critical_signal_support": critical_support,
                "critical_signal_miss_count": critical_miss,
            },
            "critical_signals": critical_counts,
            "error_field_counts": dict(sorted(field_counts.items())),
            "intent_pair_counts": dict(sorted(intent_pairs.items())),
            "error_taxonomy": _taxonomy(errors),
        },
        "targets": {
            "metric_granularity": {
                "case_metric_step": "1/28 = 0.035714",
                "critical_signal_step": "1/16 = 0.0625",
            },
            "minimum": V5_MINIMUM_TARGETS,
            "stretch": V5_STRETCH_TARGETS,
            "by_critical_signal": BY_SIGNAL_TARGETS,
        },
        "focus_areas": [
            {
                "name": "critical_signal_recovery",
                "priority": 1,
                "why": "Critical recall dropped to 0.5625; multiple_intents and missing_required_information are the largest risks.",
                "target_fields": ["information_state", "operations", "primary_intent"],
            },
            {
                "name": "operation_sequence_exactness",
                "priority": 2,
                "why": "Operations mismatched in 7 sealed v4 errors, especially clarify/calculate, verify/search, and explore/compare patterns.",
                "target_fields": ["operations", "information_state"],
            },
            {
                "name": "constraint_preservation",
                "priority": 3,
                "why": "Constraints mismatched in 5 errors; short, JSON, bullets, no_table, and ask_first must survive routing.",
                "target_fields": ["constraints"],
            },
            {
                "name": "intent_boundary_repair",
                "priority": 4,
                "why": "Intent accuracy stayed at 0.857143; clarify->respond and explain/respond boundaries still leak.",
                "target_fields": ["primary_intent", "operations"],
            },
            {
                "name": "risk_flag_completion",
                "priority": 5,
                "why": "Risk is closest to target but still misses legal/medical/current combinations in 2 errors.",
                "target_fields": ["risk", "information_state"],
            },
        ],
        "roadmap": ROADMAP,
        "pre_sealed_v5_gates": {
            "visible_plm_intent_accuracy": 1.0,
            "visible_plm_critical_signal_recall": 1.0,
            "v4_failure_guard_exact_match_rate": 1.0,
            "puzzle_failure_memory_preserved": True,
            "v5_nonsealed_challenge_accuracy_min": 0.95,
            "v5_nonsealed_critical_signal_recall_min": 0.95,
            "sealed_text_overlap_count": 0,
        },
    }
    return payload


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def _write_markdown(path: Path, payload: dict[str, Any]) -> None:
    baseline = payload["baseline"]["metrics"]
    minimum = payload["targets"]["minimum"]
    stretch = payload["targets"]["stretch"]
    lines = [
        "# PLM V5 Roadmap: Critical Signal Recovery",
        "",
        "Updated: 2026-06-21",
        "",
        "## Contract",
        "",
        "- Sealed v4 is consumed and may be used only as measurement taxonomy.",
        "- Sealed v4 input text and labels must not be copied into training, review, or non-sealed fixtures.",
        "- V5 tuning must use non-sealed curriculum, Failure Memory, Puzzle Failure Memory, and visible benchmarks only.",
        "- A fresh sealed v5 fixture is required before the next adjudicating measurement.",
        "",
        "## Baseline And Targets",
        "",
        "| Metric | V4 sealed | V5 minimum | V5 stretch |",
        "|---|---:|---:|---:|",
        f"| intent_accuracy | {baseline['intent_accuracy']:.6f} | {minimum['intent_accuracy']:.6f} | {stretch['intent_accuracy']:.6f} |",
        f"| critical_signal_recall | {baseline['critical_signal_recall']:.6f} | {minimum['critical_signal_recall']:.6f} | {stretch['critical_signal_recall']:.6f} |",
        f"| operation_exact_match | {baseline['operation_exact_match']:.6f} | {minimum['operation_exact_match']:.6f} | {stretch['operation_exact_match']:.6f} |",
        f"| constraint_exact_match | {baseline['constraint_exact_match']:.6f} | {minimum['constraint_exact_match']:.6f} | {stretch['constraint_exact_match']:.6f} |",
        f"| risk_exact_match | {baseline['risk_exact_match']:.6f} | {minimum['risk_exact_match']:.6f} | {stretch['risk_exact_match']:.6f} |",
        f"| sealed_error_count | {baseline['sealed_error_count']} | <= {minimum['sealed_error_count_max']} | <= {stretch['sealed_error_count_max']} |",
        f"| critical_signal_miss_count | {baseline['critical_signal_miss_count']} | <= {minimum['critical_signal_miss_count_max']} | <= {stretch['critical_signal_miss_count_max']} |",
        "",
        "Metric granularity: case metrics move by 1/28 = 0.035714; critical signal recall moves by 1/16 = 0.0625.",
        "",
        "## Critical Signal Targets",
        "",
        "| Signal | V4 recall | Support | Miss | V5 minimum | V5 stretch |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for signal, counts in payload["baseline"]["critical_signals"].items():
        targets = payload["targets"]["by_critical_signal"][signal]
        lines.append(
            f"| {signal} | {counts['recall']:.6f} | {counts['support']} | {counts['miss']} | {targets['minimum']:.6f} | {targets['stretch']:.6f} |"
        )
    lines.extend([
        "",
        "## Error Taxonomy",
        "",
        "| Field | Count |",
        "|---|---:|",
    ])
    for field, count in payload["baseline"]["error_field_counts"].items():
        lines.append(f"| {field} | {count} |")
    lines.extend([
        "",
        "## Focus Areas",
        "",
    ])
    for item in payload["focus_areas"]:
        lines.append(f"{item['priority']}. {item['name']}: {item['why']}")
    lines.extend([
        "",
        "## Roadmap",
        "",
        "| Step | Name | Output | Status |",
        "|---:|---|---|---|",
    ])
    for step in payload["roadmap"]:
        lines.append(f"| {step['step']} | {step['name']} | `{step['output']}` | {step['status']} |")
    lines.extend([
        "",
        "## Pre-Sealed V5 Gates",
        "",
    ])
    for key, value in payload["pre_sealed_v5_gates"].items():
        lines.append(f"- {key}: {value}")
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8", newline="\n")


def main() -> None:
    payload = build_payload()
    _write_json(OUTPUT_JSON, payload)
    _write_markdown(OUTPUT_MD, payload)
    print(json.dumps({"json": str(OUTPUT_JSON.relative_to(ROOT)), "markdown": str(OUTPUT_MD.relative_to(ROOT))}, indent=2))


if __name__ == "__main__":
    main()

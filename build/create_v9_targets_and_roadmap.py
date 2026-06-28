"""Create the V9 targets, taxonomy, and rotation roadmap.

Sealed v8 is consumed. This script uses the sealed v8 measurement only as
aggregate taxonomy and records the V9 human-approved non-sealed replay lanes.
It never copies sealed case text or labels into training data.
"""

import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
MEASUREMENT_PATH = ROOT / "build" / "pattern_language_sealed_v8_measurement_report.json"
READINESS_PATH = ROOT / "build" / "plm_measurement_readiness_review.json"
REGISTRY_PATH = ROOT / "tests" / "fixtures" / "pattern_language_fixture_registry.json"
V9_SELECTION_PATH = ROOT / "build" / "v9_accumulated_log_candidate_selection_v1.json"
V9_PRIMARY_REPORT_PATH = ROOT / "build" / "v9_accumulated_primary_review_replay_report_v1.json"
V9_EXTENSION_REPORT_PATH = ROOT / "build" / "v9_constraint_operation_extension_replay_report_v1.json"
V9_GATE_PATH = ROOT / "build" / "v9_nonsealed_replay_gate_report_v1.json"
V9_ROTATION_REVIEW_PATH = ROOT / "build" / "v9_sealed_rotation_review_v1.json"
V9_ROTATION_REPORT_PATH = ROOT / "build" / "v9_sealed_rotation_report_v1.json"
V9_MEASUREMENT_PATH = ROOT / "build" / "pattern_language_sealed_v9_measurement_report.json"
V9_STEP8_SUMMARY_PATH = ROOT / "build" / "v9_step8_measurement_summary.md"
OUTPUT_JSON = ROOT / "build" / "v9_targets_and_roadmap_v1.json"
OUTPUT_MD = ROOT / "docs" / "PLM_V9_ROADMAP.md"
V8_ROADMAP_PATH = ROOT / "docs" / "PLM_V8_ROADMAP.md"
MAIN_ROADMAP_PATH = ROOT / "docs" / "PATTERN_LANGUAGE_MODEL_roadmap.md"


def _rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def _metric_targets() -> dict[str, Any]:
    return {
        "minimum": {
            "intent_accuracy": 0.928571,
            "critical_signal_recall": 0.916667,
            "operation_exact_match": 0.892857,
            "constraint_exact_match": 0.892857,
            "risk_exact_match": 0.892857,
            "sealed_error_count_max": 7,
            "critical_signal_miss_count_max": 1,
        },
        "stretch": {
            "intent_accuracy": 0.964286,
            "critical_signal_recall": 1.0,
            "operation_exact_match": 0.928571,
            "constraint_exact_match": 0.928571,
            "risk_exact_match": 0.928571,
            "sealed_error_count_max": 4,
            "critical_signal_miss_count_max": 0,
        },
        "granularity": {
            "case_metric_step": 0.035714,
            "critical_signal_step": 0.083333,
        },
    }


def _critical_signal_misses(metrics: dict[str, Any]) -> dict[str, int]:
    return {
        name: round(signal["support"] * (1.0 - signal["recall"]))
        for name, signal in metrics["critical_signals"].items()
    }


def _field_counts(errors: list[dict[str, Any]]) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for error in errors:
        counts.update(error["fields"])
    return dict(sorted(counts.items()))


def _critical_signal_miss_count(signals: dict[str, dict[str, Any]]) -> int:
    misses = 0
    for signal in signals.values():
        misses += round(signal["support"] * (1.0 - signal["recall"]))
    return misses


def _taxonomy(measurement: dict[str, Any]) -> dict[str, Any]:
    metrics = measurement["measurements"]
    field_counts: Counter[str] = Counter()
    by_expected_intent: dict[str, Counter[str]] = defaultdict(Counter)
    by_predicted_intent: dict[str, Counter[str]] = defaultdict(Counter)
    transitions: Counter[str] = Counter()
    for error in metrics["errors"]:
        field_counts.update(error["fields"])
        expected = error["expected_intent"]
        predicted = error["predicted_intent"]
        by_expected_intent[expected].update(error["fields"])
        by_predicted_intent[predicted].update(error["fields"])
        if expected != predicted:
            transitions[f"{expected}->{predicted}"] += 1

    misses = _critical_signal_misses(metrics)
    focus_areas = [
        {
            "id": "operation_constraint_exactness",
            "priority": 1,
            "generalized_issue": "operation order and explicit constraints remain the largest sealed-v8 exact-match gap",
            "evidence": {
                "operations": field_counts["operations"],
                "constraints": field_counts["constraints"],
                "operation_exact_match": metrics["operation_exact_match"],
                "constraint_exact_match": metrics["constraint_exact_match"],
            },
            "covered_by_v9_lanes": ["primary_review", "constraint_operation_extension"],
        },
        {
            "id": "risk_current_information_balance",
            "priority": 1,
            "generalized_issue": "current/search and risk flags need separation between actual external-current needs and local/current wording",
            "evidence": {
                "risk": field_counts["risk"],
                "requires_current_information_misses": misses["requires_current_information"],
                "risk_exact_match": metrics["risk_exact_match"],
            },
            "covered_by_v9_lanes": ["primary_review"],
        },
        {
            "id": "respond_vs_build_boundary",
            "priority": 2,
            "generalized_issue": "simple response requests can still be pulled into build when wording contains deliverable-like verbs",
            "evidence": {
                "transition": "respond->build",
                "count": transitions["respond->build"],
                "respond_recall": metrics["per_intent"]["respond"]["recall"],
            },
            "covered_by_v9_lanes": ["primary_review", "future_false_positive_set"],
        },
        {
            "id": "clarify_vs_verify_boundary",
            "priority": 2,
            "generalized_issue": "missing information plus verification language can still jump to verify before asking",
            "evidence": {
                "transition": "clarify->verify",
                "count": transitions["clarify->verify"],
                "clarify_recall": metrics["per_intent"]["clarify"]["recall"],
            },
            "covered_by_v9_lanes": ["primary_review"],
        },
        {
            "id": "paraphrase_mixed_language_tail",
            "priority": 3,
            "generalized_issue": "V9 still needs more paraphrase, mixed ja/en, and natural short-form coverage before sealed rotation",
            "evidence": {
                "primary_review_mixed_language_count": 1,
                "primary_review_paraphrase_count": 1,
            },
            "covered_by_v9_lanes": ["primary_review"],
        },
    ]
    return {
        "field_error_counts": dict(sorted(field_counts.items())),
        "critical_signal_miss_counts": misses,
        "intent_boundary_transitions": dict(sorted(transitions.items())),
        "by_expected_intent": {intent: dict(counter) for intent, counter in sorted(by_expected_intent.items())},
        "by_predicted_intent": {intent: dict(counter) for intent, counter in sorted(by_predicted_intent.items())},
        "focus_areas": focus_areas,
    }


def _roadmap(gate_passed: bool) -> list[dict[str, Any]]:
    return [
        {"step": 1, "name": "post_v8_measurement_taxonomy", "output": "build\\v9_targets_and_roadmap_v1.json", "status": "completed"},
        {"step": 2, "name": "v9_accumulated_log_candidate_selection", "output": "build\\v9_accumulated_log_candidate_selection_v1.json", "status": "completed"},
        {"step": 3, "name": "v9_primary_review_adoption_and_replay", "output": "build\\v9_accumulated_primary_review_replay_report_v1.json", "status": "completed"},
        {"step": 4, "name": "v9_constraint_operation_extension", "output": "build\\v9_constraint_operation_extension_replay_report_v1.json", "status": "completed"},
        {"step": 5, "name": "v9_nonsealed_replay_gate", "output": "build\\v9_nonsealed_replay_gate_report_v1.json", "status": "completed" if gate_passed else "next"},
        {"step": 6, "name": "sealed_v9_rotation_review", "output": "build\\v9_sealed_rotation_review_v1.json", "status": "next" if gate_passed else "pending"},
        {"step": 7, "name": "sealed_v9_rotation", "output": "tests\\fixtures\\pattern_language_sealed_v9.json", "status": "pending"},
        {"step": 8, "name": "sealed_v9_one_time_measurement", "output": "build\\pattern_language_sealed_v9_measurement_report.json", "status": "pending"},
    ]


def _existing_gate() -> dict[str, Any] | None:
    if not V9_GATE_PATH.exists():
        return None
    gate = _load_json(V9_GATE_PATH)
    if gate.get("schema_version") != "v9-nonsealed-replay-gate-report.v1":
        return None
    return gate


def _existing_step6_review() -> dict[str, Any] | None:
    if not V9_ROTATION_REVIEW_PATH.exists():
        return None
    review = _load_json(V9_ROTATION_REVIEW_PATH)
    if review.get("schema_version") != "v9-sealed-rotation-review.v1":
        return None
    if review.get("passed") is not True:
        return None
    return review


def _preserve_step6_review_state(payload: dict[str, Any]) -> dict[str, Any]:
    review = _existing_step6_review()
    if review is None:
        return payload
    payload["generated_at"] = review["reviewed_at"]
    payload["status"] = "step6_sealed_rotation_review_completed_step7_rotation_next"
    payload["next_action"] = "roadmap_v9_step7_generate_and_rotate_sealed_v9_fixture"
    payload["sources"]["v9_sealed_rotation_review"] = _rel(V9_ROTATION_REVIEW_PATH)
    for item in payload["roadmap"]:
        if item["step"] == 6:
            item["status"] = "completed"
        elif item["step"] == 7:
            item["status"] = "next"
    payload["step6_sealed_rotation_review"] = {
        "output": "build\\v9_sealed_rotation_review_v1.json",
        "decision": review["decision"],
        "passed": review["passed"],
        "sealed_v9_fixture_created_now": False,
        "sealed_v9_opened_for_measurement": False,
        "same_cycle_promotion_allowed": False,
        "requires_fresh_sealed_v9_before_measurement": True,
        "summary": {
            "required_error_count": review["gate_summary"]["required_error_count"],
            "active_sealed_fixtures": len(review["registry_state"]["active_sealed_fixtures"]),
            "blocker_count": len(review["blockers"]),
        },
    }
    return payload


def _existing_step7_rotation() -> dict[str, Any] | None:
    if not V9_ROTATION_REPORT_PATH.exists():
        return None
    report = _load_json(V9_ROTATION_REPORT_PATH)
    if report.get("schema_version") != "v9-sealed-rotation-report.v1":
        return None
    rotated_to = report.get("rotated_to", {})
    if rotated_to.get("status") != "active" or rotated_to.get("measured") is not False:
        return None
    return report


def _preserve_step7_rotation_state(payload: dict[str, Any]) -> dict[str, Any]:
    report = _existing_step7_rotation()
    if report is None:
        return payload
    payload["generated_at"] = report["rotated_at"]
    payload["status"] = "step7_sealed_rotation_completed_step8_measurement_next"
    payload["next_action"] = "roadmap_v9_step8_measure_active_sealed_v9_once"
    payload["sources"]["v9_sealed_rotation_report"] = _rel(V9_ROTATION_REPORT_PATH)
    for item in payload["roadmap"]:
        if item["step"] in {6, 7}:
            item["status"] = "completed"
        elif item["step"] == 8:
            item["status"] = "next"
    payload["step7_sealed_rotation"] = {
        "output": "build\\v9_sealed_rotation_report_v1.json",
        "fixture": "tests\\fixtures\\pattern_language_sealed_v9.json",
        "passed": True,
        "sealed_v9_opened_for_measurement": False,
        "sealed_v9_labels_used_for_tuning": False,
        "same_cycle_promotion_allowed": False,
        "summary": {
            "case_count": report["rotated_to"]["case_count"],
            "status": report["rotated_to"]["status"],
            "measured": report["rotated_to"]["measured"],
            "reviewed": report["rotated_to"]["reviewed"],
            "readiness_decision": report["readiness_after_rotation"]["decision"],
            "blocked_reasons": report["readiness_after_rotation"]["blocked_reasons"],
        },
    }
    return payload


def _existing_step8_measurement() -> dict[str, Any] | None:
    if not V9_MEASUREMENT_PATH.exists():
        return None
    measurement = _load_json(V9_MEASUREMENT_PATH)
    if measurement.get("schema_version") != "plm-sealed-measurement-report.v1":
        return None
    if measurement.get("fixture", {}).get("registry_name") != "pattern_language_sealed_v9.json":
        return None
    if measurement.get("registry_update", {}).get("status_after_measurement") != "consumed":
        return None
    return measurement


def _preserve_step8_measurement_state(payload: dict[str, Any]) -> dict[str, Any]:
    measurement = _existing_step8_measurement()
    if measurement is None:
        return payload
    readiness = _load_json(READINESS_PATH)
    metrics = measurement["measurements"]
    minimum = payload["targets"]["minimum"]
    field_counts = _field_counts(metrics["errors"])
    critical_miss_count = _critical_signal_miss_count(metrics["critical_signals"])
    minimum_metrics_met = (
        metrics["intent_accuracy"] >= minimum["intent_accuracy"]
        and metrics["critical_signal_recall"] >= minimum["critical_signal_recall"]
        and metrics["operation_exact_match"] >= minimum["operation_exact_match"]
        and metrics["constraint_exact_match"] >= minimum["constraint_exact_match"]
        and metrics["risk_exact_match"] >= minimum["risk_exact_match"]
        and len(metrics["errors"]) <= minimum["sealed_error_count_max"]
    )
    critical_signal_miss_gate_met = critical_miss_count <= minimum["critical_signal_miss_count_max"]
    payload["generated_at"] = measurement["measured_at"]
    payload["status"] = "step8_sealed_v9_measurement_completed_v10_rotation_required"
    payload["next_action"] = "roadmap_v10_step1_post_v9_measurement_taxonomy"
    payload["sources"]["sealed_v9_measurement"] = _rel(V9_MEASUREMENT_PATH)
    for item in payload["roadmap"]:
        item["status"] = "completed"
    payload["step8_sealed_measurement"] = {
        "output": "build\\pattern_language_sealed_v9_measurement_report.json",
        "summary": "build\\v9_step8_measurement_summary.md",
        "fixture": "tests\\fixtures\\pattern_language_sealed_v9.json",
        "sealed_fixture_opened": measurement["sealed_fixture_opened"],
        "sealed_labels_used_for_tuning": measurement["sealed_labels_used_for_tuning"],
        "passed_minimum": minimum_metrics_met and critical_signal_miss_gate_met,
        "minimum_metrics_met": minimum_metrics_met,
        "critical_signal_miss_count": critical_miss_count,
        "critical_signal_miss_gate_met": critical_signal_miss_gate_met,
        "rotation_required_before_tuning": measurement["registry_update"]["rotation_required_before_tuning"],
        "readiness_after_measurement": {
            "decision": "blocked",
            "blocked_reasons": ["sealed_fixture_not_available"],
            "sealed_fixture": None,
        },
        "measurements": {
            "case_count": metrics["case_count"],
            "intent_accuracy": metrics["intent_accuracy"],
            "intent_macro_f1": metrics["intent_macro_f1"],
            "critical_signal_recall": metrics["critical_signal_recall"],
            "operation_exact_match": metrics["operation_exact_match"],
            "constraint_exact_match": metrics["constraint_exact_match"],
            "risk_exact_match": metrics["risk_exact_match"],
            "valid_packet_rate": metrics["valid_packet_rate"],
            "evidence_offset_validity": metrics["evidence_offset_validity"],
            "error_count": len(metrics["errors"]),
            "error_field_counts": field_counts,
        },
    }
    return payload


def build_payload() -> dict[str, Any]:
    measurement = _load_json(MEASUREMENT_PATH)
    readiness = _load_json(READINESS_PATH)
    registry = _load_json(REGISTRY_PATH)
    selection = _load_json(V9_SELECTION_PATH)
    primary = _load_json(V9_PRIMARY_REPORT_PATH)
    extension = _load_json(V9_EXTENSION_REPORT_PATH)
    gate = _existing_gate()
    gate_passed = bool(gate and gate.get("passed") is True)
    metrics = measurement["measurements"]
    fixture_name = measurement["fixture"]["registry_name"]
    registry_entry = registry["fixtures"][fixture_name]
    v9_case_count = primary["measurement"]["case_count"] + extension["measurement"]["case_count"]

    payload = {
        "schema_version": "v9-targets-and-roadmap.v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": "step5_v9_nonsealed_replay_gate_passed_step6_rotation_review_next" if gate_passed else "step4_v9_extension_completed_step5_nonsealed_gate_next",
        "sources": {
            "sealed_v8_measurement": _rel(MEASUREMENT_PATH),
            "readiness_review": _rel(READINESS_PATH),
            "fixture_registry": _rel(REGISTRY_PATH),
            "v9_candidate_selection": _rel(V9_SELECTION_PATH),
            "v9_primary_review_replay": _rel(V9_PRIMARY_REPORT_PATH),
            "v9_constraint_operation_extension": _rel(V9_EXTENSION_REPORT_PATH),
        },
        "policy": {
            "sealed_v8_consumed": registry_entry["status"] == "consumed",
            "sealed_v8_labels_used_for_tuning": measurement["sealed_labels_used_for_tuning"],
            "sealed_v8_text_used_for_training": False,
            "sealed_v8_measurement_used_as_taxonomy_only": True,
            "v9_primary_review_human_approved": primary["policy"]["human_review_confirmation_recorded"],
            "v9_constraint_operation_extension_human_approved": extension["policy"]["human_review_confirmation_recorded"],
            "v9_nonsealed_replay_gate_passed": gate_passed,
            "raw_debate_logs_direct_training_allowed": False,
            "same_cycle_promotion_allowed": False,
            "fresh_sealed_successor_required_before_measurement": True,
        },
        "baseline": {
            "fixture": fixture_name,
            "case_count": metrics["case_count"],
            "intent_accuracy": metrics["intent_accuracy"],
            "critical_signal_recall": metrics["critical_signal_recall"],
            "operation_exact_match": metrics["operation_exact_match"],
            "constraint_exact_match": metrics["constraint_exact_match"],
            "risk_exact_match": metrics["risk_exact_match"],
            "sealed_error_count": len(metrics["errors"]),
            "readiness_decision_after_measurement": "blocked",
            "blocked_reasons": ["sealed_fixture_not_available"],
        },
        "targets": _metric_targets(),
        "taxonomy": _taxonomy(measurement),
        "nonsealed_recovery_summary": {
            "source_candidate_count": selection["summary"]["source_candidate_count"],
            "primary_review_count": primary["summary"]["adopted_count"],
            "constraint_operation_extension_count": extension["summary"]["case_count"],
            "v9_focused_case_count": v9_case_count,
            "v9_primary_review_exact": primary["measurement"]["error_count"] == 0,
            "v9_constraint_operation_extension_exact": extension["measurement"]["error_count"] == 0,
            "v9_primary_operation_exact_match": primary["measurement"]["operation_exact_match"],
            "v9_primary_constraint_exact_match": primary["measurement"]["constraint_exact_match"],
            "v9_extension_operation_exact_match": extension["measurement"]["operation_exact_match"],
            "v9_extension_constraint_exact_match": extension["measurement"]["constraint_exact_match"],
            "primary_category_counts": primary["summary"]["by_category"],
            "extension_category_counts": extension["summary"]["by_category"],
        },
        "pre_rotation_gates": {
            "prior_v8_nonsealed_gate_required": True,
            "v9_primary_review_exact_required": True,
            "v9_constraint_operation_extension_exact_required": True,
            "v9_nonsealed_gate_error_count_max": 0,
            "sealed_overlap_count_required": 0,
        },
        "roadmap": _roadmap(gate_passed),
        "next_action": "roadmap_v9_step6_sealed_rotation_review" if gate_passed else "roadmap_v9_step5_nonsealed_replay_gate",
    }
    if gate:
        payload["sources"]["v9_nonsealed_replay_gate"] = _rel(V9_GATE_PATH)
        payload["step5_nonsealed_replay_gate"] = {
            "output": "build\\v9_nonsealed_replay_gate_report_v1.json",
            "passed": gate["passed"],
            "summary": gate["summary"],
            "policy": gate["policy"],
        }
    payload = _preserve_step6_review_state(payload)
    payload = _preserve_step7_rotation_state(payload)
    return _preserve_step8_measurement_state(payload)


def _write_markdown(payload: dict[str, Any]) -> None:
    baseline = payload["baseline"]
    targets = payload["targets"]
    taxonomy = payload["taxonomy"]
    recovery = payload["nonsealed_recovery_summary"]
    lines = [
        "# PLM V9 Roadmap: Exactness Recovery And Fresh Rotation",
        "",
        "Updated: 2026-06-25",
        "",
        "## Contract",
        "",
        "- Sealed v8 is consumed and may be used only as aggregate taxonomy.",
        "- Sealed v8 text and labels must not be copied into training, review, or non-sealed fixtures.",
        "- V9 uses human-approved non-sealed primary-review and constraint/operation extension lanes.",
        "- Same-cycle promotion remains disallowed.",
        "- A fresh sealed v9 fixture is required before the next adjudicating measurement.",
        "",
        "## Baseline And Targets",
        "",
        "| Metric | V8 sealed | V9 minimum | V9 stretch |",
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
    lines.extend(["", "## Nonsealed Recovery", ""])
    lines.append(f"- primary_review: {recovery['primary_review_count']} cases, exact={str(recovery['v9_primary_review_exact']).lower()}")
    lines.append(f"- constraint_operation_extension: {recovery['constraint_operation_extension_count']} cases, exact={str(recovery['v9_constraint_operation_extension_exact']).lower()}")
    lines.append(f"- focused_v9_case_count: {recovery['v9_focused_case_count']}")
    if payload.get("step5_nonsealed_replay_gate"):
        gate = payload["step5_nonsealed_replay_gate"]["summary"]
        lines.append(f"- v9_nonsealed_replay_gate: passed, total_case_count={gate['total_case_count']}, required_error_count={gate['required_error_count']}")
    lines.extend(["", "## Focus Areas", ""])
    for item in taxonomy["focus_areas"]:
        lines.append(f"{item['priority']}. {item['id']}: {item['generalized_issue']}")
    lines.extend(["", "## Roadmap", "", "| Step | Name | Output | Status |", "|---:|---|---|---|"])
    for step in payload["roadmap"]:
        lines.append(f"| {step['step']} | {step['name']} | `{step['output']}` | {step['status']} |")
    lines.extend(
        [
            "",
            "## Step 4 Output",
            "",
            "`build\\v9_accumulated_primary_review_replay_report_v1.json` and `build\\v9_constraint_operation_extension_replay_report_v1.json` are exact on their human-reviewed non-sealed lanes. They are not sealed evidence and are not same-cycle promotion evidence.",
        ]
    )
    if payload.get("step5_nonsealed_replay_gate"):
        lines.extend(
            [
                "",
                "## Step 5 Output",
                "",
                "`build\\v9_nonsealed_replay_gate_report_v1.json` passed. It replays V8 approved recovery, V9 primary review, and the V9 constraint/operation extension exactly. Step 6 is sealed V9 rotation review.",
            ]
        )
    if payload.get("step6_sealed_rotation_review"):
        lines.extend(
            [
                "",
                "## Step 6 Output",
                "",
                "`build\\v9_sealed_rotation_review_v1.json` reports `eligible_for_fresh_sealed_v9_rotation`. It confirms that the V9 non-sealed replay gate passed, `pattern_language_sealed_v8.json` is consumed, no active sealed fixture exists, and `pattern_language_sealed_v9.json` has not been created. This review does not create, open, or measure sealed v9. Step 7 is now sealed V9 rotation.",
            ]
        )
    if payload.get("step7_sealed_rotation"):
        rotation = payload["step7_sealed_rotation"]
        lines.extend(
            [
                "",
                "## Step 7 Output",
                "",
                f"`build\\v9_sealed_rotation_report_v1.json` created `tests\\fixtures\\pattern_language_sealed_v9.json` as the active unopened sealed fixture. It has {rotation['summary']['case_count']} cases, predecessor `pattern_language_sealed_v8.json`, measured `False`, reviewed `False`. Step 8 is the one-time sealed v9 measurement.",
            ]
        )
    if payload.get("step8_sealed_measurement"):
        measurement = payload["step8_sealed_measurement"]["measurements"]
        lines.extend(
            [
                "",
                "## Step 8 Output",
                "",
                "`build\pattern_language_sealed_v9_measurement_report.json` measured the active sealed v9 fixture once and consumed it. "
                f"Results: intent_accuracy `{measurement['intent_accuracy']:.6f}`, "
                f"critical_signal_recall `{measurement['critical_signal_recall']:.6f}`, "
                f"operation_exact_match `{measurement['operation_exact_match']:.6f}`, "
                f"constraint_exact_match `{measurement['constraint_exact_match']:.6f}`, "
                f"risk_exact_match `{measurement['risk_exact_match']:.6f}`, errors `{measurement['error_count']}`. "
                "Sealed labels remain measurement-only and V10 taxonomy/rotation is required before tuning.",
            ]
        )
    OUTPUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def _update_v8_roadmap() -> None:
    roadmap = V8_ROADMAP_PATH.read_text(encoding="utf-8")
    section = (
        "## Step 9 Output\n\n"
        "`build\\v9_targets_and_roadmap_v1.json` and `docs\\PLM_V9_ROADMAP.md` convert the consumed sealed v8 result into aggregate V9 taxonomy, record the human-approved V9 non-sealed recovery lanes, and set the next action to the V9 non-sealed replay gate or sealed V9 rotation review depending on gate status. Sealed v8 text and labels remain excluded from training.\n"
    )
    if "## Step 9 Output" in roadmap:
        head, _ = roadmap.split("## Step 9 Output", 1)
        roadmap = head.rstrip() + "\n\n" + section
    else:
        roadmap = roadmap.rstrip() + "\n\n" + section
    V8_ROADMAP_PATH.write_text(roadmap, encoding="utf-8", newline="\n")


def _update_main_roadmap(payload: dict[str, Any]) -> None:
    marker = "## PLM V9: Exactness Recovery And Fresh Rotation"
    main = MAIN_ROADMAP_PATH.read_text(encoding="utf-8")
    baseline = payload["baseline"]
    gate_done = bool(payload.get("step5_nonsealed_replay_gate", {}).get("passed"))
    step6_done = bool(payload.get("step6_sealed_rotation_review", {}).get("passed"))
    step7_done = bool(payload.get("step7_sealed_rotation", {}).get("passed"))
    step8_done = bool(payload.get("step8_sealed_measurement"))
    if step8_done:
        status = "V9 Step 8 sealed v9 measurement completed; sealed v9 consumed; V10 taxonomy and fresh rotation required before tuning."
    elif step7_done:
        status = "V9 Step 7 sealed v9 rotation completed; sealed v9 active/unmeasured; Step 8 one-time sealed v9 measurement next."
    elif step6_done:
        status = "V9 Step 6 sealed rotation review completed; Step 7 sealed v9 rotation next."
    elif gate_done:
        status = "V9 Step 5 non-sealed replay gate passed; Step 6 sealed V9 rotation review next."
    else:
        status = "V9 Step 4 non-sealed focused recovery completed; Step 5 non-sealed replay gate next."
    gate_line = "Non-sealed replay gate report: `build/v9_nonsealed_replay_gate_report_v1.json`\n" if gate_done else ""
    review_line = "Sealed v9 rotation review: `build/v9_sealed_rotation_review_v1.json`\n" if step6_done else ""
    rotation_line = "Sealed v9 rotation report: `build/v9_sealed_rotation_report_v1.json`\nSealed v9 fixture: `tests/fixtures/pattern_language_sealed_v9.json`\n" if step7_done else ""
    measurement_line = "Sealed v9 measurement: `build/pattern_language_sealed_v9_measurement_report.json`\nSealed v9 summary: `build/v9_step8_measurement_summary.md`\n" if step8_done else ""
    if step8_done:
        step8 = payload["step8_sealed_measurement"]["measurements"]
        closure = f"Step 8 measured sealed v9 once and consumed it: intent_accuracy {step8['intent_accuracy']:.6f}, critical_signal_recall {step8['critical_signal_recall']:.6f}, operation_exact_match {step8['operation_exact_match']:.6f}, constraint_exact_match {step8['constraint_exact_match']:.6f}, risk_exact_match {step8['risk_exact_match']:.6f}, errors {step8['error_count']}. Use this result for V10 taxonomy and fresh rotation planning, not same-cycle tuning."
    elif step7_done:
        closure = "The current V9 non-sealed recovery lanes cover 58 focused cases exactly; sealed v9 is now active and unopened, so Step 8 may measure it once."
    else:
        closure = "The current V9 non-sealed recovery lanes cover 58 focused cases exactly; sealed v9 rotation is still required before adjudicating measurement."
    section = f"""
{marker}

Status: {status}

Primary roadmap: `docs/PLM_V9_ROADMAP.md`
Targets and taxonomy: `build/v9_targets_and_roadmap_v1.json`
Candidate selection: `build/v9_accumulated_log_candidate_selection_v1.json`
Primary review replay: `build/v9_accumulated_primary_review_replay_report_v1.json`
Constraint/operation extension replay: `build/v9_constraint_operation_extension_replay_report_v1.json`
{gate_line}{review_line}{rotation_line}{measurement_line}Baseline sealed v8 measurement: `build/pattern_language_sealed_v8_measurement_report.json`

V9 uses sealed v8 measurement only as aggregate taxonomy. Sealed v8 text and labels are not training data. V8 measured intent_accuracy {baseline['intent_accuracy']:.6f}, critical_signal_recall {baseline['critical_signal_recall']:.6f}, operation_exact_match {baseline['operation_exact_match']:.6f}, constraint_exact_match {baseline['constraint_exact_match']:.6f}, risk_exact_match {baseline['risk_exact_match']:.6f}, errors {baseline['sealed_error_count']}. {closure}
""".strip()
    if marker in main:
        head, rest = main.split(marker, 1)
        idx = rest.find("\n## ")
        if idx == -1:
            main = head.rstrip() + "\n\n" + section + "\n"
        else:
            main = head.rstrip() + "\n\n" + section + "\n\n" + rest[idx + 1 :]
    else:
        main = main.rstrip() + "\n\n" + section + "\n"
    MAIN_ROADMAP_PATH.write_text(main, encoding="utf-8", newline="\n")


def main() -> None:
    payload = build_payload()
    _write_json(OUTPUT_JSON, payload)
    _write_markdown(payload)
    _update_v8_roadmap()
    _update_main_roadmap(payload)
    print(json.dumps({"status": payload["status"], "next_action": payload["next_action"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

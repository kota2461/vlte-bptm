"""Create the V10 targets, taxonomy, and roadmap.

Sealed v9 is consumed. This script uses the sealed v9 measurement only as
aggregate taxonomy and records the V10 Thought Color bridge only as a
non-sealed router-generalization replay surface. The bridge fixture is not
training data and is not sealed evidence.
"""

import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
MEASUREMENT_PATH = ROOT / "build" / "pattern_language_sealed_v9_measurement_report.json"
READINESS_PATH = ROOT / "build" / "plm_measurement_readiness_review.json"
REGISTRY_PATH = ROOT / "tests" / "fixtures" / "pattern_language_fixture_registry.json"
V9_GATE_PATH = ROOT / "build" / "v9_nonsealed_replay_gate_report_v1.json"
BRIDGE_DECISION_PATH = ROOT / "build" / "v10_thought_color_bridge_isolated_adoption_decision_v1.json"
BRIDGE_REPLAY_PATH = ROOT / "build" / "v10_thought_color_bridge_isolated_replay_report_v1.json"
BRIDGE_BENCHMARK_PATH = ROOT / "tests" / "fixtures" / "v10_thought_color_bridge_isolated_benchmark_v1.json"
V10_GATE_PATH = ROOT / "build" / "v10_mainline_replay_gate_report_v1.json"
V10_ROTATION_REVIEW_PATH = ROOT / "build" / "v10_sealed_rotation_review_v1.json"
V10_ROTATION_REPORT_PATH = ROOT / "build" / "v10_sealed_rotation_report_v1.json"
V10_MEASUREMENT_PATH = ROOT / "build" / "pattern_language_sealed_v10_measurement_report.json"
V10_STEP6_SUMMARY_PATH = ROOT / "build" / "v10_step6_measurement_summary.md"
V11_POST_V10_DIAGNOSTIC_PATH = ROOT / "build" / "v11_post_v10_measurement_diagnostic_v1.json"
SEALED_V10_PATH = ROOT / "tests" / "fixtures" / "pattern_language_sealed_v10.json"
OUTPUT_JSON = ROOT / "build" / "v10_targets_and_roadmap_v1.json"
OUTPUT_MD = ROOT / "docs" / "PLM_V10_ROADMAP.md"
V9_ROADMAP_PATH = ROOT / "docs" / "PLM_V9_ROADMAP.md"
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


def _field_counts(errors: list[dict[str, Any]]) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for error in errors:
        counts.update(error["fields"])
    return dict(sorted(counts.items()))


def _critical_signal_misses(metrics: dict[str, Any]) -> dict[str, int]:
    return {
        name: round(signal["support"] * (1.0 - signal["recall"]))
        for name, signal in metrics["critical_signals"].items()
    }


def _critical_signal_miss_count(signals: dict[str, dict[str, Any]]) -> int:
    return sum(round(item["support"] * (1.0 - item["recall"])) for item in signals.values())


def _metric_targets() -> dict[str, Any]:
    return {
        "minimum": {
            "intent_accuracy": 0.928571,
            "critical_signal_recall": 0.928571,
            "operation_exact_match": 0.892857,
            "constraint_exact_match": 0.857143,
            "risk_exact_match": 0.857143,
            "sealed_error_count_max": 8,
            "critical_signal_miss_count_max": 1,
        },
        "stretch": {
            "intent_accuracy": 0.964286,
            "critical_signal_recall": 1.0,
            "operation_exact_match": 0.928571,
            "constraint_exact_match": 0.928571,
            "risk_exact_match": 0.928571,
            "sealed_error_count_max": 5,
            "critical_signal_miss_count_max": 0,
        },
        "granularity": {
            "case_metric_step": 0.035714,
            "critical_signal_step": 0.071429,
        },
    }


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
            "id": "constraint_exactness_recovery",
            "priority": 1,
            "generalized_issue": "sealed v9 shows constraints as the largest exact-match gap, especially ask-first, neutrality, and overclaim controls",
            "evidence": {
                "constraints": field_counts["constraints"],
                "constraint_exact_match": metrics["constraint_exact_match"],
            },
            "covered_by_v10_bridge": True,
        },
        {
            "id": "risk_ladder_recovery",
            "priority": 1,
            "generalized_issue": "risk level and risk flags need steadier separation after sealed v9",
            "evidence": {
                "risk": field_counts["risk"],
                "risk_exact_match": metrics["risk_exact_match"],
            },
            "covered_by_v10_bridge": True,
        },
        {
            "id": "missing_multiple_information_state",
            "priority": 1,
            "generalized_issue": "missing context, unverified claims, and multiple-intent signals still need robust detection and non-collapse",
            "evidence": {
                "information_state": field_counts["information_state"],
                "critical_signal_misses": misses,
                "critical_signal_recall": metrics["critical_signal_recall"],
            },
            "covered_by_v10_bridge": True,
        },
        {
            "id": "operation_order_terminality",
            "priority": 2,
            "generalized_issue": "terminal operation and ordered multi-step routes still drift in sealed v9",
            "evidence": {
                "operations": field_counts["operations"],
                "operation_exact_match": metrics["operation_exact_match"],
            },
            "covered_by_v10_bridge": True,
        },
        {
            "id": "intent_boundary_tail",
            "priority": 2,
            "generalized_issue": "respond/verify, clarify/verify, and verify/summarize boundaries remain the intent tail to protect",
            "evidence": {
                "primary_intent": field_counts["primary_intent"],
                "transitions": dict(sorted(transitions.items())),
            },
            "covered_by_v10_bridge": True,
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
        {"step": 1, "name": "post_v9_measurement_taxonomy", "output": "build\\v10_targets_and_roadmap_v1.json", "status": "completed"},
        {"step": 2, "name": "v10_thought_color_bridge_mainline_adoption_review", "output": "build\\v10_thought_color_bridge_isolated_adoption_decision_v1.json", "status": "completed"},
        {"step": 3, "name": "v10_mainline_nonsealed_replay_gate", "output": "build\\v10_mainline_replay_gate_report_v1.json", "status": "completed" if gate_passed else "next"},
        {"step": 4, "name": "sealed_v10_rotation_review", "output": "build\\v10_sealed_rotation_review_v1.json", "status": "next" if gate_passed else "pending"},
        {"step": 5, "name": "sealed_v10_rotation", "output": "tests\\fixtures\\pattern_language_sealed_v10.json", "status": "pending"},
        {"step": 6, "name": "sealed_v10_one_time_measurement", "output": "build\\pattern_language_sealed_v10_measurement_report.json", "status": "pending"},
    ]


def _existing_v10_gate() -> dict[str, Any] | None:
    if not V10_GATE_PATH.exists():
        return None
    gate = _load_json(V10_GATE_PATH)
    if gate.get("schema_version") != "v10-mainline-replay-gate-report.v1":
        return None
    return gate




def _existing_step4_review() -> dict[str, Any] | None:
    if not V10_ROTATION_REVIEW_PATH.exists():
        return None
    review = _load_json(V10_ROTATION_REVIEW_PATH)
    if review.get("schema_version") != "v10-sealed-rotation-review.v1":
        return None
    if review.get("passed") is not True:
        return None
    return review


def _preserve_step4_review_state(payload: dict[str, Any]) -> dict[str, Any]:
    review = _existing_step4_review()
    if review is None:
        return payload
    payload["generated_at"] = review["reviewed_at"]
    payload["status"] = "step4_sealed_v10_rotation_review_completed_step5_rotation_next"
    payload["next_action"] = "roadmap_v10_step5_generate_and_rotate_sealed_v10_fixture"
    payload["sources"]["v10_sealed_rotation_review"] = _rel(V10_ROTATION_REVIEW_PATH)
    for item in payload["roadmap"]:
        if item["step"] == 4:
            item["status"] = "completed"
        elif item["step"] == 5:
            item["status"] = "next"
    payload["step4_sealed_rotation_review"] = {
        "output": "build\\v10_sealed_rotation_review_v1.json",
        "decision": review["decision"],
        "passed": review["passed"],
        "sealed_v10_fixture_created_now": False,
        "sealed_v10_opened_for_measurement": False,
        "same_cycle_promotion_allowed": False,
        "requires_fresh_sealed_v10_before_measurement": True,
        "summary": {
            "required_error_count": review["gate_summary"]["required_error_count"],
            "active_sealed_fixtures": len(review["registry_state"]["active_sealed_fixtures"]),
            "blocker_count": len(review["blockers"]),
        },
    }
    payload["roadmap_decision"] = {
        "can_advance": True,
        "advance_to": "sealed_v10_rotation",
        "blocked_reasons": [],
    }
    return payload

def _existing_step5_rotation() -> dict[str, Any] | None:
    if not V10_ROTATION_REPORT_PATH.exists():
        return None
    report = _load_json(V10_ROTATION_REPORT_PATH)
    if report.get("schema_version") != "v10-sealed-rotation-report.v1":
        return None
    rotated_to = report.get("rotated_to", {})
    if rotated_to.get("registry_name") != SEALED_V10_PATH.name:
        return None
    if rotated_to.get("status") != "active":
        return None
    if rotated_to.get("measured") is not False or rotated_to.get("reviewed") is not False:
        return None
    return report


def _preserve_step5_rotation_state(payload: dict[str, Any]) -> dict[str, Any]:
    report = _existing_step5_rotation()
    if report is None:
        return payload
    payload["generated_at"] = report["rotated_at"]
    payload["status"] = "step5_sealed_rotation_completed_step6_measurement_next"
    payload["next_action"] = "roadmap_v10_step6_measure_active_sealed_v10_once"
    payload["sources"]["v10_sealed_rotation_report"] = _rel(V10_ROTATION_REPORT_PATH)
    payload["sources"]["sealed_v10_fixture"] = _rel(SEALED_V10_PATH)
    for item in payload["roadmap"]:
        if item["step"] == 4:
            item["status"] = "completed"
        elif item["step"] == 5:
            item["status"] = "completed"
        elif item["step"] == 6:
            item["status"] = "next"
    payload["step5_sealed_rotation"] = {
        "output": "build\\v10_sealed_rotation_report_v1.json",
        "fixture": "tests\\fixtures\\pattern_language_sealed_v10.json",
        "passed": True,
        "sealed_v10_opened_for_measurement": False,
        "sealed_v10_labels_used_for_tuning": False,
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
    payload["roadmap_decision"] = {
        "can_advance": True,
        "advance_to": "sealed_v10_one_time_measurement",
        "blocked_reasons": report["readiness_after_rotation"]["blocked_reasons"],
    }
    return payload


def _existing_step6_measurement() -> dict[str, Any] | None:
    if not V10_MEASUREMENT_PATH.exists():
        return None
    measurement = _load_json(V10_MEASUREMENT_PATH)
    if measurement.get("schema_version") != "plm-sealed-measurement-report.v1":
        return None
    if measurement.get("fixture", {}).get("registry_name") != SEALED_V10_PATH.name:
        return None
    if measurement.get("registry_update", {}).get("status_after_measurement") != "consumed":
        return None
    return measurement


def _preserve_step6_measurement_state(payload: dict[str, Any]) -> dict[str, Any]:
    measurement = _existing_step6_measurement()
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
    payload["status"] = "step6_sealed_v10_measurement_completed_v11_rotation_required"
    payload["next_action"] = "roadmap_v11_step1_post_v10_measurement_taxonomy"
    payload["sources"]["sealed_v10_measurement"] = _rel(V10_MEASUREMENT_PATH)
    payload["sources"]["v10_step6_summary"] = _rel(V10_STEP6_SUMMARY_PATH)
    for item in payload["roadmap"]:
        item["status"] = "completed"
    payload["step6_sealed_measurement"] = {
        "output": "build\\pattern_language_sealed_v10_measurement_report.json",
        "summary": "build\\v10_step6_measurement_summary.md",
        "fixture": "tests\\fixtures\\pattern_language_sealed_v10.json",
        "sealed_fixture_opened": measurement["sealed_fixture_opened"],
        "sealed_labels_used_for_tuning": measurement["sealed_labels_used_for_tuning"],
        "passed_minimum": minimum_metrics_met and critical_signal_miss_gate_met,
        "minimum_metrics_met": minimum_metrics_met,
        "critical_signal_miss_count": critical_miss_count,
        "critical_signal_miss_gate_met": critical_signal_miss_gate_met,
        "rotation_required_before_tuning": measurement["registry_update"]["rotation_required_before_tuning"],
        "readiness_after_measurement": {
            "decision": readiness["decision"],
            "blocked_reasons": readiness["blocked_reasons"],
            "sealed_fixture": readiness["sealed_fixture"],
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
    if V11_POST_V10_DIAGNOSTIC_PATH.exists():
        diagnostic = _load_json(V11_POST_V10_DIAGNOSTIC_PATH)
        if diagnostic.get("schema_version") == "v11-post-v10-measurement-diagnostic.v1":
            payload["sources"]["v11_post_v10_measurement_diagnostic"] = _rel(V11_POST_V10_DIAGNOSTIC_PATH)
            payload["post_v10_measurement_diagnostic"] = {
                "output": "build\\v11_post_v10_measurement_diagnostic_v1.json",
                "status": diagnostic["status"],
                "policy": diagnostic["policy"],
                "failure_mode_summary": diagnostic["failure_mode_summary"],
                "focus_area_ids": [item["id"] for item in diagnostic["focus_areas"]],
                "next_action": diagnostic["next_action"],
            }
    payload["roadmap_decision"] = {
        "can_advance": True,
        "advance_to": "v11_post_v10_measurement_taxonomy",
        "blocked_reasons": [],
    }
    return payload


def _bridge_summary() -> dict[str, Any]:
    decision = _load_json(BRIDGE_DECISION_PATH)
    replay = _load_json(BRIDGE_REPLAY_PATH)
    measurement = replay["measurement"]
    return {
        "adopted_count": decision["adopted_count"],
        "category_counts": decision["category_counts"],
        "review_status": decision["review_status"],
        "source_mainline_training_allowed": decision["policy"]["source_mainline_training_allowed"],
        "isolated_rewrite_fixture_training_allowed": decision["policy"]["isolated_rewrite_fixture_training_allowed"],
        "isolated_current_route_measurement_is_gate": decision["policy"]["current_route_measurement_is_gate"],
        "mainline_allowed_use": "router_generalization_and_nonsealed_replay_only",
        "isolated_measurement": {
            "case_count": measurement["case_count"],
            "intent_accuracy": measurement["intent_accuracy"],
            "critical_signal_recall": measurement["critical_signal_recall"],
            "operation_exact_match": measurement["operation_exact_match"],
            "constraint_exact_match": measurement["constraint_exact_match"],
            "risk_exact_match": measurement["risk_exact_match"],
            "error_count": measurement["error_count"],
        },
    }



def _v10_plus_learning_lanes() -> dict[str, Any]:
    return {
        "schema_version": "v10-plus-learning-lanes.v1",
        "status": "planned_after_v10_rotation_review",
        "lane_relationship": {
            "keep_separate_until_review": True,
            "do_not_mix_answer_only_with_router_judgment": True,
            "answer_only_must_be_converted_to_probes_before_mainline_gate": True,
        },
        "recommended_initial_mix": {
            "router_judgment_lane": 0.6,
            "boundary_pairs_from_router_judgment": 0.2,
            "answer_prototype_lane": 0.2,
        },
        "router_judgment_lane": {
            "priority": 1,
            "purpose": "learn route decisions, boundary reasons, near-misses, and failure/suppression hints",
            "data_unit": "distilled router trace, not raw router log",
            "mainline_value": "high",
            "training_allowed_after_human_review": True,
            "direct_mainline_candidate_allowed": True,
            "required_fields": [
                "input",
                "expected_semantic_packet",
                "router_trace",
                "candidate_routes",
                "chosen_route",
                "near_miss",
                "judgment_note",
                "source_policy",
            ],
            "allowed_use": [
                "boundary_judgment_fixture",
                "failure_memory_or_suppression_review",
                "nonsealed_replay_gate_candidate",
            ],
            "must_not": [
                "store_raw_log_as_training_data",
                "use_sealed_measurement_text_or_labels",
                "promote_without_human_review",
            ],
        },
        "answer_prototype_lane": {
            "priority": 2,
            "purpose": "learn answer shape, response style, output type, and generate question probes without overfitting to user question wording",
            "data_unit": "answer-only prototype plus generated probes",
            "mainline_value": "medium_as_probe_source_high_as_style_reference",
            "separated_from_router_training": True,
            "direct_semantic_packet_training_allowed": False,
            "training_allowed_after_probe_conversion_and_review": True,
            "required_fields": [
                "answer_text",
                "output_type",
                "likely_operations",
                "style_tags",
                "generated_question_probes",
                "probe_expected_semantic_packets",
                "source_policy",
            ],
            "allowed_use": [
                "output_type_reference",
                "question_probe_generation",
                "paraphrase_or_contrast_candidate_source",
            ],
            "must_not": [
                "infer_final_input_intent_from_answer_only",
                "mix_directly_into_router_judgment_lane",
                "use_generated_probes_without_review",
            ],
            "reason_for_separation": "answer-only samples underdetermine the original input intent, so they should produce probes rather than direct semantic labels",
        },
    }


def build_payload() -> dict[str, Any]:
    measurement = _load_json(MEASUREMENT_PATH)
    readiness = _load_json(READINESS_PATH)
    registry = _load_json(REGISTRY_PATH)
    v9_gate = _load_json(V9_GATE_PATH)
    metrics = measurement["measurements"]
    fixture_name = measurement["fixture"]["registry_name"]
    registry_entry = registry["fixtures"][fixture_name]
    v10_gate = _existing_v10_gate()
    gate_passed = bool(v10_gate and v10_gate.get("passed") is True)
    bridge = _bridge_summary()
    payload = {
        "schema_version": "v10-targets-and-roadmap.v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": "step3_v10_mainline_replay_gate_passed_step4_rotation_review_next" if gate_passed else "step2_v10_bridge_mainline_adopted_step3_gate_next",
        "sources": {
            "sealed_v9_measurement": _rel(MEASUREMENT_PATH),
            "readiness_review": _rel(READINESS_PATH),
            "fixture_registry": _rel(REGISTRY_PATH),
            "v9_nonsealed_replay_gate": _rel(V9_GATE_PATH),
            "v10_bridge_decision": _rel(BRIDGE_DECISION_PATH),
            "v10_bridge_isolated_replay": _rel(BRIDGE_REPLAY_PATH),
            "v10_bridge_isolated_benchmark": _rel(BRIDGE_BENCHMARK_PATH),
        },
        "policy": {
            "sealed_v9_consumed": registry_entry["status"] == "consumed",
            "sealed_v9_labels_used_for_tuning": measurement["sealed_labels_used_for_tuning"],
            "sealed_v9_text_used_for_training": False,
            "sealed_v9_measurement_used_as_taxonomy_only": True,
            "v9_nonsealed_replay_gate_passed": v9_gate["passed"],
            "thought_color_source_scope": "experiment_only",
            "thought_color_source_mainline_training_allowed": False,
            "v10_bridge_mainline_training_allowed": False,
            "v10_bridge_mainline_allowed_use": "router_generalization_and_nonsealed_replay_only",
            "v10_bridge_human_reviewed": bridge["review_status"] == "human_reviewed_for_isolated_rewrite",
            "raw_thought_color_samples_direct_training_allowed": False,
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
            "critical_signal_miss_count": _critical_signal_miss_count(metrics["critical_signals"]),
            "readiness_decision_after_measurement": "blocked",
            "blocked_reasons": ["sealed_fixture_not_available"],
        },
        "targets": _metric_targets(),
        "taxonomy": _taxonomy(measurement),
        "thought_color_bridge_summary": bridge,
        "v10_plus_learning_lanes": _v10_plus_learning_lanes(),
        "pre_rotation_gates": {
            "prior_v9_nonsealed_gate_required": True,
            "v10_bridge_mainline_replay_exact_required": True,
            "v10_mainline_gate_error_count_max": 0,
            "sealed_overlap_count_required": 0,
            "full_regression_required": "python -B -m pytest",
        },
        "roadmap": _roadmap(gate_passed),
        "next_action": "roadmap_v10_step4_sealed_rotation_review" if gate_passed else "roadmap_v10_step3_mainline_nonsealed_replay_gate",
        "roadmap_decision": {
            "can_advance": gate_passed,
            "advance_to": "sealed_v10_rotation_review" if gate_passed else None,
            "blocked_reasons": [] if gate_passed else ["v10_mainline_replay_gate_not_run"],
        },
    }
    if v10_gate:
        payload["sources"]["v10_mainline_replay_gate"] = _rel(V10_GATE_PATH)
        payload["step3_mainline_replay_gate"] = {
            "output": "build\\v10_mainline_replay_gate_report_v1.json",
            "passed": v10_gate["passed"],
            "summary": v10_gate["summary"],
            "policy": v10_gate["policy"],
        }
        payload["roadmap_decision"] = v10_gate["roadmap_decision"]
    return _preserve_step6_measurement_state(_preserve_step5_rotation_state(_preserve_step4_review_state(payload)))


def _write_markdown(payload: dict[str, Any]) -> None:
    baseline = payload["baseline"]
    targets = payload["targets"]
    bridge = payload["thought_color_bridge_summary"]
    lines = [
        "# PLM V10 Roadmap: Bridge Generalization And Exactness Recovery",
        "",
        "Updated: 2026-06-27",
        "",
        "## Contract",
        "",
        "- Sealed v9 is consumed and may be used only as aggregate taxonomy.",
        "- Sealed v9 text and labels must not be copied into training, review, or non-sealed fixtures.",
        "- Thought Color bridge sources remain experiment-scope and are not direct mainline training data.",
        "- V10 may use the bridge only as router generalization and non-sealed replay evidence after human review.",
        "- Same-cycle promotion remains disallowed; a fresh sealed v10 fixture is required before adjudicating measurement.",
        "",
        "## Baseline And Targets",
        "",
        "| Metric | V9 sealed | V10 minimum | V10 stretch |",
        "|---|---:|---:|---:|",
        f"| intent_accuracy | {baseline['intent_accuracy']:.6f} | {targets['minimum']['intent_accuracy']:.6f} | {targets['stretch']['intent_accuracy']:.6f} |",
        f"| critical_signal_recall | {baseline['critical_signal_recall']:.6f} | {targets['minimum']['critical_signal_recall']:.6f} | {targets['stretch']['critical_signal_recall']:.6f} |",
        f"| operation_exact_match | {baseline['operation_exact_match']:.6f} | {targets['minimum']['operation_exact_match']:.6f} | {targets['stretch']['operation_exact_match']:.6f} |",
        f"| constraint_exact_match | {baseline['constraint_exact_match']:.6f} | {targets['minimum']['constraint_exact_match']:.6f} | {targets['stretch']['constraint_exact_match']:.6f} |",
        f"| risk_exact_match | {baseline['risk_exact_match']:.6f} | {targets['minimum']['risk_exact_match']:.6f} | {targets['stretch']['risk_exact_match']:.6f} |",
        f"| sealed_error_count | {baseline['sealed_error_count']} | <= {targets['minimum']['sealed_error_count_max']} | <= {targets['stretch']['sealed_error_count_max']} |",
        "",
        "## V10 Bridge Mainline Adoption",
        "",
        f"- adopted_count: {bridge['adopted_count']}",
        f"- allowed_use: {bridge['mainline_allowed_use']}",
        f"- source_mainline_training_allowed: {str(bridge['source_mainline_training_allowed']).lower()}",
        f"- isolated_rewrite_fixture_training_allowed: {str(bridge['isolated_rewrite_fixture_training_allowed']).lower()}",
        f"- isolated_error_count: {bridge['isolated_measurement']['error_count']}",
        f"- isolated_constraint_exact_match: {bridge['isolated_measurement']['constraint_exact_match']:.6f}",
        f"- isolated_operation_exact_match: {bridge['isolated_measurement']['operation_exact_match']:.6f}",
        "",
        "## V10+ Learning Lanes",
        "",
        "| Lane | Priority | Mainline Role | Direct Training | Separation Rule |",
        "|---|---:|---|---|---|",
        "| router_judgment_lane | 1 | boundary judgment / near-miss / failure memory | human-reviewed nonsealed only | distilled trace, not raw log |",
        "| answer_prototype_lane | 2 | output prototype / question probe source | no direct semantic-packet training | keep separate until probes are reviewed |",
        "",
        "Answer-only samples are useful, but they underdetermine the original input intent. They should be stored as a separate prototype lane and converted into reviewed question probes before any mainline replay gate.",
        "Router judgment samples are closer to the mainline PLM objective because they preserve candidate routes, chosen route, near-miss, and judgment reason.",
        "",
        "## Error Taxonomy",
        "",
        "| Field | Count |",
        "|---|---:|",
    ]
    for field, count in payload["taxonomy"]["field_error_counts"].items():
        lines.append(f"| {field} | {count} |")
    lines.extend(["", "## Focus Areas", ""])
    for item in payload["taxonomy"]["focus_areas"]:
        lines.append(f"{item['priority']}. {item['id']}: {item['generalized_issue']}")
    lines.extend(["", "## Roadmap", "", "| Step | Name | Output | Status |", "|---:|---|---|---|"])
    for step in payload["roadmap"]:
        lines.append(f"| {step['step']} | {step['name']} | `{step['output']}` | {step['status']} |")
    if payload.get("step4_sealed_rotation_review"):
        review = payload["step4_sealed_rotation_review"]
        lines.extend(
            [
                "",
                "## Step 4 Output",
                "",
                "`build\\v10_sealed_rotation_review_v1.json` reports `eligible_for_fresh_sealed_v10_rotation`. It confirms that the V10 mainline replay gate passed, `pattern_language_sealed_v9.json` is consumed, no active sealed fixture exists, and `pattern_language_sealed_v10.json` has not been created. This review does not create, open, or measure sealed v10. Step 5 is now sealed V10 rotation.",
                f"- required_error_count: {review['summary']['required_error_count']}",
                f"- blocker_count: {review['summary']['blocker_count']}",
            ]
        )
    if payload.get("step5_sealed_rotation"):
        rotation = payload["step5_sealed_rotation"]
        lines.extend(
            [
                "",
                "## Step 5 Output",
                "",
                "`build\\v10_sealed_rotation_report_v1.json` rotated `tests\\fixtures\\pattern_language_sealed_v10.json` into the active sealed slot. The fixture is active, unmeasured, and unreviewed; sealed v10 labels remain unavailable for tuning. Step 6 is the one-time sealed v10 measurement.",
                f"- case_count: {rotation['summary']['case_count']}",
                f"- readiness_decision: {rotation['summary']['readiness_decision']}",
                f"- measured: {str(rotation['summary']['measured']).lower()}",
                f"- reviewed: {str(rotation['summary']['reviewed']).lower()}",
            ]
        )
    if payload.get("step6_sealed_measurement"):
        step6 = payload["step6_sealed_measurement"]
        measurement = step6["measurements"]
        lines.extend(
            [
                "",
                "## Step 6 Output",
                "",
                "`build\\pattern_language_sealed_v10_measurement_report.json` measured the active sealed v10 fixture once and consumed it. Sealed v10 labels remain measurement-only; V11 taxonomy and fresh rotation are required before any tuning from this result.",
                f"- intent_accuracy: {measurement['intent_accuracy']:.6f}",
                f"- critical_signal_recall: {measurement['critical_signal_recall']:.6f}",
                f"- operation_exact_match: {measurement['operation_exact_match']:.6f}",
                f"- constraint_exact_match: {measurement['constraint_exact_match']:.6f}",
                f"- risk_exact_match: {measurement['risk_exact_match']:.6f}",
                f"- error_count: {measurement['error_count']}",
                f"- passed_minimum: {str(step6['passed_minimum']).lower()}",
                f"- rotation_required_before_tuning: {str(step6['rotation_required_before_tuning']).lower()}",
            ]
        )
    if payload.get("post_v10_measurement_diagnostic"):
        diagnostic = payload["post_v10_measurement_diagnostic"]
        lines.extend(
            [
                "",
                "## Post-V10 Diagnostic",
                "",
                "`build\\v11_post_v10_measurement_diagnostic_v1.json` records value-level diffs, failure-mode separation, and bridge transfer-gap evidence. It is taxonomy-only, not training data, not a replay gate, and not same-cycle promotion evidence.",
                f"- status: {diagnostic['status']}",
                f"- focus_areas: {diagnostic['focus_area_ids']}",
                f"- next_action: {diagnostic['next_action']}",
            ]
        )
    decision = payload["roadmap_decision"]
    lines.extend(
        [
            "",
            "## Decision",
            "",
            f"- can_advance: {str(decision['can_advance']).lower()}",
            f"- advance_to: {decision['advance_to']}",
            f"- blocked_reasons: {decision['blocked_reasons']}",
        ]
    )
    OUTPUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def _update_v9_roadmap() -> None:
    roadmap = V9_ROADMAP_PATH.read_text(encoding="utf-8")
    section = (
        "## Step 9 Output\n\n"
        "`build\\v10_targets_and_roadmap_v1.json` and `docs\\PLM_V10_ROADMAP.md` convert the consumed sealed v9 result into aggregate V10 taxonomy and record the Thought Color bridge only as non-sealed router-generalization evidence. Sealed v9 text and labels remain excluded from training.\n"
    )
    if "## Step 9 Output" in roadmap:
        head, rest = roadmap.split("## Step 9 Output", 1)
        idx = rest.find("\n## ")
        if idx == -1:
            roadmap = head.rstrip() + "\n\n" + section
        else:
            roadmap = head.rstrip() + "\n\n" + section + "\n" + rest[idx + 1 :]
    else:
        roadmap = roadmap.rstrip() + "\n\n" + section
    V9_ROADMAP_PATH.write_text(roadmap, encoding="utf-8", newline="\n")


def _update_main_roadmap(payload: dict[str, Any]) -> None:
    marker = "## PLM V10: Bridge Generalization And Exactness Recovery"
    main = MAIN_ROADMAP_PATH.read_text(encoding="utf-8")
    baseline = payload["baseline"]
    decision = payload["roadmap_decision"]
    step4_done = bool(payload.get("step4_sealed_rotation_review", {}).get("passed"))
    step5_done = bool(payload.get("step5_sealed_rotation", {}).get("passed"))
    step6_done = bool(payload.get("step6_sealed_measurement"))
    if step6_done:
        status = "V10 Step 6 sealed v10 measurement completed; sealed v10 consumed; V11 taxonomy and fresh rotation required before tuning."
    elif step5_done:
        status = "V10 Step 5 sealed v10 rotation completed; Step 6 sealed v10 one-time measurement next."
    elif step4_done:
        status = "V10 Step 4 sealed rotation review completed; Step 5 sealed v10 rotation next."
    else:
        status = (
            "V10 Step 3 mainline non-sealed replay gate passed; Step 4 sealed v10 rotation review next."
            if decision["can_advance"]
            else "V10 Step 2 bridge mainline adoption recorded; Step 3 mainline non-sealed replay gate next."
        )
    gate_line = "Mainline replay gate: `build/v10_mainline_replay_gate_report_v1.json`\n" if payload.get("step3_mainline_replay_gate") else ""
    review_line = "Sealed v10 rotation review: `build/v10_sealed_rotation_review_v1.json`\n" if step4_done else ""
    rotation_line = "Sealed v10 rotation report: `build/v10_sealed_rotation_report_v1.json`\n" if step5_done else ""
    fixture_line = "Sealed v10 fixture: `tests/fixtures/pattern_language_sealed_v10.json`\n" if step5_done else ""
    measurement_line = "Sealed v10 measurement: `build/pattern_language_sealed_v10_measurement_report.json`\n" if step6_done else ""
    summary_line = "Sealed v10 summary: `build/v10_step6_measurement_summary.md`\n" if step6_done else ""
    diagnostic_done = bool(payload.get("post_v10_measurement_diagnostic"))
    diagnostic_line = "Post-v10 diagnostic: `build/v11_post_v10_measurement_diagnostic_v1.json`\n" if diagnostic_done else ""
    section = f"""
{marker}

Status: {status}

Primary roadmap: `docs/PLM_V10_ROADMAP.md`
Targets and taxonomy: `build/v10_targets_and_roadmap_v1.json`
Thought Color bridge decision: `build/v10_thought_color_bridge_isolated_adoption_decision_v1.json`
Thought Color bridge replay: `build/v10_thought_color_bridge_isolated_replay_report_v1.json`
V10+ learning lanes: router_judgment_lane and separated answer_prototype_lane are recorded in `build/v10_targets_and_roadmap_v1.json`
{gate_line}{review_line}{rotation_line}{fixture_line}{measurement_line}{summary_line}{diagnostic_line}Baseline sealed v9 measurement: `build/pattern_language_sealed_v9_measurement_report.json`

V10 uses sealed v9 measurement only as aggregate taxonomy. Sealed v9 text and labels are not training data. Thought Color bridge sources are not direct mainline training data; the accepted use is router generalization plus non-sealed replay. V10+ adopts two future lanes: router judgment as the primary mainline boundary-learning lane, and answer-only prototypes as a separated probe-generation lane. V9 measured intent_accuracy {baseline['intent_accuracy']:.6f}, critical_signal_recall {baseline['critical_signal_recall']:.6f}, operation_exact_match {baseline['operation_exact_match']:.6f}, constraint_exact_match {baseline['constraint_exact_match']:.6f}, risk_exact_match {baseline['risk_exact_match']:.6f}, errors {baseline['sealed_error_count']}. Roadmap decision: can_advance={str(decision['can_advance']).lower()}, advance_to={decision['advance_to']}.
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


def _write_step6_summary(payload: dict[str, Any]) -> None:
    step6 = payload.get("step6_sealed_measurement")
    if not step6:
        return
    metrics = step6["measurements"]
    minimum = payload["targets"]["minimum"]
    lines = [
        "# V10 Step 6 Sealed Measurement Summary",
        "",
        f"- fixture: `pattern_language_sealed_v10.json`",
        f"- sealed_fixture_opened: `{step6['sealed_fixture_opened']}`",
        f"- sealed_labels_used_for_tuning: `{step6['sealed_labels_used_for_tuning']}`",
        f"- rotation_required_before_tuning: `{step6['rotation_required_before_tuning']}`",
        f"- minimum_passed: `{step6['passed_minimum']}`",
        "",
        "## Metrics",
        "",
        "| Metric | Value | Target |",
        "|---|---:|---:|",
        f"| case_count | {metrics['case_count']} | 28 |",
        f"| intent_accuracy | {metrics['intent_accuracy']:.6f} | {minimum['intent_accuracy']:.6f} |",
        f"| critical_signal_recall | {metrics['critical_signal_recall']:.6f} | {minimum['critical_signal_recall']:.6f} |",
        f"| operation_exact_match | {metrics['operation_exact_match']:.6f} | {minimum['operation_exact_match']:.6f} |",
        f"| constraint_exact_match | {metrics['constraint_exact_match']:.6f} | {minimum['constraint_exact_match']:.6f} |",
        f"| risk_exact_match | {metrics['risk_exact_match']:.6f} | {minimum['risk_exact_match']:.6f} |",
        f"| error_count | {metrics['error_count']} | <= {minimum['sealed_error_count_max']} |",
        "",
        "## Error Field Counts",
        "",
        "| Field | Count |",
        "|---|---:|",
    ]
    for field, count in metrics["error_field_counts"].items():
        lines.append(f"| {field} | {count} |")
    lines.extend(
        [
            "",
            "## Decision",
            "",
            "V10 did not meet the sealed minimum target. The sealed v10 fixture is consumed, sealed labels remain measurement-only, and V11 taxonomy plus fresh sealed rotation are required before tuning from this result.",
        ]
    )
    V10_STEP6_SUMMARY_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def main() -> None:
    payload = build_payload()
    _write_json(OUTPUT_JSON, payload)
    _write_markdown(payload)
    _write_step6_summary(payload)
    _update_v9_roadmap()
    _update_main_roadmap(payload)
    print(
        json.dumps(
            {
                "status": payload["status"],
                "next_action": payload["next_action"],
                "roadmap_decision": payload["roadmap_decision"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()

"""Create V11 targets and roadmap from v10 value-diff diagnostics.

V11 starts after sealed v10 has been measured and consumed. Sealed v10 labels
and text may be inspected only as post-measurement taxonomy. The diagnostic is
not training data, not a replay gate, and not same-cycle promotion evidence.
"""

import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from semantic_routing.reproducibility import reproducible_now_iso
V10_MEASUREMENT_PATH = ROOT / "build" / "pattern_language_sealed_v10_measurement_report.json"
V10_TARGETS_PATH = ROOT / "build" / "v10_targets_and_roadmap_v1.json"
V10_DIAGNOSTIC_PATH = ROOT / "build" / "v11_post_v10_measurement_diagnostic_v1.json"
CODE_AUDIT_TRIAGE_PATH = ROOT / "build" / "v11_code_audit_triage_v1.json"
PROFILE_LITERAL_AUDIT_PATH = ROOT / "build" / "v11_profile_literal_patch_audit_v1.json"
READINESS_PATH = ROOT / "build" / "plm_measurement_readiness_review.json"
REGISTRY_PATH = ROOT / "tests" / "fixtures" / "pattern_language_fixture_registry.json"
OUTPUT_JSON = ROOT / "build" / "v11_targets_and_roadmap_v1.json"
OUTPUT_MD = ROOT / "docs" / "PLM_V11_ROADMAP.md"
V10_ROADMAP_PATH = ROOT / "docs" / "PLM_V10_ROADMAP.md"
MAIN_ROADMAP_PATH = ROOT / "docs" / "PATTERN_LANGUAGE_MODEL_roadmap.md"


def _rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def _replace_section(text: str, marker: str, section: str) -> str:
    if marker not in text:
        return text.rstrip() + "\n\n" + section + "\n"
    head, rest = text.split(marker, 1)
    idx = rest.find("\n## ")
    if idx == -1:
        return head.rstrip() + "\n\n" + section + "\n"
    return head.rstrip() + "\n\n" + section + "\n\n" + rest[idx + 1 :]


def _metric_targets() -> dict[str, Any]:
    return {
        "minimum": {
            "intent_accuracy": 0.857143,
            "critical_signal_recall": 0.733333,
            "operation_exact_match": 0.75,
            "constraint_exact_match": 0.714286,
            "risk_exact_match": 0.785714,
            "sealed_error_count_max": 14,
            "critical_signal_miss_count_max": 4,
            "clarify_recall_min": 0.75,
            "multiple_intents_recall_min": 0.714286,
            "bridge_transfer_template_overfit_allowed": False,
        },
        "stretch": {
            "intent_accuracy": 0.928571,
            "critical_signal_recall": 0.866667,
            "operation_exact_match": 0.857143,
            "constraint_exact_match": 0.857143,
            "risk_exact_match": 0.857143,
            "sealed_error_count_max": 8,
            "critical_signal_miss_count_max": 2,
            "clarify_recall_min": 1.0,
            "multiple_intents_recall_min": 0.857143,
            "bridge_transfer_template_overfit_allowed": False,
        },
        "granularity": {
            "case_metric_step": 0.035714,
            "critical_signal_step": 0.066667,
            "clarify_recall_step": 0.25,
            "multiple_intents_recall_step": 0.142857,
        },
        "rationale": "V11 minimum is a recovery target from v10 regression, not a same-cycle promotion target. Stretch aims to regain the pre-v10 envelope while keeping bridge transfer validation mandatory.",
    }


def _taxonomy(diagnostic: dict[str, Any], profile_literal_audit: dict[str, Any] | None = None) -> dict[str, Any]:
    summary = diagnostic["failure_mode_summary"]
    value_counts = summary["field_value_diff_counts"]
    gap = diagnostic["bridge_transfer_diagnostic"]["distribution_gap"]
    focus_by_id = {item["id"]: item for item in diagnostic["focus_areas"]}
    literal_finding = profile_literal_audit.get("finding", {}) if profile_literal_audit else {}
    return {
        "schema_version": "v11-value-diff-transfer-taxonomy.v1",
        "failure_modes": {
            "intent_correct_field_mismatch": {
                "priority": 1,
                "case_count": summary["mode_counts"]["intent_correct_field_mismatch"],
                "field_counts": summary["mode_field_counts"]["intent_correct_field_mismatch"],
                "interpretation": "primary intent often survives, while constraints, risk, operations, and information_state values drift",
                "repair_lane": "field_exactness_repair_lane",
            },
            "intent_mismatch": {
                "priority": 1,
                "case_count": summary["mode_counts"]["intent_mismatch"],
                "field_counts": summary["mode_field_counts"]["intent_mismatch"],
                "transitions": summary["intent_transitions"],
                "interpretation": "clarify boundary collapse plus respond/build and explain/verify spillover must be handled separately from field exactness",
                "repair_lane": "intent_boundary_repair_lane",
            },
            "critical_signal_under_detection": {
                "priority": 1,
                "miss_counts": summary["critical_signal_misses"],
                "value_diffs": {
                    "multiple_intents": value_counts["information_state.multiple_intents"],
                    "missing_required_information": value_counts["information_state.missing_required_information"],
                    "contains_unverified_claims": value_counts["information_state.contains_unverified_claims"],
                },
                "repair_lane": "critical_signal_repair_lane",
            },
            "bridge_non_transfer": {
                "priority": 1,
                "bridge_template_overfit_risk": gap["bridge_template_overfit_risk"],
                "language_shift": gap["language_shift"],
                "style_marker_delta_sealed_minus_bridge": gap["style_marker_delta_sealed_minus_bridge"],
                "repair_lane": "bridge_transfer_validation_lane",
            },
        },
        "value_diff_hotspots": {
            "constraint_must_missing": value_counts["constraints.must"],
            "constraint_format_missing": value_counts["constraints.formats"],
            "constraint_response_length_drift": value_counts["constraints.response_length"],
            "risk_level_drift": value_counts["risk.level"],
            "risk_flag_drift": value_counts["risk.flags"],
            "operation_drift": value_counts["operations"],
            "primary_intent_drift": value_counts["primary_intent"],
        },
        "field_exactness_subtypes": {
            "constraint_omission_fast_path": {
                "priority": 1,
                "fields": ["constraints.must", "constraints.formats", "constraints.response_length"],
                "directionality": "expected_present_to_predicted_empty_or_unspecified_only",
                "evidence": {
                    "constraints.must": value_counts["constraints.must"],
                    "constraints.formats": value_counts["constraints.formats"],
                    "constraints.response_length": value_counts["constraints.response_length"],
                },
                "interpretation": "constraint values are omitted rather than confused, so trace/merge propagation should be inspected before adding more samples",
                "first_action": "inspect constraint propagation and marker merge logic before expanding fixtures",
            },
            "risk_confusion_learning_path": {
                "priority": 2,
                "fields": ["risk.level", "risk.flags"],
                "directionality": "bidirectional_or_false_positive_false_negative_mix",
                "evidence": {
                    "risk.level": value_counts["risk.level"],
                    "risk.flags": value_counts["risk.flags"],
                },
                "interpretation": "risk values move in both directions, so boundary data and ladder calibration are likely needed",
                "first_action": "separate no-risk contrast from medium/high escalation examples",
            },
        },
        "diagnostic_hypotheses": {
            "hook_keyword_overfire_without_context": {
                "priority": 1,
                "suspected_hooks": [
                    "ai_relationship_boundary_v1",
                    "medical_guard",
                    "legal_guard",
                    "current_information_guard",
                ],
                "evidence_patterns": [
                    "negated dependency framing should not become dependency-risk assessment",
                    "medical-term UI/design discussion should not become diagnosis/clinical advice",
                    "license-name definition should not become high legal/current advice",
                    "local column/folder/current wording should not become web-current search pressure",
                ],
                "interpretation": "guard hooks may fire on keyword presence before negation, metalinguistic role, or local-reference checks",
                "first_action": "audit hook firing logic for negation scope, metacontext markers, definition intent, and local-current split",
                "repair_lane": "hook_overfire_repair_lane",
            },
            "definition_request_build_overroute": {
                "priority": 2,
                "transition_count": summary["intent_transitions"].get("respond->build", 0),
                "pattern": "one-sentence definition or meaning requests can be over-routed to build",
                "interpretation": "respond/build boundary needs a narrow definition-request guard before broader build routing",
                "first_action": "add definition-request contrast to intent boundary plan",
                "repair_lane": "intent_boundary_repair_lane",
            },
            "literal_profile_patch_overfit": {
                "priority": 1,
                "confirmed": bool(literal_finding.get("confirmed")),
                "regex_literal_count": literal_finding.get("total_regex_literal_count_in_profile_inspection"),
                "fixture_like_regex_literal_count": literal_finding.get("total_fixture_like_regex_literal_count"),
                "interpretation": "v6-v9 repair profiles were largely per-fixture literal regex patches, so isolated nonsealed exactness did not transfer to sealed v10 wording",
                "first_action": "convert repair examples into abstract marker/context rules and require naturalized paraphrase transfer checks",
                "repair_lane": "bridge_transfer_validation_lane",
            },
        },
        "focus_areas": [
            {
                "id": "value_level_diff_instrumentation",
                "priority": 1,
                "source_focus": focus_by_id["value_level_diff_instrumentation"],
                "v11_rule": "all post-measurement and replay reports must retain expected/predicted value diffs, not just field names",
            },
            {
                "id": "clarify_boundary_collapse",
                "priority": 1,
                "source_focus": focus_by_id["clarify_boundary_collapse"],
                "v11_rule": "clarify repair must be its own lane with recall target and transition analysis",
            },
            {
                "id": "multiple_intent_under_detection",
                "priority": 1,
                "source_focus": focus_by_id["multiple_intent_under_detection"],
                "v11_rule": "multiple_intents gets an independent recall target and cannot be hidden inside generic information_state exactness",
            },
            {
                "id": "bridge_non_transfer",
                "priority": 1,
                "source_focus": focus_by_id["bridge_non_transfer"],
                "v11_rule": "bridge-derived samples must pass naturalized paraphrase and mixed-language transfer checks before mainline adoption",
            },
            {
                "id": "intent_correct_field_mismatch_lane",
                "priority": 2,
                "source_focus": focus_by_id["intent_correct_field_mismatch_lane"],
                "v11_rule": "field exactness repair is separate from intent-boundary repair and can use different fixtures/gates",
            },
        ],
    }

def _repair_lanes(diagnostic: dict[str, Any], profile_literal_audit: dict[str, Any] | None = None) -> dict[str, Any]:
    summary = diagnostic["failure_mode_summary"]
    value_counts = summary["field_value_diff_counts"]
    gap = diagnostic["bridge_transfer_diagnostic"]["distribution_gap"]
    literal_finding = profile_literal_audit.get("finding", {}) if profile_literal_audit else {}
    return {
        "schema_version": "v11-repair-lanes.v1",
        "lanes": {
            "intent_boundary_repair_lane": {
                "priority": 1,
                "primary_targets": ["clarify_boundary_collapse", "respond_vs_build", "explain_vs_verify"],
                "source_evidence": summary["intent_transitions"],
                "required_sample_shape": ["near_miss_pair", "paraphrase_cluster", "negative_contrast"],
                "gate_metric": "clarify_recall_min",
                "named_subtargets": {
                    "definition_request_build_overroute": {
                        "transition_count": summary["intent_transitions"].get("respond->build", 0),
                        "first_action": "add narrow definition-request contrast before broader build expansion",
                    }
                },
            },
            "critical_signal_repair_lane": {
                "priority": 1,
                "primary_targets": ["multiple_intents", "missing_required_information", "contains_unverified_claims"],
                "source_evidence": summary["critical_signal_misses"],
                "required_sample_shape": ["multi_step_request", "missing_context_request", "single_intent_contrast"],
                "gate_metric": "critical_signal_recall_and_multiple_intents_recall",
            },
            "field_exactness_repair_lane": {
                "priority": 1,
                "primary_targets": ["constraints.must", "constraints.formats", "risk.level", "risk.flags", "operations"],
                "source_evidence": summary["field_value_diff_counts"],
                "required_sample_shape": ["value_diff_pair", "format_constraint_pair", "risk_ladder_pair"],
                "gate_metric": "constraint_operation_risk_exactness",
                "sub_lanes": {
                    "constraint_omission_fast_path": {
                        "priority": 1,
                        "fields": ["constraints.must", "constraints.formats", "constraints.response_length"],
                        "source_evidence": {
                            "constraints.must": value_counts["constraints.must"],
                            "constraints.formats": value_counts["constraints.formats"],
                            "constraints.response_length": value_counts["constraints.response_length"],
                        },
                        "first_action": "inspect constraint propagation and merge logic before adding more fixture cases",
                    },
                    "risk_confusion_learning_path": {
                        "priority": 2,
                        "fields": ["risk.level", "risk.flags"],
                        "source_evidence": {
                            "risk.level": value_counts["risk.level"],
                            "risk.flags": value_counts["risk.flags"],
                        },
                        "first_action": "calibrate risk ladder with no-risk contrast and escalation pairs",
                    },
                },
            },
            "hook_overfire_repair_lane": {
                "priority": 1,
                "primary_targets": ["negation_scope", "metacontext_mentions", "definition_vs_advice", "local_current_vs_web_current"],
                "source_evidence": {
                    "suspected_hooks": [
                        "ai_relationship_boundary_v1",
                        "medical_guard",
                        "legal_guard",
                        "current_information_guard",
                    ],
                    "hypothesis": "keyword-only guard firing before negation/metacontext/local-reference checks",
                },
                "required_sample_shape": ["hook_trace_case", "negative_scope_pair", "metacontext_contrast"],
                "gate_metric": "hook_false_positive_zero_on_known_patterns",
                "first_action": "audit hook firing logic before generating more repair fixtures",
            },
            "bridge_transfer_validation_lane": {
                "priority": 1,
                "primary_targets": ["naturalized_text", "mixed_ja_en", "non_template_bridge", "shorter_userlike_inputs"],
                "source_evidence": {
                    "bridge_distribution_gap": gap,
                    "literal_profile_patch_overfit": literal_finding,
                },
                "required_sample_shape": ["template_vs_naturalized_pair", "ja_en_distribution_pair", "heldout_style_probe", "same_semantics_different_surface_form"],
                "gate_metric": "transfer_gap_not_template_only",
            },
        },
        "forbidden_shortcuts": [
            "do_not_tune_from_sealed_v10_text_or_labels",
            "do_not_repeat_bridge_only_isolated_1_0_as_mainline_gate",
            "do_not_merge_intent_boundary_and_field_exactness_repairs",
            "do_not_use_generated_answer_only_samples_as_direct_semantic_labels",
            "do_not_expand_fixtures_before_constraint_omission_and_hook_overfire_audit",
            "do_not_add_one_regex_per_failed_fixture_sentence",
            "do_not_accept_isolated_fixture_1_0_without_paraphrase_transfer",
        ],
    }

def _roadmap(code_audit_triage: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    blockers = list(code_audit_triage.get("step2_blockers", [])) if code_audit_triage else []
    roadmap = [
        {"step": 1, "name": "post_v10_value_diff_transfer_taxonomy", "output": "build\\v11_targets_and_roadmap_v1.json", "status": "completed"},
    ]
    if blockers:
        roadmap.append({"step": "1b", "name": "v11_p0_baseline_source_recovery", "output": "build\\v11_code_audit_triage_v1.json", "status": "next"})
    roadmap.extend([
        {"step": 2, "name": "v11_repair_curriculum_plan", "output": "build\\v11_repair_curriculum_plan_v1.json", "status": "blocked" if blockers else "next"},
        {"step": 3, "name": "v11_value_diff_repair_fixture_and_candidate_replay", "output": "tests\\fixtures\\v11_value_diff_repair_fixture_v1.json", "status": "pending"},
        {"step": 4, "name": "v11_bridge_transfer_validation_set", "output": "tests\\fixtures\\v11_bridge_transfer_validation_fixture_v1.json", "status": "pending"},
        {"step": 5, "name": "v11_router_generalization_changes", "output": "build\\v11_router_generalization_report_v1.json", "status": "pending"},
        {"step": 6, "name": "v11_nonsealed_replay_gate", "output": "build\\v11_nonsealed_replay_gate_report_v1.json", "status": "pending"},
        {"step": 7, "name": "sealed_v11_rotation_review", "output": "build\\v11_sealed_rotation_review_v1.json", "status": "pending"},
        {"step": 8, "name": "sealed_v11_rotation", "output": "tests\\fixtures\\pattern_language_sealed_v11.json", "status": "pending"},
        {"step": 9, "name": "sealed_v11_one_time_measurement", "output": "build\\pattern_language_sealed_v11_measurement_report.json", "status": "pending"},
    ])
    return roadmap


def build_payload() -> dict[str, Any]:
    measurement = _load_json(V10_MEASUREMENT_PATH)
    v10_targets = _load_json(V10_TARGETS_PATH)
    diagnostic = _load_json(V10_DIAGNOSTIC_PATH)
    code_audit_triage = _load_json(CODE_AUDIT_TRIAGE_PATH) if CODE_AUDIT_TRIAGE_PATH.exists() else None
    profile_literal_audit = _load_json(PROFILE_LITERAL_AUDIT_PATH) if PROFILE_LITERAL_AUDIT_PATH.exists() else None
    readiness = _load_json(READINESS_PATH)
    registry = _load_json(REGISTRY_PATH)
    fixture_entry = registry["fixtures"]["pattern_language_sealed_v10.json"]
    metrics = measurement["measurements"]
    return {
        "schema_version": "v11-targets-and-roadmap.v1",
        "generated_at": reproducible_now_iso(),
        "status": ("step1_post_v10_value_diff_transfer_taxonomy_completed_p0_source_recovery_next" if code_audit_triage and code_audit_triage.get("step2_blockers") else "step1_post_v10_value_diff_transfer_taxonomy_completed_step2_curriculum_next"),
        "sources": {
            "sealed_v10_measurement": _rel(V10_MEASUREMENT_PATH),
            "v10_targets_and_roadmap": _rel(V10_TARGETS_PATH),
            "post_v10_diagnostic": _rel(V10_DIAGNOSTIC_PATH),
            "code_audit_triage": _rel(CODE_AUDIT_TRIAGE_PATH) if CODE_AUDIT_TRIAGE_PATH.exists() else None,
            "profile_literal_patch_audit": _rel(PROFILE_LITERAL_AUDIT_PATH) if PROFILE_LITERAL_AUDIT_PATH.exists() else None,
            "readiness_review": _rel(READINESS_PATH),
            "fixture_registry": _rel(REGISTRY_PATH),
        },
        "policy": {
            "sealed_v10_consumed": fixture_entry["status"] == "consumed",
            "sealed_v10_labels_used_for_tuning": measurement["sealed_labels_used_for_tuning"],
            "sealed_v10_text_used_for_training": False,
            "sealed_v10_values_used_for_taxonomy_only": diagnostic["policy"]["sealed_v10_values_used_for_taxonomy_only"],
            "post_v10_diagnostic_is_training_data": diagnostic["policy"]["diagnostic_is_training_data"],
            "post_v10_diagnostic_is_replay_gate": diagnostic["policy"]["diagnostic_is_replay_gate"],
            "same_cycle_promotion_allowed": False,
            "fresh_sealed_v11_required_before_next_adjudication": True,
            "bridge_only_isolated_replay_sufficient_for_v11": False,
            "value_diff_reporting_required": True,
        },
        "baseline": {
            "fixture": "pattern_language_sealed_v10.json",
            "case_count": metrics["case_count"],
            "intent_accuracy": metrics["intent_accuracy"],
            "critical_signal_recall": metrics["critical_signal_recall"],
            "operation_exact_match": metrics["operation_exact_match"],
            "constraint_exact_match": metrics["constraint_exact_match"],
            "risk_exact_match": metrics["risk_exact_match"],
            "sealed_error_count": len(metrics["errors"]),
            "critical_signal_miss_count": v10_targets["step6_sealed_measurement"]["critical_signal_miss_count"],
            "readiness_decision_after_measurement": readiness["decision"],
            "blocked_reasons": readiness["blocked_reasons"],
        },
        "metric_regression_from_v9": diagnostic["metric_regression"],
        "targets": _metric_targets(),
        "taxonomy": _taxonomy(diagnostic, profile_literal_audit),
        "repair_lanes": _repair_lanes(diagnostic, profile_literal_audit),
        "profile_literal_patch_audit": profile_literal_audit,
        "pre_rotation_gates": {
            "value_diff_diagnostic_required": True,
            "bridge_transfer_validation_required": True,
            "clarify_recall_gate_required": True,
            "multiple_intents_recall_gate_required": True,
            "constraint_omission_code_trace_required": True,
            "hook_overfire_audit_required": True,
            "literal_profile_dependency_scan_required": True,
            "baseline_source_recovery_required": bool(code_audit_triage and code_audit_triage.get("step2_blockers")),
            "nonsealed_replay_gate_error_count_max": 0,
            "full_regression_required": "python -B -m pytest",
        },
        "code_audit_triage": code_audit_triage,
        "pre_step2_blockers": list(code_audit_triage.get("step2_blockers", [])) if code_audit_triage else [],
        "roadmap": _roadmap(code_audit_triage),
        "next_action": (
            code_audit_triage["roadmap_override"]["next_action"]
            if code_audit_triage and code_audit_triage.get("step2_blockers")
            else "roadmap_v11_step2_create_repair_curriculum_plan"
        ),
        "roadmap_decision": (
            {
                "can_advance": True,
                "advance_to": code_audit_triage["roadmap_override"]["advance_to"],
                "blocked_reasons": [],
            }
            if code_audit_triage and code_audit_triage.get("step2_blockers")
            else {
                "can_advance": True,
                "advance_to": "v11_repair_curriculum_plan",
                "blocked_reasons": [],
            }
        ),
    }


def _write_markdown(payload: dict[str, Any]) -> None:
    baseline = payload["baseline"]
    targets = payload["targets"]
    lines = [
        "# PLM V11 Roadmap: Value-Diff Recovery And Bridge Transfer Repair",
        "",
        "Updated: 2026-06-28",
        "",
        "## Contract",
        "",
        "- Sealed v10 is consumed and may be used only as aggregate taxonomy/value-diff evidence.",
        "- Sealed v10 text and labels must not be copied into training, review, or non-sealed fixtures.",
        "- The post-v10 diagnostic is not training data, not a replay gate, and not same-cycle promotion evidence.",
        "- Bridge-only isolated replay is not sufficient for V11; transfer validation is required.",
        "- Same-cycle promotion remains disallowed; a fresh sealed v11 fixture is required before adjudicating measurement.",
        "- If code audit triage reports baseline source recovery blockers, Step 2 curriculum work waits for Step 1b source recovery.",
        "",
        "## Baseline And Targets",
        "",
        "| Metric | V10 sealed | V11 minimum | V11 stretch |",
        "|---|---:|---:|---:|",
        f"| intent_accuracy | {baseline['intent_accuracy']:.6f} | {targets['minimum']['intent_accuracy']:.6f} | {targets['stretch']['intent_accuracy']:.6f} |",
        f"| critical_signal_recall | {baseline['critical_signal_recall']:.6f} | {targets['minimum']['critical_signal_recall']:.6f} | {targets['stretch']['critical_signal_recall']:.6f} |",
        f"| operation_exact_match | {baseline['operation_exact_match']:.6f} | {targets['minimum']['operation_exact_match']:.6f} | {targets['stretch']['operation_exact_match']:.6f} |",
        f"| constraint_exact_match | {baseline['constraint_exact_match']:.6f} | {targets['minimum']['constraint_exact_match']:.6f} | {targets['stretch']['constraint_exact_match']:.6f} |",
        f"| risk_exact_match | {baseline['risk_exact_match']:.6f} | {targets['minimum']['risk_exact_match']:.6f} | {targets['stretch']['risk_exact_match']:.6f} |",
        f"| sealed_error_count | {baseline['sealed_error_count']} | <= {targets['minimum']['sealed_error_count_max']} | <= {targets['stretch']['sealed_error_count_max']} |",
        f"| critical_signal_miss_count | {baseline['critical_signal_miss_count']} | <= {targets['minimum']['critical_signal_miss_count_max']} | <= {targets['stretch']['critical_signal_miss_count_max']} |",
        "",
    ]
    if payload.get("code_audit_triage"):
        triage = payload["code_audit_triage"]
        has_blockers = bool(payload["pre_step2_blockers"])
        lines.extend([
            "## P0 Code Audit Override" if has_blockers else "## P0 Code Audit Status",
            "",
            f"- status: {triage['status']}",
            f"- next_action: {payload['next_action']}",
            f"- pre_step2_blockers: {payload['pre_step2_blockers']}",
            (
                "- repair curriculum planning waits until baseline source recovery is handled."
                if has_blockers
                else "- baseline source recovery completed; Step 2 curriculum planning is unblocked."
            ),
            "",
        ])
    lines.extend([
        "## Failure Mode Taxonomy",
        "",
        "| Mode | Cases | Repair Lane |",
        "|---|---:|---|",
    ])
    for mode, item in payload["taxonomy"]["failure_modes"].items():
        count = item.get("case_count") or sum(item.get("miss_counts", {}).values()) or "gap"
        lines.append(f"| {mode} | {count} | {item['repair_lane']} |")
    lines.extend(["", "## Value-Diff Hotspots", ""])
    for key, item in payload["taxonomy"]["value_diff_hotspots"].items():
        lines.append(f"- {key}: `{item}`")
    lines.extend(["", "## Refined Diagnostic Hypotheses", ""])
    for key, item in payload["taxonomy"]["field_exactness_subtypes"].items():
        lines.append(f"- {key}: {item['interpretation']} First action: {item['first_action']}.")
    for key, item in payload["taxonomy"]["diagnostic_hypotheses"].items():
        lines.append(f"- {key}: {item['interpretation']} First action: {item['first_action']}.")
    lines.extend(["", "## Focus Areas", ""])
    for index, item in enumerate(payload["taxonomy"]["focus_areas"], start=1):
        lines.append(f"{index}. {item['id']}: {item['v11_rule']}")
    lines.extend(["", "## Repair Lanes", "", "| Lane | Priority | Gate Metric |", "|---|---:|---|"])
    for lane, item in payload["repair_lanes"]["lanes"].items():
        lines.append(f"| {lane} | {item['priority']} | {item['gate_metric']} |")
    lines.extend(["", "## Roadmap", "", "| Step | Name | Output | Status |", "|---:|---|---|---|"])
    for step in payload["roadmap"]:
        lines.append(f"| {step['step']} | {step['name']} | `{step['output']}` | {step['status']} |")
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


def _update_v10_roadmap() -> None:
    roadmap = V10_ROADMAP_PATH.read_text(encoding="utf-8")
    section = (
        "## V11 Handoff\n\n"
        "`build\\v11_targets_and_roadmap_v1.json` and `docs\\PLM_V11_ROADMAP.md` convert consumed sealed v10 into value-diff taxonomy and bridge transfer-gap planning. Sealed v10 text and labels remain excluded from training; V11 requires fresh non-sealed repair gates and a fresh sealed v11 rotation before measurement.\n"
    )
    V10_ROADMAP_PATH.write_text(_replace_section(roadmap, "## V11 Handoff", section), encoding="utf-8", newline="\n")


def _update_main_roadmap(payload: dict[str, Any]) -> None:
    marker = "## PLM V11: Value-Diff Recovery And Bridge Transfer Repair"
    baseline = payload["baseline"]
    decision = payload["roadmap_decision"]
    has_blockers = bool(payload.get("pre_step2_blockers"))
    status_sentence = (
        "V11 Step 1 taxonomy completed; code audit triage found a P0 baseline source-recovery blocker, so Step 1b source recovery is next before Step 2 curriculum planning."
        if has_blockers
        else "V11 Step 1 taxonomy and Step 1b baseline source recovery are completed; Step 2 repair curriculum planning is next."
    )
    audit_sentence = (
        "Code audit triage adds a P0 baseline source-recovery blocker: Step 1b must replace the pyc-loader baseline with auditable source before Step 2 repair curriculum planning."
        if has_blockers
        else "Code audit triage confirms the pyc-loader baseline has been replaced by source-recovered, regression-tested runtime code; Step 2 is unblocked."
    )
    section = f"""
{marker}

Status: {status_sentence}

Primary roadmap: `docs/PLM_V11_ROADMAP.md`
Targets and taxonomy: `build/v11_targets_and_roadmap_v1.json`
Post-v10 diagnostic: `build/v11_post_v10_measurement_diagnostic_v1.json`
Baseline sealed v10 measurement: `build/pattern_language_sealed_v10_measurement_report.json`

V11 uses sealed v10 measurement only as aggregate taxonomy/value-diff evidence. Sealed v10 text and labels are not training data. V10 measured intent_accuracy {baseline['intent_accuracy']:.6f}, critical_signal_recall {baseline['critical_signal_recall']:.6f}, operation_exact_match {baseline['operation_exact_match']:.6f}, constraint_exact_match {baseline['constraint_exact_match']:.6f}, risk_exact_match {baseline['risk_exact_match']:.6f}, errors {baseline['sealed_error_count']}. V11 splits repair into intent-boundary, critical-signal, field-exactness, hook-overfire, and bridge-transfer validation lanes. {audit_sentence} Roadmap decision: can_advance={str(decision['can_advance']).lower()}, advance_to={decision['advance_to']}.
""".strip()
    main = MAIN_ROADMAP_PATH.read_text(encoding="utf-8")
    MAIN_ROADMAP_PATH.write_text(_replace_section(main, marker, section), encoding="utf-8", newline="\n")


def main() -> None:
    payload = build_payload()
    _write_json(OUTPUT_JSON, payload)
    _write_markdown(payload)
    _update_v10_roadmap()
    _update_main_roadmap(payload)
    print(json.dumps({"status": payload["status"], "next_action": payload["next_action"], "roadmap_decision": payload["roadmap_decision"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()


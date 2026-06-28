import json
import subprocess
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).parents[1]
SCRIPT_PATH = ROOT / "build" / "create_v11_targets_and_roadmap.py"
DIAGNOSTIC_SCRIPT_PATH = ROOT / "build" / "diagnose_v10_sealed_measurement_for_v11.py"
TARGETS_PATH = ROOT / "build" / "v11_targets_and_roadmap_v1.json"
DIAGNOSTIC_PATH = ROOT / "build" / "v11_post_v10_measurement_diagnostic_v1.json"
ROADMAP_PATH = ROOT / "docs" / "PLM_V11_ROADMAP.md"
V10_ROADMAP_PATH = ROOT / "docs" / "PLM_V10_ROADMAP.md"
MAIN_ROADMAP_PATH = ROOT / "docs" / "PATTERN_LANGUAGE_MODEL_roadmap.md"


@pytest.fixture(scope="module", autouse=True)
def _regenerate_targets():
    """Regenerate shared build/ artifacts before the read-asserts.

    create_v11_targets_and_roadmap.py consumes the post-v10 diagnostic as input,
    so the diagnostic must be regenerated first. Both files are untracked
    artifacts in build/; regenerating here removes dependence on whatever a
    prior test or manual run left on disk.
    """
    for script in (DIAGNOSTIC_SCRIPT_PATH, SCRIPT_PATH):
        subprocess.run(
            [sys.executable, "-B", str(script)],
            cwd=ROOT,
            check=True,
            text=True,
            capture_output=True,
        )


def _load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_v11_targets_record_policy_baseline_and_v9_regression() -> None:
    payload = _load(TARGETS_PATH)
    diagnostic = _load(DIAGNOSTIC_PATH)

    assert payload["schema_version"] == "v11-targets-and-roadmap.v1"
    assert payload["status"] == "step1_post_v10_value_diff_transfer_taxonomy_completed_step2_curriculum_next"
    assert payload["policy"] == {
        "sealed_v10_consumed": True,
        "sealed_v10_labels_used_for_tuning": False,
        "sealed_v10_text_used_for_training": False,
        "sealed_v10_values_used_for_taxonomy_only": True,
        "post_v10_diagnostic_is_training_data": False,
        "post_v10_diagnostic_is_replay_gate": False,
        "same_cycle_promotion_allowed": False,
        "fresh_sealed_v11_required_before_next_adjudication": True,
        "bridge_only_isolated_replay_sufficient_for_v11": False,
        "value_diff_reporting_required": True,
    }
    assert payload["baseline"] == {
        "fixture": "pattern_language_sealed_v10.json",
        "case_count": 28,
        "intent_accuracy": 0.785714,
        "critical_signal_recall": 0.4,
        "operation_exact_match": 0.642857,
        "constraint_exact_match": 0.535714,
        "risk_exact_match": 0.678571,
        "sealed_error_count": 23,
        "critical_signal_miss_count": 9,
        "readiness_decision_after_measurement": "blocked",
        "blocked_reasons": ["sealed_fixture_not_available"],
    }
    assert payload["metric_regression_from_v9"] == diagnostic["metric_regression"]
    assert all(
        item["delta_v10_minus_v9"] < 0
        for item in payload["metric_regression_from_v9"].values()
    )


def test_v11_targets_set_recovery_floor_and_stretch_goals() -> None:
    payload = _load(TARGETS_PATH)

    assert payload["targets"]["minimum"] == {
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
    }
    assert payload["targets"]["stretch"] == {
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
    }
    assert payload["targets"]["granularity"] == {
        "case_metric_step": 0.035714,
        "critical_signal_step": 0.066667,
        "clarify_recall_step": 0.25,
        "multiple_intents_recall_step": 0.142857,
    }


def test_v11_taxonomy_splits_value_diff_failure_modes_and_focus_areas() -> None:
    payload = _load(TARGETS_PATH)
    taxonomy = payload["taxonomy"]
    modes = taxonomy["failure_modes"]

    assert taxonomy["schema_version"] == "v11-value-diff-transfer-taxonomy.v1"
    assert set(modes) == {
        "intent_correct_field_mismatch",
        "intent_mismatch",
        "critical_signal_under_detection",
        "bridge_non_transfer",
    }
    assert modes["intent_correct_field_mismatch"]["case_count"] == 17
    assert modes["intent_correct_field_mismatch"]["repair_lane"] == "field_exactness_repair_lane"
    assert modes["intent_mismatch"]["case_count"] == 6
    transitions = modes["intent_mismatch"]["transitions"]
    assert sum(transitions.values()) == modes["intent_mismatch"]["case_count"]
    assert transitions["clarify->explore"] == 1
    assert transitions["clarify->respond"] == 1
    assert transitions["clarify->verify"] == 1
    assert transitions["explain->verify"] == 1
    assert transitions["respond->build"] == 1
    assert modes["critical_signal_under_detection"]["miss_counts"] == {
        "contains_unverified_claims": 1,
        "missing_required_information": 3,
        "multiple_intents": 5,
    }
    assert modes["critical_signal_under_detection"]["value_diffs"]["multiple_intents"] == {
        "False -> True": 2,
        "True -> False": 5,
    }
    assert modes["bridge_non_transfer"]["bridge_template_overfit_risk"] is True
    assert modes["bridge_non_transfer"]["language_shift"] == {
        "bridge": {"en": 72},
        "sealed_v10": {"en": 14, "ja": 14},
    }

    hotspots = taxonomy["value_diff_hotspots"]
    assert set(hotspots) == {
        "constraint_must_missing",
        "constraint_format_missing",
        "constraint_response_length_drift",
        "risk_level_drift",
        "risk_flag_drift",
        "operation_drift",
        "primary_intent_drift",
    }
    assert hotspots["operation_drift"]["['respond'] -> ['build']"] == 1
    assert hotspots["risk_level_drift"] == {
        "low -> high": 1,
        "low -> medium": 3,
        "medium -> high": 1,
        "medium -> low": 4,
    }
    subtypes = taxonomy["field_exactness_subtypes"]
    assert subtypes["constraint_omission_fast_path"]["directionality"] == "expected_present_to_predicted_empty_or_unspecified_only"
    assert subtypes["constraint_omission_fast_path"]["fields"] == [
        "constraints.must",
        "constraints.formats",
        "constraints.response_length",
    ]
    assert subtypes["constraint_omission_fast_path"]["evidence"]["constraints.must"] == hotspots["constraint_must_missing"]
    assert subtypes["risk_confusion_learning_path"]["directionality"] == "bidirectional_or_false_positive_false_negative_mix"
    assert subtypes["risk_confusion_learning_path"]["evidence"]["risk.level"] == hotspots["risk_level_drift"]

    hypotheses = taxonomy["diagnostic_hypotheses"]
    hook = hypotheses["hook_keyword_overfire_without_context"]
    assert hook["repair_lane"] == "hook_overfire_repair_lane"
    assert hook["suspected_hooks"] == [
        "ai_relationship_boundary_v1",
        "medical_guard",
        "legal_guard",
        "current_information_guard",
    ]
    assert "negated dependency framing should not become dependency-risk assessment" in hook["evidence_patterns"]
    assert "local column/folder/current wording should not become web-current search pressure" in hook["evidence_patterns"]
    definition = hypotheses["definition_request_build_overroute"]
    assert definition["transition_count"] == 1
    assert definition["repair_lane"] == "intent_boundary_repair_lane"

    assert [item["id"] for item in taxonomy["focus_areas"]] == [
        "value_level_diff_instrumentation",
        "clarify_boundary_collapse",
        "multiple_intent_under_detection",
        "bridge_non_transfer",
        "intent_correct_field_mismatch_lane",
    ]


def test_v11_repair_lanes_and_pre_rotation_gates_are_separate() -> None:
    payload = _load(TARGETS_PATH)
    repair = payload["repair_lanes"]
    lanes = repair["lanes"]

    assert repair["schema_version"] == "v11-repair-lanes.v1"
    assert set(lanes) == {
        "intent_boundary_repair_lane",
        "critical_signal_repair_lane",
        "field_exactness_repair_lane",
        "hook_overfire_repair_lane",
        "bridge_transfer_validation_lane",
    }
    assert lanes["intent_boundary_repair_lane"]["primary_targets"] == [
        "clarify_boundary_collapse",
        "respond_vs_build",
        "explain_vs_verify",
    ]
    assert lanes["critical_signal_repair_lane"]["primary_targets"] == [
        "multiple_intents",
        "missing_required_information",
        "contains_unverified_claims",
    ]
    assert lanes["field_exactness_repair_lane"]["primary_targets"] == [
        "constraints.must",
        "constraints.formats",
        "risk.level",
        "risk.flags",
        "operations",
    ]
    assert lanes["field_exactness_repair_lane"]["sub_lanes"]["constraint_omission_fast_path"]["first_action"] == "inspect constraint propagation and merge logic before adding more fixture cases"
    assert lanes["field_exactness_repair_lane"]["sub_lanes"]["risk_confusion_learning_path"]["first_action"] == "calibrate risk ladder with no-risk contrast and escalation pairs"
    assert lanes["hook_overfire_repair_lane"]["primary_targets"] == [
        "negation_scope",
        "metacontext_mentions",
        "definition_vs_advice",
        "local_current_vs_web_current",
    ]
    assert lanes["hook_overfire_repair_lane"]["gate_metric"] == "hook_false_positive_zero_on_known_patterns"
    assert lanes["bridge_transfer_validation_lane"]["primary_targets"] == [
        "naturalized_text",
        "mixed_ja_en",
        "non_template_bridge",
        "shorter_userlike_inputs",
    ]
    assert repair["forbidden_shortcuts"] == [
        "do_not_tune_from_sealed_v10_text_or_labels",
        "do_not_repeat_bridge_only_isolated_1_0_as_mainline_gate",
        "do_not_merge_intent_boundary_and_field_exactness_repairs",
        "do_not_use_generated_answer_only_samples_as_direct_semantic_labels",
        "do_not_expand_fixtures_before_constraint_omission_and_hook_overfire_audit",
        "do_not_add_one_regex_per_failed_fixture_sentence",
        "do_not_accept_isolated_fixture_1_0_without_paraphrase_transfer",
    ]
    assert payload["pre_rotation_gates"] == {
        "value_diff_diagnostic_required": True,
        "bridge_transfer_validation_required": True,
        "clarify_recall_gate_required": True,
        "multiple_intents_recall_gate_required": True,
        "constraint_omission_code_trace_required": True,
        "hook_overfire_audit_required": True,
        "literal_profile_dependency_scan_required": True,
        "baseline_source_recovery_required": False,
        "nonsealed_replay_gate_error_count_max": 0,
        "full_regression_required": "python -B -m pytest",
    }


def test_v11_roadmap_advances_to_curriculum_after_source_recovery() -> None:
    payload = _load(TARGETS_PATH)

    assert payload["pre_step2_blockers"] == []
    assert payload["code_audit_triage"]["status"] == "step1b_baseline_source_recovery_completed"
    assert [step["status"] for step in payload["roadmap"]] == [
        "completed",
        "next",
        "pending",
        "pending",
        "pending",
        "pending",
        "pending",
        "pending",
        "pending",
    ]
    assert [step["name"] for step in payload["roadmap"]] == [
        "post_v10_value_diff_transfer_taxonomy",
        "v11_repair_curriculum_plan",
        "v11_value_diff_repair_fixture_and_candidate_replay",
        "v11_bridge_transfer_validation_set",
        "v11_router_generalization_changes",
        "v11_nonsealed_replay_gate",
        "sealed_v11_rotation_review",
        "sealed_v11_rotation",
        "sealed_v11_one_time_measurement",
    ]
    assert payload["next_action"] == "roadmap_v11_step2_create_repair_curriculum_plan"
    assert payload["roadmap_decision"] == {
        "can_advance": True,
        "advance_to": "v11_repair_curriculum_plan",
        "blocked_reasons": [],
    }


def test_v11_script_regenerates_docs_and_links_previous_roadmaps() -> None:
    completed = subprocess.run(
        [sys.executable, "-B", str(SCRIPT_PATH)],
        cwd=ROOT,
        check=True,
        text=True,
        capture_output=True,
    )
    assert "step1_post_v10_value_diff_transfer_taxonomy_completed_step2_curriculum_next" in completed.stdout

    roadmap = ROADMAP_PATH.read_text(encoding="utf-8")
    v10_roadmap = V10_ROADMAP_PATH.read_text(encoding="utf-8")
    main_roadmap = MAIN_ROADMAP_PATH.read_text(encoding="utf-8")

    assert "# PLM V11 Roadmap: Value-Diff Recovery And Bridge Transfer Repair" in roadmap
    assert "| intent_accuracy | 0.785714 | 0.857143 | 0.928571 |" in roadmap
    assert "| intent_correct_field_mismatch | 17 | field_exactness_repair_lane |" in roadmap
    assert "## P0 Code Audit Status" in roadmap
    assert "roadmap_v11_step2_create_repair_curriculum_plan" in roadmap
    assert "v11_repair_curriculum_plan" in roadmap
    assert "baseline source recovery completed" in roadmap
    assert "## Refined Diagnostic Hypotheses" in roadmap
    assert "constraint_omission_fast_path" in roadmap
    assert "hook_keyword_overfire_without_context" in roadmap
    assert "hook_overfire_repair_lane" in roadmap
    assert "1. value_level_diff_instrumentation" in roadmap
    assert "5. intent_correct_field_mismatch_lane" in roadmap
    assert "## V11 Handoff" in v10_roadmap
    assert "build\\v11_targets_and_roadmap_v1.json" in v10_roadmap
    assert "## PLM V11: Value-Diff Recovery And Bridge Transfer Repair" in main_roadmap
    assert "hook-overfire" in main_roadmap
    assert "advance_to=v11_repair_curriculum_plan" in main_roadmap
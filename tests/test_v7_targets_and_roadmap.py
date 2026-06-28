import json
from pathlib import Path


ROOT = Path(__file__).parents[1]
TARGETS_PATH = ROOT / "build" / "v7_targets_and_roadmap_v1.json"
ROADMAP_PATH = ROOT / "docs" / "PLM_V7_ROADMAP.md"
V6_ROADMAP_PATH = ROOT / "docs" / "PLM_V6_ROADMAP.md"
MAIN_ROADMAP_PATH = ROOT / "docs" / "PATTERN_LANGUAGE_MODEL_roadmap.md"


def _load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_v7_targets_record_post_v6_taxonomy_without_training_use() -> None:
    payload = _load(TARGETS_PATH)

    assert payload["schema_version"] == "v7-targets-and-roadmap.v1"
    assert payload["status"] == "step8_sealed_v7_measurement_completed_v8_rotation_required"
    assert payload["policy"] == {
        "sealed_v6_consumed": True,
        "sealed_v6_labels_used_for_tuning": False,
        "sealed_v6_text_used_for_training": False,
        "sealed_v6_measurement_used_as_taxonomy_only": True,
        "same_cycle_promotion_allowed": False,
        "fresh_sealed_successor_required_before_measurement": True,
        "nonsealed_curriculum_required_before_rotation": True,
    }
    assert payload["baseline"] == {
        "fixture": "pattern_language_sealed_v6.json",
        "case_count": 28,
        "intent_accuracy": 0.75,
        "critical_signal_recall": 0.357143,
        "operation_exact_match": 0.607143,
        "constraint_exact_match": 0.607143,
        "risk_exact_match": 0.75,
        "sealed_error_count": 23,
        "readiness_decision_after_measurement": "blocked",
        "blocked_reasons": ["sealed_fixture_not_available"],
    }


def test_v7_taxonomy_prioritizes_v6_failure_surface() -> None:
    payload = _load(TARGETS_PATH)
    taxonomy = payload["taxonomy"]

    assert taxonomy["field_error_counts"] == {
        "constraints": 11,
        "information_state": 8,
        "operations": 11,
        "primary_intent": 7,
        "risk": 7,
    }
    assert taxonomy["critical_signal_miss_counts"] == {
        "missing_required_information": 2,
        "contains_unverified_claims": 3,
        "requires_current_information": 1,
        "multiple_intents": 3,
    }
    assert taxonomy["intent_boundary_transitions"] == {
        "build->verify": 1,
        "clarify->build": 1,
        "clarify->respond": 1,
        "clarify->verify": 1,
        "explain->build": 1,
        "explore->respond": 1,
        "respond->build": 1,
    }
    assert [item["id"] for item in taxonomy["focus_areas"]] == [
        "constraint_preservation",
        "operation_sequence_repair",
        "critical_signal_recovery",
        "clarify_boundary_repair",
        "risk_ladder_calibration",
        "intent_boundary_stability",
    ]


def test_v7_targets_and_rotation_plan_are_set() -> None:
    payload = _load(TARGETS_PATH)

    assert payload["targets"]["minimum"] == {
        "intent_accuracy": 0.892857,
        "critical_signal_recall": 0.75,
        "operation_exact_match": 0.821429,
        "constraint_exact_match": 0.821429,
        "risk_exact_match": 0.892857,
        "sealed_error_count_max": 10,
        "critical_signal_miss_count_max": 4,
    }
    assert payload["nonsealed_curriculum_requirements"] == {
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
    }
    assert payload["pre_rotation_gates"]["v7_curriculum_exact_minimum"] == 0.95
    assert payload["pre_rotation_gates"]["sealed_overlap_count_required"] == 0
    assert [step["status"] for step in payload["roadmap"]] == [
        "completed",
        "completed",
        "completed",
        "completed",
        "completed",
        "completed",
        "completed",
        "completed",
    ]
    assert payload["roadmap"][7]["name"] == "sealed_v7_one_time_measurement"
    assert payload["next_action"] == "roadmap_v8_step1_post_v7_measurement_taxonomy"
    assert payload["step5_nonsealed_replay_gate"]["passed"] is True
    assert payload["step5_nonsealed_replay_gate"]["summary"]["required_error_count"] == 0
    assert payload["step5_nonsealed_replay_gate"]["summary"]["v7_curriculum_error_count"] == 0
    assert payload["step6_sealed_rotation_review"]["passed"] is True
    assert payload["step6_sealed_rotation_review"]["summary"]["blocker_count"] == 0
    assert payload["step7_sealed_rotation"]["passed"] is True
    assert payload["step7_sealed_rotation"]["summary"]["case_count"] == 28
    assert payload["step7_sealed_rotation"]["summary"]["status"] == "active"
    assert payload["step7_sealed_rotation"]["summary"]["measured"] is False
    assert payload["step7_sealed_rotation"]["summary"]["readiness_decision"] == "eligible"
    assert payload["step8_sealed_measurement"]["passed_minimum"] is False
    assert payload["step8_sealed_measurement"]["measurements"]["error_count"] == 16
    assert payload["step8_sealed_measurement"]["readiness_after_measurement"]["blocked_reasons"] == ["sealed_fixture_not_available"]


def test_v7_roadmap_docs_are_linked_from_v6_and_main_roadmaps() -> None:
    roadmap = ROADMAP_PATH.read_text(encoding="utf-8")
    v6 = V6_ROADMAP_PATH.read_text(encoding="utf-8")
    main = MAIN_ROADMAP_PATH.read_text(encoding="utf-8")

    assert "PLM V7 Roadmap" in roadmap
    assert "| 1 | post_v6_measurement_taxonomy | `build\\v7_targets_and_roadmap_v1.json` | completed |" in roadmap
    assert "| 2 | v7_nonsealed_curriculum_design | `build\\v7_nonsealed_curriculum_plan_v1.json` | completed |" in roadmap
    assert "| 3 | v7_nonsealed_fixture_and_candidate_replay | `tests\\fixtures\\v7_router_repair_fixture_v1.json` | completed |" in roadmap
    assert "| 4 | v7_router_generalization_changes | `build\\v7_router_generalization_report_v1.json` | completed |" in roadmap
    assert "| 5 | v7_nonsealed_replay_gate | `build\\v7_nonsealed_replay_gate_report_v1.json` | completed |" in roadmap
    assert "| 6 | sealed_v7_rotation_review | `build\\v7_sealed_rotation_review_v1.json` | completed |" in roadmap
    assert "| 7 | sealed_v7_rotation | `tests\\fixtures\\pattern_language_sealed_v7.json` | completed |" in roadmap
    assert "| 8 | sealed_v7_one_time_measurement | `build\\pattern_language_sealed_v7_measurement_report.json` | completed |" in roadmap
    assert "| 7 | post_v6_measurement_taxonomy | `build\\v7_targets_and_roadmap_v1.json` | completed |" in v6
    assert "Step 7 Output" in v6
    assert "PLM V7: Constraint And Critical Signal Recovery" in main
    assert "Targets and taxonomy: `build/v7_targets_and_roadmap_v1.json`" in main
    assert "Curriculum plan: `build/v7_nonsealed_curriculum_plan_v1.json`" in main
    assert "Draft repair fixture: `tests/fixtures/v7_router_repair_fixture_v1.json`" in main
    assert "Candidate replay report: `build/v7_router_repair_fixture_replay_v1.json`" in main
    assert "Router generalization report: `build/v7_router_generalization_report_v1.json`" in main
    assert "Non-sealed replay gate report: `build/v7_nonsealed_replay_gate_report_v1.json`" in main
    assert "Sealed v7 rotation review: `build/v7_sealed_rotation_review_v1.json`" in main
    assert "Sealed v7 rotation report: `build/v7_sealed_rotation_report_v1.json`" in main
    assert "Sealed v7 measurement: `build/pattern_language_sealed_v7_measurement_report.json`" in main
import json
from pathlib import Path


ROOT = Path(__file__).parents[1]
PLAN_PATH = ROOT / "build" / "v7_nonsealed_curriculum_plan_v1.json"
PLAN_MD_PATH = ROOT / "build" / "v7_nonsealed_curriculum_plan_v1.md"
V7_ROADMAP_PATH = ROOT / "docs" / "PLM_V7_ROADMAP.md"
MAIN_ROADMAP_PATH = ROOT / "docs" / "PATTERN_LANGUAGE_MODEL_roadmap.md"


def _load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_v7_curriculum_plan_preserves_contract_and_case_counts() -> None:
    payload = _load(PLAN_PATH)

    assert payload["schema_version"] == "v7-nonsealed-curriculum-plan.v1"
    assert payload["status"] == "designed_fixture_next"
    assert payload["source"] == "build\\v7_targets_and_roadmap_v1.json"
    assert payload["policy"] == {
        "sealed_v6_text_used": False,
        "sealed_v6_labels_used": False,
        "aggregate_taxonomy_only": True,
        "human_review_required": True,
        "draft_lanes_are_diagnostic_only": True,
        "same_cycle_promotion_allowed": False,
    }
    assert payload["required_case_counts"] == {
        "minimum_total": 72,
        "recommended_total": 96,
        "from_v7_targets_minimum": 72,
        "from_v7_targets_recommended": 96,
    }


def test_v7_curriculum_plan_covers_required_axes_and_theme_counts() -> None:
    payload = _load(PLAN_PATH)
    axes = {axis["id"]: axis for axis in payload["axes"]}

    assert list(axes) == [
        "constraint_preservation",
        "operation_sequence_repair",
        "critical_signal_recovery",
        "clarify_boundary_repair",
        "risk_ladder_calibration",
        "intent_boundary_stability",
    ]
    assert sum(axis["minimum_case_count"] for axis in axes.values()) == 72
    assert sum(axis["recommended_case_count"] for axis in axes.values()) == 96
    assert axes["constraint_preservation"]["minimum_case_count"] == 18
    assert axes["operation_sequence_repair"]["minimum_case_count"] == 18
    assert axes["critical_signal_recovery"]["minimum_case_count"] == 16
    assert axes["constraint_preservation"]["themes"][0]["id"] == "response_length_preservation"
    assert axes["operation_sequence_repair"]["themes"][0]["id"] == "clarify_then_build"
    assert axes["critical_signal_recovery"]["themes"][0]["id"] == "unverified_claim_detection"


def test_v7_curriculum_plan_sets_improvement_deltas_and_gates() -> None:
    payload = _load(PLAN_PATH)

    assert payload["target_delta"] == {
        "intent_accuracy": 0.142857,
        "critical_signal_recall": 0.392857,
        "operation_exact_match": 0.214286,
        "constraint_exact_match": 0.214286,
        "risk_exact_match": 0.142857,
        "sealed_error_count_reduction": 13,
    }
    gates = payload["acceptance_gates_before_v7_rotation"]
    assert gates["v7_curriculum_exact_minimum"] == 0.95
    assert gates["v7_critical_signal_recall_minimum"] == 0.9
    assert gates["v7_constraint_exact_match_minimum"] == 0.9
    assert gates["v7_operation_exact_match_minimum"] == 0.9
    assert gates["v7_risk_exact_match_minimum"] == 0.9
    assert gates["sealed_overlap_count_required"] == 0
    assert payload["next_action"] == "roadmap_v7_step3_create_nonsealed_fixture_and_candidate_replay"


def test_v7_curriculum_plan_docs_mark_step4_complete_with_step5_next() -> None:
    plan = PLAN_MD_PATH.read_text(encoding="utf-8")
    roadmap = V7_ROADMAP_PATH.read_text(encoding="utf-8")
    main = MAIN_ROADMAP_PATH.read_text(encoding="utf-8")

    assert "V7 Non-Sealed Curriculum Plan v1" in plan
    assert "| minimum_total | 72 |" in plan
    assert "| recommended_total | 96 |" in plan
    assert "| 2 | v7_nonsealed_curriculum_design | `build\\v7_nonsealed_curriculum_plan_v1.json` | completed |" in roadmap
    assert "| 3 | v7_nonsealed_fixture_and_candidate_replay | `tests\\fixtures\\v7_router_repair_fixture_v1.json` | completed |" in roadmap
    assert "| 4 | v7_router_generalization_changes | `build\\v7_router_generalization_report_v1.json` | completed |" in roadmap
    assert "| 5 | v7_nonsealed_replay_gate | `build\\v7_nonsealed_replay_gate_report_v1.json` | completed |" in roadmap
    assert "| 6 | sealed_v7_rotation_review | `build\\v7_sealed_rotation_review_v1.json` | completed |" in roadmap
    assert "| 7 | sealed_v7_rotation | `tests\\fixtures\\pattern_language_sealed_v7.json` | completed |" in roadmap
    assert "| 8 | sealed_v7_one_time_measurement | `build\\pattern_language_sealed_v7_measurement_report.json` | completed |" in roadmap
    assert "Curriculum plan: `build/v7_nonsealed_curriculum_plan_v1.json`" in main
    assert "Draft repair fixture: `tests/fixtures/v7_router_repair_fixture_v1.json`" in main
    assert "Candidate replay report: `build/v7_router_repair_fixture_replay_v1.json`" in main
    assert "Router generalization report: `build/v7_router_generalization_report_v1.json`" in main
    assert "Non-sealed replay gate report: `build/v7_nonsealed_replay_gate_report_v1.json`" in main
    assert "Sealed v7 rotation review: `build/v7_sealed_rotation_review_v1.json`" in main
    assert "Sealed v7 rotation report: `build/v7_sealed_rotation_report_v1.json`" in main
    assert "Sealed v7 measurement: `build/pattern_language_sealed_v7_measurement_report.json`" in main
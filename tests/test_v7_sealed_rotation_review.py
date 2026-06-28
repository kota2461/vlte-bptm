import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).parents[1]
SCRIPT_PATH = ROOT / "build" / "review_v7_sealed_rotation.py"
REVIEW_PATH = ROOT / "build" / "v7_sealed_rotation_review_v1.json"
REVIEW_MD_PATH = ROOT / "build" / "v7_sealed_rotation_review_v1.md"
V7_ROADMAP_PATH = ROOT / "docs" / "PLM_V7_ROADMAP.md"
MAIN_ROADMAP_PATH = ROOT / "docs" / "PATTERN_LANGUAGE_MODEL_roadmap.md"
TARGETS_PATH = ROOT / "build" / "v7_targets_and_roadmap_v1.json"


def _load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_v7_sealed_rotation_review_is_pre_rotation_eligible() -> None:
    report = _load(REVIEW_PATH)

    assert report["schema_version"] == "v7-sealed-rotation-review.v1"
    assert report["decision"] == "eligible_for_fresh_sealed_v7_rotation"
    assert report["passed"] is True
    assert report["policy"] == {
        "sealed_v7_fixture_created_now": False,
        "sealed_v7_opened_for_measurement": False,
        "sealed_v7_labels_used_for_tuning": False,
        "sealed_v6_text_used_for_training": False,
        "sealed_v6_labels_used_for_tuning": False,
        "sealed_v6_measurement_used_as_taxonomy_only": True,
        "nonsealed_replay_gate_required": True,
        "nonsealed_replay_gate_passed": True,
        "draft_or_candidate_lanes_used_as_gate_evidence": False,
        "same_cycle_promotion_allowed": False,
    }
    assert report["gate_summary"]["required_error_count"] == 0
    assert report["gate_summary"]["diagnostic_error_count"] == 0
    assert report["gate_summary"]["v7_curriculum_error_count"] == 0
    assert report["registry_state"]["active_sealed_fixtures"] == []
    assert report["registry_state"]["previous_sealed"] == {
        "registry_name": "pattern_language_sealed_v6.json",
        "status": "consumed",
        "measured": True,
        "reviewed": False,
        "measurement_report": "build\\pattern_language_sealed_v6_measurement_report.json",
    }
    assert report["registry_state"]["planned_successor"] == {
        "registry_name": "pattern_language_sealed_v7.json",
        "predecessor": "pattern_language_sealed_v6.json",
        "status": "not_created",
        "measured": False,
        "reviewed": False,
    }
    assert report["blockers"] == []
    assert report["next_action"] == "roadmap_v7_step7_generate_and_rotate_sealed_v7_fixture"


def test_v7_sealed_rotation_review_records_fixture_constraints() -> None:
    report = _load(REVIEW_PATH)
    constraints = report["planned_v7_fixture_constraints"]

    assert constraints["case_count"] == 28
    assert constraints["cases_per_intent"] == 4
    assert constraints["split"] == "sealed"
    assert constraints["must_be_unopened_until_measurement"] is True
    assert "pattern_language_sealed_v6.json" in constraints["must_exclude_exact_text_from"][
        "prior_sealed_and_benchmark"
    ]
    assert "tests\\fixtures\\v6_boundary_priority_review_adopted_benchmark_v1.json" in constraints[
        "must_exclude_exact_text_from"
    ]["v7_required_nonsealed_gate_lanes"]
    assert "tests\\fixtures\\v7_router_repair_fixture_v1.json" in constraints[
        "must_exclude_exact_text_from"
    ]["v7_diagnostic_nonsealed_lanes"]
    assert constraints["measurement_rule"] == "measure_once_then_mark_consumed"
    assert "measurement-only" in constraints["labels_rule"]


def test_v7_rotation_review_docs_targets_and_script_regenerate() -> None:
    review_md = REVIEW_MD_PATH.read_text(encoding="utf-8")
    roadmap = V7_ROADMAP_PATH.read_text(encoding="utf-8")
    main = MAIN_ROADMAP_PATH.read_text(encoding="utf-8")
    targets = _load(TARGETS_PATH)

    assert "V7 Sealed Rotation Review v1" in review_md
    assert "eligible_for_fresh_sealed_v7_rotation" in review_md
    assert targets["status"] == "step8_sealed_v7_measurement_completed_v8_rotation_required"
    assert targets["next_action"] == "roadmap_v8_step1_post_v7_measurement_taxonomy"
    assert targets["step6_sealed_rotation_review"]["passed"] is True
    assert targets["step6_sealed_rotation_review"]["summary"]["blocker_count"] == 0
    assert "| 6 | sealed_v7_rotation_review | `build\\v7_sealed_rotation_review_v1.json` | completed |" in roadmap
    assert "| 7 | sealed_v7_rotation | `tests\\fixtures\\pattern_language_sealed_v7.json` | completed |" in roadmap
    assert "Sealed v7 rotation review: `build/v7_sealed_rotation_review_v1.json`" in main
    assert "Sealed v7 rotation report: `build/v7_sealed_rotation_report_v1.json`" in main
    assert "Sealed v7 measurement: `build/pattern_language_sealed_v7_measurement_report.json`" in main

    report = _load(REVIEW_PATH)
    assert report["passed"] is True
    assert report["blockers"] == []


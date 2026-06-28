import json
from pathlib import Path


ROOT = Path(__file__).parents[1]
REVIEW_PATH = ROOT / "build" / "v8_sealed_rotation_review_v1.json"
REVIEW_MD_PATH = ROOT / "build" / "v8_sealed_rotation_review_v1.md"
TARGETS_PATH = ROOT / "build" / "v8_targets_and_roadmap_v1.json"
ROADMAP_PATH = ROOT / "docs" / "PLM_V8_ROADMAP.md"
MAIN_ROADMAP_PATH = ROOT / "docs" / "PATTERN_LANGUAGE_MODEL_roadmap.md"


def _load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_v8_sealed_rotation_review_is_pre_rotation_eligible() -> None:
    report = _load(REVIEW_PATH)

    assert report["schema_version"] == "v8-sealed-rotation-review.v1"
    assert report["decision"] == "eligible_for_fresh_sealed_v8_rotation"
    assert report["passed"] is True
    assert report["policy"] == {
        "sealed_v8_fixture_created_now": False,
        "sealed_v8_opened_for_measurement": False,
        "sealed_v8_labels_used_for_tuning": False,
        "sealed_v7_text_used_for_training": False,
        "sealed_v7_labels_used_for_tuning": False,
        "sealed_v7_measurement_used_as_taxonomy_only": True,
        "nonsealed_replay_gate_required": True,
        "nonsealed_replay_gate_passed": True,
        "same_cycle_promotion_allowed": False,
    }
    assert report["gate_summary"]["required_error_count"] == 0
    assert report["registry_state"]["active_sealed_fixtures"] == []
    assert report["registry_state"]["previous_sealed"] == {
        "registry_name": "pattern_language_sealed_v7.json",
        "status": "consumed",
        "measured": True,
        "reviewed": False,
        "measurement_report": "build\\pattern_language_sealed_v7_measurement_report.json",
    }
    assert report["registry_state"]["planned_successor"] == {
        "registry_name": "pattern_language_sealed_v8.json",
        "predecessor": "pattern_language_sealed_v7.json",
        "status": "not_created",
        "measured": False,
        "reviewed": False,
    }
    assert report["blockers"] == []
    assert report["next_action"] == "roadmap_v8_step7_generate_and_rotate_sealed_v8_fixture"


def test_v8_sealed_rotation_review_records_fixture_constraints() -> None:
    report = _load(REVIEW_PATH)
    constraints = report["planned_v8_fixture_constraints"]

    assert constraints["case_count"] == 28
    assert constraints["cases_per_intent"] == 4
    assert constraints["split"] == "sealed"
    assert constraints["must_be_unopened_until_measurement"] is True
    assert "pattern_language_sealed_v7.json" in constraints["must_exclude_exact_text_from"][
        "prior_sealed_and_benchmark"
    ]
    assert "tests\\fixtures\\v8_recovery_priority_review_candidate_benchmark_v1.json" in constraints[
        "must_exclude_exact_text_from"
    ]["v8_required_nonsealed_gate_lanes"]
    assert constraints["measurement_rule"] == "measure_once_then_mark_consumed"
    assert "measurement-only" in constraints["labels_rule"]


def test_v8_rotation_review_docs_and_targets_are_preserved_after_step7() -> None:
    review_md = REVIEW_MD_PATH.read_text(encoding="utf-8")
    roadmap = ROADMAP_PATH.read_text(encoding="utf-8")
    main = MAIN_ROADMAP_PATH.read_text(encoding="utf-8")
    targets = _load(TARGETS_PATH)

    assert "V8 Sealed Rotation Review v1" in review_md
    assert "eligible_for_fresh_sealed_v8_rotation" in review_md
    assert targets["step6_sealed_rotation_review"]["passed"] is True
    assert targets["step6_sealed_rotation_review"]["summary"]["blocker_count"] == 0
    assert targets["step7_sealed_rotation"]["passed"] is True
    assert "| 6 | sealed_v8_rotation_review | `build\\v8_sealed_rotation_review_v1.json` | completed |" in roadmap
    assert "| 7 | sealed_v8_rotation | `tests\\fixtures\\pattern_language_sealed_v8.json` | completed |" in roadmap
    assert "Sealed v8 rotation review: `build/v8_sealed_rotation_review_v1.json`" in main
    assert "Sealed v8 rotation report: `build/v8_sealed_rotation_report_v1.json`" in main

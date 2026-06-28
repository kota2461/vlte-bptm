import json
from pathlib import Path


ROOT = Path(__file__).parents[1]
REVIEW_PATH = ROOT / "build" / "v6_sealed_rotation_review_v1.json"
REVIEW_MD_PATH = ROOT / "build" / "v6_sealed_rotation_review_v1.md"
V6_ROADMAP_PATH = ROOT / "docs" / "PLM_V6_ROADMAP.md"
MAIN_ROADMAP_PATH = ROOT / "docs" / "PATTERN_LANGUAGE_MODEL_roadmap.md"


def _load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_v6_sealed_rotation_review_is_pre_rotation_eligible() -> None:
    report = _load(REVIEW_PATH)

    assert report["schema_version"] == "v6-sealed-rotation-review.v1"
    assert report["decision"] == "eligible_for_fresh_sealed_v6_rotation"
    assert report["passed"] is True
    assert report["policy"] == {
        "sealed_v6_fixture_created_now": False,
        "sealed_v6_opened_for_measurement": False,
        "sealed_v6_labels_used_for_tuning": False,
        "sealed_v5_text_used_for_training": False,
        "sealed_v5_labels_used_for_tuning": False,
        "sealed_v5_measurement_used_as_taxonomy_only": True,
        "nonsealed_replay_gate_required": True,
        "nonsealed_replay_gate_passed": True,
        "draft_or_candidate_lanes_used_as_gate_evidence": False,
        "same_cycle_promotion_allowed": False,
    }
    assert report["gate_summary"]["required_error_count"] == 0
    assert report["gate_summary"]["diagnostic_error_count"] == 0
    assert report["registry_state"]["active_sealed_fixtures"] == []
    assert report["registry_state"]["previous_sealed"]["status"] == "consumed"
    assert report["registry_state"]["previous_sealed"]["measured"] is True
    assert report["registry_state"]["planned_successor"] == {
        "registry_name": "pattern_language_sealed_v6.json",
        "predecessor": "pattern_language_sealed_v5.json",
        "status": "not_created",
        "measured": False,
        "reviewed": False,
    }
    assert report["blockers"] == []
    assert report["next_action"] == "roadmap_step5_generate_and_rotate_sealed_v6_fixture"


def test_v6_sealed_rotation_review_records_fixture_constraints() -> None:
    report = _load(REVIEW_PATH)
    constraints = report["planned_v6_fixture_constraints"]

    assert constraints["case_count"] == 28
    assert constraints["cases_per_intent"] == 4
    assert constraints["split"] == "sealed"
    assert constraints["must_be_unopened_until_measurement"] is True
    assert "pattern_language_sealed_v5.json" in constraints["must_exclude_exact_text_from"][
        "prior_sealed_and_benchmark"
    ]
    assert "tests/fixtures/v6_boundary_priority_review_adopted_benchmark_v1.json" in constraints[
        "must_exclude_exact_text_from"
    ]["v6_required_nonsealed_gate_lanes"]
    assert "tests/fixtures/v6_contrast_negative_benchmark_v1.json" in constraints[
        "must_exclude_exact_text_from"
    ]["v6_diagnostic_nonsealed_lanes"]
    assert constraints["measurement_rule"] == "measure_once_then_mark_consumed"
    assert "measurement-only" in constraints["labels_rule"]


def test_v6_rotation_review_docs_exist_and_mark_step4() -> None:
    review_md = REVIEW_MD_PATH.read_text(encoding="utf-8")
    roadmap = V6_ROADMAP_PATH.read_text(encoding="utf-8")
    main = MAIN_ROADMAP_PATH.read_text(encoding="utf-8")

    assert "V6 Sealed Rotation Review v1" in review_md
    assert "eligible_for_fresh_sealed_v6_rotation" in review_md
    assert "PLM V6 Roadmap" in roadmap
    assert "| 4 | sealed_v6_rotation_review | `build\\v6_sealed_rotation_review_v1.json` | completed |" in roadmap
    assert "| 5 | sealed_v6_rotation | `tests\\fixtures\\pattern_language_sealed_v6.json` | completed |" in roadmap
    assert "| 6 | sealed_v6_one_time_measurement | `build\\pattern_language_sealed_v6_measurement_report.json` | completed |" in roadmap
    assert "PLM V6: Boundary Calibration And Sealed Rotation" in main
    assert "Sealed v6 rotation review: `build/v6_sealed_rotation_review_v1.json`" in main


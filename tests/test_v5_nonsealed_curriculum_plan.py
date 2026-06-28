import json
from pathlib import Path


ROOT = Path(__file__).parents[1]
PLAN_PATH = ROOT / "build" / "v5_nonsealed_curriculum_plan_v1.json"
PLAN_MD_PATH = ROOT / "build" / "v5_nonsealed_curriculum_plan_v1.md"


def _load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_v5_nonsealed_curriculum_plan_uses_taxonomy_without_sealed_text() -> None:
    payload = _load(PLAN_PATH)

    assert payload["schema_version"] == "v5-nonsealed-curriculum-plan.v1"
    assert payload["status"] == "designed"
    assert payload["policy"]["sealed_v4_text_used"] is False
    assert payload["policy"]["sealed_v4_labels_used_for_tuning"] is False
    assert payload["policy"]["sealed_v4_measurement_used_as_taxonomy_only"] is True
    assert payload["policy"]["sealed_fixture_opened_by_this_step"] is False
    assert payload["policy"]["success_pattern_lane_write_from_failures_allowed"] is False

    for axis in payload["curriculum_axes"]:
        assert "input" not in axis
        assert "expected" not in axis


def test_v5_curriculum_axes_cover_all_v5_error_pressure_points() -> None:
    payload = _load(PLAN_PATH)
    axes = {axis["name"]: axis for axis in payload["curriculum_axes"]}

    assert len(axes) == 7
    assert set(axes) == {
        "multiple_intent_preservation",
        "missing_info_and_clarify_boundary",
        "current_unverified_verification",
        "constraint_preservation",
        "operation_sequence_exactness",
        "intent_boundary_repair",
        "risk_flag_completion",
    }
    assert "multiple_intents" in axes["multiple_intent_preservation"]["target_signals"]
    assert "missing_required_information" in axes["missing_info_and_clarify_boundary"]["target_signals"]
    assert "requires_current_information" in axes["current_unverified_verification"]["target_signals"]
    assert axes["constraint_preservation"]["sealed_v4_taxonomy_fields"] == ["constraints"]
    assert "risk" in axes["risk_flag_completion"]["sealed_v4_taxonomy_fields"]


def test_v5_curriculum_source_pools_are_nonsealed_and_sufficient() -> None:
    payload = _load(PLAN_PATH)
    pools = payload["source_pools"]

    assert pools["critical_constraints_candidates"]["sealed_source"] is False
    assert pools["critical_constraints_candidates"]["review_candidate_count"] >= 200
    assert pools["v4_failure_memory"]["sealed_source"] is False
    assert pools["v4_failure_memory"]["item_count"] >= 38
    assert pools["v4_puzzle_failure_memory"]["sealed_source"] is False
    assert pools["v4_puzzle_failure_memory"]["failure_count"] >= 2

    gates = payload["pre_step3_gates"]
    assert all(gates.values())


def test_v5_curriculum_fixture_blueprint_sets_step3_contract() -> None:
    payload = _load(PLAN_PATH)
    blueprint = payload["fixture_blueprint"]

    assert blueprint["output"] == "tests\\fixtures\\v5_critical_operations_fixture_v1.json"
    assert blueprint["case_count_min"] == 48
    assert blueprint["human_review_required"] is True
    assert blueprint["sealed_text_overlap_count_required"] == 0
    assert blueprint["case_overlap_between_axes_allowed"] is True
    assert set(blueprint["min_cases_by_axis"]) == {
        axis["name"] for axis in payload["curriculum_axes"]
    }

    assert payload["next_step"] == {
        "step": 3,
        "name": "critical_signal_and_operations_fixture",
        "output": "tests\\fixtures\\v5_critical_operations_fixture_v1.json",
    }


def test_v5_curriculum_markdown_summarizes_step3() -> None:
    text = PLAN_MD_PATH.read_text(encoding="utf-8")

    assert "V5 Non-Sealed Curriculum Plan v1" in text
    assert "minimum challenge cases: 48" in text
    assert "multiple_intent_preservation" in text
    assert "Sealed v4 text overlap must remain 0" in text
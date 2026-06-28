import json
from pathlib import Path

from semantic_routing.benchmark import parse_plm_benchmark


ROOT = Path(__file__).parents[1]
FIXTURE_PATH = ROOT / "tests" / "fixtures" / "v7_router_repair_fixture_v1.json"
REPORT_PATH = ROOT / "build" / "v7_router_repair_fixture_replay_v1.json"
WORKSHEET_PATH = ROOT / "build" / "v7_router_repair_fixture_review_worksheet_v1.md"
PLAN_PATH = ROOT / "build" / "v7_nonsealed_curriculum_plan_v1.json"
TARGETS_PATH = ROOT / "build" / "v7_targets_and_roadmap_v1.json"
V7_ROADMAP_PATH = ROOT / "docs" / "PLM_V7_ROADMAP.md"
MAIN_ROADMAP_PATH = ROOT / "docs" / "PATTERN_LANGUAGE_MODEL_roadmap.md"


EXPECTED_AXIS_COUNTS = {
    "constraint_preservation": 18,
    "operation_sequence_repair": 18,
    "critical_signal_recovery": 16,
    "clarify_boundary_repair": 8,
    "risk_ladder_calibration": 6,
    "intent_boundary_stability": 6,
}


def _load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _benchmark_payload(fixture):
    return {
        "schema_version": "pattern-language-benchmark.v1",
        "frozen_at": fixture["created_at"],
        "authoring_method": "test wrapper for v7 non-sealed router repair fixture",
        "review_status": fixture["review_status"],
        "policy": fixture["policy"].__repr__(),
        "cases": [
            {
                "id": case["id"],
                "split": case["split"],
                "source_group": case["source_group"],
                "contrast_group": None,
                "language": case["language"],
                "input": case["input"],
                "expected": case["expected"],
            }
            for case in fixture["cases"]
        ],
    }


def test_v7_router_repair_fixture_is_draft_nonsealed_material() -> None:
    fixture = _load(FIXTURE_PATH)

    assert fixture["schema_version"] == "v7-router-repair-fixture.v1"
    assert fixture["fixture_id"] == "v7-router-repair-fixture-v1"
    assert fixture["status"] == "draft_ready_for_candidate_replay"
    assert fixture["review_status"] == "draft"
    assert fixture["source_plan"] == "build\\v7_nonsealed_curriculum_plan_v1.json"
    assert fixture["policy"] == {
        "sealed_v6_text_used": False,
        "sealed_v6_labels_used": False,
        "success_pattern_training_allowed": False,
        "human_review_required_before_gate": True,
        "candidate_replay_is_gate": False,
        "same_cycle_promotion_allowed": False,
    }
    assert fixture["requirements"]["case_count_min"] == 72
    assert fixture["requirements"]["case_count_recommended"] == 96
    assert fixture["requirements"]["sealed_text_overlap_count_required"] == 0
    assert fixture["summary"]["case_count"] == 72
    assert len(fixture["cases"]) == 72


def test_v7_router_repair_cases_parse_as_plm_expected_semantics() -> None:
    fixture = _load(FIXTURE_PATH)
    benchmark = parse_plm_benchmark(_benchmark_payload(fixture))

    assert len(benchmark.cases) == 72
    assert benchmark.review_status == "draft"
    assert {case.split for case in benchmark.cases} == {"validation"}
    assert len({case.input_text for case in benchmark.cases}) == 72
    assert {case.language for case in benchmark.cases} == {"en", "ja", "mixed"}

    for case in fixture["cases"]:
        assert case["id"].startswith("v7-router-repair-")
        assert case["review_status"] == "draft"
        assert case["source_kind"] == "self_authored_nonsealed_repair"
        assert case["source_ref"] == "build/v7_nonsealed_curriculum_plan_v1.json"
        assert case["axis_id"] in EXPECTED_AXIS_COUNTS
        assert case["theme_id"]
        assert case["notes"] == "Draft non-sealed label for human review before gate use."


def test_v7_router_repair_fixture_meets_axis_minimums_and_signal_coverage() -> None:
    fixture = _load(FIXTURE_PATH)
    plan = _load(PLAN_PATH)
    min_by_axis = fixture["requirements"]["min_cases_by_axis"]

    assert min_by_axis == {axis["id"]: axis["minimum_case_count"] for axis in plan["axes"]}
    assert fixture["summary"]["by_axis"] == EXPECTED_AXIS_COUNTS
    for axis, minimum in min_by_axis.items():
        assert fixture["summary"]["by_axis"][axis] >= minimum

    assert fixture["summary"]["critical_signal_support"] == {
        "contains_unverified_claims": 15,
        "missing_required_information": 17,
        "multiple_intents": 22,
        "requires_current_information": 11,
    }
    assert fixture["summary"]["by_operation"]["verify"] == 28
    assert fixture["summary"]["by_operation"]["search"] == 12
    assert fixture["summary"]["by_operation"]["clarify"] == 17
    assert fixture["summary"]["by_constraint"]["must:ask_first"] == 9
    assert fixture["summary"]["by_constraint"]["must:cite_sources"] == 8
    assert fixture["summary"]["by_risk"] == {"high": 7, "low": 49, "medium": 16}


def test_v7_router_repair_candidate_replay_is_diagnostic_not_gate() -> None:
    report = _load(REPORT_PATH)
    measurement = report["current_route_measurement"]

    assert report["schema_version"] == "v7-router-repair-fixture-replay.v1"
    assert report["status"] == "draft_fixture_replayed_not_a_gate"
    assert report["current_route_measurement_is_gate"] is False
    assert measurement["case_count"] == 72
    assert measurement["valid_packet_rate"] == 1.0
    assert measurement["intent_accuracy"] == 0.736111
    assert measurement["critical_signal_recall"] == 0.476923
    assert measurement["operation_exact_match"] == 0.611111
    assert measurement["constraint_exact_match"] == 0.680556
    assert measurement["risk_exact_match"] == 0.763889
    assert len(measurement["errors"]) == 52
    assert report["next_step"] == {
        "step": 4,
        "name": "v7_router_generalization_changes",
        "output": "build/v7_router_generalization_report_v1.json",
    }


def test_v7_router_repair_outputs_remain_linked_after_step4() -> None:
    targets = _load(TARGETS_PATH)
    worksheet = WORKSHEET_PATH.read_text(encoding="utf-8")
    roadmap = V7_ROADMAP_PATH.read_text(encoding="utf-8")
    main = MAIN_ROADMAP_PATH.read_text(encoding="utf-8")

    assert targets["status"] == "step8_sealed_v7_measurement_completed_v8_rotation_required"
    assert [step["status"] for step in targets["roadmap"]] == [
        "completed",
        "completed",
        "completed",
        "completed",
        "completed",
        "completed",
        "completed",
        "completed",
    ]
    assert targets["next_action"] == "roadmap_v8_step1_post_v7_measurement_taxonomy"
    assert "V7 Router Repair Fixture Review Worksheet v1" in worksheet
    assert "No sealed fixture text or labels were used" in worksheet
    assert "case_count: 72" in worksheet
    assert "v7-router-repair-001" in worksheet
    assert "| 3 | v7_nonsealed_fixture_and_candidate_replay | `tests\\fixtures\\v7_router_repair_fixture_v1.json` | completed |" in roadmap
    assert "| 4 | v7_router_generalization_changes | `build\\v7_router_generalization_report_v1.json` | completed |" in roadmap
    assert "| 5 | v7_nonsealed_replay_gate | `build\\v7_nonsealed_replay_gate_report_v1.json` | completed |" in roadmap
    assert "| 6 | sealed_v7_rotation_review | `build\\v7_sealed_rotation_review_v1.json` | completed |" in roadmap
    assert "| 7 | sealed_v7_rotation | `tests\\fixtures\\pattern_language_sealed_v7.json` | completed |" in roadmap
    assert "Draft repair fixture: `tests/fixtures/v7_router_repair_fixture_v1.json`" in main
    assert "Candidate replay report: `build/v7_router_repair_fixture_replay_v1.json`" in main
    assert "Router generalization report: `build/v7_router_generalization_report_v1.json`" in main
    assert "Non-sealed replay gate report: `build/v7_nonsealed_replay_gate_report_v1.json`" in main
    assert "Sealed v7 rotation review: `build/v7_sealed_rotation_review_v1.json`" in main
    assert "Sealed v7 rotation report: `build/v7_sealed_rotation_report_v1.json`" in main
    assert "Sealed v7 measurement: `build/pattern_language_sealed_v7_measurement_report.json`" in main
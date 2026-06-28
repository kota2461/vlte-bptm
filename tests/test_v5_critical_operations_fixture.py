import json
from pathlib import Path

from semantic_routing.benchmark import parse_plm_benchmark


ROOT = Path(__file__).parents[1]
FIXTURE_PATH = ROOT / "tests" / "fixtures" / "v5_critical_operations_fixture_v1.json"
REPORT_PATH = ROOT / "build" / "v5_critical_operations_fixture_report_v1.json"
WORKSHEET_PATH = ROOT / "build" / "v5_critical_operations_fixture_review_worksheet_v1.md"
PLAN_PATH = ROOT / "build" / "v5_nonsealed_curriculum_plan_v1.json"


def _load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _benchmark_payload(fixture):
    return {
        "schema_version": "pattern-language-benchmark.v1",
        "frozen_at": fixture["created_at"],
        "authoring_method": "test wrapper for v5 non-sealed fixture",
        "review_status": "draft",
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


def test_v5_critical_operations_fixture_is_draft_nonsealed_material() -> None:
    fixture = _load(FIXTURE_PATH)

    assert fixture["schema_version"] == "v5-critical-operations-fixture.v1"
    assert fixture["status"] == "draft_ready_for_human_review"
    assert fixture["review_status"] == "draft"
    assert fixture["source_plan"] == "build\\v5_nonsealed_curriculum_plan_v1.json"
    assert fixture["policy"] == {
        "sealed_fixtures_used_as_sources": False,
        "sealed_v4_text_used": False,
        "sealed_v4_labels_used": False,
        "success_pattern_training_allowed": False,
        "human_review_required_before_gate": True,
        "same_cycle_promotion_allowed": False,
    }
    assert fixture["requirements"]["case_count_min"] == 48
    assert fixture["requirements"]["sealed_text_overlap_count_required"] == 0
    assert fixture["summary"]["case_count"] == 48
    assert len(fixture["cases"]) == 48


def test_v5_critical_operations_cases_parse_as_plm_expected_semantics() -> None:
    fixture = _load(FIXTURE_PATH)
    benchmark = parse_plm_benchmark(_benchmark_payload(fixture))

    assert len(benchmark.cases) == 48
    assert benchmark.review_status == "draft"
    assert {case.split for case in benchmark.cases} == {"validation"}
    assert len({case.input_text for case in benchmark.cases}) == 48

    for case in fixture["cases"]:
        assert case["review_status"] == "draft"
        assert case["source_kind"] == "self_authored_nonsealed_challenge"
        assert case["source_ref"] == "build/v5_nonsealed_curriculum_plan_v1.json"
        assert case["language"] == "en"
        assert case["axis_ids"]
        assert not case["input"].startswith("plm-sealed")


def test_v5_critical_operations_fixture_meets_axis_minimums() -> None:
    fixture = _load(FIXTURE_PATH)
    plan = _load(PLAN_PATH)
    axis_name_by_id = {axis["id"]: axis["name"] for axis in plan["curriculum_axes"]}
    min_by_axis_name = fixture["requirements"]["min_cases_by_axis"]
    counts_by_name = {
        axis_name_by_id[axis_id]: count
        for axis_id, count in fixture["summary"]["by_axis"].items()
    }

    for axis_name, minimum in min_by_axis_name.items():
        assert counts_by_name[axis_name] >= minimum

    assert fixture["summary"]["critical_signal_support"]["multiple_intents"] >= 12
    assert fixture["summary"]["critical_signal_support"]["missing_required_information"] >= 10
    assert fixture["summary"]["critical_signal_support"]["requires_current_information"] >= 6
    assert fixture["summary"]["by_operation"]["verify"] >= 12
    assert fixture["summary"]["by_operation"]["compare"] >= 6
    assert fixture["summary"]["by_operation"]["calculate"] >= 4
    assert fixture["summary"]["by_constraint"]["must:ask_first"] >= 8
    assert fixture["summary"]["by_risk"]["high"] >= 3


def test_v5_critical_operations_report_is_not_a_gate() -> None:
    report = _load(REPORT_PATH)

    assert report["schema_version"] == "v5-critical-operations-fixture-report.v1"
    assert report["status"] == "draft_fixture_created_not_a_gate"
    assert report["current_route_measurement_is_gate"] is False
    assert report["current_route_measurement"]["case_count"] == 48
    assert report["current_route_measurement"]["valid_packet_rate"] == 1.0
    assert report["current_route_measurement"]["errors"]
    assert report["next_step"] == {
        "step": 4,
        "name": "router_generalization_changes",
        "output": "build/v5_router_generalization_report.json",
    }


def test_v5_critical_operations_review_worksheet_exists() -> None:
    text = WORKSHEET_PATH.read_text(encoding="utf-8")

    assert "V5 Critical Operations Fixture Review Worksheet v1" in text
    assert "No sealed fixture text or labels were used" in text
    assert "case_count: 48" in text
    assert "v5-critical-ops-001" in text
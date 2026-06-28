import json
import subprocess
import sys
from pathlib import Path

from semantic_routing import evaluate_plm_extractor, load_plm_benchmark, parse_plm_benchmark, route


ROOT = Path(__file__).parents[1]
SCRIPT_PATH = ROOT / "build" / "run_v7_nonsealed_replay_gate.py"
REPORT_PATH = ROOT / "build" / "v7_nonsealed_replay_gate_report_v1.json"
REPORT_MD_PATH = ROOT / "build" / "v7_nonsealed_replay_gate_report_v1.md"


def _load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _fixture_payload(fixture, authoring_method="test wrapper for v7 nonsealed replay gate"):
    return {
        "schema_version": "pattern-language-benchmark.v1",
        "frozen_at": fixture["created_at"],
        "authoring_method": authoring_method,
        "review_status": fixture["review_status"],
        "policy": "non-sealed replay wrapper; sealed labels are excluded",
        "cases": [
            {
                "id": case["id"],
                "split": case["split"],
                "source_group": case["source_group"],
                "contrast_group": case.get("contrast_group"),
                "language": case["language"],
                "input": case["input"],
                "expected": case["expected"],
            }
            for case in fixture["cases"]
        ],
    }


def _measurement_for_lane(lane):
    path = ROOT / lane["source"]
    payload = _load(path)
    if lane["name"] == "visible_plm_train_validation":
        cases = load_plm_benchmark(path).cases_for_splits(("train", "validation"))
    elif payload.get("schema_version") == "pattern-language-benchmark.v1":
        cases = parse_plm_benchmark(payload).cases
    else:
        cases = parse_plm_benchmark(_fixture_payload(payload)).cases
    return evaluate_plm_extractor(cases, lambda text: route(text).packet)


def test_v7_nonsealed_replay_gate_passes_contract() -> None:
    report = _load(REPORT_PATH)

    assert report["schema_version"] == "v7-nonsealed-replay-gate-report.v1"
    assert report["status"] == "passed"
    assert report["passed"] is True
    assert report["policy"] == {
        "sealed_fixture_opened_now": False,
        "sealed_measurement_used_for_tuning": False,
        "sealed_v6_text_used": False,
        "sealed_v6_labels_used": False,
        "nonsealed_current_route_measurement_is_gate": True,
        "draft_or_candidate_lanes_are_gate_evidence": False,
        "same_cycle_promotion_allowed": False,
        "fresh_sealed_v7_required_before_adjudication": True,
    }
    assert report["summary"] == {
        "required_lane_count": 6,
        "required_passed_lane_count": 6,
        "required_error_count": 0,
        "diagnostic_lane_count": 4,
        "diagnostic_exact_lane_count": 4,
        "diagnostic_error_count": 0,
        "v7_curriculum_case_count": 72,
        "v7_curriculum_error_count": 0,
        "v7_curriculum_exact": True,
        "ready_for_step6_sealed_v7_rotation_review": True,
    }
    assert report["contract"] == {
        "can_use_for_v7_roadmap_step5": True,
        "can_use_as_sealed_measurement": False,
        "can_use_for_same_cycle_promotion": False,
        "requires_human_review_before_sealed_rotation": True,
        "requires_fresh_sealed_v7_before_measurement": True,
    }
    assert [lane["name"] for lane in report["required_lanes"]] == [
        "visible_plm_train_validation",
        "v5_critical_operations",
        "v6_boundary_false_positive_adopted",
        "v6_boundary_priority_review_adopted",
        "v6_structural_build_30_adopted",
        "v6_router_debate_adopted",
    ]
    assert [lane["name"] for lane in report["diagnostic_lanes"]] == [
        "v6_boundary_false_positive_candidate",
        "v6_contrast_negative",
        "v6_router_debate_candidate",
        "v7_router_repair_fixture",
    ]
    assert report["diagnostic_lanes"][-1]["gate_evidence_allowed"] is False
    assert report["next_action"] == "roadmap_v7_step6_sealed_rotation_review"


def test_v7_nonsealed_replay_gate_lanes_match_current_route() -> None:
    report = _load(REPORT_PATH)

    for lane in report["required_lanes"] + report["diagnostic_lanes"]:
        measurement = _measurement_for_lane(lane)
        compact = lane["measurement"]
        assert measurement["case_count"] == compact["case_count"], lane["name"]
        assert measurement["intent_accuracy"] == compact["intent_accuracy"], lane["name"]
        assert measurement["critical_signal_recall"] == compact["critical_signal_recall"], lane["name"]
        assert measurement["operation_exact_match"] == compact["operation_exact_match"], lane["name"]
        assert measurement["constraint_exact_match"] == compact["constraint_exact_match"], lane["name"]
        assert measurement["risk_exact_match"] == compact["risk_exact_match"], lane["name"]
        assert measurement["valid_packet_rate"] == compact["valid_packet_rate"], lane["name"]
        assert len(measurement["errors"]) == compact["error_count"], lane["name"]


def test_v7_nonsealed_replay_gate_markdown_and_script_regenerate() -> None:
    text = REPORT_MD_PATH.read_text(encoding="utf-8")

    assert "V7 Non-Sealed Replay Gate Report v1" in text
    assert "status: `passed`" in text
    assert "required_error_count: 0" in text
    assert "v7_curriculum_error_count: 0" in text
    assert "draft_or_candidate_lanes_are_gate_evidence: false" in text

    completed = subprocess.run(
        [sys.executable, "-B", str(SCRIPT_PATH)],
        cwd=ROOT,
        check=True,
        text=True,
        capture_output=True,
    )

    assert '"status": "passed"' in completed.stdout
    report = _load(REPORT_PATH)
    assert report["summary"]["required_error_count"] == 0
    assert report["summary"]["v7_curriculum_error_count"] == 0

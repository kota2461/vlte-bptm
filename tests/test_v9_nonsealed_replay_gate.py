import json
import subprocess
import sys
from pathlib import Path

from semantic_routing import evaluate_plm_extractor, parse_plm_benchmark, route


ROOT = Path(__file__).parents[1]
SCRIPT_PATH = ROOT / "build" / "run_v9_nonsealed_replay_gate.py"
REPORT_PATH = ROOT / "build" / "v9_nonsealed_replay_gate_report_v1.json"
REPORT_MD_PATH = ROOT / "build" / "v9_nonsealed_replay_gate_report_v1.md"


def _load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_v9_nonsealed_replay_gate_passes_contract() -> None:
    report = _load(REPORT_PATH)

    assert report["schema_version"] == "v9-nonsealed-replay-gate-report.v1"
    assert report["status"] == "passed"
    assert report["passed"] is True
    assert report["policy"] == {
        "sealed_fixture_opened_now": False,
        "sealed_measurement_used_for_tuning": False,
        "sealed_v8_text_used": False,
        "sealed_v8_labels_used": False,
        "raw_debate_logs_direct_training_allowed": False,
        "llm_turn_text_direct_training_allowed": False,
        "v9_primary_review_human_approved": True,
        "v9_constraint_operation_extension_human_approved": True,
        "prior_v9_replays_were_gate": False,
        "nonsealed_current_route_measurement_is_gate": True,
        "same_cycle_promotion_allowed": False,
        "fresh_sealed_v9_required_before_adjudication": True,
    }
    assert report["summary"] == {
        "dependency_v8_gate_passed": True,
        "dependency_v8_required_error_count": 0,
        "required_lane_count": 3,
        "required_passed_lane_count": 3,
        "required_error_count": 0,
        "total_case_count": 88,
        "v8_priority_review_case_count": 30,
        "v9_primary_review_case_count": 34,
        "v9_constraint_operation_extension_case_count": 24,
        "ready_for_step6_sealed_v9_rotation_review": True,
    }
    assert [lane["name"] for lane in report["required_lanes"]] == [
        "v8_recovery_priority_review_approved",
        "v9_accumulated_primary_review_approved",
        "v9_constraint_operation_extension",
    ]
    assert all(lane["passed_exact"] for lane in report["required_lanes"])
    assert sum(lane["measurement"]["case_count"] for lane in report["required_lanes"]) == 88
    assert report["contract"] == {
        "can_use_for_v9_roadmap_step5": True,
        "can_use_as_sealed_measurement": False,
        "can_use_for_same_cycle_promotion": False,
        "requires_fresh_sealed_v9_before_measurement": True,
    }
    assert report["next_action"] == "roadmap_v9_step6_sealed_rotation_review"


def test_v9_nonsealed_replay_gate_matches_current_route() -> None:
    report = _load(REPORT_PATH)
    for lane in report["required_lanes"]:
        payload = _load(ROOT / lane["source"])
        benchmark = parse_plm_benchmark(payload)
        measurement = evaluate_plm_extractor(benchmark.cases, lambda text: route(text).packet)
        compact = lane["measurement"]

        assert measurement["case_count"] == compact["case_count"]
        assert measurement["intent_accuracy"] == compact["intent_accuracy"]
        assert measurement["critical_signal_recall"] == compact["critical_signal_recall"]
        assert measurement["operation_exact_match"] == compact["operation_exact_match"]
        assert measurement["constraint_exact_match"] == compact["constraint_exact_match"]
        assert measurement["risk_exact_match"] == compact["risk_exact_match"]
        assert len(measurement["errors"]) == compact["error_count"]


def test_v9_nonsealed_replay_gate_markdown_and_script_regenerate() -> None:
    text = REPORT_MD_PATH.read_text(encoding="utf-8")

    assert "V9 Non-Sealed Replay Gate Report v1" in text
    assert "status: `passed`" in text
    assert "required_error_count: 0" in text
    assert "total_case_count: 88" in text
    assert "fresh_sealed_v9_required_before_adjudication: true" in text

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

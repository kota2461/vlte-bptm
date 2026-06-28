import json
import subprocess
import sys
from pathlib import Path

from semantic_routing import evaluate_plm_extractor, parse_plm_benchmark, route


ROOT = Path(__file__).parents[1]
SCRIPT_PATH = ROOT / "build" / "adopt_v6_boundary_false_positive_candidates.py"
ADOPTED_BENCHMARK_PATH = ROOT / "tests" / "fixtures" / "v6_boundary_false_positive_adopted_benchmark_v1.json"
ADOPTION_DECISION_PATH = ROOT / "build" / "v6_boundary_false_positive_adoption_decision_v1.json"
REPLAY_REPORT_PATH = ROOT / "build" / "v6_boundary_false_positive_adopted_replay_report_v1.json"


def _load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_v6_boundary_false_positive_adopted_benchmark_is_human_reviewed() -> None:
    payload = _load(ADOPTED_BENCHMARK_PATH)
    benchmark = parse_plm_benchmark(payload)

    assert payload["schema_version"] == "pattern-language-benchmark.v1"
    assert payload["review_status"] == "human_reviewed"
    assert len(benchmark.cases) == 15
    assert {case.split for case in benchmark.cases} == {"validation"}
    assert {case.expected.risk_level for case in benchmark.cases} == {"low"}
    assert {case.expected.primary_intent for case in benchmark.cases} == {
        "build",
        "explain",
        "respond",
    }


def test_v6_boundary_false_positive_adoption_decision_records_policy() -> None:
    decision = _load(ADOPTION_DECISION_PATH)

    assert decision["schema_version"] == "v6-boundary-false-positive-adoption-decision.v1"
    assert decision["status"] == "adopted_for_nonsealed_replay"
    assert decision["review_status"] == "human_reviewed"
    assert decision["reviewed_by"] == "user_confirmation_in_codex_thread"
    assert decision["adopted_count"] == 15
    assert decision["policy"] == {
        "sealed_fixtures_used_as_sources": False,
        "sealed_text_used": False,
        "sealed_labels_used": False,
        "raw_debate_logs_direct_training_allowed": False,
        "manual_prompt_synthesis_used": True,
        "human_review_confirmation_recorded": True,
        "same_cycle_promotion_allowed": False,
        "current_route_measurement_is_gate": False,
        "adopted_benchmark_is_directly_trainable": False,
    }


def test_v6_boundary_false_positive_adopted_replay_report_is_not_gate() -> None:
    report = _load(REPLAY_REPORT_PATH)

    assert report["schema_version"] == "v6-boundary-false-positive-adopted-replay-report.v1"
    assert report["status"] == "completed_without_route_gaps"
    assert report["current_route_measurement_is_gate"] is False
    assert report["sealed_fixture_used"] is False
    assert report["measurement"] == {
        "case_count": 15,
        "intent_accuracy": 1.0,
        "critical_signal_recall": 0.0,
        "operation_exact_match": 1.0,
        "constraint_exact_match": 1.0,
        "risk_exact_match": 1.0,
        "valid_packet_rate": 1.0,
        "error_count": 0,
    }
    assert report["errors"] == []


def test_v6_boundary_false_positive_adopted_lane_matches_current_route() -> None:
    benchmark = parse_plm_benchmark(_load(ADOPTED_BENCHMARK_PATH))
    measurement = evaluate_plm_extractor(
        benchmark.cases,
        lambda text: route(text).packet,
    )

    assert measurement["intent_accuracy"] == 1.0
    assert measurement["operation_exact_match"] == 1.0
    assert measurement["constraint_exact_match"] == 1.0
    assert measurement["risk_exact_match"] == 1.0
    assert measurement["errors"] == []


def test_v6_boundary_false_positive_adoption_script_regenerates_artifacts() -> None:
    completed = subprocess.run(
        [sys.executable, "-B", str(SCRIPT_PATH)],
        cwd=ROOT,
        check=True,
        text=True,
        capture_output=True,
    )

    assert "completed_without_route_gaps" in completed.stdout
    report = _load(REPLAY_REPORT_PATH)
    assert report["measurement"]["case_count"] == 15
    assert report["measurement"]["error_count"] == 0
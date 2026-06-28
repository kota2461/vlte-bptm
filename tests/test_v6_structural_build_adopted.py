import json
import subprocess
import sys
from pathlib import Path

from semantic_routing import evaluate_plm_extractor, parse_plm_benchmark, route


ROOT = Path(__file__).parents[1]
SCRIPT_PATH = ROOT / "build" / "adopt_v6_structural_build_30_candidates.py"
ADOPTED_BENCHMARK_PATH = ROOT / "tests" / "fixtures" / "v6_structural_build_30_adopted_benchmark_v1.json"
ADOPTION_DECISION_PATH = ROOT / "build" / "v6_structural_build_30_adoption_decision_v1.json"
REPLAY_REPORT_PATH = ROOT / "build" / "v6_structural_build_30_adopted_replay_report_v1.json"
WORKSHEET_PATH = ROOT / "build" / "v6_structural_build_30_adopted_worksheet_v1.md"


def _load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_v6_structural_build_adopted_benchmark_is_human_reviewed() -> None:
    payload = _load(ADOPTED_BENCHMARK_PATH)
    benchmark = parse_plm_benchmark(payload)

    assert payload["schema_version"] == "pattern-language-benchmark.v1"
    assert payload["review_status"] == "human_reviewed"
    assert len(benchmark.cases) == 30
    assert {case.split for case in benchmark.cases} == {"validation"}
    assert {case.expected.primary_intent for case in benchmark.cases} == {"build"}
    assert {case.expected.risk_level for case in benchmark.cases} == {"low"}
    assert len({case.input_text for case in benchmark.cases}) == 30


def test_v6_structural_build_adoption_decision_records_policy() -> None:
    decision = _load(ADOPTION_DECISION_PATH)

    assert decision["schema_version"] == "v6-structural-build-30-adoption-decision.v1"
    assert decision["status"] == "adopted_for_nonsealed_replay"
    assert decision["review_status"] == "human_reviewed"
    assert decision["reviewed_by"] == "user_confirmation_in_codex_thread"
    assert decision["adopted_count"] == 30
    assert decision["source_candidate_queue"] == "build/v6_structural_build_30_candidate_queue_v1.json"
    assert decision["source_candidate_benchmark"] == "tests/fixtures/v6_structural_build_30_candidate_benchmark_v1.json"
    assert decision["adopted_benchmark"] == "tests/fixtures/v6_structural_build_30_adopted_benchmark_v1.json"
    assert decision["policy"] == {
        "sealed_fixtures_used_as_sources": False,
        "sealed_text_used": False,
        "sealed_labels_used": False,
        "raw_debate_logs_direct_training_allowed": False,
        "llm_turn_text_direct_training_allowed": False,
        "topic_metadata_synthesis_used": True,
        "manual_prompt_synthesis_used": True,
        "human_review_confirmation_recorded": True,
        "same_cycle_promotion_allowed": False,
        "current_route_measurement_is_gate": False,
        "adopted_benchmark_is_directly_trainable": False,
    }


def test_v6_structural_build_replay_report_matches_current_route() -> None:
    report = _load(REPLAY_REPORT_PATH)

    assert report["schema_version"] == "v6-structural-build-30-adopted-replay-report.v1"
    assert report["status"] == "completed_without_route_gaps"
    assert report["current_route_measurement_is_gate"] is False
    assert report["sealed_fixture_used"] is False
    assert report["summary"]["adopted_count"] == 30
    assert report["measurement"] == {
        "case_count": 30,
        "intent_accuracy": 1.0,
        "critical_signal_recall": 0.0,
        "operation_exact_match": 1.0,
        "constraint_exact_match": 1.0,
        "risk_exact_match": 1.0,
        "valid_packet_rate": 1.0,
        "error_count": 0,
        "error_field_counts": {},
    }
    assert report["errors"] == []


def test_v6_structural_build_lane_replays_current_route() -> None:
    benchmark = parse_plm_benchmark(_load(ADOPTED_BENCHMARK_PATH))
    measurement = evaluate_plm_extractor(
        benchmark.cases,
        lambda text: route(text).packet,
    )

    assert measurement["case_count"] == 30
    assert measurement["intent_accuracy"] == 1.0
    assert measurement["operation_exact_match"] == 1.0
    assert measurement["constraint_exact_match"] == 1.0
    assert measurement["risk_exact_match"] == 1.0
    assert measurement["errors"] == []


def test_v6_structural_build_adopted_worksheet_exists() -> None:
    text = WORKSHEET_PATH.read_text(encoding="utf-8")

    assert "V6 Structural Build 30 Adopted Worksheet v1" in text
    assert "adopted_count: 30" in text
    assert "current_route_error_count: 0" in text
    assert "v6-structural-build-adopted-001" in text
    assert "sbr-label-medical-dataset-column" in text
    assert "current_route_measurement_is_gate: false" in text


def test_v6_structural_build_adoption_script_regenerates_artifacts() -> None:
    completed = subprocess.run(
        [sys.executable, "-B", str(SCRIPT_PATH)],
        cwd=ROOT,
        check=True,
        text=True,
        capture_output=True,
    )

    assert "completed_without_route_gaps" in completed.stdout
    report = _load(REPLAY_REPORT_PATH)
    assert report["measurement"]["case_count"] == 30
    assert report["measurement"]["error_count"] == 0
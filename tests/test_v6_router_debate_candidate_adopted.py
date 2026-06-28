import json
from pathlib import Path

from semantic_routing import evaluate_plm_extractor, parse_plm_benchmark, route


ROOT = Path(__file__).parents[1]
ADOPTED_BENCHMARK_PATH = ROOT / "tests" / "fixtures" / "v6_router_debate_adopted_benchmark_v1.json"
ADOPTION_DECISION_PATH = ROOT / "build" / "v6_router_debate_candidate_adoption_decision_v1.json"
PROVISIONAL_REPORT_PATH = ROOT / "build" / "v6_router_debate_adopted_provisional_test_report_v1.json"


def _load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_v6_router_debate_adopted_benchmark_is_human_reviewed() -> None:
    payload = _load(ADOPTED_BENCHMARK_PATH)
    benchmark = parse_plm_benchmark(payload)

    assert payload["schema_version"] == "pattern-language-benchmark.v1"
    assert payload["review_status"] == "human_reviewed"
    assert len(benchmark.cases) == 12
    assert {case.split for case in benchmark.cases} == {"validation"}
    assert {case.expected.primary_intent for case in benchmark.cases} == {
        "build",
        "clarify",
        "explore",
        "verify",
    }


def test_v6_router_debate_adoption_decision_records_policy() -> None:
    decision = _load(ADOPTION_DECISION_PATH)

    assert decision["schema_version"] == "v6-router-debate-candidate-adoption-decision.v1"
    assert decision["status"] == "adopted_for_nonsealed_provisional_test"
    assert decision["review_status"] == "human_reviewed"
    assert decision["reviewed_by"] == "user_confirmation_in_codex_thread"
    assert decision["adopted_count"] == 12
    assert decision["policy"]["sealed_fixtures_used_as_sources"] is False
    assert decision["policy"]["raw_debate_logs_direct_training_allowed"] is False
    assert decision["policy"]["same_cycle_promotion_allowed"] is False
    assert decision["policy"]["current_route_measurement_is_gate"] is False


def test_v6_router_debate_provisional_report_is_not_gate() -> None:
    report = _load(PROVISIONAL_REPORT_PATH)

    assert report["schema_version"] == "v6-router-debate-adopted-provisional-test-report.v1"
    assert report["status"] == "completed_without_route_gaps"
    assert report["current_route_measurement_is_gate"] is False
    assert report["sealed_fixture_used"] is False
    assert report["measurement"]["case_count"] == 12
    assert report["measurement"]["valid_packet_rate"] == 1.0
    assert report["measurement"]["error_count"] == 0


def test_v6_router_debate_adopted_lane_matches_current_route() -> None:
    benchmark = parse_plm_benchmark(_load(ADOPTED_BENCHMARK_PATH))
    measurement = evaluate_plm_extractor(
        benchmark.cases,
        lambda text: route(text).packet,
    )

    assert measurement["intent_accuracy"] == 1.0
    assert measurement["critical_signal_recall"] == 1.0
    assert measurement["constraint_exact_match"] == 1.0
    assert measurement["operation_exact_match"] == 1.0
    assert measurement["risk_exact_match"] == 1.0
    assert measurement["errors"] == []
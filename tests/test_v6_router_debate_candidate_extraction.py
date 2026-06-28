import json
from pathlib import Path

from semantic_routing import parse_plm_benchmark


ROOT = Path(__file__).parents[1]
FIXTURE_PATH = ROOT / "tests" / "fixtures" / "v6_router_debate_candidate_fixture_v1.json"
REPORT_PATH = ROOT / "build" / "v6_router_debate_candidate_probe_report_v1.json"
SELECTION_PATH = ROOT / "build" / "v6_router_debate_candidate_selection_v1.json"
WORKSHEET_PATH = ROOT / "build" / "v6_router_debate_candidate_review_worksheet_v1.md"


def _load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _benchmark_payload(fixture):
    return {
        "schema_version": "pattern-language-benchmark.v1",
        "frozen_at": fixture["created_at"],
        "authoring_method": "test wrapper for v6 router debate candidate fixture",
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


def test_v6_router_debate_selection_uses_clean_nonsealed_debate_log() -> None:
    selection = _load(SELECTION_PATH)
    fixture = _load(FIXTURE_PATH)

    assert selection["schema_version"] == "v6-router-debate-candidate-selection.v1"
    assert selection["summary"] == {
        "source_topics": 20,
        "selected_topics": 12,
        "held_topics": 8,
        "issue_topics": 0,
    }
    assert fixture["schema_version"] == "v6-router-debate-candidate-fixture.v1"
    assert fixture["status"] == "draft_candidate_ready_for_human_review"
    assert fixture["source"]["topic_count"] == 20
    assert fixture["source"]["turn_count"] == 120
    assert fixture["source"]["closed_topic_count"] == 20
    assert fixture["source"]["raw_debate_log_direct_training_allowed"] is False
    assert fixture["source"]["topic_synthesis_allowed"] is True
    assert fixture["policy"] == {
        "sealed_fixtures_used_as_sources": False,
        "sealed_text_used": False,
        "sealed_labels_used": False,
        "raw_debate_logs_direct_training_allowed": False,
        "topic_synthesis_used": True,
        "llm_turn_text_direct_training_allowed": False,
        "human_review_required_before_training": True,
        "human_review_required_before_gate": True,
        "same_cycle_promotion_allowed": False,
    }


def test_v6_router_debate_fixture_parses_as_plm_benchmark() -> None:
    fixture = _load(FIXTURE_PATH)
    benchmark = parse_plm_benchmark(_benchmark_payload(fixture))

    assert len(benchmark.cases) == 12
    assert benchmark.review_status == "draft"
    assert {case.split for case in benchmark.cases} == {"validation"}
    assert len({case.input_text for case in benchmark.cases}) == 12
    assert len({case["source_topic_id"] for case in fixture["cases"]}) == 12

    for case in fixture["cases"]:
        assert case["source_kind"] == "router_debate_topic_synthesis"
        assert case["source_ref"] == "build/router_debate_live_31stock_r3.json"
        assert case["review_status"] == "draft"
        assert case["language"] == "ja"
        assert case["candidate_value_score"] >= 6
        assert case["debate_trace"]["turn_count"] == 6
        assert case["debate_trace"]["reasoning_content_chars"] == 0


def test_v6_router_debate_candidates_cover_guard_and_retrieval_axes() -> None:
    fixture = _load(FIXTURE_PATH)
    summary = fixture["summary"]

    assert summary["case_count"] == 12
    assert summary["by_intent"] == {
        "build": 2,
        "clarify": 1,
        "explore": 4,
        "verify": 5,
    }
    assert summary["by_operation"]["verify"] >= 10
    assert summary["by_constraint"]["must:avoid_overclaim"] == 12
    assert summary["by_constraint"]["must:cite_sources"] >= 2
    assert summary["by_constraint"]["must_not:no_web_search"] == 1
    assert summary["critical_signal_support"]["multiple_intents"] == 12
    assert summary["critical_signal_support"]["contains_unverified_claims"] >= 8
    assert summary["critical_signal_support"]["requires_current_information"] >= 3
    assert summary["by_risk"] == {"high": 4, "medium": 8}
    assert set(summary["by_retrieval_domain"]) >= {
        "ai_relationship_boundary",
        "legal_guard",
        "medical_guard",
        "political_future",
    }


def test_v6_router_debate_report_marks_probe_not_gate() -> None:
    report = _load(REPORT_PATH)

    assert report["schema_version"] == "v6-router-debate-candidate-probe-report.v1"
    assert report["status"] == "promoted_to_candidate_fixture"
    assert report["candidate_readiness"] is True
    assert report["current_route_measurement_is_gate"] is False
    assert report["current_route_measurement"]["case_count"] == 12
    assert report["current_route_measurement"]["valid_packet_rate"] == 1.0
    assert report["current_route_measurement"]["error_count"] == 12
    assert report["next_step"] == {
        "name": "human_review_v6_router_debate_candidates",
        "input": "build/v6_router_debate_candidate_review_worksheet_v1.md",
        "output": "tests/fixtures/v6_router_debate_candidate_fixture_v1.json",
    }


def test_v6_router_debate_review_worksheet_exists() -> None:
    text = WORKSHEET_PATH.read_text(encoding="utf-8")

    assert "V6 Router Debate Candidate Review Worksheet v1" in text
    assert "selected_candidates: 12" in text
    assert "held_topics: 8" in text
    assert "v6-router-debate-001" in text
    assert "v6-router-debate-012" in text

import json
import subprocess
import pytest
import sys
from pathlib import Path

from semantic_routing import parse_plm_benchmark


ROOT = Path(__file__).parents[1]
SCRIPT_PATH = ROOT / "build" / "extract_v7_router_debate_candidates.py"
FIXTURE_PATH = ROOT / "tests" / "fixtures" / "v7_router_debate_candidate_fixture_v1.json"
SELECTION_PATH = ROOT / "build" / "v7_router_debate_candidate_selection_v1.json"
REPORT_PATH = ROOT / "build" / "v7_router_debate_candidate_probe_report_v1.json"
WORKSHEET_PATH = ROOT / "build" / "v7_router_debate_candidate_review_worksheet_v1.md"


EXPECTED_POLICY = {
    "sealed_fixtures_used_as_sources": False,
    "sealed_text_used": False,
    "sealed_labels_used": False,
    "raw_debate_logs_direct_training_allowed": False,
    "llm_turn_text_direct_training_allowed": False,
    "topic_synthesis_used": True,
    "human_review_required_before_training": True,
    "human_review_required_before_gate": True,
    "same_cycle_promotion_allowed": False,
    "candidate_fixture_is_training_data": False,
    "candidate_replay_is_gate": False,
}


def _load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _benchmark_payload(fixture):
    return {
        "schema_version": "pattern-language-benchmark.v1",
        "frozen_at": fixture["created_at"],
        "authoring_method": "test wrapper for v7 router debate candidate fixture",
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


@pytest.fixture(scope="module", autouse=True)
def _regenerate_artifact():
    """Regenerate the build/ artifact before the read-asserts so these tests do
    not depend on stale on-disk state left by a prior test or manual run (S4)."""
    subprocess.run(
        [sys.executable, "-B", str(SCRIPT_PATH)],
        cwd=ROOT,
        check=True,
        text=True,
        capture_output=True,
    )


def test_v7_router_debate_candidate_selection_and_policy() -> None:
    selection = _load(SELECTION_PATH)

    assert selection["schema_version"] == "v7-router-debate-candidate-selection.v1"
    assert selection["status"] == "candidate_queue_prepared_from_nonsealed_debate_log"
    assert selection["source_log"] == "build/v7_router_repair_debate_run.json"
    assert selection["policy"] == EXPECTED_POLICY
    assert selection["summary"] == {
        "source_topics": 5,
        "selected_topics": 5,
        "selected_candidates": 18,
        "caution_topics": 1,
        "issue_topics": 0,
        "current_route_error_count": 0,
        "provisional_pass_count": 18,
        "provisional_repair_gap_count": 0,
    }
    assert selection["caution_topic_ids"] == ["v7-constraint-stacking"]
    assert selection["selected_topic_ids"] == [
        "v7-ambiguous-clarify-vs-build",
        "v7-current-search-split-local-vs-web",
        "v7-unverified-claim-strength",
        "v7-constraint-stacking",
        "v7-terminal-action-boundary",
    ]


def test_v7_router_debate_candidate_fixture_is_parseable_review_material() -> None:
    fixture = _load(FIXTURE_PATH)
    benchmark = parse_plm_benchmark(_benchmark_payload(fixture))

    assert fixture["schema_version"] == "v7-router-debate-candidate-fixture.v1"
    assert fixture["fixture_id"] == "v7-router-debate-candidate-fixture-v1"
    assert fixture["status"] == "draft_candidate_ready_for_human_review"
    assert fixture["review_status"] == "draft"
    assert fixture["source"] == {
        "log": "build/v7_router_repair_debate_run.json",
        "topic_count": 5,
        "turn_count": 20,
        "closed_topic_count": 5,
        "moderator_comment_count": 10,
        "raw_debate_log_direct_training_allowed": False,
        "topic_synthesis_allowed": True,
    }
    assert fixture["policy"] == EXPECTED_POLICY
    assert len(fixture["cases"]) == 18
    assert len(benchmark.cases) == 18
    assert {case.split for case in benchmark.cases} == {"validation"}
    assert len({case.input_text for case in benchmark.cases}) == 18
    assert {case.language for case in benchmark.cases} == {"en", "mixed"}

    assert fixture["cases"][0]["input"] == (
        "Please make this sound better. I have not provided the target text yet."
    )
    assert "latest_config" in fixture["cases"][5]["input"]
    for case in fixture["cases"]:
        assert case["id"].startswith("v7-router-debate-candidate-")
        assert case["source_kind"] == "router_debate_topic_synthesis"
        assert case["source_ref"] == "build/v7_router_repair_debate_run.json"
        assert case["review_status"] == "draft"
        assert case["candidate_value_score"] >= 8
        assert case["debate_trace"]["turn_count"] == 4
        assert case["debate_trace"]["reasoning_content_chars"] == 0
        assert case["notes"].startswith("Draft synthesized candidate")
        assert case["provisional_test_status"] in {
            "passes_current_route",
            "repair_gap",
        }


def test_v7_router_debate_candidate_summary_marks_repaired_replay() -> None:
    fixture = _load(FIXTURE_PATH)
    summary = fixture["summary"]

    assert summary["case_count"] == 18
    assert summary["by_source_topic"] == {
        "v7-ambiguous-clarify-vs-build": 3,
        "v7-constraint-stacking": 3,
        "v7-current-search-split-local-vs-web": 4,
        "v7-terminal-action-boundary": 4,
        "v7-unverified-claim-strength": 4,
    }
    assert summary["by_axis"] == {
        "clarify_boundary_repair": 3,
        "constraint_preservation": 3,
        "critical_signal_recovery": 5,
        "operation_sequence_repair": 4,
        "risk_ladder_calibration": 3,
    }
    assert summary["by_intent"] == {
        "build": 8,
        "clarify": 2,
        "explain": 2,
        "summarize": 2,
        "verify": 4,
    }
    assert summary["by_language"] == {"en": 15, "mixed": 3}
    assert summary["provisional_pass_count"] == 18
    assert summary["provisional_repair_gap_count"] == 0
    assert summary["provisional_pass_ids"] == [
        "v7-router-debate-candidate-001",
        "v7-router-debate-candidate-002",
        "v7-router-debate-candidate-003",
        "v7-router-debate-candidate-004",
        "v7-router-debate-candidate-005",
        "v7-router-debate-candidate-006",
        "v7-router-debate-candidate-007",
        "v7-router-debate-candidate-008",
        "v7-router-debate-candidate-009",
        "v7-router-debate-candidate-010",
        "v7-router-debate-candidate-011",
        "v7-router-debate-candidate-012",
        "v7-router-debate-candidate-013",
        "v7-router-debate-candidate-014",
        "v7-router-debate-candidate-015",
        "v7-router-debate-candidate-016",
        "v7-router-debate-candidate-017",
        "v7-router-debate-candidate-018",
    ]
    assert summary["critical_signal_support"] == {
        "contains_unverified_claims": 2,
        "missing_required_information": 2,
        "multiple_intents": 4,
        "requires_current_information": 1,
    }


def test_v7_router_debate_candidate_probe_is_diagnostic_not_gate() -> None:
    report = _load(REPORT_PATH)

    assert report["schema_version"] == "v7-router-debate-candidate-probe-report.v1"
    assert report["status"] == "draft_candidate_probe_completed_not_a_gate"
    assert report["candidate_readiness"] is True
    assert report["adoption_readiness"] is True
    assert report["requires_router_repair_or_human_label_review"] is False
    assert report["current_route_measurement_is_gate"] is False
    assert report["current_route_measurement"] == {
        "case_count": 18,
        "intent_accuracy": 1.0,
        "critical_signal_recall": 1.0,
        "operation_exact_match": 1.0,
        "constraint_exact_match": 1.0,
        "risk_exact_match": 1.0,
        "valid_packet_rate": 1.0,
        "error_count": 0,
        "error_field_counts": {},
    }
    assert len(report["errors"]) == 0
    assert report["next_step"] == {
        "name": "human_review_v7_router_debate_candidates",
        "input": "build/v7_router_debate_candidate_review_worksheet_v1.md",
        "output": "tests/fixtures/v7_router_debate_candidate_fixture_v1.json",
    }


def test_v7_router_debate_candidate_worksheet_and_script_regenerate() -> None:
    text = WORKSHEET_PATH.read_text(encoding="utf-8")

    assert "V7 Router Debate Candidate Review Worksheet v1" in text
    assert "selected_candidates: 18" in text
    assert "provisional_pass_count: 18" in text
    assert "provisional_repair_gap_count: 0" in text
    assert "v7-router-debate-candidate-001" in text
    assert "v7-router-debate-candidate-018" in text

    completed = subprocess.run(
        [sys.executable, "-B", str(SCRIPT_PATH)],
        cwd=ROOT,
        check=True,
        text=True,
        capture_output=True,
    )

    assert "draft_candidate_probe_completed_not_a_gate" in completed.stdout
    report = _load(REPORT_PATH)
    assert report["current_route_measurement"]["error_count"] == 0
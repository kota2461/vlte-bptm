import json
import subprocess
import pytest
import sys
from pathlib import Path

from semantic_routing import parse_plm_benchmark


ROOT = Path(__file__).parents[1]
SCRIPT_PATH = ROOT / "build" / "synthesize_v6_boundary_false_positive_candidates.py"
BENCHMARK_PATH = ROOT / "tests" / "fixtures" / "v6_boundary_false_positive_candidate_benchmark_v1.json"
REPORT_PATH = ROOT / "build" / "v6_boundary_false_positive_candidate_report_v1.json"
WORKSHEET_PATH = ROOT / "build" / "v6_boundary_false_positive_candidate_review_worksheet_v1.md"


def _load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


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


def test_v6_boundary_false_positive_benchmark_is_plm_draft() -> None:
    payload = _load(BENCHMARK_PATH)
    benchmark = parse_plm_benchmark(payload)

    assert payload["schema_version"] == "pattern-language-benchmark.v1"
    assert payload["review_status"] == "draft"
    assert len(benchmark.cases) == 15
    assert {case.split for case in benchmark.cases} == {"validation"}
    assert {case.expected.risk_level for case in benchmark.cases} == {"low"}
    assert len({case.input_text for case in benchmark.cases}) == 15



def test_v6_boundary_false_positive_report_keeps_review_contract() -> None:
    report = _load(REPORT_PATH)

    assert report["schema_version"] == "v6-boundary-false-positive-candidate-report.v1"
    assert report["status"] == "candidate_lane_ready_for_human_review"
    assert report["current_route_measurement_is_gate"] is False
    assert report["policy"] == {
        "sealed_fixtures_used_as_sources": False,
        "sealed_text_used": False,
        "sealed_labels_used": False,
        "raw_debate_logs_direct_training_allowed": False,
        "llm_turn_text_direct_training_allowed": False,
        "topic_metadata_selection_allowed": True,
        "manual_prompt_synthesis_used": True,
        "human_review_required_before_training": True,
        "human_review_required_before_gate": True,
        "same_cycle_gate_use_allowed": False,
        "current_route_measurement_is_gate": False,
    }
    artifact = report["candidate_artifact"]
    assert artifact["schema_version"] == "v6-boundary-false-positive-candidate-artifact.v1"
    assert artifact["status"] == "draft_candidate_ready_for_human_review"
    assert artifact["review_status"] == "draft"
    assert all(case["training_allowed"] is False for case in artifact["cases"])
    assert all(case["gate_use_allowed"] is False for case in artifact["cases"])


def test_v6_boundary_false_positive_candidates_cover_requested_boundaries() -> None:
    report = _load(REPORT_PATH)
    cases = report["candidate_artifact"]["cases"]
    by_topic = {case["source_topic_id"]: case for case in cases}

    expected_topics = {
        "fp-ai-light-chat-healing",
        "fp-ai-task-support-not-dependency",
        "paraphrase-apache-general-question",
        "paraphrase-medical-ui-design",
        "contrast-ai-word-only-low-risk",
        "contrast-medical-word-only-low-risk",
        "contrast-license-word-only-low-risk",
    }
    assert expected_topics <= set(by_topic)
    assert by_topic["fp-ai-light-chat-healing"]["expected"]["risk"] == {"level": "low", "flags": []}
    assert by_topic["paraphrase-apache-general-question"]["expected"]["primary_intent"] == "explain"
    assert by_topic["paraphrase-apache-general-question"]["expected"]["information_state"]["requires_current_information"] is False
    assert by_topic["paraphrase-medical-ui-design"]["expected"]["primary_intent"] == "build"
    assert by_topic["paraphrase-medical-ui-design"]["expected"]["risk"] == {"level": "low", "flags": []}


def test_v6_boundary_false_positive_report_records_current_route_match() -> None:
    report = _load(REPORT_PATH)
    summary = report["summary"]
    measurement = report["current_route_measurement"]

    assert summary["case_count"] == 15
    assert summary["all_expected_risk_low"] is True
    assert summary["overfire_count"] == 0
    assert summary["overfire_details"] == []
    assert measurement["case_count"] == 15
    assert measurement["valid_packet_rate"] == 1.0
    assert measurement["error_count"] == 0
    assert measurement["intent_accuracy"] == 1.0
    assert measurement["operation_exact_match"] == 1.0
    assert measurement["risk_exact_match"] == 1.0


def test_v6_boundary_false_positive_worksheet_exists() -> None:
    text = WORKSHEET_PATH.read_text(encoding="utf-8")

    assert "V6 Boundary False-Positive Candidate Review Worksheet v1" in text
    assert "candidate_count: 15" in text
    assert "overfire_count: 0" in text
    assert "v6-boundary-fp-001" in text
    assert "paraphrase-apache-general-question" in text
    assert "paraphrase-medical-ui-design" in text


def test_v6_boundary_false_positive_script_regenerates_artifacts() -> None:
    completed = subprocess.run(
        [sys.executable, "-B", str(SCRIPT_PATH)],
        cwd=ROOT,
        check=True,
        text=True,
        capture_output=True,
    )

    assert "candidate_lane_ready_for_human_review" in completed.stdout
    report = _load(REPORT_PATH)
    assert report["summary"]["case_count"] == 15
    assert report["summary"]["overfire_count"] == 0
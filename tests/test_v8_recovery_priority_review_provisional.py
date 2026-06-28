import json
import subprocess
import pytest
import sys
from collections import Counter
from pathlib import Path

from semantic_routing import parse_plm_benchmark


ROOT = Path(__file__).parents[1]
SCRIPT_PATH = ROOT / "build" / "replay_v8_recovery_priority_review_candidates.py"
BENCHMARK_PATH = ROOT / "tests" / "fixtures" / "v8_recovery_priority_review_candidate_benchmark_v1.json"
REPORT_PATH = ROOT / "build" / "v8_recovery_priority_review_provisional_test_report_v1.json"
WORKSHEET_PATH = ROOT / "build" / "v8_recovery_priority_review_candidate_worksheet_v1.md"


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


def test_v8_recovery_priority_review_candidate_benchmark_contract() -> None:
    payload = _load(BENCHMARK_PATH)
    benchmark = parse_plm_benchmark(payload)

    assert payload["schema_version"] == "pattern-language-benchmark.v1"
    assert payload["review_status"] == "human_reviewed"
    assert "Raw Gemma/Qwen debate turns are not training data" in payload["policy"]
    assert len(benchmark.cases) == 30
    assert {case.split for case in benchmark.cases} == {"validation"}
    assert len({case.input_text for case in benchmark.cases}) == 30
    assert Counter(case.contrast_group for case in benchmark.cases) == {
        "constraints": 3,
        "current_search_split": 3,
        "false_positive": 3,
        "missing_info": 3,
        "mixed_language": 3,
        "multiple_intents": 3,
        "operation_terminal": 3,
        "paraphrase": 3,
        "risk_ladder": 3,
        "unverified_claim": 3,
    }


def test_v8_recovery_priority_review_report_is_provisional_not_gate() -> None:
    report = _load(REPORT_PATH)

    assert report["schema_version"] == "v8-recovery-priority-review-provisional-test-report.v1"
    assert report["current_route_measurement_is_gate"] is False
    assert report["sealed_fixture_used"] is False
    assert report["policy"] == {
        "sealed_fixtures_used_as_sources": False,
        "sealed_text_used": False,
        "sealed_labels_used": False,
        "raw_debate_logs_direct_training_allowed": False,
        "llm_turn_text_direct_training_allowed": False,
        "topic_metadata_synthesis_used": True,
        "human_review_confirmation_recorded": True,
        "same_cycle_promotion_allowed": False,
        "current_route_measurement_is_gate": False,
        "candidate_benchmark_is_directly_trainable": False,
    }
    assert report["summary"]["candidate_count"] == 30
    assert report["measurement"]["case_count"] == 30
    assert report["measurement"]["valid_packet_rate"] == 1.0
    assert set(report["category_summary"]) == set(report["summary"]["by_category"])
    assert len(report["case_results"]) == 30


def test_v8_recovery_priority_review_worksheet_exists() -> None:
    text = WORKSHEET_PATH.read_text(encoding="utf-8")

    assert "V8 Recovery Priority Review Candidate Worksheet v1" in text
    assert "current_route_measurement_is_gate: false" in text
    assert "v8-recovery-priority-review-001" in text
    assert "v8-unverified_claim-05-legal-template-claim" in text


def test_v8_recovery_priority_review_replay_script_regenerates_artifacts() -> None:
    completed = subprocess.run(
        [sys.executable, "-B", str(SCRIPT_PATH)],
        cwd=ROOT,
        check=True,
        text=True,
        capture_output=True,
    )

    assert "v8-recovery-priority-review-provisional-test-report.v1" not in completed.stderr
    assert "completed_" in completed.stdout
    report = _load(REPORT_PATH)
    assert report["measurement"]["case_count"] == 30
    assert report["summary"]["by_category"]["constraints"] == 3

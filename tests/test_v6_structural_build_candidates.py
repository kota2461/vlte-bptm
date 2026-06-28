import json
import subprocess
import sys
from pathlib import Path

from semantic_routing import parse_plm_benchmark


ROOT = Path(__file__).parents[1]
SCRIPT_PATH = ROOT / "build" / "extract_v6_structural_build_30_candidates.py"
QUEUE_PATH = ROOT / "build" / "v6_structural_build_30_candidate_queue_v1.json"
REPORT_PATH = ROOT / "build" / "v6_structural_build_30_candidate_probe_report_v1.json"
WORKSHEET_PATH = ROOT / "build" / "v6_structural_build_30_candidate_review_worksheet_v1.md"
BENCHMARK_PATH = ROOT / "tests" / "fixtures" / "v6_structural_build_30_candidate_benchmark_v1.json"


def _load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_v6_structural_build_candidate_benchmark_is_draft_plm() -> None:
    payload = _load(BENCHMARK_PATH)
    benchmark = parse_plm_benchmark(payload)

    assert payload["schema_version"] == "pattern-language-benchmark.v1"
    assert payload["review_status"] == "draft"
    assert len(benchmark.cases) == 30
    assert {case.split for case in benchmark.cases} == {"validation"}
    assert {case.expected.primary_intent for case in benchmark.cases} == {"build"}
    assert {case.expected.risk_level for case in benchmark.cases} == {"low"}
    assert len({case.input_text for case in benchmark.cases}) == 30


def test_v6_structural_build_candidate_queue_contract() -> None:
    payload = _load(QUEUE_PATH)

    assert payload["schema_version"] == "v6-structural-build-30-candidate-queue.v1"
    assert payload["status"] == "candidate_queue_ready_for_human_review"
    assert payload["target_set"] == "structural_build_repair_30"
    assert payload["source_review"] == "build/router_debate_v6_structural_build_30_review_with_rerun_v1.json"
    assert payload["source_topics"] == "debate_lab/topics_v6_structural_build_30.json"
    assert payload["policy"] == {
        "sealed_fixtures_used_as_sources": False,
        "sealed_text_used": False,
        "sealed_labels_used": False,
        "raw_debate_logs_direct_training_allowed": False,
        "llm_turn_text_direct_training_allowed": False,
        "topic_metadata_synthesis_used": True,
        "manual_prompt_synthesis_used": True,
        "human_review_required_before_training": True,
        "human_review_required_before_gate": True,
        "same_cycle_gate_use_allowed": False,
        "candidate_queue_is_training_data": False,
        "current_route_measurement_is_gate": False,
    }
    assert payload["summary"]["candidate_count"] == 30
    assert payload["summary"]["by_status"] == {"ready_for_human_review": 30}
    assert payload["summary"]["by_expected_intent"] == {"build": 30}
    assert payload["summary"]["by_expected_risk"] == {"low": 30}
    assert all(candidate["training_allowed"] is False for candidate in payload["candidates"])
    assert all(candidate["gate_use_allowed"] is False for candidate in payload["candidates"])
    assert all(candidate["human_review_required"] is True for candidate in payload["candidates"])
    assert all(candidate["raw_turn_text_direct_training_allowed"] is False for candidate in payload["candidates"])


def test_v6_structural_build_candidates_cover_requested_boundaries() -> None:
    payload = _load(QUEUE_PATH)
    by_topic = {candidate["source_topic_id"]: candidate for candidate in payload["candidates"]}

    expected_topics = {
        "sbr-label-ai-persona-heading",
        "sbr-label-legal-risk-column",
        "sbr-label-medical-dataset-column",
        "sbr-label-license-tag",
        "sbr-label-ai-regulation-tag",
        "sbr-filename-latest-notes",
        "sbr-current-folder-command",
        "sbr-ui-medical-ai-layout",
        "sbr-doc-ai-label-vs-dependency",
    }
    assert expected_topics <= set(by_topic)
    assert by_topic["sbr-label-ai-persona-heading"]["suggested_expected"]["primary_intent"] == "build"
    assert by_topic["sbr-label-legal-risk-column"]["suggested_expected"]["risk"] == {"level": "low", "flags": []}
    assert by_topic["sbr-current-folder-command"]["suggested_expected"]["information_state"]["requires_current_information"] is False
    assert by_topic["sbr-ui-medical-ai-layout"]["suggested_expected"]["risk"] == {"level": "low", "flags": []}


def test_v6_structural_build_probe_report_is_not_gate() -> None:
    report = _load(REPORT_PATH)

    assert report["schema_version"] == "v6-structural-build-30-candidate-probe-report.v1"
    assert report["status"] == "candidate_extraction_complete_review_required"
    assert report["current_route_measurement_is_gate"] is False
    assert report["summary"]["candidate_count"] == 30
    assert report["current_route_measurement"]["case_count"] == 30
    assert report["current_route_measurement"]["valid_packet_rate"] == 1.0


def test_v6_structural_build_candidate_worksheet_exists() -> None:
    text = WORKSHEET_PATH.read_text(encoding="utf-8")

    assert "V6 Structural Build 30 Candidate Review Worksheet v1" in text
    assert "candidate_count: 30" in text
    assert "training_allowed_before_review: false" in text
    assert "v6-structural-build-30-001" in text
    assert "sbr-label-medical-dataset-column" in text


def test_v6_structural_build_candidate_script_regenerates_artifacts() -> None:
    completed = subprocess.run(
        [sys.executable, "-B", str(SCRIPT_PATH)],
        cwd=ROOT,
        check=True,
        text=True,
        capture_output=True,
    )

    assert "candidate_extraction_complete_review_required" in completed.stdout
    payload = _load(QUEUE_PATH)
    assert payload["summary"]["candidate_count"] == 30
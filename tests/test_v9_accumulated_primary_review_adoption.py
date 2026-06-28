import json
import subprocess
import sys
from collections import Counter
from pathlib import Path

from semantic_routing import evaluate_plm_extractor, parse_plm_benchmark, route


ROOT = Path(__file__).parents[1]
SCRIPT_PATH = ROOT / "build" / "adopt_v9_accumulated_primary_review_candidates.py"
SELECTION_PATH = ROOT / "build" / "v9_accumulated_log_candidate_selection_v1.json"
ADOPTION_PATH = ROOT / "build" / "v9_accumulated_primary_review_adoption_decision_v1.json"
BENCHMARK_PATH = ROOT / "tests" / "fixtures" / "v9_accumulated_primary_review_candidate_benchmark_v1.json"
REPORT_PATH = ROOT / "build" / "v9_accumulated_primary_review_replay_report_v1.json"
WORKSHEET_PATH = ROOT / "build" / "v9_accumulated_primary_review_worksheet_v1.md"


def _load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_v9_primary_review_adoption_uses_only_34_selected_rows() -> None:
    selection = _load(SELECTION_PATH)
    decision = _load(ADOPTION_PATH)

    primary_ids = {row["id"] for row in selection["primary_review"]}
    rerun_ids = {row["id"] for row in selection["rerun_before_use"]}
    reserve_ids = {row["id"] for row in selection["reserve_review"]}
    selected_ids = set(decision["selected_candidate_ids"])

    assert decision["schema_version"] == "v9-accumulated-primary-review-adoption-decision.v1"
    assert decision["status"] == "adopted_for_nonsealed_replay"
    assert decision["review_status"] == "human_reviewed"
    assert decision["adopted_count"] == 34
    assert selected_ids == primary_ids
    assert selected_ids.isdisjoint(rerun_ids)
    assert selected_ids.isdisjoint(reserve_ids)
    assert decision["excluded_lanes"] == {
        "rerun_before_use": 8,
        "reserve_review": 28,
        "already_used_excluded": 30,
    }
    assert decision["policy"]["only_primary_review_34_used"] is True
    assert decision["policy"]["raw_debate_logs_direct_training_allowed"] is False
    assert decision["policy"]["adopted_benchmark_is_directly_trainable"] is False


def test_v9_primary_review_benchmark_contract() -> None:
    payload = _load(BENCHMARK_PATH)
    benchmark = parse_plm_benchmark(payload)

    assert payload["schema_version"] == "pattern-language-benchmark.v1"
    assert payload["review_status"] == "human_reviewed"
    assert "Only the 34 primary_review rows are used" in payload["policy"]
    assert "Raw Gemma/Qwen debate turns are not training data" in payload["policy"]
    assert len(benchmark.cases) == 34
    assert {case.split for case in benchmark.cases} == {"validation"}
    assert len({case.input_text for case in benchmark.cases}) == 34
    assert Counter(case.contrast_group for case in benchmark.cases) == {
        "constraints": 5,
        "current_search_split": 5,
        "false_positive": 2,
        "missing_info": 3,
        "mixed_language": 1,
        "multiple_intents": 5,
        "operation_terminal": 5,
        "paraphrase": 1,
        "risk_ladder": 5,
        "unverified_claim": 2,
    }


def test_v9_primary_review_replay_report_passes_after_candidate_repair_not_gate() -> None:
    report = _load(REPORT_PATH)

    assert report["schema_version"] == "v9-accumulated-primary-review-replay-report.v1"
    assert report["status"] == "completed_without_route_gaps"
    assert report["current_route_measurement_is_gate"] is False
    assert report["sealed_fixture_used"] is False
    assert report["summary"]["adopted_count"] == 34
    assert report["measurement"] == {
        "case_count": 34,
        "valid_packet_rate": 1.0,
        "intent_accuracy": 1.0,
        "intent_macro_f1": 1.0,
        "critical_signal_recall": 1.0,
        "operation_exact_match": 1.0,
        "constraint_exact_match": 1.0,
        "risk_exact_match": 1.0,
        "evidence_offset_validity": 1.0,
        "error_count": 0,
        "error_field_counts": {},
    }
    assert len(report["case_results"]) == 34
    assert report["next_step"] == "v9_nonsealed_replay_gate_candidate"


def test_v9_primary_review_replay_matches_current_route() -> None:
    report = _load(REPORT_PATH)
    payload = _load(BENCHMARK_PATH)
    benchmark = parse_plm_benchmark(payload)
    measurement = evaluate_plm_extractor(benchmark.cases, lambda text: route(text).packet)

    assert measurement["case_count"] == report["measurement"]["case_count"]
    assert measurement["intent_accuracy"] == report["measurement"]["intent_accuracy"]
    assert measurement["critical_signal_recall"] == report["measurement"]["critical_signal_recall"]
    assert measurement["operation_exact_match"] == report["measurement"]["operation_exact_match"]
    assert measurement["constraint_exact_match"] == report["measurement"]["constraint_exact_match"]
    assert measurement["risk_exact_match"] == report["measurement"]["risk_exact_match"]
    assert len(measurement["errors"]) == report["measurement"]["error_count"]


def test_v9_primary_review_worksheet_and_script_regenerate() -> None:
    text = WORKSHEET_PATH.read_text(encoding="utf-8")

    assert "V9 Accumulated Primary Review Worksheet v1" in text
    assert "only_primary_review_34_used: true" in text
    assert "rerun_before_use: excluded from this adoption" in text
    assert "v9-accumulated-primary-review-034" in text

    completed = subprocess.run(
        [sys.executable, "-B", str(SCRIPT_PATH)],
        cwd=ROOT,
        check=True,
        text=True,
        capture_output=True,
    )

    assert '"adopted_count": 34' in completed.stdout
    report = _load(REPORT_PATH)
    assert report["measurement"]["error_count"] == 0

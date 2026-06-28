import json
import subprocess
import sys
from collections import Counter
from pathlib import Path

from semantic_routing import evaluate_plm_extractor, parse_plm_benchmark, route


ROOT = Path(__file__).parents[1]
SCRIPT_PATH = ROOT / "build" / "adopt_v10_thought_color_bridge_candidates.py"
SELECTION_PATH = ROOT / "build" / "v10_thought_color_bridge_candidate_selection_v1.json"
ADOPTION_PATH = ROOT / "build" / "v10_thought_color_bridge_isolated_adoption_decision_v1.json"
BENCHMARK_PATH = ROOT / "tests" / "fixtures" / "v10_thought_color_bridge_isolated_benchmark_v1.json"
REPORT_PATH = ROOT / "build" / "v10_thought_color_bridge_isolated_replay_report_v1.json"
WORKSHEET_PATH = ROOT / "build" / "v10_thought_color_bridge_isolated_worksheet_v1.md"


def _load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _normalize(text: str) -> str:
    return " ".join(text.split()).lower()


def test_v10_bridge_isolated_adoption_contract() -> None:
    selection = _load(SELECTION_PATH)
    decision = _load(ADOPTION_PATH)

    selected_ids = set(decision["selected_candidate_ids"])
    primary_ids = {row["id"] for row in selection["primary_review"]}
    reserve_ids = {row["id"] for row in selection["reserve_review"]}

    assert decision["schema_version"] == "v10-thought-color-bridge-isolated-adoption-decision.v1"
    assert decision["status"] == "adopted_for_isolated_provisional_replay"
    assert decision["review_status"] == "human_reviewed_for_isolated_rewrite"
    assert decision["adopted_count"] == 72
    assert selected_ids == primary_ids
    assert selected_ids.isdisjoint(reserve_ids)
    assert decision["category_counts"] == {
        "constraint_bridge": 18,
        "information_state_bridge": 14,
        "intent_boundary_bridge": 10,
        "operation_bridge": 14,
        "risk_bridge": 16,
    }
    assert decision["policy"]["source_mainline_training_allowed"] is False
    assert decision["policy"]["raw_thought_color_samples_direct_training_allowed"] is False
    assert decision["policy"]["isolated_rewrite_fixture_training_allowed"] is False
    assert decision["policy"]["isolated_replay_only"] is True
    assert decision["policy"]["same_cycle_promotion_allowed"] is False
    assert decision["policy"]["current_route_measurement_is_gate"] is False


def test_v10_bridge_isolated_benchmark_is_quarantined_rewrite() -> None:
    selection = _load(SELECTION_PATH)
    payload = _load(BENCHMARK_PATH)
    benchmark = parse_plm_benchmark(payload)

    source_inputs = {_normalize(row["input"]) for row in selection["primary_review"]}
    fixture_inputs = {_normalize(case["input"]) for case in payload["cases"]}

    assert payload["schema_version"] == "pattern-language-benchmark.v1"
    assert payload["review_status"] == "human_reviewed"
    assert "Quarantined V10 bridge replay lane" in payload["policy"]
    assert "not trainable" in payload["policy"]
    assert len(benchmark.cases) == 72
    assert {case.split for case in benchmark.cases} == {"validation"}
    assert len(fixture_inputs) == 72
    assert fixture_inputs.isdisjoint(source_inputs)
    assert {case.source_group for case in benchmark.cases} == {
        "v10-thought-color-bridge-isolated-rewrite-nonsealed"
    }
    assert Counter(case.contrast_group for case in benchmark.cases) == {
        "constraint_bridge": 18,
        "information_state_bridge": 14,
        "intent_boundary_bridge": 10,
        "operation_bridge": 14,
        "risk_bridge": 16,
    }


def test_v10_bridge_isolated_replay_report_is_diagnostic_not_gate() -> None:
    report = _load(REPORT_PATH)

    assert report["schema_version"] == "v10-thought-color-bridge-isolated-replay-report.v1"
    assert report["status"] == "completed_with_provisional_scores"
    assert report["sealed_fixture_used"] is False
    assert report["current_route_measurement_is_gate"] is False
    assert report["isolated_rewrite_fixture_training_allowed"] is False
    assert report["summary"]["adopted_count"] == 72
    assert report["summary"]["source_inputs_copied_verbatim"] is False
    assert report["measurement"]["case_count"] == 72
    assert report["measurement"]["intent_accuracy"] == 1.0
    assert report["measurement"]["critical_signal_recall"] == 1.0
    assert report["measurement"]["operation_exact_match"] == 1.0
    assert report["measurement"]["constraint_exact_match"] == 1.0
    assert report["measurement"]["risk_exact_match"] == 1.0
    assert report["measurement"]["error_count"] == 0
    assert report["measurement"]["error_count"] == len(
        [result for result in report["case_results"] if result["fields"]]
    )
    assert report["next_step"] == "review_route_gaps_before_any_v10_training_or_gate_use"


def test_v10_bridge_isolated_replay_matches_current_route() -> None:
    report = _load(REPORT_PATH)
    benchmark = parse_plm_benchmark(_load(BENCHMARK_PATH))
    measurement = evaluate_plm_extractor(benchmark.cases, lambda text: route(text).packet)

    for key in (
        "case_count",
        "valid_packet_rate",
        "intent_accuracy",
        "intent_macro_f1",
        "critical_signal_recall",
        "operation_exact_match",
        "constraint_exact_match",
        "risk_exact_match",
        "evidence_offset_validity",
    ):
        assert measurement[key] == report["measurement"][key]
    assert len(measurement["errors"]) == report["measurement"]["error_count"]


def test_v10_bridge_isolated_worksheet_and_script_regenerate() -> None:
    text = WORKSHEET_PATH.read_text(encoding="utf-8")

    assert "V10 Thought Color Bridge Isolated Worksheet v1" in text
    assert "isolated_replay_only: true" in text
    assert "current_route_measurement_is_gate: false" in text
    assert "v10-thought-color-bridge-isolated-072" in text

    completed = subprocess.run(
        [sys.executable, "-B", str(SCRIPT_PATH)],
        cwd=ROOT,
        check=True,
        text=True,
        capture_output=True,
    )

    assert '"adopted_count": 72' in completed.stdout
    report = _load(REPORT_PATH)
    assert report["measurement"]["case_count"] == 72


import json
import subprocess
import pytest
import sys
from collections import Counter
from pathlib import Path

from semantic_routing import evaluate_plm_extractor, parse_plm_benchmark, route


ROOT = Path(__file__).parents[1]
SCRIPT_PATH = ROOT / "build" / "create_v9_constraint_operation_extension.py"
BENCHMARK_PATH = ROOT / "tests" / "fixtures" / "v9_constraint_operation_extension_benchmark_v1.json"
REPORT_PATH = ROOT / "build" / "v9_constraint_operation_extension_replay_report_v1.json"
WORKSHEET_PATH = ROOT / "build" / "v9_constraint_operation_extension_worksheet_v1.md"


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


def test_v9_constraint_operation_extension_benchmark_contract() -> None:
    payload = _load(BENCHMARK_PATH)
    benchmark = parse_plm_benchmark(payload)

    assert payload["schema_version"] == "pattern-language-benchmark.v1"
    assert payload["review_status"] == "human_reviewed"
    assert "No sealed text or labels used" in payload["policy"]
    assert len(benchmark.cases) == 24
    assert {case.split for case in benchmark.cases} == {"validation"}
    assert len({case.input_text for case in benchmark.cases}) == 24
    assert Counter(case.contrast_group for case in benchmark.cases) == {
        "constraints": 12,
        "operation_terminal": 12,
    }


def test_v9_constraint_operation_extension_report_passes_not_gate() -> None:
    report = _load(REPORT_PATH)

    assert report["schema_version"] == "v9-constraint-operation-extension-replay-report.v1"
    assert report["status"] == "completed_without_route_gaps"
    assert report["current_route_measurement_is_gate"] is False
    assert report["sealed_fixture_used"] is False
    assert report["policy"]["sealed_fixtures_used_as_sources"] is False
    assert report["summary"]["focused_targets"] == ["constraint_exact_match", "operation_exact_match"]
    assert report["summary"]["by_category"] == {"constraints": 12, "operation_terminal": 12}
    assert report["summary"]["by_target_field"]["constraints"] >= 12
    assert report["summary"]["by_target_field"]["operations"] >= 12
    assert report["measurement"] == {
        "case_count": 24,
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
    assert len(report["case_results"]) == 24
    assert report["next_step"] == "v9_nonsealed_replay_gate_candidate"


def test_v9_constraint_operation_extension_matches_current_route() -> None:
    report = _load(REPORT_PATH)
    payload = _load(BENCHMARK_PATH)
    benchmark = parse_plm_benchmark(payload)
    measurement = evaluate_plm_extractor(benchmark.cases, lambda text: route(text).packet)

    assert measurement["case_count"] == report["measurement"]["case_count"]
    assert measurement["operation_exact_match"] == report["measurement"]["operation_exact_match"]
    assert measurement["constraint_exact_match"] == report["measurement"]["constraint_exact_match"]
    assert measurement["risk_exact_match"] == report["measurement"]["risk_exact_match"]
    assert len(measurement["errors"]) == report["measurement"]["error_count"]


def test_v9_constraint_operation_extension_worksheet_and_script_regenerate() -> None:
    text = WORKSHEET_PATH.read_text(encoding="utf-8")

    assert "V9 Constraint/Operation Extension Worksheet v1" in text
    assert "sealed_fixture_used: false" in text
    assert "current_route_measurement_is_gate: false" in text
    assert "v9-constraint-operation-extension-024" in text

    completed = subprocess.run(
        [sys.executable, "-B", str(SCRIPT_PATH)],
        cwd=ROOT,
        check=True,
        text=True,
        capture_output=True,
    )

    assert '"case_count": 24' in completed.stdout
    report = _load(REPORT_PATH)
    assert report["measurement"]["error_count"] == 0

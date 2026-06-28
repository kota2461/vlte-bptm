import json
from pathlib import Path

from semantic_routing import parse_plm_benchmark


ROOT = Path(__file__).parents[1]
FIXTURE_PATH = ROOT / "tests" / "fixtures" / "v6_contrast_negative_benchmark_v1.json"
REPORT_PATH = ROOT / "build" / "v6_contrast_negative_probe_report_v1.json"
WORKSHEET_PATH = ROOT / "build" / "v6_contrast_negative_review_worksheet_v1.md"


def _load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_v6_contrast_negative_fixture_is_plm_draft() -> None:
    payload = _load(FIXTURE_PATH)
    benchmark = parse_plm_benchmark(payload)

    assert payload["schema_version"] == "pattern-language-benchmark.v1"
    assert payload["review_status"] == "draft"
    assert len(benchmark.cases) == 30
    assert {case.split for case in benchmark.cases} == {"validation"}
    assert {case.expected.risk_level for case in benchmark.cases} == {"low"}
    assert len({case.input_text for case in benchmark.cases}) == 30


def test_v6_contrast_negative_fixture_has_targeted_groups() -> None:
    payload = _load(FIXTURE_PATH)
    groups = {case["contrast_group"] for case in payload["cases"]}

    assert "ai_light_use" in groups
    assert "license_general" in groups
    assert "medical_ui_design" in groups
    assert "neutrality_word_use" in groups
    assert "current_local_context" in groups
    assert "regulation_label_use" in groups


def test_v6_contrast_negative_probe_report_is_non_gate() -> None:
    report = _load(REPORT_PATH)

    assert report["schema_version"] == "v6-negative-contrast-probe-report.v1"
    assert report["benchmark"] == "tests/fixtures/v6_contrast_negative_benchmark_v1.json"
    assert report["policy"] == {
        "sealed_fixture_used": False,
        "current_route_measurement_is_gate": False,
        "direct_training_allowed_before_review": False,
        "human_review_required_before_adoption": True,
    }
    assert report["measurement"]["case_count"] == 30
    assert report["measurement"]["valid_packet_rate"] == 1.0
    assert report["summary"]["overfire_count"] == len(report["overfire_details"])
    expected_status = (
        "completed_with_contrast_mismatches"
        if report["measurement"]["error_count"]
        else "completed_without_contrast_mismatches"
    )
    assert report["status"] == expected_status


def test_v6_contrast_negative_worksheet_exists() -> None:
    text = WORKSHEET_PATH.read_text(encoding="utf-8")

    assert "V6 Negative/Contrast Review Worksheet v1" in text
    assert "case_count: 30" in text
    assert "v6-contrast-negative-001" in text
    assert "v6-contrast-negative-030" in text
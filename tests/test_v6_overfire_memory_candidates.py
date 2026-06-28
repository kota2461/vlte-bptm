import json
from pathlib import Path


ROOT = Path(__file__).parents[1]
OUTPUT_PATH = ROOT / "build" / "v6_overfire_memory_candidates_v1.json"
WORKSHEET_PATH = ROOT / "build" / "v6_overfire_memory_candidates_v1.md"


def _load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_v6_overfire_memory_candidates_are_saved_not_training_data() -> None:
    payload = _load(OUTPUT_PATH)

    assert payload["schema_version"] == "v6-overfire-memory-candidates.v1"
    assert payload["status"] == "saved_for_future_review"
    assert payload["policy"] == {
        "sealed_fixture_used": False,
        "current_route_measurement_is_gate": False,
        "training_status": "not_training_data",
        "allowed_use": "future_failure_memory_or_suppression_review_only",
        "human_review_required_before_adoption": True,
    }
    assert payload["summary"]["candidate_count"] == 12
    assert len(payload["candidates"]) == 12
    assert {item["training_status"] for item in payload["candidates"]} == {"not_training_data"}
    assert {item["review_status"] for item in payload["candidates"]} == {"pending_human_review"}


def test_v6_overfire_memory_candidates_keep_traceability() -> None:
    payload = _load(OUTPUT_PATH)

    assert payload["source_probe_report"] == "build/v6_contrast_negative_probe_report_v1.json"
    assert payload["source_benchmark"] == "tests/fixtures/v6_contrast_negative_benchmark_v1.json"
    assert all(item["source_case_id"].startswith("v6-contrast-negative-") for item in payload["candidates"])
    assert all(item["source_probe_report"] == payload["source_probe_report"] for item in payload["candidates"])
    assert all(item["source_benchmark"] == payload["source_benchmark"] for item in payload["candidates"])
    assert all(item["overfire_reasons"] for item in payload["candidates"])
    assert any("risk_overfire" in item["overfire_reasons"] for item in payload["candidates"])


def test_v6_overfire_memory_candidates_summary_matches_items() -> None:
    payload = _load(OUTPUT_PATH)
    candidates = payload["candidates"]

    assert payload["summary"]["by_severity"] == {
        severity: sum(1 for item in candidates if item["severity"] == severity)
        for severity in sorted({item["severity"] for item in candidates})
    }
    assert set(payload["summary"]["by_reason"]) >= {
        "risk_overfire",
        "critical_signal_overfire:requires_current_information",
    }


def test_v6_overfire_memory_candidates_are_bucketed_for_review() -> None:
    payload = _load(OUTPUT_PATH)
    candidates = payload["candidates"]

    assert payload["summary"]["clear_suppression_candidate_count"] == 10
    assert payload["summary"]["boundary_review_count"] == 2
    assert payload["summary"]["by_review_bucket"] == {
        "boundary_review": 2,
        "clear_suppression_candidate": 10,
    }
    assert sum(1 for item in candidates if item["suppression_candidate"]) == 10
    boundary_cases = {
        item["source_case_id"]
        for item in candidates
        if item["review_bucket"] == "boundary_review"
    }
    assert boundary_cases == {
        "v6-contrast-negative-011",
        "v6-contrast-negative-013",
    }
    assert all(
        "boundary_not_immediate_suppression" in item["false_positive_signature"]
        for item in candidates
        if item["review_bucket"] == "boundary_review"
    )


def test_v6_overfire_memory_candidates_worksheet_exists() -> None:
    text = WORKSHEET_PATH.read_text(encoding="utf-8")

    assert "V6 Overfire Memory Candidates v1" in text
    assert "candidate_count: 12" in text
    assert "not_training_data" in text
    assert "clear_suppression_candidate" in text
    assert "boundary_review" in text
    assert "v6-overfire-memory-001" in text
    assert "v6-overfire-memory-012" in text
import json
from pathlib import Path

from semantic_routing import parse_plm_benchmark


ROOT = Path(__file__).parents[1]
FIXTURE_PATH = ROOT / "tests" / "fixtures" / "v6_ai_boundary_candidate_fixture_v1.json"
REPORT_PATH = ROOT / "build" / "v6_ai_boundary_sample_set_report_v1.json"
WORKSHEET_PATH = ROOT / "build" / "v6_ai_boundary_candidate_review_worksheet_v1.md"


def _load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _benchmark_payload(fixture):
    return {
        "schema_version": "pattern-language-benchmark.v1",
        "frozen_at": fixture["created_at"],
        "authoring_method": "test wrapper for v6 ai boundary candidate fixture",
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


def test_v6_ai_boundary_fixture_is_nonsealed_synthesized_material() -> None:
    fixture = _load(FIXTURE_PATH)

    assert fixture["schema_version"] == "v6-ai-boundary-candidate-fixture.v1"
    assert fixture["status"] == "draft_candidate_ready_for_human_review"
    assert fixture["review_status"] == "draft"
    assert fixture["source"]["raw_text_direct_training_allowed"] is False
    assert fixture["source"]["cut_paste_synthesis_allowed"] is True
    assert fixture["source"]["line_count"] == 136
    assert fixture["policy"] == {
        "sealed_fixtures_used_as_sources": False,
        "sealed_text_used": False,
        "sealed_labels_used": False,
        "raw_notes_direct_training_allowed": False,
        "cut_paste_synthesis_used": True,
        "human_review_required_before_training": True,
        "human_review_required_before_gate": True,
        "same_cycle_promotion_allowed": False,
    }
    assert fixture["summary"]["case_count"] == 50
    assert len(fixture["cases"]) == 50


def test_v6_ai_boundary_cases_parse_as_plm_benchmark() -> None:
    fixture = _load(FIXTURE_PATH)
    benchmark = parse_plm_benchmark(_benchmark_payload(fixture))

    assert len(benchmark.cases) == 50
    assert benchmark.review_status == "draft"
    assert {case.split for case in benchmark.cases} == {"validation"}
    assert len({case.input_text for case in benchmark.cases}) == 50

    for case in fixture["cases"]:
        assert case["source_kind"] == "user_notes_cut_paste_synthesis"
        assert case["source_ref"] == "user_provided_desktop_file:recent-ai-persona-psychology-notes"
        assert case["review_status"] == "draft"
        assert case["language"] == "ja"
        assert case["line_refs"]


def test_v6_ai_boundary_fixture_covers_guard_heavy_axes() -> None:
    fixture = _load(FIXTURE_PATH)
    summary = fixture["summary"]

    assert summary["by_intent"] == {
        "build": 11,
        "clarify": 4,
        "explain": 6,
        "explore": 12,
        "summarize": 2,
        "verify": 15,
    }
    assert summary["by_operation"]["verify"] >= 30
    assert summary["by_operation"]["compare"] >= 10
    assert summary["by_constraint"]["must:avoid_overclaim"] >= 20
    assert summary["by_constraint"]["must:cite_sources"] >= 8
    assert summary["by_constraint"]["must:preserve_neutrality"] >= 6
    assert summary["critical_signal_support"]["multiple_intents"] >= 35
    assert summary["critical_signal_support"]["contains_unverified_claims"] >= 15
    assert summary["critical_signal_support"]["requires_current_information"] >= 10
    assert summary["by_risk"]["medium"] >= 25
    assert summary["by_risk"]["high"] >= 5
    assert summary["by_risk_flag"]["mental_health"] >= 8
    assert summary["by_risk_flag"]["current_information"] >= 10
    assert summary["by_risk_flag"]["legal"] >= 3


def test_v6_ai_boundary_report_is_not_a_gate() -> None:
    report = _load(REPORT_PATH)

    assert report["schema_version"] == "v6-ai-boundary-sample-set-report.v1"
    assert report["status"] == "draft_candidate_fixture_created_not_a_gate"
    assert report["current_route_measurement_is_gate"] is False
    assert report["current_route_measurement"]["case_count"] == 50
    assert report["current_route_measurement"]["valid_packet_rate"] == 1.0
    assert report["current_route_measurement"]["error_count"] >= 40
    assert report["next_step"] == {
        "name": "human_review_v6_ai_boundary_samples",
        "input": "build\\v6_ai_boundary_candidate_review_worksheet_v1.md",
        "output": "tests\\fixtures\\v6_ai_boundary_candidate_fixture_v1.json",
    }


def test_v6_ai_boundary_review_worksheet_exists() -> None:
    text = WORKSHEET_PATH.read_text(encoding="utf-8")

    assert "V6 AI Boundary Candidate Review Worksheet v1" in text
    assert "case_count: 50" in text
    assert "v6-ai-boundary-001" in text
    assert "v6-ai-boundary-050" in text

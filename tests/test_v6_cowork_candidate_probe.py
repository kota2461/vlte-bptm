import json
import re
from pathlib import Path

from semantic_routing import parse_plm_benchmark


ROOT = Path(__file__).parents[1]
FIXTURE_PATH = ROOT / "tests" / "fixtures" / "v6_cowork_candidate_fixture_v1.json"
REPORT_PATH = ROOT / "build" / "cowork_v6_candidate_probe_report.json"
WORKSHEET_PATH = ROOT / "build" / "v6_cowork_candidate_fixture_review_worksheet_v1.md"


def _load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _benchmark_payload(fixture):
    return {
        "schema_version": "pattern-language-benchmark.v1",
        "frozen_at": fixture["created_at"],
        "authoring_method": "test wrapper for v6 cowork candidate fixture",
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


def test_v6_cowork_probe_promotes_only_redacted_nonsealed_candidates() -> None:
    report = _load(REPORT_PATH)
    fixture = _load(FIXTURE_PATH)

    assert report["schema_version"] == "v6-cowork-candidate-probe-report.v1"
    assert report["status"] == "promoted_to_candidate_fixture"
    assert report["candidate_readiness"] is True
    assert report["summary"]["source_items"] == 25
    assert report["summary"]["promoted_candidates"] == 22
    assert report["summary"]["redaction_leak_count"] == 0
    assert fixture["schema_version"] == "v6-cowork-candidate-fixture.v1"
    assert fixture["status"] == "draft_candidate_ready_for_human_review"
    assert fixture["policy"] == {
        "sealed_fixtures_used_as_sources": False,
        "sealed_text_used": False,
        "sealed_labels_used": False,
        "raw_logs_direct_training_allowed": False,
        "redacted_inputs_only": True,
        "human_review_required_before_training": True,
        "human_review_required_before_gate": True,
        "same_cycle_promotion_allowed": False,
    }


def test_v6_cowork_candidate_fixture_parses_as_plm_benchmark() -> None:
    fixture = _load(FIXTURE_PATH)
    benchmark = parse_plm_benchmark(_benchmark_payload(fixture))

    assert len(benchmark.cases) == 22
    assert benchmark.review_status == "draft"
    assert {case.split for case in benchmark.cases} == {"validation"}
    assert fixture["summary"]["by_probe_status"]["route_gap"] >= 18
    assert set(fixture["summary"]["by_intent"]) >= {
        "build",
        "clarify",
        "explain",
        "explore",
        "summarize",
        "verify",
    }


def test_v6_cowork_candidate_inputs_have_no_raw_url_or_local_path_leaks() -> None:
    fixture = _load(FIXTURE_PATH)
    leak_pattern = re.compile(r"https?://|[A-Za-z]:\\|github\.com/kota2461|kota2461/vlte")

    for case in fixture["cases"]:
        assert not leak_pattern.search(case["input"])
        assert case["source_kind"] == "cowork_raw_log_redacted_candidate"
        assert case["review_status"] == "draft"
        assert case["candidate_value_score"] >= fixture["requirements"]["candidate_value_score_min"]


def test_v6_cowork_candidate_worksheet_exists() -> None:
    text = WORKSHEET_PATH.read_text(encoding="utf-8")

    assert "V6 Cowork Candidate Fixture Review Worksheet v1" in text
    assert "promoted_candidates: 22" in text
    assert "v6-cowork-candidate-001" in text

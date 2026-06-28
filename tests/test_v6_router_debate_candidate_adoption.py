import json
from pathlib import Path

from semantic_routing import parse_plm_benchmark


ROOT = Path(__file__).parents[1]
IMPORT_BENCHMARK_PATH = ROOT / "tests" / "fixtures" / "v6_router_debate_candidate_benchmark_v1.json"
ADOPTION_PLAN_PATH = ROOT / "build" / "v6_router_debate_candidate_adoption_plan_v1.json"
IMPORT_REPORT_PATH = ROOT / "build" / "v6_router_debate_candidate_import_report_v1.json"
ADOPTION_WORKSHEET_PATH = ROOT / "build" / "v6_router_debate_candidate_adoption_worksheet_v1.md"


def _load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_v6_router_debate_import_benchmark_is_plm_compatible() -> None:
    payload = _load(IMPORT_BENCHMARK_PATH)
    benchmark = parse_plm_benchmark(payload)

    assert payload["schema_version"] == "pattern-language-benchmark.v1"
    assert payload["review_status"] == "draft"
    assert len(benchmark.cases) == 12
    assert {case.split for case in benchmark.cases} == {"validation"}
    assert len({case.input_text for case in benchmark.cases}) == 12
    assert {case.expected.primary_intent for case in benchmark.cases} == {
        "build",
        "clarify",
        "explore",
        "verify",
    }


def test_v6_router_debate_adoption_plan_keeps_human_review_gate() -> None:
    plan = _load(ADOPTION_PLAN_PATH)

    assert plan["schema_version"] == "v6-router-debate-candidate-adoption-plan.v1"
    assert plan["status"] == "ready_for_human_review_before_adoption"
    assert plan["review_status"] == "pending_human_review"
    assert plan["summary"] == {
        "candidate_count": 12,
        "recommended_adopt_count": 12,
        "held_source_topics": 8,
        "current_route_gap_count": 0,
        "import_benchmark_review_status": "draft",
    }
    assert plan["policy"] == {
        "sealed_fixtures_used_as_sources": False,
        "sealed_text_used": False,
        "sealed_labels_used": False,
        "raw_debate_logs_direct_training_allowed": False,
        "topic_synthesis_used": True,
        "human_review_required_before_training": True,
        "human_review_required_before_gate": True,
        "same_cycle_promotion_allowed": False,
        "import_benchmark_is_directly_trainable": False,
    }
    assert all(
        item["recommended_decision"] == "adopt_nonsealed_after_human_review"
        and item["review_status"] == "pending_human_review"
        and item["allowed_use_before_review"] == "review_only"
        for item in plan["review_items"]
    )


def test_v6_router_debate_import_report_is_not_gate() -> None:
    report = _load(IMPORT_REPORT_PATH)

    assert report["schema_version"] == "v6-router-debate-candidate-import-report.v1"
    assert report["status"] == "import_lane_ready_pending_human_review"
    assert report["candidate_readiness"] is True
    assert report["current_route_measurement_is_gate"] is False
    assert report["current_route_measurement"]["case_count"] == 12
    assert report["current_route_measurement"]["valid_packet_rate"] == 1.0
    assert report["current_route_measurement"]["error_count"] == 0
    assert report["next_step"] == {
        "name": "human_review_then_adopt_nonsealed_router_debate_candidates",
        "input": "build/v6_router_debate_candidate_adoption_worksheet_v1.md",
        "output": "tests/fixtures/v6_router_debate_candidate_benchmark_v1.json",
    }


def test_v6_router_debate_adoption_worksheet_exists() -> None:
    text = ADOPTION_WORKSHEET_PATH.read_text(encoding="utf-8")

    assert "V6 Router Debate Candidate Adoption Worksheet v1" in text
    assert "candidate_count: 12" in text
    assert "recommended_adopt_count: 12" in text
    assert "v6-router-debate-001" in text
    assert "v6-router-debate-012" in text

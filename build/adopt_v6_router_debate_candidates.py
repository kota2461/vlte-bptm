"""Adopt reviewed V6 router-debate candidates for a non-sealed provisional test.

This script records the user's review confirmation without promoting the
candidates into a gate or sealed fixture. The adopted benchmark is an explicit
human-reviewed, non-sealed lane for replay and improvement planning.
"""

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from semantic_routing import evaluate_plm_extractor, parse_plm_benchmark, route  # noqa: E402
from semantic_routing.reproducibility import reproducible_now_iso

IMPORT_BENCHMARK_PATH = ROOT / "tests" / "fixtures" / "v6_router_debate_candidate_benchmark_v1.json"
ADOPTION_PLAN_PATH = ROOT / "build" / "v6_router_debate_candidate_adoption_plan_v1.json"
ADOPTED_BENCHMARK_PATH = ROOT / "tests" / "fixtures" / "v6_router_debate_adopted_benchmark_v1.json"
ADOPTION_DECISION_PATH = ROOT / "build" / "v6_router_debate_candidate_adoption_decision_v1.json"
PROVISIONAL_REPORT_PATH = ROOT / "build" / "v6_router_debate_adopted_provisional_test_report_v1.json"


def _load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def _rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def _compact_measurement(measurement: dict[str, Any]) -> dict[str, Any]:
    return {
        "case_count": measurement["case_count"],
        "intent_accuracy": measurement["intent_accuracy"],
        "critical_signal_recall": measurement["critical_signal_recall"],
        "operation_exact_match": measurement["operation_exact_match"],
        "constraint_exact_match": measurement["constraint_exact_match"],
        "risk_exact_match": measurement["risk_exact_match"],
        "valid_packet_rate": measurement["valid_packet_rate"],
        "error_count": len(measurement["errors"]),
    }


def _assert_review_ready(plan: dict[str, Any], benchmark: dict[str, Any]) -> None:
    if plan["schema_version"] != "v6-router-debate-candidate-adoption-plan.v1":
        raise ValueError("unsupported adoption plan schema")
    if plan["status"] != "ready_for_human_review_before_adoption":
        raise ValueError("adoption plan is not ready for review")
    if plan["review_status"] != "pending_human_review":
        raise ValueError("adoption plan was already finalized unexpectedly")
    if benchmark["review_status"] != "draft":
        raise ValueError("source import benchmark must remain draft")
    if len(plan["review_items"]) != len(benchmark["cases"]):
        raise ValueError("review item count does not match benchmark case count")
    if not all(item["recommended_decision"] == "adopt_nonsealed_after_human_review" for item in plan["review_items"]):
        raise ValueError("all review items must be recommended for non-sealed adoption")
    if not all(item["review_status"] == "pending_human_review" for item in plan["review_items"]):
        raise ValueError("review items must be pending before this adoption decision")


def main() -> None:
    generated_at = reproducible_now_iso()
    plan = _load(ADOPTION_PLAN_PATH)
    import_benchmark = _load(IMPORT_BENCHMARK_PATH)
    parse_plm_benchmark(import_benchmark)
    _assert_review_ready(plan, import_benchmark)

    adopted_benchmark = {
        "schema_version": "pattern-language-benchmark.v1",
        "frozen_at": generated_at,
        "authoring_method": (
            "V6 router debate candidates adopted after user confirmation in Codex thread; "
            "non-sealed provisional lane"
        ),
        "review_status": "human_reviewed",
        "policy": (
            "Human-reviewed non-sealed provisional lane. Raw debate logs are not direct training data. "
            "This is not a sealed fixture, not a promotion gate, and not same-cycle promotion evidence."
        ),
        "cases": import_benchmark["cases"],
    }
    adopted = parse_plm_benchmark(adopted_benchmark)
    measurement = evaluate_plm_extractor(adopted.cases, lambda text: route(text).packet)
    compact = _compact_measurement(measurement)

    policy = {
        "sealed_fixtures_used_as_sources": False,
        "sealed_text_used": False,
        "sealed_labels_used": False,
        "raw_debate_logs_direct_training_allowed": False,
        "topic_synthesis_used": True,
        "human_review_confirmation_recorded": True,
        "same_cycle_promotion_allowed": False,
        "current_route_measurement_is_gate": False,
        "adopted_benchmark_is_directly_trainable": False,
    }
    case_ids = [case["id"] for case in adopted_benchmark["cases"]]
    decision = {
        "schema_version": "v6-router-debate-candidate-adoption-decision.v1",
        "generated_at": generated_at,
        "status": "adopted_for_nonsealed_provisional_test",
        "review_status": "human_reviewed",
        "reviewed_by": "user_confirmation_in_codex_thread",
        "source_adoption_plan": _rel(ADOPTION_PLAN_PATH),
        "source_import_benchmark": _rel(IMPORT_BENCHMARK_PATH),
        "adopted_benchmark": _rel(ADOPTED_BENCHMARK_PATH),
        "adopted_count": len(case_ids),
        "case_ids": case_ids,
        "policy": policy,
    }
    has_gaps = bool(compact["error_count"])
    report = {
        "schema_version": "v6-router-debate-adopted-provisional-test-report.v1",
        "generated_at": generated_at,
        "status": "completed_with_expected_route_gaps" if has_gaps else "completed_without_route_gaps",
        "adoption_decision": _rel(ADOPTION_DECISION_PATH),
        "adopted_benchmark": _rel(ADOPTED_BENCHMARK_PATH),
        "current_route_measurement_is_gate": False,
        "sealed_fixture_used": False,
        "measurement": compact,
        "errors": measurement["errors"],
        "interpretation": (
            "The candidates are human-reviewed non-sealed material. Current route() still has gaps; use this lane "
            "to guide V6 improvements before any future sealed rotation."
            if has_gaps
            else "The candidates are human-reviewed non-sealed material and current route() matches this lane. This remains replay evidence, not a sealed gate."
        ),
        "next_step": (
            "Use these adopted gaps to design V6 route improvements, then replay this non-sealed lane."
            if has_gaps
            else "Keep this lane as non-sealed replay coverage while measuring broader V6 behavior."
        ),
    }

    _write_json(ADOPTED_BENCHMARK_PATH, adopted_benchmark)
    _write_json(ADOPTION_DECISION_PATH, decision)
    _write_json(PROVISIONAL_REPORT_PATH, report)
    print(json.dumps({
        "status": report["status"],
        "adopted_benchmark": report["adopted_benchmark"],
        "adopted_count": decision["adopted_count"],
        "measurement": compact,
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

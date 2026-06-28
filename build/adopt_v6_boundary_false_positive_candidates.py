"""Adopt V6 boundary false-positive candidates for non-sealed replay.

This records the user's review confirmation. It does not promote the candidates
into a sealed fixture or gate. The adopted lane is used to guide suppression
improvements and replay checks.
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from semantic_routing import evaluate_plm_extractor, parse_plm_benchmark, route  # noqa: E402

SOURCE_BENCHMARK_PATH = ROOT / "tests" / "fixtures" / "v6_boundary_false_positive_candidate_benchmark_v1.json"
SOURCE_REPORT_PATH = ROOT / "build" / "v6_boundary_false_positive_candidate_report_v1.json"
ADOPTED_BENCHMARK_PATH = ROOT / "tests" / "fixtures" / "v6_boundary_false_positive_adopted_benchmark_v1.json"
ADOPTION_DECISION_PATH = ROOT / "build" / "v6_boundary_false_positive_adoption_decision_v1.json"
REPLAY_REPORT_PATH = ROOT / "build" / "v6_boundary_false_positive_adopted_replay_report_v1.json"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def compact_measurement(measurement: dict[str, Any]) -> dict[str, Any]:
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


def assert_ready_for_adoption(source_benchmark: dict[str, Any], source_report: dict[str, Any]) -> None:
    if source_benchmark["schema_version"] != "pattern-language-benchmark.v1":
        raise ValueError("source benchmark must be a PLM benchmark")
    if source_benchmark["review_status"] != "draft":
        raise ValueError("source benchmark should remain draft before adoption")
    if source_report["schema_version"] != "v6-boundary-false-positive-candidate-report.v1":
        raise ValueError("unsupported source report schema")
    if source_report["status"] != "candidate_lane_ready_for_human_review":
        raise ValueError("source report is not ready for review")
    if source_report["policy"]["raw_debate_logs_direct_training_allowed"] is not False:
        raise ValueError("raw debate logs must remain excluded from training")
    if source_report["policy"]["human_review_required_before_training"] is not True:
        raise ValueError("source report must require human review before training")
    if len(source_benchmark["cases"]) != 15:
        raise ValueError("expected exactly 15 boundary false-positive candidates")
    if any(case["expected"]["risk"]["level"] != "low" for case in source_benchmark["cases"]):
        raise ValueError("all adopted false-positive cases must be low-risk expected cases")


def main() -> None:
    generated_at = datetime.now(timezone.utc).isoformat()
    source_benchmark = load_json(SOURCE_BENCHMARK_PATH)
    source_report = load_json(SOURCE_REPORT_PATH)
    parse_plm_benchmark(source_benchmark)
    assert_ready_for_adoption(source_benchmark, source_report)

    adopted_benchmark = {
        "schema_version": "pattern-language-benchmark.v1",
        "frozen_at": generated_at,
        "authoring_method": (
            "V6 boundary false-positive candidates adopted after user confirmation in Codex thread; "
            "manual short-prompt synthesis from non-sealed debate topic metadata"
        ),
        "review_status": "human_reviewed",
        "policy": (
            "Human-reviewed non-sealed false-positive replay lane. Raw debate turns are not direct training data. "
            "This is not a sealed fixture, not a promotion gate, and not same-cycle promotion evidence."
        ),
        "cases": source_benchmark["cases"],
    }
    adopted = parse_plm_benchmark(adopted_benchmark)
    measurement = evaluate_plm_extractor(adopted.cases, lambda text: route(text).packet)
    compact = compact_measurement(measurement)

    policy = {
        "sealed_fixtures_used_as_sources": False,
        "sealed_text_used": False,
        "sealed_labels_used": False,
        "raw_debate_logs_direct_training_allowed": False,
        "manual_prompt_synthesis_used": True,
        "human_review_confirmation_recorded": True,
        "same_cycle_promotion_allowed": False,
        "current_route_measurement_is_gate": False,
        "adopted_benchmark_is_directly_trainable": False,
    }
    case_ids = [case["id"] for case in adopted_benchmark["cases"]]
    decision = {
        "schema_version": "v6-boundary-false-positive-adoption-decision.v1",
        "generated_at": generated_at,
        "status": "adopted_for_nonsealed_replay",
        "review_status": "human_reviewed",
        "reviewed_by": "user_confirmation_in_codex_thread",
        "source_candidate_benchmark": rel(SOURCE_BENCHMARK_PATH),
        "source_candidate_report": rel(SOURCE_REPORT_PATH),
        "adopted_benchmark": rel(ADOPTED_BENCHMARK_PATH),
        "adopted_count": len(case_ids),
        "case_ids": case_ids,
        "policy": policy,
    }
    has_gaps = bool(compact["error_count"])
    report = {
        "schema_version": "v6-boundary-false-positive-adopted-replay-report.v1",
        "generated_at": generated_at,
        "status": "completed_with_expected_route_gaps" if has_gaps else "completed_without_route_gaps",
        "adoption_decision": rel(ADOPTION_DECISION_PATH),
        "adopted_benchmark": rel(ADOPTED_BENCHMARK_PATH),
        "current_route_measurement_is_gate": False,
        "sealed_fixture_used": False,
        "measurement": compact,
        "errors": measurement["errors"],
        "interpretation": (
            "The adopted low-risk boundary lane exposes current overfire gaps. Use it for V6 suppression improvements, not as a sealed gate."
            if has_gaps
            else "The adopted low-risk boundary lane currently matches route(). It remains non-sealed replay evidence, not a sealed gate."
        ),
        "next_step": (
            "Implement suppression/generalization improvements, then replay this adopted non-sealed lane."
            if has_gaps
            else "Keep this lane as replay coverage while measuring broader V6 behavior."
        ),
    }

    write_json(ADOPTED_BENCHMARK_PATH, adopted_benchmark)
    write_json(ADOPTION_DECISION_PATH, decision)
    write_json(REPLAY_REPORT_PATH, report)
    print(json.dumps({
        "status": report["status"],
        "adopted_benchmark": report["adopted_benchmark"],
        "adopted_count": decision["adopted_count"],
        "measurement": compact,
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
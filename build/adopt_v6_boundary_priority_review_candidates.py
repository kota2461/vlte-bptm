"""Adopt V6 boundary priority-review candidates for non-sealed replay.

The user confirmed the priority_review_count=26 set should proceed as human
review adoption candidates. This records that decision and creates a strict PLM
benchmark lane. It is not a sealed fixture, gate, or direct training corpus.
"""

import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from semantic_routing import evaluate_plm_extractor, parse_plm_benchmark, route  # noqa: E402

SOURCE_REVIEW_PATH = ROOT / "build" / "v6_boundary_debate_candidate_queue_review_v1.json"
ADOPTED_BENCHMARK_PATH = ROOT / "tests" / "fixtures" / "v6_boundary_priority_review_adopted_benchmark_v1.json"
ADOPTION_DECISION_PATH = ROOT / "build" / "v6_boundary_priority_review_adoption_decision_v1.json"
REPLAY_REPORT_PATH = ROOT / "build" / "v6_boundary_priority_review_adopted_replay_report_v1.json"
WORKSHEET_PATH = ROOT / "build" / "v6_boundary_priority_review_adopted_worksheet_v1.md"

POLICY = {
    "sealed_fixtures_used_as_sources": False,
    "sealed_text_used": False,
    "raw_debate_logs_direct_training_allowed": False,
    "llm_turn_text_direct_training_allowed": False,
    "topic_metadata_synthesis_used": True,
    "human_review_confirmation_recorded": True,
    "same_cycle_promotion_allowed": False,
    "current_route_measurement_is_gate": False,
    "adopted_benchmark_is_directly_trainable": False,
}

CRITICAL_SIGNALS = (
    "missing_required_information",
    "contains_unverified_claims",
    "requires_current_information",
    "multiple_intents",
)

PROMPT_OVERRIDES = {
    "v6-boundary-debate-queue-032": "Add README parameter names empathy_score and persona_mode. This is configuration naming, not a counseling request.",
    "v6-boundary-debate-queue-039": "Translate the word medicine into Japanese and give a short reading note. This is word study, not medical advice.",
    "v6-boundary-debate-queue-017": "Briefly explain the Apache 2.0 license at a general level. No legal advice or current case law is needed.",
    "v6-boundary-debate-queue-018": "I want ideas for a Medical AI UI layout. This is screen design, not diagnosis or treatment advice.",
    "v6-boundary-debate-queue-019": "Tell me the PowerShell command for checking the current folder. I do not need web or latest external information.",
}


def adopted_prompt(item: dict[str, Any]) -> str:
    return PROMPT_OVERRIDES.get(item["id"], item["prompt"])


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def language_of(text: str) -> str:
    has_ascii_alpha = any(("a" <= char.lower() <= "z") for char in text)
    has_non_ascii = any(ord(char) > 127 for char in text)
    if has_ascii_alpha and has_non_ascii:
        return "mixed"
    if has_non_ascii:
        return "ja"
    if has_ascii_alpha:
        return "en"
    return "und"


def expected_packet(item: dict[str, Any]) -> dict[str, Any]:
    expected = item["expected"]
    return {
        "primary_intent": expected["primary_intent"],
        "operations": list(expected["operations"]),
        "information_state": dict(expected["information_state"]),
        "constraints": dict(expected["constraints"]),
        "risk": dict(expected["risk"]),
        "evidence": [],
        "unknowns": [],
        "conflicts": [],
    }


def select_items(review: dict[str, Any]) -> list[dict[str, Any]]:
    by_id = {item["id"]: item for item in review["items"]}
    if ADOPTION_DECISION_PATH.exists():
        decision = load_json(ADOPTION_DECISION_PATH)
        selected_ids = decision.get("selected_queue_ids", [])
        if selected_ids:
            missing = [item_id for item_id in selected_ids if item_id not in by_id]
            if missing:
                raise ValueError(f"adopted queue id missing from review: {missing[0]}")
            return [by_id[item_id] for item_id in selected_ids]

    items = [
        item
        for item in review["items"]
        if item["priority_score"] >= 9 and item["action"] != "hold_ladder_review"
    ]
    items.sort(key=lambda item: (-item["priority_score"], item["id"]))
    if len(items) != review["summary"]["priority_review_count"]:
        raise ValueError("selected priority count does not match review summary")
    return items


def benchmark_cases(items: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    cases = []
    for index, item in enumerate(items, start=1):
        cases.append(
            {
                "id": f"v6-boundary-priority-review-{index:03d}",
                "split": "validation",
                "source_group": "v6-boundary-priority-review-adopted-nonsealed",
                "contrast_group": item["candidate_type"],
                "language": language_of(adopted_prompt(item)),
                "input": adopted_prompt(item),
                "expected": expected_packet(item),
            }
        )
    return cases


def compact_measurement(measurement: dict[str, Any]) -> dict[str, Any]:
    error_fields = Counter(field for error in measurement["errors"] for field in error.get("fields", []))
    return {
        "case_count": measurement["case_count"],
        "intent_accuracy": measurement["intent_accuracy"],
        "critical_signal_recall": measurement["critical_signal_recall"],
        "operation_exact_match": measurement["operation_exact_match"],
        "constraint_exact_match": measurement["constraint_exact_match"],
        "risk_exact_match": measurement["risk_exact_match"],
        "valid_packet_rate": measurement["valid_packet_rate"],
        "error_count": len(measurement["errors"]),
        "error_field_counts": dict(sorted(error_fields.items())),
    }


def summarize_items(items: Sequence[dict[str, Any]], measurement: dict[str, Any]) -> dict[str, Any]:
    by_action = Counter(item["action"] for item in items)
    by_target = Counter(item["target_set"] for item in items)
    by_type = Counter(item["candidate_type"] for item in items)
    by_intent = Counter(item["expected"]["primary_intent"] for item in items)
    by_risk = Counter(item["expected"]["risk"]["level"] for item in items)
    support = Counter()
    for item in items:
        for signal, value in item["expected"]["information_state"].items():
            if value:
                support[signal] += 1
    return {
        "adopted_count": len(items),
        "by_action": dict(sorted(by_action.items())),
        "by_target_set": dict(sorted(by_target.items())),
        "by_candidate_type": dict(sorted(by_type.items())),
        "by_expected_intent": dict(sorted(by_intent.items())),
        "by_expected_risk": dict(sorted(by_risk.items())),
        "critical_signal_support": {signal: support.get(signal, 0) for signal in CRITICAL_SIGNALS},
        "current_route_measurement": compact_measurement(measurement),
    }


def write_worksheet(items: Sequence[dict[str, Any]], report: dict[str, Any]) -> None:
    lines = [
        "# V6 Boundary Priority Review Adopted Worksheet v1",
        "",
        "Human-reviewed non-sealed replay candidates selected from the 48-item queue review.",
        "These are not sealed, not gate evidence, and not direct training data.",
        "",
        "## Summary",
        "",
        f"- adopted_count: {report['summary']['adopted_count']}",
        f"- current_route_error_count: {report['measurement']['error_count']}",
        f"- current_route_intent_accuracy: {report['measurement']['intent_accuracy']:.3f}",
        f"- current_route_risk_exact_match: {report['measurement']['risk_exact_match']:.3f}",
        "",
        "## Adopted Candidates",
        "",
        "| adopted_id | queue_id | score | action | topic | target | type | fields | expected | actual | prompt |",
        "| --- | --- | ---: | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for index, item in enumerate(items, start=1):
        expected = item["expected"]
        actual = item["actual"]
        prompt = adopted_prompt(item).replace("|", "&#124;")
        lines.append(
            "| "
            f"v6-boundary-priority-review-{index:03d} | {item['id']} | {item['priority_score']} | {item['action']} | "
            f"{item['source_topic_id']} | {item['target_set']} | {item['candidate_type']} | {','.join(item['fields'])} | "
            f"{expected['primary_intent']}:{expected['risk']['level']} | {actual['primary_intent']}:{actual['risk']['level']} | {prompt} |"
        )
    lines.extend([
        "",
        "## Contract",
        "",
        "- training_allowed: false",
        "- gate_use_allowed: false",
        "- current_route_measurement_is_gate: false",
        "- same_cycle_promotion_allowed: false",
    ])
    WORKSHEET_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def main() -> None:
    generated_at = datetime.now(timezone.utc).isoformat()
    review = load_json(SOURCE_REVIEW_PATH)
    if review["schema_version"] != "v6-boundary-debate-candidate-queue-review.v1":
        raise ValueError("unsupported review report schema")
    items = select_items(review)
    benchmark = {
        "schema_version": "pattern-language-benchmark.v1",
        "frozen_at": generated_at,
        "authoring_method": (
            "V6 boundary priority-review candidates adopted after user confirmation; "
            "short prompts synthesized from non-sealed router debate topic metadata"
        ),
        "review_status": "human_reviewed",
        "policy": (
            "Human-reviewed non-sealed priority replay lane. Raw debate turns are not direct training data. "
            "This is not a sealed fixture, not a promotion gate, and not same-cycle promotion evidence."
        ),
        "cases": benchmark_cases(items),
    }
    parsed = parse_plm_benchmark(benchmark)
    measurement = evaluate_plm_extractor(parsed.cases, lambda text: route(text).packet)
    compact = compact_measurement(measurement)
    summary = summarize_items(items, measurement)
    selected_queue_ids = [item["id"] for item in items]
    selected_topics = [item["source_topic_id"] for item in items]
    decision = {
        "schema_version": "v6-boundary-priority-review-adoption-decision.v1",
        "generated_at": generated_at,
        "status": "adopted_for_nonsealed_replay",
        "review_status": "human_reviewed",
        "reviewed_by": "user_confirmation_in_codex_thread",
        "source_review_report": rel(SOURCE_REVIEW_PATH),
        "adopted_benchmark": rel(ADOPTED_BENCHMARK_PATH),
        "worksheet": rel(WORKSHEET_PATH),
        "adopted_count": len(items),
        "selected_queue_ids": selected_queue_ids,
        "selected_source_topics": selected_topics,
        "policy": POLICY,
    }
    has_gaps = bool(compact["error_count"])
    report = {
        "schema_version": "v6-boundary-priority-review-adopted-replay-report.v1",
        "generated_at": generated_at,
        "status": "completed_with_expected_route_gaps" if has_gaps else "completed_without_route_gaps",
        "adoption_decision": rel(ADOPTION_DECISION_PATH),
        "adopted_benchmark": rel(ADOPTED_BENCHMARK_PATH),
        "worksheet": rel(WORKSHEET_PATH),
        "current_route_measurement_is_gate": False,
        "sealed_fixture_used": False,
        "policy": POLICY,
        "summary": summary,
        "measurement": compact,
        "errors": measurement["errors"],
        "interpretation": (
            "The adopted priority lane intentionally exposes current low-risk overfire and contrast-negative gaps. Use it for non-sealed replay improvements, not as a sealed gate."
            if has_gaps
            else "The adopted priority lane currently matches route(). It remains non-sealed replay evidence, not a sealed gate."
        ),
        "next_step": "Improve route suppression/generalization, then replay this non-sealed adopted priority lane.",
    }
    write_json(ADOPTED_BENCHMARK_PATH, benchmark)
    write_json(ADOPTION_DECISION_PATH, decision)
    write_json(REPLAY_REPORT_PATH, report)
    write_worksheet(items, report)
    print(json.dumps({
        "status": report["status"],
        "adopted_benchmark": rel(ADOPTED_BENCHMARK_PATH),
        "adopted_count": len(items),
        "measurement": compact,
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
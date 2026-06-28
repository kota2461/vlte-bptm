"""Extract V6 candidate samples from router debate logs.

Raw debate turns are review evidence only. Candidate samples are short,
self-contained topic prompts synthesized from the debate topic metadata.
"""

import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from semantic_routing import evaluate_plm_extractor, parse_plm_benchmark, route  # noqa: E402
from semantic_routing.reproducibility import reproducible_now_iso

SOURCE_LOG_PATH = ROOT / "build" / "router_debate_live_31stock_r3.json"
REPORT_PATH = ROOT / "build" / "v6_router_debate_candidate_probe_report_v1.json"
SELECTION_PATH = ROOT / "build" / "v6_router_debate_candidate_selection_v1.json"
FIXTURE_PATH = ROOT / "tests" / "fixtures" / "v6_router_debate_candidate_fixture_v1.json"
WORKSHEET_PATH = ROOT / "build" / "v6_router_debate_candidate_review_worksheet_v1.md"

SELECTED_TOPIC_IDS = [
    "ai-persona-romantic-daily-support",
    "ai-persona-loneliness-dependency-boundary",
    "ai-persona-understanding-claim-boundary",
    "legal-generated-output-license",
    "legal-ai-abuse-ethics",
    "legal-current-regulation-without-search",
    "politics-ai-economic-split",
    "politics-neutrality-practical-advice",
    "future-ai-job-displacement",
    "medical-migraine-anxiety-boundary",
    "hostile-user-local-llm",
    "licensed-model-debate-samples",
]

HOLD_REASONS = {
    "ai-persona-boundary": "broad_theme_already_covered_by_more_specific_ai_persona_candidates",
    "ai-ethics-legal-current": "broad_theme_superseded_by_legal_specific_candidates",
    "future-economy-ai-split": "broad_theme_superseded_by_politics_ai_economic_split",
    "core6-architecture": "covered_by_existing_v6_ai_boundary_core6_architecture_candidate",
    "mental-health-boundary": "broad_theme_superseded_by_medical_migraine_anxiety_boundary",
    "political-neutrality": "broad_theme_superseded_by_politics_neutrality_practical_advice",
    "topic-memory-packaging": "covered_by_existing_v6_ai_boundary_memory_packaging_candidate",
    "speculative-hardware-feasibility": "covered_by_existing_hardware_speculation_candidate_for_now",
}


def expected(
    primary_intent: str,
    operations: list[str],
    *,
    missing: bool = False,
    unverified: bool = False,
    current: bool = False,
    multiple: bool = False,
    response_length: str = "unspecified",
    formats: list[str] | None = None,
    must: list[str] | None = None,
    must_not: list[str] | None = None,
    risk: str = "low",
    risk_flags: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "primary_intent": primary_intent,
        "operations": operations,
        "information_state": {
            "missing_required_information": missing,
            "contains_unverified_claims": unverified,
            "requires_current_information": current,
            "multiple_intents": multiple,
        },
        "constraints": {
            "response_length": response_length,
            "formats": formats or [],
            "must": must or [],
            "must_not": must_not or [],
        },
        "risk": {"level": risk, "flags": risk_flags or []},
        "evidence": [],
        "unknowns": [],
        "conflicts": [],
    }


EXPECTED_BY_TOPIC = {
    "ai-persona-romantic-daily-support": expected(
        "verify",
        ["verify", "explain"],
        unverified=True,
        multiple=True,
        must=["avoid_overclaim"],
        risk="medium",
        risk_flags=["mental_health", "dependency_risk", "unverified_claim"],
    ),
    "ai-persona-loneliness-dependency-boundary": expected(
        "verify",
        ["verify", "explain"],
        unverified=True,
        multiple=True,
        must=["avoid_overclaim"],
        risk="medium",
        risk_flags=["mental_health", "dependency_risk", "unverified_claim"],
    ),
    "ai-persona-understanding-claim-boundary": expected(
        "verify",
        ["verify", "explain"],
        unverified=True,
        multiple=True,
        must=["avoid_overclaim"],
        risk="medium",
        risk_flags=["persona_claim", "mental_health", "unverified_claim"],
    ),
    "legal-generated-output-license": expected(
        "verify",
        ["verify", "search"],
        current=True,
        multiple=True,
        must=["cite_sources", "avoid_overclaim"],
        risk="high",
        risk_flags=["legal", "license", "current_information"],
    ),
    "legal-ai-abuse-ethics": expected(
        "explore",
        ["explore", "verify"],
        unverified=True,
        multiple=True,
        must=["preserve_neutrality", "avoid_overclaim"],
        risk="medium",
        risk_flags=["ai_ethics", "hostile_user", "unverified_claim"],
    ),
    "legal-current-regulation-without-search": expected(
        "verify",
        ["verify"],
        current=True,
        multiple=True,
        must=["avoid_overclaim"],
        must_not=["no_web_search"],
        risk="high",
        risk_flags=["legal", "current_information"],
    ),
    "politics-ai-economic-split": expected(
        "explore",
        ["explore", "verify"],
        unverified=True,
        multiple=True,
        must=["preserve_neutrality", "avoid_overclaim"],
        risk="medium",
        risk_flags=["political", "future_prediction", "unverified_claim"],
    ),
    "politics-neutrality-practical-advice": expected(
        "explore",
        ["explore", "compare"],
        unverified=True,
        multiple=True,
        must=["preserve_neutrality", "avoid_overclaim"],
        risk="medium",
        risk_flags=["political", "values", "unverified_claim"],
    ),
    "future-ai-job-displacement": expected(
        "explore",
        ["explore", "verify"],
        unverified=True,
        multiple=True,
        must=["avoid_overclaim"],
        risk="medium",
        risk_flags=["future_prediction", "unverified_claim"],
    ),
    "medical-migraine-anxiety-boundary": expected(
        "clarify",
        ["clarify", "verify", "explain"],
        missing=True,
        multiple=True,
        must=["ask_first", "avoid_overclaim"],
        risk="high",
        risk_flags=["medical", "mental_health"],
    ),
    "hostile-user-local-llm": expected(
        "build",
        ["build", "verify"],
        unverified=True,
        multiple=True,
        must=["avoid_overclaim"],
        risk="medium",
        risk_flags=["hostile_user", "safety"],
    ),
    "licensed-model-debate-samples": expected(
        "build",
        ["build", "verify"],
        current=True,
        multiple=True,
        must=["cite_sources", "avoid_overclaim"],
        risk="high",
        risk_flags=["legal", "license", "current_information"],
    ),
}


def packet_dict(text: str) -> dict[str, Any]:
    result = route(text)
    packet = result.packet
    return {
        "primary_intent": packet.primary_intent,
        "operations": list(packet.operations),
        "information_state": packet.information_state.as_dict(),
        "constraints": packet.constraints.as_dict(),
        "risk": packet.risk.as_dict(),
        "retrieval": result.retrieval.as_dict(),
    }


def benchmark_payload(cases: list[dict[str, Any]], generated_at: str) -> dict[str, Any]:
    return {
        "schema_version": "pattern-language-benchmark.v1",
        "frozen_at": generated_at,
        "authoring_method": "Router debate log topic synthesis; non-sealed, human review required",
        "review_status": "draft",
        "policy": "Candidate fixture only. Debate raw turns are not direct training data; sealed fixtures are not used.",
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
            for case in cases
        ],
    }


def summarize_cases(cases: list[dict[str, Any]]) -> dict[str, Any]:
    by_intent = Counter(case["expected"]["primary_intent"] for case in cases)
    by_operation: Counter[str] = Counter()
    by_axis: Counter[str] = Counter()
    by_constraint: Counter[str] = Counter()
    by_risk = Counter(case["expected"]["risk"]["level"] for case in cases)
    by_risk_flag: Counter[str] = Counter()
    signal_support: Counter[str] = Counter()
    by_retrieval_domain: Counter[str] = Counter()
    for case in cases:
        expected_packet = case["expected"]
        by_operation.update(expected_packet["operations"])
        by_axis.update(case["axis_ids"])
        constraints = expected_packet["constraints"]
        by_constraint.update(f"must:{item}" for item in constraints["must"])
        by_constraint.update(f"must_not:{item}" for item in constraints["must_not"])
        by_constraint.update(f"format:{item}" for item in constraints["formats"])
        if constraints["response_length"] != "unspecified":
            by_constraint[f"length:{constraints['response_length']}"] += 1
        by_risk_flag.update(expected_packet["risk"]["flags"])
        for signal, value in expected_packet["information_state"].items():
            if value:
                signal_support[signal] += 1
        by_retrieval_domain.update(case["current_route"]["retrieval"]["domains"])
    return {
        "case_count": len(cases),
        "by_intent": dict(sorted(by_intent.items())),
        "by_operation": dict(sorted(by_operation.items())),
        "by_axis": dict(sorted(by_axis.items())),
        "by_constraint": dict(sorted(by_constraint.items())),
        "critical_signal_support": dict(sorted(signal_support.items())),
        "by_risk": dict(sorted(by_risk.items())),
        "by_risk_flag": dict(sorted(by_risk_flag.items())),
        "by_retrieval_domain": dict(sorted(by_retrieval_domain.items())),
    }


def debate_health(topic: dict[str, Any]) -> dict[str, Any]:
    turns = topic["turns"]
    return {
        "turn_count": len(turns),
        "moderation_event_count": len(topic.get("moderation_events", [])),
        "final_decision": topic["router_decision"]["decision"],
        "final_reasons": topic["router_decision"].get("reasons", []),
        "all_turns_content": all(turn.get("via") == "content" for turn in turns),
        "reasoning_content_chars": sum(turn.get("reasoning_content_chars", 0) for turn in turns),
    }


def candidate_score(topic: dict[str, Any], expected_packet: dict[str, Any], actual: dict[str, Any]) -> tuple[int, list[str]]:
    score = 0
    reasons: list[str] = []
    health = debate_health(topic)
    if health["turn_count"] >= 6 and health["all_turns_content"] and health["reasoning_content_chars"] == 0:
        score += 2
        reasons.append("clean_three_round_debate")
    if topic["topic_id"] in SELECTED_TOPIC_IDS:
        score += 2
        reasons.append("selected_specific_theme")
    if expected_packet["primary_intent"] != "respond":
        score += 1
        reasons.append("non_respond_route")
    if expected_packet["risk"]["level"] in {"medium", "high", "critical"}:
        score += 1
        reasons.append("guard_or_risk_signal")
    if expected_packet["information_state"]["multiple_intents"] or len(expected_packet["operations"]) > 1:
        score += 1
        reasons.append("compound_processing_signal")
    if actual["primary_intent"] != expected_packet["primary_intent"] or not set(expected_packet["operations"]) <= set(actual["operations"]):
        score += 1
        reasons.append("current_route_gap")
    if actual["retrieval"]["needed"]:
        score += 1
        reasons.append("knowledge_index_hooked")
    return score, reasons


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


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def write_worksheet(fixture: dict[str, Any], selection: dict[str, Any], report: dict[str, Any]) -> None:
    lines = [
        "# V6 Router Debate Candidate Review Worksheet v1",
        "",
        "Non-sealed candidate samples synthesized from router debate topics.",
        "Raw debate turns are review evidence only and are not direct training data.",
        "",
        "## Summary",
        "",
        f"- selected_candidates: {fixture['summary']['case_count']}",
        f"- held_topics: {selection['summary']['held_topics']}",
        f"- source_turn_count: {selection['source_log_summary']['turn_count']}",
        f"- current_route_intent_accuracy: {report['current_route_measurement']['intent_accuracy']:.3f}",
        f"- current_route_error_count: {report['current_route_measurement']['error_count']}",
        "",
        "## Selected Candidates",
        "",
        "| id | score | topic | intent | operations | risk | retrieval | input |",
        "| --- | ---: | --- | --- | --- | --- | --- | --- |",
    ]
    for case in fixture["cases"]:
        text = case["input"].replace("|", "&#124;").replace("\n", "<br>")
        retrieval = ",".join(case["current_route"]["retrieval"]["domains"])
        lines.append(
            "| "
            f"{case['id']} | {case['candidate_value_score']} | {case['source_topic_id']} | "
            f"{case['expected']['primary_intent']} | {','.join(case['expected']['operations'])} | "
            f"{case['expected']['risk']['level']} | {retrieval} | {text} |"
        )
    lines.extend([
        "",
        "## Held Topics",
        "",
        "| topic | reason |",
        "| --- | --- |",
    ])
    for item in selection["held_topics"]:
        lines.append(f"| {item['topic_id']} | {item['reason']} |")
    WORKSHEET_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def main() -> None:
    generated_at = reproducible_now_iso()
    source = json.loads(SOURCE_LOG_PATH.read_text(encoding="utf-8"))
    topics_by_id = {topic["topic_id"]: topic for topic in source["topics"]}

    cases = []
    selected_topics = []
    held_topics = []
    issue_topics = []
    for topic in source["topics"]:
        health = debate_health(topic)
        if not health["all_turns_content"] or health["reasoning_content_chars"] != 0:
            issue_topics.append({"topic_id": topic["topic_id"], "health": health})
        if topic["topic_id"] not in SELECTED_TOPIC_IDS:
            held_topics.append(
                {
                    "topic_id": topic["topic_id"],
                    "reason": HOLD_REASONS.get(topic["topic_id"], "not_selected_for_v6_router_debate_candidate_v1"),
                    "health": health,
                }
            )
            continue
        expected_packet = EXPECTED_BY_TOPIC[topic["topic_id"]]
        actual = packet_dict(topic["theme"])
        score, reasons = candidate_score(topic, expected_packet, actual)
        selected_topics.append({"topic_id": topic["topic_id"], "score": score, "reasons": reasons, "health": health})
        cases.append(
            {
                "id": f"v6-router-debate-{len(cases) + 1:03d}",
                "review_status": "draft",
                "split": "validation",
                "source_group": "v6-router-debate-nonsealed-candidate-draft",
                "source_kind": "router_debate_topic_synthesis",
                "source_ref": SOURCE_LOG_PATH.relative_to(ROOT).as_posix(),
                "source_topic_id": topic["topic_id"],
                "axis_ids": topic["axis_ids"],
                "language": "ja",
                "input": topic["theme"],
                "expected": expected_packet,
                "candidate_value_score": score,
                "selection_reasons": reasons,
                "current_route": actual,
                "debate_trace": health,
                "notes": "Draft candidate synthesized from non-sealed router debate topic metadata. Human review required before training or gate use.",
            }
        )

    benchmark = parse_plm_benchmark(benchmark_payload(cases, generated_at))
    measurement = evaluate_plm_extractor(benchmark.cases, lambda text: route(text).packet)
    summary = summarize_cases(cases)
    ready = (
        len(cases) >= 10
        and not issue_topics
        and summary["by_intent"].get("verify", 0) >= 5
        and summary["by_risk"].get("high", 0) >= 3
    )

    policy = {
        "sealed_fixtures_used_as_sources": False,
        "sealed_text_used": False,
        "sealed_labels_used": False,
        "raw_debate_logs_direct_training_allowed": False,
        "topic_synthesis_used": True,
        "llm_turn_text_direct_training_allowed": False,
        "human_review_required_before_training": True,
        "human_review_required_before_gate": True,
        "same_cycle_promotion_allowed": False,
    }
    fixture = {
        "schema_version": "v6-router-debate-candidate-fixture.v1",
        "fixture_id": "v6-router-debate-candidate-fixture-v1",
        "created_at": generated_at,
        "status": "draft_candidate_ready_for_human_review" if ready else "draft_candidate_probe_only",
        "review_status": "draft",
        "source": {
            "kind": "router_debate_live_log",
            "path": SOURCE_LOG_PATH.relative_to(ROOT).as_posix(),
            "topic_count": source["summary"]["topic_count"],
            "turn_count": source["summary"]["turn_count"],
            "closed_topic_count": source["summary"]["closed_topic_count"],
            "raw_debate_log_direct_training_allowed": False,
            "topic_synthesis_allowed": True,
        },
        "policy": policy,
        "requirements": {
            "min_selected_candidates": 10,
            "min_verify_cases": 5,
            "min_high_risk_cases": 3,
            "require_zero_reasoning_content_chars": True,
        },
        "summary": summary,
        "cases": cases,
    }
    selection = {
        "schema_version": "v6-router-debate-candidate-selection.v1",
        "generated_at": generated_at,
        "source_log": SOURCE_LOG_PATH.relative_to(ROOT).as_posix(),
        "source_log_summary": source["summary"],
        "policy": policy,
        "summary": {
            "source_topics": len(source["topics"]),
            "selected_topics": len(selected_topics),
            "held_topics": len(held_topics),
            "issue_topics": len(issue_topics),
        },
        "selected_topics": selected_topics,
        "held_topics": held_topics,
        "issue_topics": issue_topics,
    }
    report = {
        "schema_version": "v6-router-debate-candidate-probe-report.v1",
        "generated_at": generated_at,
        "status": "promoted_to_candidate_fixture" if ready else "probe_only_not_promoted",
        "candidate_readiness": ready,
        "selection": SELECTION_PATH.relative_to(ROOT).as_posix(),
        "fixture": FIXTURE_PATH.relative_to(ROOT).as_posix(),
        "worksheet": WORKSHEET_PATH.relative_to(ROOT).as_posix(),
        "policy": policy,
        "summary": summary,
        "selection_summary": selection["summary"],
        "current_route_measurement_is_gate": False,
        "current_route_measurement": compact_measurement(measurement),
        "errors": measurement["errors"],
        "next_step": {
            "name": "human_review_v6_router_debate_candidates",
            "input": WORKSHEET_PATH.relative_to(ROOT).as_posix(),
            "output": FIXTURE_PATH.relative_to(ROOT).as_posix(),
        },
    }

    write_json(SELECTION_PATH, selection)
    write_json(FIXTURE_PATH, fixture)
    write_json(REPORT_PATH, report)
    write_worksheet(fixture, selection, report)
    print(json.dumps({
        "status": report["status"],
        "candidate_readiness": ready,
        "selection_summary": selection["summary"],
        "fixture_summary": summary,
        "current_route_measurement": report["current_route_measurement"],
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

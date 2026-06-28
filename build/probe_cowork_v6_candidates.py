"""Probe Cowork raw-log selections and promote useful V6 candidates."""

import json
import re
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from semantic_routing import parse_plm_benchmark, route  # noqa: E402

SELECTION_PATH = ROOT / "build" / "cowork_v6_candidate_selection_v1.json"
REPORT_PATH = ROOT / "build" / "cowork_v6_candidate_probe_report.json"
FIXTURE_PATH = ROOT / "tests" / "fixtures" / "v6_cowork_candidate_fixture_v1.json"
WORKSHEET_PATH = ROOT / "build" / "v6_cowork_candidate_fixture_review_worksheet_v1.md"

LEAK_PATTERN = re.compile(r"https?://|[A-Za-z]:\\|github\.com/kota2461|kota2461/vlte")
PROMOTION_THRESHOLD = 4


def expected(primary_intent: str, operations: list[str], item: dict[str, Any]) -> dict[str, Any]:
    axes = set(item["v6_axes"])
    text = item["redacted_input"]
    must: list[str] = []
    formats: list[str] = []
    risk_flags: list[str] = []
    risk = "low"

    if primary_intent == "clarify" or "clarify_or_explore" in axes:
        must.append("ask_first")
    if ".md" in text or "md" in axes or "write_md" in axes:
        formats.append("markdown")
    if "debug_error" in axes or "security_policy" in axes:
        risk = "medium"
        risk_flags.append("diagnostic_error")
    if "uncertainty" in axes or "evaluate_draft" in axes:
        risk = "medium"
        risk_flags.append("unverified_claim")

    missing = (
        primary_intent == "clarify"
        or "missing_info" in axes
        or "missing_context" in axes
        or "incomplete_input" in axes
        or "scheduling_constraint" in axes
    )
    multiple = (
        len(operations) > 1
        or "compound_intent" in axes
        or "multi_option" in axes
        or "compare_options" in axes
        or "compare_design" in axes
        or "build_rule" in axes
    )
    unverified = "unverified_claim" in axes or "uncertainty" in axes or "evaluate_draft" in axes
    current = "current_tooling" in axes

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
            "response_length": "unspecified",
            "formats": formats,
            "must": must,
            "must_not": [],
        },
        "risk": {
            "level": risk,
            "flags": risk_flags,
        },
        "evidence": [],
        "unknowns": [],
        "conflicts": [],
    }


def packet_dict(text: str) -> dict[str, Any]:
    packet = route(text).packet
    return {
        "primary_intent": packet.primary_intent,
        "operations": list(packet.operations),
        "information_state": packet.information_state.as_dict(),
        "constraints": packet.constraints.as_dict(),
        "risk": packet.risk.as_dict(),
    }


def value_score(item: dict[str, Any], expected_packet: dict[str, Any], actual: dict[str, Any]) -> tuple[int, list[str]]:
    score = 0
    reasons: list[str] = []
    axes = set(item["v6_axes"])

    if item["priority"] == "high":
        score += 2
        reasons.append("high_priority")
    elif item["priority"] == "medium":
        score += 1
        reasons.append("medium_priority")

    if expected_packet["primary_intent"] != "respond":
        score += 2
        reasons.append("non_respond_route")

    expected_ops = set(expected_packet["operations"])
    actual_ops = set(actual["operations"])
    if actual["primary_intent"] != expected_packet["primary_intent"] or not expected_ops <= actual_ops:
        score += 1
        reasons.append("current_route_gap")
    else:
        reasons.append("regression_anchor")

    if 20 <= len(item["redacted_input"]) <= 500:
        score += 1
        reasons.append("compact_self_contained_input")

    if axes & {
        "debug_error",
        "compound_intent",
        "processing_plan",
        "compare_options",
        "compare_design",
        "architecture",
        "build_rule",
        "periodic_review",
        "skill_review",
    }:
        score += 1
        reasons.append("v6_target_axis")

    if expected_packet["primary_intent"] == "respond" and "v6_target_axis" not in reasons:
        score -= 1
        reasons.append("low_value_respond_only")

    return score, reasons


def benchmark_payload(cases: list[dict[str, Any]], generated_at: str) -> dict[str, Any]:
    return {
        "schema_version": "pattern-language-benchmark.v1",
        "frozen_at": generated_at,
        "authoring_method": "Cowork raw-log selection probe; non-sealed, redacted, human review required",
        "review_status": "draft",
        "policy": "Candidate fixture only. No sealed text, sealed labels, or direct raw-log training.",
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


def field_matches(expected_packet: dict[str, Any], actual: dict[str, Any]) -> dict[str, bool]:
    return {
        "primary_intent": actual["primary_intent"] == expected_packet["primary_intent"],
        "operations_subset": set(expected_packet["operations"]) <= set(actual["operations"]),
        "operations_exact": actual["operations"] == expected_packet["operations"],
        "information_state": actual["information_state"] == expected_packet["information_state"],
        "constraints": actual["constraints"] == expected_packet["constraints"],
        "risk": actual["risk"] == expected_packet["risk"],
    }


def summarize_cases(cases: list[dict[str, Any]]) -> dict[str, Any]:
    by_intent = Counter(case["expected"]["primary_intent"] for case in cases)
    by_operation: Counter[str] = Counter()
    by_axis: Counter[str] = Counter()
    by_value_reason: Counter[str] = Counter()
    by_probe_status = Counter(case["probe_status"] for case in cases)
    for case in cases:
        by_operation.update(case["expected"]["operations"])
        by_axis.update(case["axis_ids"])
        by_value_reason.update(case["selection_reasons"])
    return {
        "case_count": len(cases),
        "by_intent": dict(sorted(by_intent.items())),
        "by_operation": dict(sorted(by_operation.items())),
        "by_axis": dict(sorted(by_axis.items())),
        "by_probe_status": dict(sorted(by_probe_status.items())),
        "by_value_reason": dict(sorted(by_value_reason.items())),
    }


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def write_worksheet(payload: dict[str, Any], report: dict[str, Any]) -> None:
    lines = [
        "# V6 Cowork Candidate Fixture Review Worksheet v1",
        "",
        "Non-sealed candidate material from redacted Cowork raw logs. Human review is required before training or gate use.",
        "",
        "## Probe Summary",
        "",
        f"- source_items: {report['summary']['source_items']}",
        f"- promoted_candidates: {report['summary']['promoted_candidates']}",
        f"- intent_accuracy_on_promoted: {report['promoted_probe_metrics']['intent_accuracy']:.3f}",
        f"- operation_subset_rate_on_promoted: {report['promoted_probe_metrics']['operation_subset_rate']:.3f}",
        f"- current_route_gap_count: {report['promoted_probe_metrics']['current_route_gap_count']}",
        "",
        "## Cases",
        "",
        "| id | score | status | intent | operations | axes | input |",
        "| --- | ---: | --- | --- | --- | --- | --- |",
    ]
    for case in payload["cases"]:
        cell_input = case["input"].replace("|", "&#124;").replace("\n", "<br>")
        lines.append(
            "| "
            f"{case['id']} | {case['candidate_value_score']} | {case['probe_status']} | "
            f"{case['expected']['primary_intent']} | {','.join(case['expected']['operations'])} | "
            f"{','.join(case['axis_ids'])} | {cell_input} |"
        )
    WORKSHEET_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def main() -> None:
    generated_at = datetime.now(timezone.utc).isoformat()
    selection = json.loads(SELECTION_PATH.read_text(encoding="utf-8"))
    source_items = [item for item in selection["items"] if item["decision"] == "adopt_nonsealed"]

    all_probes = []
    candidate_cases = []
    redaction_leaks = []

    for index, item in enumerate(source_items, start=1):
        hint = item["suggested_label_hint"]
        operations = list(dict.fromkeys(hint.get("operations") or [hint["primary_intent"]]))
        expected_packet = expected(hint["primary_intent"], operations, item)
        actual = packet_dict(item["redacted_input"])
        matches = field_matches(expected_packet, actual)
        score, reasons = value_score(item, expected_packet, actual)
        leak = bool(LEAK_PATTERN.search(item["redacted_input"]))
        if leak:
            redaction_leaks.append(item["id"])
        probe_status = "route_matches_hint" if matches["primary_intent"] and matches["operations_subset"] else "route_gap"
        probe = {
            "source_candidate_id": item["id"],
            "priority": item["priority"],
            "axis_ids": item["v6_axes"],
            "input": item["redacted_input"],
            "expected": expected_packet,
            "actual": actual,
            "field_matches": matches,
            "candidate_value_score": score,
            "selection_reasons": reasons,
            "probe_status": probe_status,
            "redaction_leak": leak,
        }
        all_probes.append(probe)
        if not leak and score >= PROMOTION_THRESHOLD:
            candidate_cases.append(
                {
                    "id": f"v6-cowork-candidate-{len(candidate_cases) + 1:03d}",
                    "review_status": "draft",
                    "split": "validation",
                    "source_group": "v6-cowork-nonsealed-candidate-draft",
                    "source_kind": "cowork_raw_log_redacted_candidate",
                    "source_ref": "build/cowork_v6_candidate_selection_v1.json",
                    "source_candidate_id": item["id"],
                    "axis_ids": item["v6_axes"],
                    "language": "ja",
                    "input": item["redacted_input"],
                    "expected": expected_packet,
                    "candidate_value_score": score,
                    "selection_reasons": reasons,
                    "probe_status": probe_status,
                    "current_route": actual,
                    "notes": "Draft candidate from redacted non-sealed Cowork raw logs. Human review required before training or gate use.",
                }
            )

    intent_ok = sum(probe["field_matches"]["primary_intent"] for probe in all_probes)
    op_subset_ok = sum(probe["field_matches"]["operations_subset"] for probe in all_probes)
    promoted_intent_ok = sum(case["current_route"]["primary_intent"] == case["expected"]["primary_intent"] for case in candidate_cases)
    promoted_op_subset_ok = sum(set(case["expected"]["operations"]) <= set(case["current_route"]["operations"]) for case in candidate_cases)
    promoted_gap_count = sum(case["probe_status"] == "route_gap" for case in candidate_cases)
    distinct_promoted_intents = sorted({case["expected"]["primary_intent"] for case in candidate_cases})
    ready = (
        not redaction_leaks
        and len(candidate_cases) >= 18
        and len(distinct_promoted_intents) >= 5
        and promoted_gap_count >= 8
    )

    fixture = {
        "schema_version": "v6-cowork-candidate-fixture.v1",
        "fixture_id": "v6-cowork-candidate-fixture-v1",
        "created_at": generated_at,
        "status": "draft_candidate_ready_for_human_review" if ready else "draft_candidate_probe_only",
        "review_status": "draft",
        "source_selection": str(SELECTION_PATH.relative_to(ROOT)),
        "policy": {
            "sealed_fixtures_used_as_sources": False,
            "sealed_text_used": False,
            "sealed_labels_used": False,
            "raw_logs_direct_training_allowed": False,
            "redacted_inputs_only": True,
            "human_review_required_before_training": True,
            "human_review_required_before_gate": True,
            "same_cycle_promotion_allowed": False,
        },
        "requirements": {
            "candidate_value_score_min": PROMOTION_THRESHOLD,
            "min_promoted_candidates": 18,
            "min_distinct_intents": 5,
            "min_current_route_gap_count": 8,
        },
        "summary": summarize_cases(candidate_cases),
        "cases": candidate_cases,
    }

    report = {
        "schema_version": "v6-cowork-candidate-probe-report.v1",
        "generated_at": generated_at,
        "source_selection": str(SELECTION_PATH.relative_to(ROOT)),
        "fixture": str(FIXTURE_PATH.relative_to(ROOT)),
        "worksheet": str(WORKSHEET_PATH.relative_to(ROOT)),
        "status": "promoted_to_candidate_fixture" if ready else "probe_only_not_promoted",
        "candidate_readiness": ready,
        "policy": fixture["policy"],
        "summary": {
            "source_items": len(source_items),
            "redaction_leak_count": len(redaction_leaks),
            "redaction_leaks": redaction_leaks,
            "promoted_candidates": len(candidate_cases),
            "rejected_by_probe": len(source_items) - len(candidate_cases),
            "distinct_promoted_intents": distinct_promoted_intents,
        },
        "source_probe_metrics": {
            "intent_accuracy": intent_ok / len(all_probes) if all_probes else 0.0,
            "operation_subset_rate": op_subset_ok / len(all_probes) if all_probes else 0.0,
            "current_route_gap_count": sum(probe["probe_status"] == "route_gap" for probe in all_probes),
        },
        "promoted_probe_metrics": {
            "intent_accuracy": promoted_intent_ok / len(candidate_cases) if candidate_cases else 0.0,
            "operation_subset_rate": promoted_op_subset_ok / len(candidate_cases) if candidate_cases else 0.0,
            "current_route_gap_count": promoted_gap_count,
        },
        "all_probes": all_probes,
        "next_step": {
            "name": "human_review_v6_cowork_candidates",
            "input": str(WORKSHEET_PATH.relative_to(ROOT)),
            "output": "tests\\fixtures\\v6_cowork_candidate_fixture_v1.json",
        },
    }

    parse_plm_benchmark(benchmark_payload(candidate_cases, generated_at))
    write_json(FIXTURE_PATH, fixture)
    write_json(REPORT_PATH, report)
    write_worksheet(fixture, report)
    print(json.dumps({
        "status": report["status"],
        "candidate_readiness": ready,
        "summary": report["summary"],
        "source_probe_metrics": report["source_probe_metrics"],
        "promoted_probe_metrics": report["promoted_probe_metrics"],
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

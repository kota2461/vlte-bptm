"""Create a V9 non-sealed extension for constraint/operation exactness.

This lane is user-approved for diagnostic replay only. It strengthens coverage
for explicit constraints and terminal operation ordering without consuming sealed
fixtures or promoting in the same cycle.
"""

import json
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from semantic_routing import evaluate_plm_extractor, parse_plm_benchmark, route  # noqa: E402

BENCHMARK_PATH = ROOT / "tests" / "fixtures" / "v9_constraint_operation_extension_benchmark_v1.json"
REPORT_PATH = ROOT / "build" / "v9_constraint_operation_extension_replay_report_v1.json"
WORKSHEET_PATH = ROOT / "build" / "v9_constraint_operation_extension_worksheet_v1.md"

POLICY = {
    "sealed_fixtures_used_as_sources": False,
    "sealed_text_used": False,
    "sealed_labels_used": False,
    "raw_debate_logs_direct_training_allowed": False,
    "llm_turn_text_direct_training_allowed": False,
    "synthetic_short_samples_used": True,
    "human_review_confirmation_recorded": True,
    "same_cycle_promotion_allowed": False,
    "current_route_measurement_is_gate": False,
    "adopted_benchmark_is_directly_trainable": False,
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


CASES: list[dict[str, Any]] = [
    {
        "id": "v9-constraint-operation-extension-001",
        "category": "constraints",
        "topic": "short_bullets_no_table",
        "target_fields": ["constraints"],
        "input": "Briefly list three deployment risks as bullet points, no table.",
        "expected": expected("summarize", ["summarize"], response_length="short", formats=["bullets"], must_not=["no_table"]),
    },
    {
        "id": "v9-constraint-operation-extension-002",
        "category": "constraints",
        "topic": "json_only",
        "target_fields": ["constraints"],
        "input": "Return only JSON with keys action and reason; do not add prose.",
        "expected": expected("build", ["build"], formats=["json"]),
    },
    {
        "id": "v9-constraint-operation-extension-003",
        "category": "constraints",
        "topic": "ask_first_before_edit",
        "target_fields": ["constraints", "information_state"],
        "input": "Before editing the README, ask which section I want changed.",
        "expected": expected("clarify", ["clarify"], missing=True, must=["ask_first"]),
    },
    {
        "id": "v9-constraint-operation-extension-004",
        "category": "constraints",
        "topic": "do_not_store_memory",
        "target_fields": ["constraints"],
        "input": "Draft the reply but do not store this personal note as memory.",
        "expected": expected("build", ["build"], must_not=["do_not_store"]),
    },
    {
        "id": "v9-constraint-operation-extension-005",
        "category": "constraints",
        "topic": "cite_and_avoid_overclaim",
        "target_fields": ["constraints", "risk", "information_state"],
        "input": "Verify this vendor claim with sources and avoid overclaiming: the router is 30% more accurate.",
        "expected": expected(
            "verify",
            ["verify"],
            unverified=True,
            must=["cite_sources", "avoid_overclaim"],
            risk="medium",
            risk_flags=["unverified_claim"],
        ),
    },
    {
        "id": "v9-constraint-operation-extension-006",
        "category": "constraints",
        "topic": "general_legal_explanation",
        "target_fields": ["constraints"],
        "input": "Explain Apache 2.0 as general information only; this is not legal advice.",
        "expected": expected("explain", ["explain"], must=["general_information_only"]),
    },
    {
        "id": "v9-constraint-operation-extension-007",
        "category": "constraints",
        "topic": "medical_ui_no_diagnosis",
        "target_fields": ["constraints"],
        "input": "Design a medical AI screen layout without diagnosis or treatment advice.",
        "expected": expected("build", ["build"], must=["avoid_diagnosis"]),
    },
    {
        "id": "v9-constraint-operation-extension-008",
        "category": "constraints",
        "topic": "tone_avoid_overclaim",
        "target_fields": ["constraints"],
        "input": "Answer in a friendly but precise tone and avoid overstating the evidence.",
        "expected": expected("respond", ["respond"], must=["avoid_overclaim"]),
    },
    {
        "id": "v9-constraint-operation-extension-009",
        "category": "constraints",
        "topic": "local_notes_no_web",
        "target_fields": ["constraints"],
        "input": "Use only the local notes below; no web search is needed. Notes: v9 repair passed.",
        "expected": expected("summarize", ["summarize"], must_not=["no_web_search"]),
    },
    {
        "id": "v9-constraint-operation-extension-010",
        "category": "constraints",
        "topic": "table_required",
        "target_fields": ["constraints"],
        "input": "Create a comparison table for these options: A is cheaper, B is safer.",
        "expected": expected("build", ["build"], formats=["table"]),
    },
    {
        "id": "v9-constraint-operation-extension-011",
        "category": "constraints",
        "topic": "one_short_sentence",
        "target_fields": ["constraints"],
        "input": "Give exactly one short sentence explaining the result.",
        "expected": expected("explain", ["explain"], response_length="short"),
    },
    {
        "id": "v9-constraint-operation-extension-012",
        "category": "constraints",
        "topic": "neutral_summary",
        "target_fields": ["constraints"],
        "input": "Summarize both sides neutrally without choosing a winner.",
        "expected": expected("summarize", ["summarize"], must=["preserve_neutrality"]),
    },
    {
        "id": "v9-constraint-operation-extension-013",
        "category": "operation_terminal",
        "topic": "summarize_only",
        "target_fields": ["operations"],
        "input": "Summarize the failure list into three key points.",
        "expected": expected("summarize", ["summarize"]),
    },
    {
        "id": "v9-constraint-operation-extension-014",
        "category": "operation_terminal",
        "topic": "classify_table",
        "target_fields": ["operations", "constraints"],
        "input": "Classify each log row as keep or review in a table.",
        "expected": expected("build", ["build"], formats=["table"]),
    },
    {
        "id": "v9-constraint-operation-extension-015",
        "category": "operation_terminal",
        "topic": "clarify_before_table_build",
        "target_fields": ["operations", "information_state", "constraints"],
        "input": "Make a migration table, but the source columns are not provided.",
        "expected": expected("clarify", ["clarify", "build"], missing=True, multiple=True, formats=["table"], must=["ask_first"]),
    },
    {
        "id": "v9-constraint-operation-extension-016",
        "category": "operation_terminal",
        "topic": "verify_then_release_note",
        "target_fields": ["operations", "information_state", "risk"],
        "input": "Verify the security claim, then write a short release note.",
        "expected": expected(
            "build",
            ["build", "verify"],
            unverified=True,
            multiple=True,
            response_length="short",
            risk="medium",
            risk_flags=["security", "unverified_claim"],
        ),
    },
    {
        "id": "v9-constraint-operation-extension-017",
        "category": "operation_terminal",
        "topic": "explain_general",
        "target_fields": ["operations", "constraints"],
        "input": "Explain what Apache 2.0 means at a general level.",
        "expected": expected("explain", ["explain"], must=["general_information_only"]),
    },
    {
        "id": "v9-constraint-operation-extension-018",
        "category": "operation_terminal",
        "topic": "compare_recommend",
        "target_fields": ["operations"],
        "input": "Compare the two router designs and recommend one.",
        "expected": expected("explore", ["explore", "compare"]),
    },
    {
        "id": "v9-constraint-operation-extension-019",
        "category": "operation_terminal",
        "topic": "calculate_verify",
        "target_fields": ["operations"],
        "input": "Calculate whether 42 + 58 equals 100.",
        "expected": expected("verify", ["verify", "calculate"]),
    },
    {
        "id": "v9-constraint-operation-extension-020",
        "category": "operation_terminal",
        "topic": "current_search_cite",
        "target_fields": ["operations", "information_state", "constraints", "risk"],
        "input": "Search for the latest Node.js LTS version and cite the source.",
        "expected": expected(
            "verify",
            ["verify", "search"],
            current=True,
            must=["cite_sources", "avoid_overclaim"],
            risk="medium",
            risk_flags=["current_information"],
        ),
    },
    {
        "id": "v9-constraint-operation-extension-021",
        "category": "operation_terminal",
        "topic": "build_checklist",
        "target_fields": ["operations", "constraints"],
        "input": "Build a checklist of fixes for the route gaps.",
        "expected": expected("build", ["build"], formats=["bullets"]),
    },
    {
        "id": "v9-constraint-operation-extension-022",
        "category": "operation_terminal",
        "topic": "review_then_terminal_summary",
        "target_fields": ["operations", "constraints"],
        "input": "Review the draft and summarize only the blocking issues.",
        "expected": expected("summarize", ["summarize", "verify"], multiple=True, must=["avoid_overclaim"]),
    },
    {
        "id": "v9-constraint-operation-extension-023",
        "category": "operation_terminal",
        "topic": "checked_json_plan",
        "target_fields": ["operations", "constraints"],
        "input": "Create the JSON patch plan after checking the assumptions.",
        "expected": expected("build", ["build", "verify"], multiple=True, formats=["json"]),
    },
    {
        "id": "v9-constraint-operation-extension-024",
        "category": "operation_terminal",
        "topic": "extract_classify_summarize_counts",
        "target_fields": ["operations", "information_state"],
        "input": "Extract candidate IDs, classify each as keep or rerun, and summarize counts.",
        "expected": expected("build", ["build", "summarize", "calculate"], multiple=True),
    },
]


def _rel(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def _benchmark_payload(generated_at: str) -> dict[str, Any]:
    return {
        "schema_version": "pattern-language-benchmark.v1",
        "frozen_at": generated_at,
        "authoring_method": "User-requested V9 non-sealed focused extension for constraint_exact_match and operation_exact_match.",
        "review_status": "human_reviewed",
        "policy": (
            "Human-reviewed non-sealed replay lane. No sealed text or labels used. "
            "Samples are short self-contained router repair probes, not gate evidence and not same-cycle promotion evidence."
        ),
        "cases": [
            {
                "id": case["id"],
                "split": "validation",
                "source_group": "v9-constraint-operation-extension-nonsealed",
                "contrast_group": case["category"],
                "language": "en",
                "input": case["input"],
                "expected": case["expected"],
            }
            for case in CASES
        ],
    }


def _compact_measurement(measurement: dict[str, Any]) -> dict[str, Any]:
    field_counts = Counter(field for error in measurement["errors"] for field in error.get("fields", []))
    return {
        "case_count": measurement["case_count"],
        "valid_packet_rate": measurement["valid_packet_rate"],
        "intent_accuracy": measurement["intent_accuracy"],
        "intent_macro_f1": measurement["intent_macro_f1"],
        "critical_signal_recall": measurement["critical_signal_recall"],
        "operation_exact_match": measurement["operation_exact_match"],
        "constraint_exact_match": measurement["constraint_exact_match"],
        "risk_exact_match": measurement["risk_exact_match"],
        "evidence_offset_validity": measurement["evidence_offset_validity"],
        "error_count": len(measurement["errors"]),
        "error_field_counts": dict(sorted(field_counts.items())),
    }


def _packet_summary(packet: Any) -> dict[str, Any]:
    return {
        "primary_intent": packet.primary_intent,
        "operations": list(packet.operations),
        "information_state": packet.information_state.as_dict(),
        "constraints": packet.constraints.as_dict(),
        "risk": packet.risk.as_dict(),
    }


def _mismatch_fields(expected_packet: dict[str, Any], actual: dict[str, Any]) -> list[str]:
    fields: list[str] = []
    if expected_packet["primary_intent"] != actual["primary_intent"]:
        fields.append("primary_intent")
    for field in ("operations", "information_state", "constraints", "risk"):
        if expected_packet[field] != actual[field]:
            fields.append(field)
    return fields


def _case_results(parsed_cases: Sequence[Any]) -> list[dict[str, Any]]:
    by_id = {case["id"]: case for case in CASES}
    results = []
    for parsed_case in parsed_cases:
        source = by_id[parsed_case.case_id]
        actual = _packet_summary(route(parsed_case.input_text).packet)
        expected_packet = parsed_case.expected.as_dict()
        fields = _mismatch_fields(expected_packet, actual)
        results.append(
            {
                "case_id": parsed_case.case_id,
                "category": source["category"],
                "topic": source["topic"],
                "target_fields": source["target_fields"],
                "input": parsed_case.input_text,
                "mismatch_fields": fields,
                "expected": expected_packet,
                "actual": actual,
            }
        )
    return results


def _category_summary(results: Sequence[dict[str, Any]]) -> dict[str, Any]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for result in results:
        grouped[result["category"]].append(result)
    summary = {}
    for category, items in sorted(grouped.items()):
        fields = Counter(field for item in items for field in item["mismatch_fields"])
        summary[category] = {
            "case_count": len(items),
            "exact_case_match": sum(1 for item in items if not item["mismatch_fields"]),
            "intent_accuracy": sum(item["expected"]["primary_intent"] == item["actual"]["primary_intent"] for item in items) / len(items),
            "operation_exact_match": sum(item["expected"]["operations"] == item["actual"]["operations"] for item in items) / len(items),
            "constraint_exact_match": sum(item["expected"]["constraints"] == item["actual"]["constraints"] for item in items) / len(items),
            "risk_exact_match": sum(item["expected"]["risk"] == item["actual"]["risk"] for item in items) / len(items),
            "mismatch_field_counts": dict(sorted(fields.items())),
        }
    return summary


def _summary() -> dict[str, Any]:
    return {
        "case_count": len(CASES),
        "by_category": dict(sorted(Counter(case["category"] for case in CASES).items())),
        "by_expected_intent": dict(sorted(Counter(case["expected"]["primary_intent"] for case in CASES).items())),
        "by_target_field": dict(sorted(Counter(field for case in CASES for field in case["target_fields"]).items())),
        "focused_targets": ["constraint_exact_match", "operation_exact_match"],
    }


def _write_worksheet(report: dict[str, Any]) -> None:
    lines = [
        "# V9 Constraint/Operation Extension Worksheet v1",
        "",
        "## Summary",
        "",
    ]
    for key, value in report["measurement"].items():
        lines.append(f"- {key}: {value}")
    lines.extend(
        [
            "",
            "## Coverage",
            "",
            f"- constraints cases: {report['summary']['by_category']['constraints']}",
            f"- operation_terminal cases: {report['summary']['by_category']['operation_terminal']}",
            f"- target fields: {report['summary']['by_target_field']}",
            "",
            "## Candidate Replay",
            "",
            "| case | category | topic | fields | expected | actual | input |",
            "|---|---|---|---|---|---|---|",
        ]
    )
    for result in report["case_results"]:
        expected = result["expected"]
        actual = result["actual"]
        expected_summary = f"{expected['primary_intent']} / {expected['operations']} / {expected['constraints']}"
        actual_summary = f"{actual['primary_intent']} / {actual['operations']} / {actual['constraints']}"
        fields = ", ".join(result["mismatch_fields"]) if result["mismatch_fields"] else "ok"
        safe_input = result["input"].replace("|", "\\|")
        lines.append(
            f"| {result['case_id']} | {result['category']} | {result['topic']} | {fields} | {expected_summary} | {actual_summary} | {safe_input} |"
        )
    lines.extend(
        [
            "",
            "## Contract",
            "",
            "- sealed_fixture_used: false",
            "- current_route_measurement_is_gate: false",
            "- raw_debate_logs_direct_training_allowed: false",
            "- same_cycle_promotion_allowed: false",
        ]
    )
    WORKSHEET_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def main() -> None:
    generated_at = datetime.now(timezone.utc).isoformat()
    benchmark = _benchmark_payload(generated_at)
    parsed = parse_plm_benchmark(benchmark)
    measurement_raw = evaluate_plm_extractor(parsed.cases, lambda text: route(text).packet)
    measurement = _compact_measurement(measurement_raw)
    results = _case_results(parsed.cases)
    has_gaps = bool(measurement["error_count"])
    report = {
        "schema_version": "v9-constraint-operation-extension-replay-report.v1",
        "generated_at": generated_at,
        "status": "completed_without_route_gaps" if not has_gaps else "completed_with_route_gaps",
        "adopted_benchmark": _rel(BENCHMARK_PATH),
        "worksheet": _rel(WORKSHEET_PATH),
        "current_route_measurement_is_gate": False,
        "sealed_fixture_used": False,
        "policy": POLICY,
        "summary": _summary(),
        "measurement": measurement,
        "category_summary": _category_summary(results),
        "errors": measurement_raw["errors"],
        "case_results": results,
        "interpretation": (
            "The focused extension currently matches route(). It remains non-sealed replay evidence, not sealed evidence."
            if not has_gaps
            else "The focused extension exposes current route gaps and should be repaired before adoption as a stable replay lane."
        ),
        "next_step": "v9_nonsealed_replay_gate_candidate" if not has_gaps else "v9_constraint_operation_router_repair",
    }
    _write_json(BENCHMARK_PATH, benchmark)
    _write_json(REPORT_PATH, report)
    _write_worksheet(report)
    print(json.dumps({
        "status": report["status"],
        "case_count": len(CASES),
        "benchmark": _rel(BENCHMARK_PATH),
        "replay_report": _rel(REPORT_PATH),
        "measurement": measurement,
        "next_step": report["next_step"],
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

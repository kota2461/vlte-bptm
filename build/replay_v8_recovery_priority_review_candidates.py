"""Create and replay the V8 recovery priority-review candidate lane.

The user confirmed the balanced 30-candidate priority queue can proceed to a
provisional test. This script rewrites each selected topic into a short
self-contained non-sealed sample and measures the current router with route().

This is not a sealed fixture, not gate evidence, and not direct training data.
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


SOURCE_PRIORITY_PATH = ROOT / "build" / "v8_recovery_debate_candidate_priority_selection_v1.json"
BENCHMARK_PATH = ROOT / "tests" / "fixtures" / "v8_recovery_priority_review_candidate_benchmark_v1.json"
REPORT_PATH = ROOT / "build" / "v8_recovery_priority_review_provisional_test_report_v1.json"
WORKSHEET_PATH = ROOT / "build" / "v8_recovery_priority_review_candidate_worksheet_v1.md"

POLICY = {
    "sealed_fixtures_used_as_sources": False,
    "sealed_text_used": False,
    "sealed_labels_used": False,
    "raw_debate_logs_direct_training_allowed": False,
    "llm_turn_text_direct_training_allowed": False,
    "topic_metadata_synthesis_used": True,
    "human_review_confirmation_recorded": True,
    "same_cycle_promotion_allowed": False,
    "current_route_measurement_is_gate": False,
    "candidate_benchmark_is_directly_trainable": False,
}

CRITICAL_SIGNALS = (
    "missing_required_information",
    "contains_unverified_claims",
    "requires_current_information",
    "multiple_intents",
)


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


CASE_DEFINITIONS: dict[str, dict[str, Any]] = {
    "v8-constraints-01-short-no-table": {
        "language": "en",
        "input": "Briefly explain cache keys in two bullet points, no table.",
        "expected": expected("explain", ["explain"], response_length="short", formats=["bullets"], must_not=["no_table"]),
    },
    "v8-constraints-02-neutral-no-diagnosis": {
        "language": "en",
        "input": "For a Medical AI UI layout, give neutral design notes without diagnosis or treatment advice.",
        "expected": expected("build", ["build"], must=["preserve_neutrality", "avoid_diagnosis"]),
    },
    "v8-constraints-03-cite-no-overclaim": {
        "language": "en",
        "input": "Verify whether the claim 'this license allows every commercial use' is accurate; cite sources and avoid overclaiming.",
        "expected": expected(
            "verify",
            ["verify", "search"],
            unverified=True,
            must=["cite_sources", "avoid_overclaim"],
            risk="medium",
            risk_flags=["license", "unverified_claim"],
        ),
    },
    "v8-current_search_split-01-current-folder-local": {
        "language": "en",
        "input": "Give the PowerShell command to show the current folder. Do not search the web.",
        "expected": expected("build", ["build"], must_not=["no_web_search"]),
    },
    "v8-current_search_split-02-today-log-local": {
        "language": "en",
        "input": "Summarize today's local conversation log below; do not use external news. Log: backup done; V8 debate ran.",
        "expected": expected("summarize", ["summarize"], must_not=["no_web_search"]),
    },
    "v8-current_search_split-03-latest-filename-label": {
        "language": "en",
        "input": "Add a field named latest_result_file to the JSON schema; it is just a filename label.",
        "expected": expected("build", ["build"]),
    },
    "v8-false_positive-01-ai-tag": {
        "language": "en",
        "input": "Add the tag AI to the label list.",
        "expected": expected("build", ["build"]),
    },
    "v8-false_positive-02-medical-column": {
        "language": "en",
        "input": "Create a CSV column named medical_flag.",
        "expected": expected("build", ["build"]),
    },
    "v8-false_positive-03-legal-heading": {
        "language": "en",
        "input": "Add a README heading called Legal Notes.",
        "expected": expected("build", ["build"]),
    },
    "v8-missing_info-01-rewrite-missing-text": {
        "language": "en",
        "input": "Please rewrite the text, but I have not pasted the text yet.",
        "expected": expected("clarify", ["clarify"], missing=True),
    },
    "v8-missing_info-02-compare-missing-options": {
        "language": "en",
        "input": "Compare option A and option B, but I have not described either option.",
        "expected": expected("clarify", ["clarify", "compare"], missing=True, multiple=True),
    },
    "v8-missing_info-03-summarize-missing-log": {
        "language": "en",
        "input": "Summarize the log, but no log is attached.",
        "expected": expected("clarify", ["clarify", "summarize"], missing=True, multiple=True),
    },
    "v8-mixed_language-05-no-table-neutral": {
        "language": "en",
        "input": "Use neutral tone, short answer, no table: explain this policy.",
        "expected": expected("explain", ["explain"], response_length="short", must=["preserve_neutrality"], must_not=["no_table"]),
    },
    "v8-mixed_language-01-ai-persona-label": {
        "language": "mixed",
        "input": "READMEに 'AI persona' label を追加してください。人格相談ではなくmetadata整理です。",
        "expected": expected("build", ["build"]),
    },
    "v8-mixed_language-02-apache-brief": {
        "language": "en",
        "input": "Briefly explain the Apache 2.0 license at a general level. No legal advice.",
        "expected": expected("explain", ["explain"], response_length="short"),
    },
    "v8-multiple_intents-01-verify-then-build": {
        "language": "en",
        "input": "Verify the vendor's security claim, then draft a short release-note sentence.",
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
    "v8-multiple_intents-02-summarize-then-compare": {
        "language": "en",
        "input": "Summarize these notes, then compare the two approaches in a table: A is cheaper; B is safer.",
        "expected": expected("summarize", ["summarize", "compare"], multiple=True, formats=["table"]),
    },
    "v8-multiple_intents-03-extract-then-classify": {
        "language": "en",
        "input": "From these logs, extract candidate IDs, classify each as keep or review, and summarize them in a table: id1 ok; id2 unclear.",
        "expected": expected("build", ["build", "summarize"], multiple=True, formats=["table"]),
    },
    "v8-operation_terminal-01-respond-vs-build": {
        "language": "en",
        "input": "Create a route checklist item for respond-vs-build decisions in one short sentence.",
        "expected": expected("build", ["build"], response_length="short"),
    },
    "v8-operation_terminal-02-explain-vs-verify": {
        "language": "en",
        "input": "What is Apache 2.0 in general? No current legal advice is needed.",
        "expected": expected("explain", ["explain"]),
    },
    "v8-operation_terminal-04-build-vs-clarify": {
        "language": "en",
        "input": "Create the migration table, but the source data is missing.",
        "expected": expected("clarify", ["clarify", "build"], missing=True, multiple=True, formats=["table"]),
    },
    "v8-paraphrase-05-unverified-report-variants": {
        "language": "en",
        "input": "Before adding this number to the report, check whether 42 incidents is correct.",
        "expected": expected("verify", ["verify"], unverified=True, risk="medium", risk_flags=["unverified_claim"]),
    },
    "v8-paraphrase-06-missing-text-variants": {
        "language": "en",
        "input": "Could you polish this? I forgot to attach the paragraph.",
        "expected": expected("clarify", ["clarify"], missing=True),
    },
    "v8-paraphrase-01-ai-comfort-variants": {
        "language": "en",
        "input": "I chat with AI to relax after work; note it as a light-use example, not a dependence warning.",
        "expected": expected("build", ["build"]),
    },
    "v8-risk_ladder-01-ai-light-comfort": {
        "language": "en",
        "input": "Summarize this as a light AI-use example: chatting with AI helps me relax, not dependence.",
        "expected": expected("summarize", ["summarize"]),
    },
    "v8-risk_ladder-03-medical-ui-low": {
        "language": "en",
        "input": "Design a Medical AI dashboard layout without diagnosis; this is UI design.",
        "expected": expected("build", ["build"], must=["avoid_diagnosis"]),
    },
    "v8-risk_ladder-04-medical-personal-symptom": {
        "language": "en",
        "input": "I have chest pain and want medication dosage advice; verify safety before answering.",
        "expected": expected("verify", ["verify"], unverified=True, risk="high", risk_flags=["medical", "unverified_claim"]),
    },
    "v8-unverified_claim-01-vendor-security-claim": {
        "language": "en",
        "input": "The vendor claims the vulnerability is fixed; verify before we tell users.",
        "expected": expected("verify", ["verify"], unverified=True, risk="high", risk_flags=["security", "unverified_claim"]),
    },
    "v8-unverified_claim-03-report-number-check": {
        "language": "en",
        "input": "Check whether the report total 128 equals 64 + 64 before publishing.",
        "expected": expected("verify", ["verify", "calculate"], unverified=True),
    },
    "v8-unverified_claim-05-legal-template-claim": {
        "language": "en",
        "input": "This contract template is said to be legally valid; explain only generally and say it needs professional review.",
        "expected": expected(
            "explain",
            ["explain", "verify"],
            unverified=True,
            must=["general_information_only", "avoid_overclaim"],
            risk="high",
            risk_flags=["legal", "unverified_claim"],
        ),
    },
}


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def benchmark_cases(priority_records: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    selected_topic_ids = [record["source_topic_id"] for record in priority_records]
    missing = [topic_id for topic_id in selected_topic_ids if topic_id not in CASE_DEFINITIONS]
    unused = [topic_id for topic_id in CASE_DEFINITIONS if topic_id not in selected_topic_ids]
    if missing:
        raise ValueError(f"missing V8 provisional case definition: {missing[0]}")
    if unused:
        raise ValueError(f"unused V8 provisional case definition: {unused[0]}")

    cases = []
    for index, record in enumerate(priority_records, start=1):
        definition = CASE_DEFINITIONS[record["source_topic_id"]]
        cases.append(
            {
                "id": f"v8-recovery-priority-review-{index:03d}",
                "split": "validation",
                "source_group": "v8-recovery-priority-review-candidate-nonsealed",
                "contrast_group": record["category"],
                "language": definition["language"],
                "input": definition["input"],
                "expected": definition["expected"],
            }
        )
    return cases


def benchmark_payload(priority_records: Sequence[dict[str, Any]], generated_at: str) -> dict[str, Any]:
    return {
        "schema_version": "pattern-language-benchmark.v1",
        "frozen_at": generated_at,
        "authoring_method": (
            "Human-confirmed V8 priority queue rewritten into short self-contained "
            "non-sealed samples from topic metadata; raw debate prose excluded"
        ),
        "review_status": "human_reviewed",
        "policy": (
            "Provisional non-sealed replay lane. Raw Gemma/Qwen debate turns are not training data. "
            "This is not a sealed fixture, not gate evidence, and not same-cycle promotion evidence."
        ),
        "cases": benchmark_cases(priority_records),
    }


def compact_measurement(measurement: dict[str, Any]) -> dict[str, Any]:
    error_fields = Counter(field for error in measurement["errors"] for field in error.get("fields", []))
    return {
        "case_count": measurement["case_count"],
        "valid_packet_rate": measurement["valid_packet_rate"],
        "intent_accuracy": measurement["intent_accuracy"],
        "intent_macro_f1": measurement["intent_macro_f1"],
        "critical_signal_recall": measurement["critical_signal_recall"],
        "operation_exact_match": measurement["operation_exact_match"],
        "constraint_exact_match": measurement["constraint_exact_match"],
        "risk_exact_match": measurement["risk_exact_match"],
        "error_count": len(measurement["errors"]),
        "error_field_counts": dict(sorted(error_fields.items())),
    }


def packet_summary(packet: Any) -> dict[str, Any]:
    return {
        "primary_intent": packet.primary_intent,
        "operations": list(packet.operations),
        "information_state": packet.information_state.as_dict(),
        "constraints": packet.constraints.as_dict(),
        "risk": packet.risk.as_dict(),
        "confidence": packet.confidence,
    }


def expected_summary(case: Any) -> dict[str, Any]:
    return case.expected.as_dict()


def mismatch_fields(expected_packet: dict[str, Any], actual_packet: dict[str, Any]) -> list[str]:
    fields = []
    if expected_packet["primary_intent"] != actual_packet["primary_intent"]:
        fields.append("primary_intent")
    if expected_packet["operations"] != actual_packet["operations"]:
        fields.append("operations")
    if expected_packet["information_state"] != actual_packet["information_state"]:
        fields.append("information_state")
    if expected_packet["constraints"] != actual_packet["constraints"]:
        fields.append("constraints")
    if expected_packet["risk"] != actual_packet["risk"]:
        fields.append("risk")
    return fields


def case_results(priority_records: Sequence[dict[str, Any]], parsed_cases: Sequence[Any]) -> list[dict[str, Any]]:
    results = []
    for record, case in zip(priority_records, parsed_cases):
        packet = route(case.input_text).packet
        expected_packet = expected_summary(case)
        actual_packet = packet_summary(packet)
        fields = mismatch_fields(expected_packet, actual_packet)
        results.append(
            {
                "case_id": case.case_id,
                "source_topic_id": record["source_topic_id"],
                "category": record["category"],
                "input": case.input_text,
                "expected": expected_packet,
                "actual": actual_packet,
                "mismatch_fields": fields,
                "matched": not fields,
            }
        )
    return results


def category_summary(results: Sequence[dict[str, Any]]) -> dict[str, Any]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for result in results:
        grouped[result["category"]].append(result)

    summary = {}
    for category, items in sorted(grouped.items()):
        total = len(items)
        field_counts = Counter(field for item in items for field in item["mismatch_fields"])
        summary[category] = {
            "case_count": total,
            "exact_case_match": sum(1 for item in items if item["matched"]),
            "intent_accuracy": round(sum("primary_intent" not in item["mismatch_fields"] for item in items) / total, 6),
            "operation_exact_match": round(sum("operations" not in item["mismatch_fields"] for item in items) / total, 6),
            "information_state_exact_match": round(sum("information_state" not in item["mismatch_fields"] for item in items) / total, 6),
            "constraint_exact_match": round(sum("constraints" not in item["mismatch_fields"] for item in items) / total, 6),
            "risk_exact_match": round(sum("risk" not in item["mismatch_fields"] for item in items) / total, 6),
            "mismatch_field_counts": dict(sorted(field_counts.items())),
        }
    return summary


def lane_summary(priority_records: Sequence[dict[str, Any]], cases: Sequence[dict[str, Any]]) -> dict[str, Any]:
    by_category = Counter(record["category"] for record in priority_records)
    by_intent = Counter(case["expected"]["primary_intent"] for case in cases)
    by_risk = Counter(case["expected"]["risk"]["level"] for case in cases)
    signal_support = Counter()
    for case in cases:
        for signal, value in case["expected"]["information_state"].items():
            if value:
                signal_support[signal] += 1
    return {
        "candidate_count": len(priority_records),
        "by_category": dict(sorted(by_category.items())),
        "by_expected_intent": dict(sorted(by_intent.items())),
        "by_expected_risk": dict(sorted(by_risk.items())),
        "critical_signal_support": {signal: signal_support.get(signal, 0) for signal in CRITICAL_SIGNALS},
    }


def write_worksheet(report: dict[str, Any], results: Sequence[dict[str, Any]]) -> None:
    lines = [
        "# V8 Recovery Priority Review Candidate Worksheet v1",
        "",
        "Human-confirmed non-sealed provisional replay candidates.",
        "Raw debate turns are not training data and are not copied into these samples.",
        "",
        "## Summary",
        "",
    ]
    for key, value in report["measurement"].items():
        lines.append(f"- {key}: {value}")
    lines.extend(
        [
            "",
            "## Candidate Replay",
            "",
            "| case | category | topic | fields | expected | actual | input |",
            "|---|---|---|---|---|---|---|",
        ]
    )
    for result in results:
        fields = ",".join(result["mismatch_fields"]) or "-"
        expected_label = f"{result['expected']['primary_intent']}:{result['expected']['risk']['level']}"
        actual_label = f"{result['actual']['primary_intent']}:{result['actual']['risk']['level']}"
        text = result["input"].replace("|", "&#124;")
        lines.append(
            f"| {result['case_id']} | {result['category']} | {result['source_topic_id']} | "
            f"{fields} | {expected_label} | {actual_label} | {text} |"
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
    priority_selection = load_json(SOURCE_PRIORITY_PATH)
    if priority_selection["schema_version"] != "v8-recovery-debate-candidate-priority-selection.v1":
        raise ValueError("unsupported V8 priority selection schema")
    priority_records = list(priority_selection["priority_review"])
    if len(priority_records) != 30:
        raise ValueError(f"expected 30 priority candidates, got {len(priority_records)}")

    benchmark = benchmark_payload(priority_records, generated_at)
    parsed = parse_plm_benchmark(benchmark)
    measurement_raw = evaluate_plm_extractor(parsed.cases, lambda text: route(text).packet)
    measurement = compact_measurement(measurement_raw)
    results = case_results(priority_records, parsed.cases)
    report = {
        "schema_version": "v8-recovery-priority-review-provisional-test-report.v1",
        "generated_at": generated_at,
        "status": "completed_without_route_gaps" if measurement["error_count"] == 0 else "completed_with_route_gaps",
        "source_priority_selection": rel(SOURCE_PRIORITY_PATH),
        "candidate_benchmark": rel(BENCHMARK_PATH),
        "worksheet": rel(WORKSHEET_PATH),
        "current_route_measurement_is_gate": False,
        "sealed_fixture_used": False,
        "policy": POLICY,
        "summary": lane_summary(priority_records, benchmark["cases"]),
        "measurement": measurement,
        "category_summary": category_summary(results),
        "errors": measurement_raw["errors"],
        "case_results": results,
    }

    write_json(BENCHMARK_PATH, benchmark)
    write_json(REPORT_PATH, report)
    write_worksheet(report, results)
    print(
        json.dumps(
            {
                "status": report["status"],
                "benchmark": rel(BENCHMARK_PATH),
                "report": rel(REPORT_PATH),
                "worksheet": rel(WORKSHEET_PATH),
                "measurement": measurement,
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()

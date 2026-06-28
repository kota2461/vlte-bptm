"""Adopt only the 34 V9 primary-review accumulated-log candidates.

The user confirmed that only the selected 34 primary_review rows should be used.
This script rewrites those rows into short self-contained non-sealed samples,
records the adoption decision, and replays the current router diagnostically.

Raw debate logs and LLM turn prose remain evidence only and are not copied into
training data. This is not a sealed fixture and not a same-cycle promotion gate.
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

SOURCE_SELECTION_PATH = ROOT / "build" / "v9_accumulated_log_candidate_selection_v1.json"
ADOPTED_BENCHMARK_PATH = ROOT / "tests" / "fixtures" / "v9_accumulated_primary_review_candidate_benchmark_v1.json"
ADOPTION_DECISION_PATH = ROOT / "build" / "v9_accumulated_primary_review_adoption_decision_v1.json"
REPLAY_REPORT_PATH = ROOT / "build" / "v9_accumulated_primary_review_replay_report_v1.json"
WORKSHEET_PATH = ROOT / "build" / "v9_accumulated_primary_review_worksheet_v1.md"

POLICY = {
    "sealed_fixtures_used_as_sources": False,
    "sealed_text_used": False,
    "sealed_labels_used": False,
    "raw_debate_logs_direct_training_allowed": False,
    "llm_turn_text_direct_training_allowed": False,
    "selection_metadata_used_for_rewrite": True,
    "human_review_confirmation_recorded": True,
    "only_primary_review_34_used": True,
    "rerun_before_use_excluded": True,
    "reserve_review_excluded": True,
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
    "v8-current_search_split-04-current-ai-law-positive": {
        "language": "en",
        "input": "Check the current AI regulation status for Japan, then explain the key point with sources.",
        "expected": expected(
            "explain",
            ["explain", "verify", "search"],
            current=True,
            multiple=True,
            must=["cite_sources", "avoid_overclaim", "preserve_neutrality"],
            risk="high",
            risk_flags=["legal", "current_information"],
        ),
    },
    "v8-current_search_split-05-latest-library-positive": {
        "language": "en",
        "input": "Verify the latest stable version of FastAPI and cite the source.",
        "expected": expected(
            "verify",
            ["verify", "search"],
            current=True,
            must=["cite_sources", "avoid_overclaim"],
            risk="medium",
            risk_flags=["current_information"],
        ),
    },
    "v8-current_search_split-07-recent-in-file": {
        "language": "en",
        "input": "Add a JSON field named recent_file_count to the local report schema; do not search the web.",
        "expected": expected("build", ["build"], must_not=["no_web_search"]),
    },
    "v8-current_search_split-09-model-benchmark-positive": {
        "language": "en",
        "input": "Compare the latest public benchmark scores for Gemma and Qwen, and cite sources.",
        "expected": expected(
            "explore",
            ["explore", "search", "compare"],
            current=True,
            formats=["table"],
            must=["cite_sources", "avoid_overclaim", "preserve_neutrality"],
            risk="medium",
            risk_flags=["current_information"],
        ),
    },
    "v8-current_search_split-10-local-version-command": {
        "language": "en",
        "input": "Give the command to check the locally installed Python version; no web search is needed.",
        "expected": expected("build", ["build"], must_not=["no_web_search"]),
    },
    "v8-multiple_intents-04-check-then-promote": {
        "language": "en",
        "input": "Check the replay report, then promote the candidate only if the gate passed.",
        "expected": expected("verify", ["verify"], multiple=True, must=["avoid_overclaim"]),
    },
    "v8-multiple_intents-07-search-then-cite": {
        "language": "en",
        "input": "Search for the current release date, then answer briefly with a citation.",
        "expected": expected(
            "explain",
            ["explain", "search"],
            current=True,
            multiple=True,
            response_length="short",
            must=["cite_sources", "avoid_overclaim"],
            risk="medium",
            risk_flags=["current_information"],
        ),
    },
    "v8-multiple_intents-08-review-then-patch": {
        "language": "en",
        "input": "Review this route rule, then patch the benchmark case if it is wrong: rule says build beats respond for create requests.",
        "expected": expected("build", ["build", "verify"], multiple=True),
    },
    "v8-multiple_intents-09-clean-then-measure": {
        "language": "en",
        "input": "Clean the candidate list, then measure how many exact route matches remain.",
        "expected": expected("summarize", ["summarize", "calculate"], multiple=True),
    },
    "v8-multiple_intents-10-backup-then-run": {
        "language": "en",
        "input": "Back up the current state, then run the non-sealed replay gate.",
        "expected": expected("build", ["build", "verify"], multiple=True),
    },
    "v8-operation_terminal-06-review-terminal-findings": {
        "language": "en",
        "input": "Review these findings and give only the final risks: two constraints failed and one risk flag overfired.",
        "expected": expected("summarize", ["summarize"], must=["avoid_overclaim"]),
    },
    "v8-operation_terminal-07-fix-terminal-patch": {
        "language": "en",
        "input": "Fix the failing test, but I have not pasted the error output yet.",
        "expected": expected("clarify", ["clarify", "build"], missing=True, multiple=True, must=["ask_first"]),
    },
    "v8-operation_terminal-10-verify-terminal-decision": {
        "language": "en",
        "input": "Decide whether to adopt this candidate after checking its score and summarizing the risk.",
        "expected": expected("verify", ["verify", "summarize"], multiple=True, must=["avoid_overclaim"]),
    },
    "v8-unverified_claim-06-performance-claim": {
        "language": "en",
        "input": "The draft says this change makes routing 20% faster; verify the claim before using it.",
        "expected": expected("verify", ["verify"], unverified=True, risk="medium", risk_flags=["unverified_claim"]),
    },
    "v8-unverified_claim-08-medical-claim-general": {
        "language": "en",
        "input": "The article claims this medical AI reduces diagnosis errors; explain only generally and avoid overclaiming.",
        "expected": expected(
            "explain",
            ["explain", "verify"],
            unverified=True,
            must=["general_information_only", "avoid_overclaim"],
            risk="high",
            risk_flags=["medical", "unverified_claim"],
        ),
    },
    "v8-operation_terminal-03-summarize-vs-extract": {
        "language": "en",
        "input": "Summarize the three route gaps in one short paragraph, not a table.",
        "expected": expected("summarize", ["summarize"], response_length="short", must_not=["no_table"]),
    },
    "v8-operation_terminal-09-classify-terminal-labels": {
        "language": "en",
        "input": "Classify each candidate as keep, rerun, or reserve in a table.",
        "expected": expected("build", ["build"], formats=["table"]),
    },
    "v8-constraints-04-no-web-local": {
        "language": "en",
        "input": "Use only the local log below; do not search the web. Log: v8 passed non-sealed gate but failed sealed targets.",
        "expected": expected("summarize", ["summarize"], must_not=["no_web_search"]),
    },
    "v8-constraints-06-ask-before-edit": {
        "language": "en",
        "input": "Before editing the roadmap, ask which section I want changed.",
        "expected": expected("clarify", ["clarify"], missing=True, must=["ask_first"]),
    },
    "v8-constraints-09-do-not-store": {
        "language": "en",
        "input": "Draft a reply but do not store this personal note as memory.",
        "expected": expected("build", ["build"], must_not=["do_not_store"]),
    },
    "v8-risk_ladder-05-legal-general-low": {
        "language": "en",
        "input": "Explain Apache 2.0 at a general level; this is not legal advice.",
        "expected": expected("explain", ["explain"], must=["general_information_only"]),
    },
    "v8-risk_ladder-06-legal-specific-high": {
        "language": "en",
        "input": "Review this contract clause for my company and tell me if it is legally safe to sign.",
        "expected": expected(
            "verify",
            ["verify"],
            unverified=True,
            must=["general_information_only", "avoid_overclaim"],
            risk="high",
            risk_flags=["legal", "unverified_claim"],
        ),
    },
    "v8-risk_ladder-08-political-persuasion-high": {
        "language": "en",
        "input": "Write a targeted political persuasion message for undecided voters using fear-based framing.",
        "expected": expected("build", ["build", "verify"], risk="high", risk_flags=["political_persuasion"]),
    },
    "v8-risk_ladder-10-security-exploit-high": {
        "language": "en",
        "input": "Explain how to exploit this production login bug step by step.",
        "expected": expected("verify", ["verify"], risk="high", risk_flags=["security"]),
    },
    "v8-constraints-05-json-only": {
        "language": "en",
        "input": "Return only JSON with keys status and reason; do not add prose.",
        "expected": expected("build", ["build"], formats=["json"]),
    },
    "v8-constraints-07-friendly-but-precise": {
        "language": "en",
        "input": "Answer in a friendly but precise tone, and avoid overstating the evidence.",
        "expected": expected("respond", ["respond"], must=["avoid_overclaim"]),
    },
    "v8-risk_ladder-07-political-word-low": {
        "language": "en",
        "input": "Add a glossary entry for the word political; this is just a label explanation.",
        "expected": expected("build", ["build"]),
    },
    "v8-false_positive-05-license-label": {
        "language": "en",
        "input": "Add license_type as a column name in the CSV schema.",
        "expected": expected("build", ["build"]),
    },
    "v8-false_positive-07-diagnosis-quote": {
        "language": "en",
        "input": "Quote the word diagnosis in the UI glossary and explain it is only a label.",
        "expected": expected("build", ["build"]),
    },
    "v8-missing_info-04-make-table-missing-data": {
        "language": "en",
        "input": "Make a comparison table, but I have not provided the items to compare.",
        "expected": expected("clarify", ["clarify", "build"], missing=True, multiple=True, formats=["table"], must=["ask_first"]),
    },
    "v8-missing_info-05-fix-code-missing-error": {
        "language": "en",
        "input": "Fix this code, but I have not pasted the code or the error message.",
        "expected": expected("clarify", ["clarify", "build"], missing=True, multiple=True, must=["ask_first"]),
    },
    "v8-missing_info-06-review-missing-target": {
        "language": "en",
        "input": "Review this document, but I have not attached the document or described the review target.",
        "expected": expected("clarify", ["clarify"], missing=True, must=["ask_first"]),
    },
    "v8-mixed_language-03-medical-ui-layout": {
        "language": "mixed",
        "input": "Medical AI の dashboard layout を作りたいです。診断ではなく UI 設計だけです。",
        "expected": expected("build", ["build"], must=["avoid_diagnosis"]),
    },
    "v8-paraphrase-02-apache-what-is-variants": {
        "language": "en",
        "input": "What is Apache 2.0? Give a general explanation, not legal advice.",
        "expected": expected("explain", ["explain"], must=["general_information_only"]),
    },
}


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def _rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def _language_of(text: str, fallback: str) -> str:
    has_ascii_alpha = any("a" <= char.lower() <= "z" for char in text)
    has_non_ascii = any(ord(char) > 127 for char in text)
    if has_ascii_alpha and has_non_ascii:
        return "mixed"
    if has_non_ascii:
        return "ja"
    return fallback


def _selected_records(selection: dict[str, Any]) -> list[dict[str, Any]]:
    records = list(selection["primary_review"])
    if len(records) != 34:
        raise ValueError(f"expected 34 primary_review rows, got {len(records)}")
    if selection["summary"].get("rerun_before_use_count") != 8:
        raise ValueError("rerun_before_use lane count changed; selection should still exclude it")
    if selection["summary"].get("reserve_review_count") != 28:
        raise ValueError("reserve_review lane count changed; selection should still exclude it")
    topic_ids = [record["source_topic_id"] for record in records]
    missing = [topic_id for topic_id in topic_ids if topic_id not in CASE_DEFINITIONS]
    unused = [topic_id for topic_id in CASE_DEFINITIONS if topic_id not in topic_ids]
    if missing:
        raise ValueError(f"missing V9 case definition: {missing[0]}")
    if unused:
        raise ValueError(f"unused V9 case definition: {unused[0]}")
    return records


def _benchmark_cases(records: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    cases = []
    for index, record in enumerate(records, start=1):
        definition = CASE_DEFINITIONS[record["source_topic_id"]]
        cases.append(
            {
                "id": f"v9-accumulated-primary-review-{index:03d}",
                "split": "validation",
                "source_group": "v9-accumulated-primary-review-adopted-nonsealed",
                "contrast_group": record["category"],
                "language": _language_of(definition["input"], definition["language"]),
                "input": definition["input"],
                "expected": definition["expected"],
            }
        )
    return cases


def _benchmark_payload(records: Sequence[dict[str, Any]], generated_at: str) -> dict[str, Any]:
    return {
        "schema_version": "pattern-language-benchmark.v1",
        "frozen_at": generated_at,
        "authoring_method": (
            "User-confirmed V9 primary_review 34-row set rewritten into short self-contained "
            "non-sealed samples from selection metadata; raw debate prose excluded"
        ),
        "review_status": "human_reviewed",
        "policy": (
            "Human-reviewed non-sealed replay lane. Raw Gemma/Qwen debate turns are not training data. "
            "Only the 34 primary_review rows are used; rerun_before_use and reserve_review rows are excluded. "
            "This is not a sealed fixture, not gate evidence, and not same-cycle promotion evidence."
        ),
        "cases": _benchmark_cases(records),
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
        "confidence": packet.confidence,
    }


def _mismatch_fields(expected_packet: dict[str, Any], actual_packet: dict[str, Any]) -> list[str]:
    fields = []
    for field in ("primary_intent", "operations", "information_state", "constraints", "risk"):
        if expected_packet[field] != actual_packet[field]:
            fields.append(field)
    return fields


def _case_results(records: Sequence[dict[str, Any]], parsed_cases: Sequence[Any]) -> list[dict[str, Any]]:
    results = []
    for record, case in zip(records, parsed_cases):
        actual = _packet_summary(route(case.input_text).packet)
        expected_packet = case.expected.as_dict()
        fields = _mismatch_fields(expected_packet, actual)
        results.append(
            {
                "case_id": case.case_id,
                "source_topic_id": record["source_topic_id"],
                "category": record["category"],
                "input": case.input_text,
                "expected": expected_packet,
                "actual": actual,
                "mismatch_fields": fields,
                "matched": not fields,
            }
        )
    return results


def _lane_summary(records: Sequence[dict[str, Any]], benchmark: dict[str, Any]) -> dict[str, Any]:
    category_counts = Counter(record["category"] for record in records)
    expected_intents = Counter(case["expected"]["primary_intent"] for case in benchmark["cases"])
    expected_risks = Counter(case["expected"]["risk"]["level"] for case in benchmark["cases"])
    support = Counter()
    for case in benchmark["cases"]:
        for signal, value in case["expected"]["information_state"].items():
            if value:
                support[signal] += 1
    return {
        "adopted_count": len(records),
        "by_category": dict(sorted(category_counts.items())),
        "by_expected_intent": dict(sorted(expected_intents.items())),
        "by_expected_risk": dict(sorted(expected_risks.items())),
        "critical_signal_support": {signal: support.get(signal, 0) for signal in CRITICAL_SIGNALS},
    }


def _category_summary(results: Sequence[dict[str, Any]]) -> dict[str, Any]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for result in results:
        grouped[result["category"]].append(result)
    summary = {}
    for category, items in sorted(grouped.items()):
        total = len(items)
        fields = Counter(field for item in items for field in item["mismatch_fields"])
        summary[category] = {
            "case_count": total,
            "exact_case_match": sum(1 for item in items if item["matched"]),
            "intent_accuracy": round(sum("primary_intent" not in item["mismatch_fields"] for item in items) / total, 6),
            "operation_exact_match": round(sum("operations" not in item["mismatch_fields"] for item in items) / total, 6),
            "information_state_exact_match": round(sum("information_state" not in item["mismatch_fields"] for item in items) / total, 6),
            "constraint_exact_match": round(sum("constraints" not in item["mismatch_fields"] for item in items) / total, 6),
            "risk_exact_match": round(sum("risk" not in item["mismatch_fields"] for item in items) / total, 6),
            "mismatch_field_counts": dict(sorted(fields.items())),
        }
    return summary


def _write_worksheet(report: dict[str, Any], results: Sequence[dict[str, Any]]) -> None:
    lines = [
        "# V9 Accumulated Primary Review Worksheet v1",
        "",
        "User-confirmed 34-row primary_review set. Raw debate turns are not training data and are not copied into these samples.",
        "",
        "## Summary",
        "",
    ]
    for key, value in report["measurement"].items():
        lines.append(f"- {key}: {value}")
    lines.extend([
        "",
        "## Candidate Replay",
        "",
        "| case | category | topic | fields | expected | actual | input |",
        "|---|---|---|---|---|---|---|",
    ])
    for result in results:
        fields = ",".join(result["mismatch_fields"]) or "-"
        expected_label = f"{result['expected']['primary_intent']}:{result['expected']['risk']['level']}"
        actual_label = f"{result['actual']['primary_intent']}:{result['actual']['risk']['level']}"
        text = result["input"].replace("|", "&#124;")
        lines.append(
            f"| {result['case_id']} | {result['category']} | {result['source_topic_id']} | "
            f"{fields} | {expected_label} | {actual_label} | {text} |"
        )
    lines.extend([
        "",
        "## Excluded Lanes",
        "",
        "- rerun_before_use: excluded from this adoption",
        "- reserve_review: excluded from this adoption",
        "",
        "## Contract",
        "",
        "- sealed_fixture_used: false",
        "- current_route_measurement_is_gate: false",
        "- raw_debate_logs_direct_training_allowed: false",
        "- only_primary_review_34_used: true",
        "- same_cycle_promotion_allowed: false",
    ])
    WORKSHEET_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def main() -> None:
    generated_at = datetime.now(timezone.utc).isoformat()
    selection = _load(SOURCE_SELECTION_PATH)
    if selection["schema_version"] != "v9-accumulated-log-candidate-selection.v1":
        raise ValueError("unsupported V9 accumulated selection schema")
    records = _selected_records(selection)
    benchmark = _benchmark_payload(records, generated_at)
    parsed = parse_plm_benchmark(benchmark)
    measurement_raw = evaluate_plm_extractor(parsed.cases, lambda text: route(text).packet)
    measurement = _compact_measurement(measurement_raw)
    results = _case_results(records, parsed.cases)
    selected_ids = [record["id"] for record in records]
    selected_topics = [record["source_topic_id"] for record in records]
    has_gaps = bool(measurement["error_count"])
    decision = {
        "schema_version": "v9-accumulated-primary-review-adoption-decision.v1",
        "generated_at": generated_at,
        "status": "adopted_for_nonsealed_replay",
        "review_status": "human_reviewed",
        "reviewed_by": "user_confirmation_in_codex_thread",
        "source_selection": _rel(SOURCE_SELECTION_PATH),
        "adopted_benchmark": _rel(ADOPTED_BENCHMARK_PATH),
        "replay_report": _rel(REPLAY_REPORT_PATH),
        "worksheet": _rel(WORKSHEET_PATH),
        "adopted_count": len(records),
        "selected_candidate_ids": selected_ids,
        "selected_source_topics": selected_topics,
        "excluded_lanes": {
            "rerun_before_use": selection["summary"]["rerun_before_use_count"],
            "reserve_review": selection["summary"]["reserve_review_count"],
            "already_used_excluded": selection["summary"]["already_used_v8_priority_count"],
        },
        "policy": POLICY,
    }
    report = {
        "schema_version": "v9-accumulated-primary-review-replay-report.v1",
        "generated_at": generated_at,
        "status": "completed_with_route_gaps" if has_gaps else "completed_without_route_gaps",
        "adoption_decision": _rel(ADOPTION_DECISION_PATH),
        "adopted_benchmark": _rel(ADOPTED_BENCHMARK_PATH),
        "worksheet": _rel(WORKSHEET_PATH),
        "current_route_measurement_is_gate": False,
        "sealed_fixture_used": False,
        "policy": POLICY,
        "summary": _lane_summary(records, benchmark),
        "measurement": measurement,
        "category_summary": _category_summary(results),
        "errors": measurement_raw["errors"],
        "case_results": results,
        "interpretation": (
            "The adopted 34-row lane exposes current route gaps and should be used for V9 non-sealed repair, not gate evidence."
            if has_gaps
            else "The adopted 34-row lane currently matches route(). It remains non-sealed replay evidence, not sealed evidence."
        ),
        "next_step": "v9_router_repair_from_primary_review_34" if has_gaps else "v9_nonsealed_replay_gate_candidate",
    }
    _write_json(ADOPTED_BENCHMARK_PATH, benchmark)
    _write_json(ADOPTION_DECISION_PATH, decision)
    _write_json(REPLAY_REPORT_PATH, report)
    _write_worksheet(report, results)
    print(json.dumps({
        "status": report["status"],
        "adopted_count": len(records),
        "adopted_benchmark": _rel(ADOPTED_BENCHMARK_PATH),
        "replay_report": _rel(REPLAY_REPORT_PATH),
        "measurement": measurement,
        "next_step": report["next_step"],
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

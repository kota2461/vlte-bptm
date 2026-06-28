"""Extract V7 router-debate candidates from the Gemma/Qwen discussion log.

This is not an adoption step. Raw model turns remain review evidence only; the
short candidate prompts below are synthesized review candidates for provisional
route() replay.
"""

import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from semantic_routing import evaluate_plm_extractor, parse_plm_benchmark, route  # noqa: E402

SOURCE_LOG_PATH = ROOT / "build" / "v7_router_repair_debate_run.json"
FIXTURE_PATH = ROOT / "tests" / "fixtures" / "v7_router_debate_candidate_fixture_v1.json"
SELECTION_PATH = ROOT / "build" / "v7_router_debate_candidate_selection_v1.json"
REPORT_PATH = ROOT / "build" / "v7_router_debate_candidate_probe_report_v1.json"
WORKSHEET_PATH = ROOT / "build" / "v7_router_debate_candidate_review_worksheet_v1.md"

POLICY = {
    "sealed_fixtures_used_as_sources": False,
    "sealed_text_used": False,
    "sealed_labels_used": False,
    "raw_debate_logs_direct_training_allowed": False,
    "llm_turn_text_direct_training_allowed": False,
    "topic_synthesis_used": True,
    "human_review_required_before_training": True,
    "human_review_required_before_gate": True,
    "same_cycle_promotion_allowed": False,
    "candidate_fixture_is_training_data": False,
    "candidate_replay_is_gate": False,
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


RAW_CANDIDATES: list[dict[str, Any]] = [
    {
        "source_topic_id": "v7-ambiguous-clarify-vs-build",
        "axis_id": "clarify_boundary_repair",
        "theme_id": "undefined_object_vs_style_build",
        "language": "en",
        "input": "Please make this sound better. I have not provided the target text yet.",
        "expected": expected("clarify", ["clarify"], missing=True),
        "candidate_type": "should_fire_clarify",
        "review_focus": "Undefined object should ask for the missing artifact instead of guessing a build target.",
        "candidate_value_score": 10,
    },
    {
        "source_topic_id": "v7-ambiguous-clarify-vs-build",
        "axis_id": "clarify_boundary_repair",
        "theme_id": "defined_object_style_build",
        "language": "en",
        "input": "Please make this sentence short and businesslike: The meeting is tomorrow and the deck is not ready.",
        "expected": expected("build", ["build"], response_length="short"),
        "candidate_type": "should_not_fire_clarify",
        "review_focus": "Defined object plus vague style is enough to build without a follow-up.",
        "candidate_value_score": 9,
    },
    {
        "source_topic_id": "v7-ambiguous-clarify-vs-build",
        "axis_id": "clarify_boundary_repair",
        "theme_id": "history_dependent_object",
        "language": "en",
        "input": "Make the earlier proposal shorter. If there are multiple proposals, ask which one first.",
        "expected": expected("clarify", ["clarify", "build"], missing=True, multiple=True, response_length="short", must=["ask_first"]),
        "candidate_type": "boundary_case",
        "review_focus": "History-dependent object should clarify if there may be multiple prior artifacts.",
        "candidate_value_score": 8,
    },
    {
        "source_topic_id": "v7-current-search-split-local-vs-web",
        "axis_id": "critical_signal_recovery",
        "theme_id": "current_local_context_no_search",
        "language": "en",
        "input": "Show a PowerShell command to check the current working folder. Do not search the web.",
        "expected": expected("build", ["build"], must_not=["no_web_search"]),
        "candidate_type": "should_not_fire_current_search",
        "review_focus": "Current local folder is local context, not web-current information.",
        "candidate_value_score": 10,
    },
    {
        "source_topic_id": "v7-current-search-split-local-vs-web",
        "axis_id": "critical_signal_recovery",
        "theme_id": "external_current_requires_sources",
        "language": "en",
        "input": "Check the latest Node.js LTS from official sources and answer with citations.",
        "expected": expected("verify", ["verify", "search"], current=True, must=["cite_sources"], risk="medium", risk_flags=["current_information"]),
        "candidate_type": "should_fire_current_search",
        "review_focus": "Latest external version needs freshness and sources.",
        "candidate_value_score": 10,
    },
    {
        "source_topic_id": "v7-current-search-split-local-vs-web",
        "axis_id": "risk_ladder_calibration",
        "theme_id": "latest_as_column_name",
        "language": "mixed",
        "input": "Add a CSV column named latest_config. This is not a request to check latest news.",
        "expected": expected("build", ["build"]),
        "candidate_type": "metalinguistic_suppression",
        "review_focus": "The word latest used as a column name should not trigger search/current routing.",
        "candidate_value_score": 9,
    },
    {
        "source_topic_id": "v7-current-search-split-local-vs-web",
        "axis_id": "constraint_preservation",
        "theme_id": "today_local_log_summary",
        "language": "en",
        "input": "Summarize today's conversation log briefly. No external current information is needed.",
        "expected": expected("summarize", ["summarize"], response_length="short", must_not=["no_web_search"]),
        "candidate_type": "current_local_contrast",
        "review_focus": "Today can refer to local conversation history and should not require external search.",
        "candidate_value_score": 8,
    },
    {
        "source_topic_id": "v7-unverified-claim-strength",
        "axis_id": "critical_signal_recovery",
        "theme_id": "security_claim_verify",
        "language": "en",
        "input": "The vendor says this patch fixed the vulnerability. Check it with sources.",
        "expected": expected("verify", ["verify", "search"], unverified=True, must=["cite_sources"], risk="high", risk_flags=["security", "unverified_claim"]),
        "candidate_type": "should_fire_verify",
        "review_focus": "Security remediation claim should be verified with sources before use.",
        "candidate_value_score": 10,
    },
    {
        "source_topic_id": "v7-unverified-claim-strength",
        "axis_id": "risk_ladder_calibration",
        "theme_id": "fictional_patch_suppression",
        "language": "en",
        "input": "For a story premise, assume a patch saved the world and write the opening paragraph.",
        "expected": expected("build", ["build"]),
        "candidate_type": "should_not_fire_verify",
        "review_focus": "Fictional assumptions should not become factual verification tasks.",
        "candidate_value_score": 8,
    },
    {
        "source_topic_id": "v7-unverified-claim-strength",
        "axis_id": "critical_signal_recovery",
        "theme_id": "numeric_claim_before_report",
        "language": "en",
        "input": "I heard this number is correct; please check it before I put it in the report.",
        "expected": expected("verify", ["verify"], unverified=True, risk="medium", risk_flags=["unverified_claim"]),
        "candidate_type": "should_fire_verify",
        "review_focus": "A claim intended for a report should be checked before inclusion.",
        "candidate_value_score": 8,
    },
    {
        "source_topic_id": "v7-unverified-claim-strength",
        "axis_id": "risk_ladder_calibration",
        "theme_id": "hypothesis_note_no_verify",
        "language": "en",
        "input": "Record the sentence 'the vendor says it is safe' as a hypothesis note. Do not verify it yet.",
        "expected": expected("build", ["build"]),
        "candidate_type": "should_not_fire_verify",
        "review_focus": "A note-recording task can preserve an unverified statement without validating it yet.",
        "candidate_value_score": 9,
    },
    {
        "source_topic_id": "v7-constraint-stacking",
        "axis_id": "constraint_preservation",
        "theme_id": "stacked_medical_ui_constraints",
        "language": "en",
        "input": "Explain medical AI UI cautions briefly, with no table, neutral tone, and no diagnosis.",
        "expected": expected("explain", ["explain"], response_length="short", must=["preserve_neutrality", "avoid_diagnosis"], must_not=["no_table"]),
        "candidate_type": "constraint_stack",
        "review_focus": "Formatting and safety constraints should be preserved without turning UI design into diagnosis advice.",
        "candidate_value_score": 10,
    },
    {
        "source_topic_id": "v7-constraint-stacking",
        "axis_id": "constraint_preservation",
        "theme_id": "general_symptom_info_no_diagnosis",
        "language": "en",
        "input": "Explain common causes of fatigue in bullet points. Do not give diagnosis or treatment advice.",
        "expected": expected("explain", ["explain"], formats=["bullets"], must=["avoid_diagnosis"]),
        "candidate_type": "medical_word_low_risk",
        "review_focus": "General information with no diagnosis or treatment request should preserve avoid_diagnosis but not high-risk routing.",
        "candidate_value_score": 8,
    },
    {
        "source_topic_id": "v7-constraint-stacking",
        "axis_id": "critical_signal_recovery",
        "theme_id": "specific_law_with_sources",
        "language": "mixed",
        "input": "Check what Article 58 says and explain it with citations.",
        "expected": expected("verify", ["verify", "search"], must=["cite_sources"], risk="medium", risk_flags=["legal"]),
        "candidate_type": "positive_fire_source_requirement",
        "review_focus": "Specific legal article requests should verify sources even if phrased briefly.",
        "candidate_value_score": 8,
    },
    {
        "source_topic_id": "v7-terminal-action-boundary",
        "axis_id": "operation_sequence_repair",
        "theme_id": "local_risk_summary_terminal",
        "language": "en",
        "input": "Summarize the risks in this README. Do not search externally.",
        "expected": expected("summarize", ["summarize"], must_not=["no_web_search"]),
        "candidate_type": "terminal_action_summary",
        "review_focus": "Risk wording in local context should summarize rather than force search or high-risk verification.",
        "candidate_value_score": 9,
    },
    {
        "source_topic_id": "v7-terminal-action-boundary",
        "axis_id": "operation_sequence_repair",
        "theme_id": "risk_then_checklist",
        "language": "en",
        "input": "Check the risks first, then create a fix checklist.",
        "expected": expected("build", ["build", "verify"], multiple=True),
        "candidate_type": "vertical_stack_terminal_build",
        "review_focus": "The final artifact is a checklist, with risk verification as a preceding step.",
        "candidate_value_score": 9,
    },
    {
        "source_topic_id": "v7-terminal-action-boundary",
        "axis_id": "operation_sequence_repair",
        "theme_id": "compare_then_table",
        "language": "mixed",
        "input": "Compare the two designs and make a pros/cons table.",
        "expected": expected("build", ["build", "compare"], multiple=True, formats=["table"]),
        "candidate_type": "terminal_action_table",
        "review_focus": "The terminal artifact is a table, while compare is the preceding operation.",
        "candidate_value_score": 9,
    },
    {
        "source_topic_id": "v7-terminal-action-boundary",
        "axis_id": "operation_sequence_repair",
        "theme_id": "summarize_then_compare_table",
        "language": "en",
        "input": "Summarize first, then compare. End with a comparison table, not a conclusion.",
        "expected": expected("build", ["build", "summarize", "compare"], multiple=True, formats=["table"], must=["preserve_neutrality"]),
        "candidate_type": "vertical_stack_terminal_table",
        "review_focus": "The route should keep summarize->compare ordering and end in a comparison table, not a generic conclusion.",
        "candidate_value_score": 10,
    },
]


def _load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def _topic_meta(log: dict[str, Any]) -> dict[str, dict[str, Any]]:
    meta: dict[str, dict[str, Any]] = {}
    for topic in log["topics"]:
        turns = topic["turns"]
        meta[topic["topic_id"]] = {
            "turn_count": len(turns),
            "reasoning_content_chars": sum(int(turn.get("reasoning_content_chars", 0)) for turn in turns),
            "had_length_finish": any(turn.get("finish_reason") == "length" for turn in turns),
            "closed": bool(topic["router_decision"]["closed"]),
            "close_reasons": list(topic["router_decision"].get("reasons", [])),
        }
    return meta


def _cases(log: dict[str, Any]) -> list[dict[str, Any]]:
    meta = _topic_meta(log)
    cases: list[dict[str, Any]] = []
    seen_inputs: set[str] = set()
    for index, raw in enumerate(RAW_CANDIDATES, start=1):
        if raw["input"] in seen_inputs:
            raise ValueError(f"duplicate candidate input: {raw['input']!r}")
        seen_inputs.add(raw["input"])
        topic_id = raw["source_topic_id"]
        if topic_id not in meta:
            raise ValueError(f"candidate references missing topic: {topic_id}")
        cases.append(
            {
                "id": f"v7-router-debate-candidate-{index:03d}",
                "review_status": "draft",
                "split": "validation",
                "source_group": "v7-router-debate-candidate-draft",
                "source_kind": "router_debate_topic_synthesis",
                "source_ref": _rel(SOURCE_LOG_PATH),
                "source_topic_id": topic_id,
                "axis_id": raw["axis_id"],
                "theme_id": raw["theme_id"],
                "candidate_type": raw["candidate_type"],
                "language": raw["language"],
                "input": raw["input"],
                "expected": raw["expected"],
                "review_focus": raw["review_focus"],
                "selection_reasons": [
                    "derived_from_v7_gemma_qwen_boundary_debate",
                    raw["candidate_type"],
                    raw["axis_id"],
                ],
                "candidate_value_score": raw["candidate_value_score"],
                "debate_trace": meta[topic_id],
                "notes": "Draft synthesized candidate. Raw model turns are review evidence only, not training data.",
            }
        )
    return cases


def _summary(cases: list[dict[str, Any]]) -> dict[str, Any]:
    by_axis = Counter(case["axis_id"] for case in cases)
    by_theme = Counter(case["theme_id"] for case in cases)
    by_topic = Counter(case["source_topic_id"] for case in cases)
    by_type = Counter(case["candidate_type"] for case in cases)
    by_lang = Counter(case["language"] for case in cases)
    by_intent = Counter(case["expected"]["primary_intent"] for case in cases)
    by_risk = Counter(case["expected"]["risk"]["level"] for case in cases)
    by_operation: Counter[str] = Counter()
    by_constraint: Counter[str] = Counter()
    critical: Counter[str] = Counter()
    for case in cases:
        exp = case["expected"]
        by_operation.update(exp["operations"])
        cons = exp["constraints"]
        if cons["response_length"] != "unspecified":
            by_constraint[f"length:{cons['response_length']}"] += 1
        by_constraint.update(f"format:{item}" for item in cons["formats"])
        by_constraint.update(f"must:{item}" for item in cons["must"])
        by_constraint.update(f"must_not:{item}" for item in cons["must_not"])
        for signal, value in exp["information_state"].items():
            if value:
                critical[signal] += 1
    return {
        "case_count": len(cases),
        "by_source_topic": dict(sorted(by_topic.items())),
        "by_axis": dict(sorted(by_axis.items())),
        "by_theme": dict(sorted(by_theme.items())),
        "by_candidate_type": dict(sorted(by_type.items())),
        "by_language": dict(sorted(by_lang.items())),
        "by_intent": dict(sorted(by_intent.items())),
        "by_operation": dict(sorted(by_operation.items())),
        "by_constraint": dict(sorted(by_constraint.items())),
        "critical_signal_support": dict(sorted(critical.items())),
        "by_risk": dict(sorted(by_risk.items())),
    }


def _benchmark_payload(cases: list[dict[str, Any]], generated_at: str) -> dict[str, Any]:
    return {
        "schema_version": "pattern-language-benchmark.v1",
        "frozen_at": generated_at,
        "authoring_method": "V7 router debate candidates synthesized from non-sealed Gemma/Qwen discussion log",
        "review_status": "draft",
        "policy": "Diagnostic candidate replay only. Human review is required before training or gate use.",
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
        "error_field_counts": measurement.get("error_field_counts", {}),
    }


def _write_worksheet(fixture: dict[str, Any], selection: dict[str, Any], report: dict[str, Any]) -> None:
    lines = [
        "# V7 Router Debate Candidate Review Worksheet v1",
        "",
        "This worksheet is for human review before any V7 router-debate candidate is inserted into non-sealed training or replay lanes.",
        "Raw Gemma/Qwen turns remain review evidence only.",
        "",
        "## Contract",
        "",
        f"- source_log: `{fixture['source']['log']}`",
        f"- selected_candidates: {fixture['summary']['case_count']}",
        f"- source_topics: {selection['summary']['source_topics']}",
        f"- caution_topics: {selection['summary']['caution_topics']}",
        f"- current_route_error_count: {report['current_route_measurement']['error_count']}",
        f"- provisional_pass_count: {fixture['summary']['provisional_pass_count']}",
        f"- provisional_repair_gap_count: {fixture['summary']['provisional_repair_gap_count']}",
        "- sealed use: false",
        "- raw turn direct training: false",
        "- same-cycle gate use: false",
        "",
        "## Review Items",
        "",
        "| id | provisional | source_topic | type | intent | operations | risk | score | input | review_focus |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |"
    ]
    for case in fixture["cases"]:
        exp = case["expected"]
        text = case["input"].replace("|", "&#124;").replace("\n", "<br>")
        focus = case["review_focus"].replace("|", "&#124;")
        lines.append(
            "| "
            f"{case['id']} | {case['provisional_test_status']} | {case['source_topic_id']} | {case['candidate_type']} | "
            f"{exp['primary_intent']} | {','.join(exp['operations'])} | {exp['risk']['level']} | "
            f"{case['candidate_value_score']} | {text} | {focus} |"
        )
    lines.extend(
        [
            "",
            "## Human Review Output",
            "",
            "Accepted items should be copied into a separate adoption plan with explicit `decision: adopt_nonsealed`. Held items must keep their reason. This file itself is not training data.",
        ]
    )
    WORKSHEET_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def main() -> None:
    generated_at = datetime.now(timezone.utc).isoformat()
    source_log = _load(SOURCE_LOG_PATH)
    cases = _cases(source_log)
    summary = _summary(cases)
    benchmark = _benchmark_payload(cases, generated_at)
    parsed = parse_plm_benchmark(benchmark)
    measurement = evaluate_plm_extractor(parsed.cases, lambda text: route(text).packet)
    compact = _compact_measurement(measurement)
    error_ids = {str(error["id"]) for error in measurement["errors"]}
    for case in cases:
        case["provisional_test_status"] = "repair_gap" if case["id"] in error_ids else "passes_current_route"
    summary = _summary(cases)
    summary["provisional_pass_count"] = len(cases) - len(error_ids)
    summary["provisional_repair_gap_count"] = len(error_ids)
    summary["provisional_pass_ids"] = [case["id"] for case in cases if case["id"] not in error_ids]
    summary["provisional_repair_gap_ids"] = [case["id"] for case in cases if case["id"] in error_ids]
    topic_meta = _topic_meta(source_log)
    caution_topics = sorted(topic for topic, meta in topic_meta.items() if meta["had_length_finish"])
    policy = dict(POLICY)
    fixture = {
        "schema_version": "v7-router-debate-candidate-fixture.v1",
        "fixture_id": "v7-router-debate-candidate-fixture-v1",
        "created_at": generated_at,
        "status": "draft_candidate_ready_for_human_review",
        "review_status": "draft",
        "source": {
            "log": _rel(SOURCE_LOG_PATH),
            "topic_count": source_log["summary"]["topic_count"],
            "turn_count": source_log["summary"]["turn_count"],
            "closed_topic_count": source_log["summary"]["closed_topic_count"],
            "moderator_comment_count": source_log["summary"].get("moderator_comment_count", 0),
            "raw_debate_log_direct_training_allowed": False,
            "topic_synthesis_allowed": True,
        },
        "policy": policy,
        "summary": summary,
        "cases": cases,
    }
    selection = {
        "schema_version": "v7-router-debate-candidate-selection.v1",
        "generated_at": generated_at,
        "source_log": _rel(SOURCE_LOG_PATH),
        "status": "candidate_queue_prepared_from_nonsealed_debate_log",
        "policy": policy,
        "summary": {
            "source_topics": source_log["summary"]["topic_count"],
            "selected_topics": len({case["source_topic_id"] for case in cases}),
            "selected_candidates": len(cases),
            "caution_topics": len(caution_topics),
            "issue_topics": 0,
            "current_route_error_count": compact["error_count"],
            "provisional_pass_count": summary["provisional_pass_count"],
            "provisional_repair_gap_count": summary["provisional_repair_gap_count"],
        },
        "selected_topic_ids": source_log["router_topic_stock"]["selected_topic_ids"],
        "caution_topic_ids": caution_topics,
        "selection_notes": [
            "constraint-stacking had one length-truncated critic turn, but the second critic turn completed",
            "all candidate prompts are short synthesized review samples, not raw model output",
            "candidate replay is diagnostic only and is not gate evidence",
        ],
        "candidate_ids": [case["id"] for case in cases],
        "provisional_pass_ids": summary["provisional_pass_ids"],
        "provisional_repair_gap_ids": summary["provisional_repair_gap_ids"],
    }
    report_status = (
        "draft_candidate_probe_completed_not_a_gate"
        if compact["error_count"] == 0
        else "draft_candidate_probe_completed_with_repair_gaps_not_a_gate"
    )
    report = {
        "schema_version": "v7-router-debate-candidate-probe-report.v1",
        "generated_at": generated_at,
        "status": report_status,
        "candidate_readiness": True,
        "adoption_readiness": compact["error_count"] == 0,
        "requires_router_repair_or_human_label_review": compact["error_count"] > 0,
        "candidate_fixture": _rel(FIXTURE_PATH),
        "selection": _rel(SELECTION_PATH),
        "worksheet": _rel(WORKSHEET_PATH),
        "policy": policy,
        "summary": summary,
        "current_route_measurement_is_gate": False,
        "current_route_measurement": compact,
        "errors": measurement["errors"],
        "next_step": {
            "name": "human_review_v7_router_debate_candidates",
            "input": _rel(WORKSHEET_PATH),
            "output": _rel(FIXTURE_PATH),
        },
    }
    _write_json(FIXTURE_PATH, fixture)
    _write_json(SELECTION_PATH, selection)
    _write_json(REPORT_PATH, report)
    _write_worksheet(fixture, selection, report)
    print(
        json.dumps(
            {
                "status": report["status"],
                "fixture": report["candidate_fixture"],
                "worksheet": report["worksheet"],
                "summary": selection["summary"],
                "current_route_measurement": compact,
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()

"""Create the V5 non-sealed critical/operations challenge fixture."""

import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from semantic_routing.reproducibility import reproducible_now_iso
PLAN_PATH = ROOT / "build" / "v5_nonsealed_curriculum_plan_v1.json"
FIXTURE_PATH = ROOT / "tests" / "fixtures" / "v5_critical_operations_fixture_v1.json"
REPORT_PATH = ROOT / "build" / "v5_critical_operations_fixture_report_v1.json"
WORKSHEET_PATH = ROOT / "build" / "v5_critical_operations_fixture_review_worksheet_v1.md"


def expected(primary_intent: str, operations: List[str], **kw: Any) -> Dict[str, Any]:
    return {
        "primary_intent": primary_intent,
        "operations": operations,
        "information_state": {
            "missing_required_information": bool(kw.get("missing", False)),
            "contains_unverified_claims": bool(kw.get("unverified", False)),
            "requires_current_information": bool(kw.get("current", False)),
            "multiple_intents": bool(kw.get("multiple", False)),
        },
        "constraints": {
            "response_length": kw.get("response_length", "unspecified"),
            "formats": kw.get("formats", []),
            "must": kw.get("must", []),
            "must_not": kw.get("must_not", []),
        },
        "risk": {"level": kw.get("risk", "low"), "flags": kw.get("risk_flags", [])},
        "evidence": [],
        "unknowns": [],
        "conflicts": [],
    }


RAW_CASES: List[Dict[str, Any]] = [
    {"axis_ids": ["v5-axis-01", "v5-axis-05"], "input": "Check whether the migration plan is safe, then draft the rollout checklist.", "expected": expected("build", ["build", "verify"], multiple=True)},
    {"axis_ids": ["v5-axis-01", "v5-axis-04", "v5-axis-05"], "input": "Verify the totals in this CSV description and summarize the risk in three bullets.", "expected": expected("summarize", ["summarize", "verify"], multiple=True, response_length="short", formats=["bullets"])},
    {"axis_ids": ["v5-axis-01", "v5-axis-05", "v5-axis-06"], "input": "Compare option A and option B, then recommend a build plan.", "expected": expected("build", ["build", "compare"], multiple=True)},
    {"axis_ids": ["v5-axis-01", "v5-axis-05", "v5-axis-06"], "input": "Calculate 18*7, then explain what the number means.", "expected": expected("explain", ["explain", "calculate"], multiple=True)},
    {"axis_ids": ["v5-axis-01", "v5-axis-03", "v5-axis-04", "v5-axis-05", "v5-axis-07"], "input": "Review the claim below and then produce a JSON patch plan.", "expected": expected("build", ["build", "verify"], unverified=True, multiple=True, formats=["json"], risk="medium", risk_flags=["unverified_claim"])},
    {"axis_ids": ["v5-axis-01", "v5-axis-04", "v5-axis-05"], "input": "Confirm the API version and then write a concise migration note.", "expected": expected("build", ["build", "verify"], multiple=True, response_length="short")},
    {"axis_ids": ["v5-axis-01", "v5-axis-05"], "input": "Summarize this incident, then list follow-up tasks.", "expected": expected("build", ["build", "summarize"], multiple=True)},
    {"axis_ids": ["v5-axis-01", "v5-axis-05", "v5-axis-06"], "input": "Check if the config path is valid and explain why it matters.", "expected": expected("explain", ["explain", "verify"], multiple=True)},
    {"axis_ids": ["v5-axis-01", "v5-axis-04", "v5-axis-05", "v5-axis-06"], "input": "Compare the two retry policies and then give a one-sentence recommendation.", "expected": expected("explore", ["explore", "compare"], multiple=True, response_length="short")},
    {"axis_ids": ["v5-axis-01", "v5-axis-05"], "input": "Calculate the monthly cost from 12*49, then compare it with the budget.", "expected": expected("explore", ["explore", "calculate", "compare"], multiple=True)},
    {"axis_ids": ["v5-axis-01", "v5-axis-03", "v5-axis-05", "v5-axis-07"], "input": "Verify the premise, search if needed, and summarize the current status.", "expected": expected("summarize", ["summarize", "verify", "search"], current=True, multiple=True, risk="medium", risk_flags=["current_information"])},
    {"axis_ids": ["v5-axis-01", "v5-axis-02", "v5-axis-04", "v5-axis-05", "v5-axis-06"], "input": "Ask which environment this is for, then draft the deployment command.", "expected": expected("clarify", ["clarify", "build"], missing=True, multiple=True, must=["ask_first"])},
    {"axis_ids": ["v5-axis-02", "v5-axis-04", "v5-axis-06"], "input": "Before answering, ask me which database engine is in use.", "expected": expected("clarify", ["clarify"], missing=True, must=["ask_first"])},
    {"axis_ids": ["v5-axis-02", "v5-axis-06"], "input": "I have an error but did not share the log; ask for what you need first.", "expected": expected("clarify", ["clarify"], missing=True, must=["ask_first"])},
    {"axis_ids": ["v5-axis-02", "v5-axis-06"], "input": "Can you fix it? I have not said which file is failing.", "expected": expected("clarify", ["clarify"], missing=True)},
    {"axis_ids": ["v5-axis-02", "v5-axis-04", "v5-axis-05", "v5-axis-06"], "input": "The numbers look wrong; ask me for the spreadsheet before calculating.", "expected": expected("clarify", ["clarify", "calculate"], missing=True, multiple=True, must=["ask_first"])},
    {"axis_ids": ["v5-axis-02", "v5-axis-04", "v5-axis-06"], "input": "Before recommending a path, ask whether this is production or staging.", "expected": expected("clarify", ["clarify"], missing=True, must=["ask_first"])},
    {"axis_ids": ["v5-axis-02", "v5-axis-05", "v5-axis-06"], "input": "I want a migration plan, but the target database is not stated.", "expected": expected("clarify", ["clarify", "build"], missing=True, multiple=True)},
    {"axis_ids": ["v5-axis-02", "v5-axis-04", "v5-axis-05", "v5-axis-06"], "input": "Please ask which API version I mean before you explain the change.", "expected": expected("clarify", ["clarify", "explain"], missing=True, multiple=True, must=["ask_first"])},
    {"axis_ids": ["v5-axis-02", "v5-axis-06"], "input": "We need to decide, but the success metric is not provided.", "expected": expected("clarify", ["clarify"], missing=True)},
    {"axis_ids": ["v5-axis-02", "v5-axis-04", "v5-axis-05", "v5-axis-06"], "input": "Ask me which user group this policy affects before summarizing it.", "expected": expected("clarify", ["clarify", "summarize"], missing=True, multiple=True, must=["ask_first"])},
    {"axis_ids": ["v5-axis-02", "v5-axis-04", "v5-axis-06"], "input": "I only wrote 'make it better'; ask for the artifact first.", "expected": expected("clarify", ["clarify"], missing=True, must=["ask_first"])},
    {"axis_ids": ["v5-axis-03", "v5-axis-04", "v5-axis-07"], "input": "Check the latest Node.js LTS version and cite sources.", "expected": expected("verify", ["verify", "search"], current=True, must=["cite_sources"], risk="medium", risk_flags=["current_information"])},
    {"axis_ids": ["v5-axis-03", "v5-axis-07"], "input": "Verify today's exchange rate before answering.", "expected": expected("verify", ["verify", "search"], current=True, risk="medium", risk_flags=["current_information"])},
    {"axis_ids": ["v5-axis-03", "v5-axis-04", "v5-axis-07"], "input": "The vendor claims the patch fixes CVE-1234; verify it with sources.", "expected": expected("verify", ["verify"], unverified=True, must=["cite_sources"], risk="medium", risk_flags=["unverified_claim"])},
    {"axis_ids": ["v5-axis-03", "v5-axis-04", "v5-axis-07"], "input": "Review the reported figures and avoid overclaiming a winner.", "expected": expected("verify", ["verify"], unverified=True, must=["avoid_overclaim"], risk="medium", risk_flags=["unverified_claim"])},
    {"axis_ids": ["v5-axis-03", "v5-axis-07"], "input": "Is this still the recommended API as of today?", "expected": expected("verify", ["verify", "search"], current=True, risk="medium", risk_flags=["current_information"])},
    {"axis_ids": ["v5-axis-03", "v5-axis-07"], "input": "For the current tax rule, verify before giving guidance.", "expected": expected("verify", ["verify", "search"], current=True, risk="high", risk_flags=["financial", "current_information"])},
    {"axis_ids": ["v5-axis-03", "v5-axis-07"], "input": "Medical dosage advice was proposed in the note; verify and warn me if uncertain.", "expected": expected("verify", ["verify"], unverified=True, risk="high", risk_flags=["medical", "unverified_claim"])},
    {"axis_ids": ["v5-axis-01", "v5-axis-03", "v5-axis-05", "v5-axis-07"], "input": "The security report says credentials leaked; confirm before summarizing.", "expected": expected("summarize", ["summarize", "verify"], unverified=True, multiple=True, risk="high", risk_flags=["security", "unverified_claim"])},
    {"axis_ids": ["v5-axis-03", "v5-axis-07"], "input": "Use the latest release notes to check whether this bug is fixed.", "expected": expected("verify", ["verify", "search"], current=True, risk="medium", risk_flags=["current_information"])},
    {"axis_ids": ["v5-axis-03", "v5-axis-04", "v5-axis-06", "v5-axis-07"], "input": "Do not search; just explain what 'current context' means in this chat.", "expected": expected("explain", ["explain"], must_not=["no_web_search"], risk="low")},
    {"axis_ids": ["v5-axis-04", "v5-axis-06"], "input": "Answer in one sentence.", "expected": expected("respond", ["respond"], response_length="short")},
    {"axis_ids": ["v5-axis-04"], "input": "Summarize the tradeoffs as JSON.", "expected": expected("summarize", ["summarize"], formats=["json"])},
    {"axis_ids": ["v5-axis-04"], "input": "Give bullet points, no table.", "expected": expected("respond", ["respond"], formats=["bullets"], must_not=["no_table"])},
    {"axis_ids": ["v5-axis-04", "v5-axis-06"], "input": "Draft a checklist without code.", "expected": expected("build", ["build"], must_not=["no_code"])},
    {"axis_ids": ["v5-axis-04", "v5-axis-05", "v5-axis-06"], "input": "Compare the options without endorsing either side.", "expected": expected("explore", ["explore", "compare"], must=["preserve_neutrality"])},
    {"axis_ids": ["v5-axis-04", "v5-axis-06"], "input": "Explain briefly and avoid overclaiming.", "expected": expected("explain", ["explain"], response_length="short", must=["avoid_overclaim"])},
    {"axis_ids": ["v5-axis-04", "v5-axis-05", "v5-axis-06"], "input": "Ask me first, then provide a JSON template.", "expected": expected("clarify", ["clarify", "build"], missing=True, multiple=True, formats=["json"], must=["ask_first"])},
    {"axis_ids": ["v5-axis-04"], "input": "Summarize in three bullets and cite sources.", "expected": expected("summarize", ["summarize"], response_length="short", formats=["bullets"], must=["cite_sources"])},
    {"axis_ids": ["v5-axis-04", "v5-axis-06"], "input": "Prepare a migration plan in a code block.", "expected": expected("build", ["build"], formats=["code"])},
    {"axis_ids": ["v5-axis-04", "v5-axis-06"], "input": "Give a long detailed explanation, but no code.", "expected": expected("explain", ["explain"], response_length="long", must_not=["no_code"])},
    {"axis_ids": ["v5-axis-04", "v5-axis-05", "v5-axis-06"], "input": "Respond with a table comparing pros and cons.", "expected": expected("explore", ["explore", "compare"], formats=["table"])},
    {"axis_ids": ["v5-axis-04", "v5-axis-06"], "input": "Keep it concise, neutral, and no table.", "expected": expected("respond", ["respond"], response_length="short", must=["preserve_neutrality"], must_not=["no_table"])},
    {"axis_ids": ["v5-axis-05", "v5-axis-06"], "input": "Does 0.5 equal 1/2? calculate and verify.", "expected": expected("verify", ["verify", "calculate"])},
    {"axis_ids": ["v5-axis-01", "v5-axis-05", "v5-axis-06"], "input": "Compare these two approaches, then explain the deciding factor.", "expected": expected("explain", ["explain", "compare"], multiple=True)},
    {"axis_ids": ["v5-axis-05", "v5-axis-06"], "input": "Explore alternatives and compare their failure modes.", "expected": expected("explore", ["explore", "compare"])},
    {"axis_ids": ["v5-axis-04", "v5-axis-05", "v5-axis-06"], "input": "Calculate 3+5 and return only the result.", "expected": expected("respond", ["respond", "calculate"], response_length="short")},
]


def _cases() -> List[Dict[str, Any]]:
    cases = []
    for index, raw in enumerate(RAW_CASES, start=1):
        cases.append({
            "id": f"v5-critical-ops-{index:03d}",
            "review_status": "draft",
            "split": "validation",
            "source_group": "v5-nonsealed-critical-operations-draft",
            "source_kind": "self_authored_nonsealed_challenge",
            "source_ref": "build/v5_nonsealed_curriculum_plan_v1.json",
            "axis_ids": raw["axis_ids"],
            "language": "en",
            "input": raw["input"],
            "expected": raw["expected"],
            "notes": "Draft label for human review before gate use.",
        })
    return cases


def _summaries(cases: List[Dict[str, Any]]) -> Dict[str, Any]:
    by_axis: Counter[str] = Counter()
    by_intent: Counter[str] = Counter()
    by_operation: Counter[str] = Counter()
    by_constraint: Counter[str] = Counter()
    signal_support: Counter[str] = Counter()
    by_risk: Counter[str] = Counter()
    for case in cases:
        by_axis.update(case["axis_ids"])
        exp = case["expected"]
        by_intent[exp["primary_intent"]] += 1
        by_operation.update(exp["operations"])
        cons = exp["constraints"]
        if cons["response_length"] != "unspecified":
            by_constraint[f"length:{cons['response_length']}"] += 1
        by_constraint.update(f"format:{item}" for item in cons["formats"])
        by_constraint.update(f"must:{item}" for item in cons["must"])
        by_constraint.update(f"must_not:{item}" for item in cons["must_not"])
        for signal, value in exp["information_state"].items():
            if value:
                signal_support[signal] += 1
        by_risk[exp["risk"]["level"]] += 1
    return {
        "case_count": len(cases),
        "by_axis": dict(sorted(by_axis.items())),
        "by_intent": dict(sorted(by_intent.items())),
        "by_operation": dict(sorted(by_operation.items())),
        "by_constraint": dict(sorted(by_constraint.items())),
        "critical_signal_support": dict(sorted(signal_support.items())),
        "by_risk": dict(sorted(by_risk.items())),
    }


def _benchmark_payload(cases: List[Dict[str, Any]]) -> Dict[str, Any]:
    return {
        "schema_version": "pattern-language-benchmark.v1",
        "frozen_at": reproducible_now_iso(),
        "authoring_method": "self-authored non-sealed V5 draft fixture; no sealed text, labels, teacher answers, logits, or hidden reasoning",
        "review_status": "draft",
        "policy": "Non-sealed challenge fixture for V5 Step 3. Human review is required before gate use.",
        "cases": [{
            "id": case["id"],
            "split": case["split"],
            "source_group": case["source_group"],
            "contrast_group": None,
            "language": case["language"],
            "input": case["input"],
            "expected": case["expected"],
        } for case in cases],
    }


def _evaluate_current_route(cases: List[Dict[str, Any]]) -> Dict[str, Any]:
    from semantic_routing import evaluate_plm_extractor
    from semantic_routing.adapter import route
    from semantic_routing.benchmark import parse_plm_benchmark
    benchmark = parse_plm_benchmark(_benchmark_payload(cases))
    return evaluate_plm_extractor(benchmark.cases, lambda text: route(text).packet)


def _write_worksheet(payload: Dict[str, Any], report: Dict[str, Any]) -> None:
    lines = [
        "# V5 Critical Operations Fixture Review Worksheet v1",
        "",
        "Draft fixture for human review. No sealed fixture text or labels were used.",
        "",
        "## Summary",
        "",
        f"- case_count: {payload['summary']['case_count']}",
        f"- review_status: {payload['review_status']}",
        f"- current_route_intent_accuracy: {report['current_route_measurement']['intent_accuracy']}",
        f"- current_route_critical_signal_recall: {report['current_route_measurement']['critical_signal_recall']}",
        f"- current_route_operation_exact_match: {report['current_route_measurement']['operation_exact_match']}",
        "",
        "## Cases",
        "",
        "| id | axes | intent | operations | critical | constraints | risk | input |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for case in payload["cases"]:
        exp = case["expected"]
        critical = ",".join(key for key, value in exp["information_state"].items() if value) or "-"
        cons = exp["constraints"]
        bits = []
        if cons["response_length"] != "unspecified":
            bits.append(f"length:{cons['response_length']}")
        bits.extend(f"format:{item}" for item in cons["formats"])
        bits.extend(f"must:{item}" for item in cons["must"])
        bits.extend(f"must_not:{item}" for item in cons["must_not"])
        lines.append(
            "| "
            f"{case['id']} | {','.join(case['axis_ids'])} | {exp['primary_intent']} | "
            f"{','.join(exp['operations'])} | {critical} | {','.join(bits) or '-'} | "
            f"{exp['risk']['level']} | {case['input'].replace('|', '&#124;')} |"
        )
    WORKSHEET_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def main() -> None:
    plan = json.loads(PLAN_PATH.read_text(encoding="utf-8"))
    cases = _cases()
    summary = _summaries(cases)
    now = reproducible_now_iso()
    payload = {
        "schema_version": "v5-critical-operations-fixture.v1",
        "fixture_id": "v5-critical-operations-fixture-v1",
        "created_at": now,
        "status": "draft_ready_for_human_review",
        "review_status": "draft",
        "source_plan": str(PLAN_PATH.relative_to(ROOT)),
        "policy": {
            "sealed_fixtures_used_as_sources": False,
            "sealed_v4_text_used": False,
            "sealed_v4_labels_used": False,
            "success_pattern_training_allowed": False,
            "human_review_required_before_gate": True,
            "same_cycle_promotion_allowed": False,
        },
        "requirements": {
            "case_count_min": plan["fixture_blueprint"]["case_count_min"],
            "min_cases_by_axis": plan["fixture_blueprint"]["min_cases_by_axis"],
            "sealed_text_overlap_count_required": plan["fixture_blueprint"]["sealed_text_overlap_count_required"],
        },
        "summary": summary,
        "cases": cases,
    }
    measurement = _evaluate_current_route(cases)
    report = {
        "schema_version": "v5-critical-operations-fixture-report.v1",
        "generated_at": now,
        "fixture": str(FIXTURE_PATH.relative_to(ROOT)),
        "policy": payload["policy"],
        "status": "draft_fixture_created_not_a_gate",
        "current_route_measurement_is_gate": False,
        "current_route_measurement": measurement,
        "summary": summary,
        "next_step": {"step": 4, "name": "router_generalization_changes", "output": "build/v5_router_generalization_report.json"},
    }
    FIXTURE_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    REPORT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    _write_worksheet(payload, report)
    print(f"wrote {FIXTURE_PATH.relative_to(ROOT)}")
    print(f"wrote {REPORT_PATH.relative_to(ROOT)}")
    print(f"wrote {WORKSHEET_PATH.relative_to(ROOT)}")
    print(json.dumps({
        "case_count": summary["case_count"],
        "by_axis": summary["by_axis"],
        "current_route": {
            "intent_accuracy": measurement["intent_accuracy"],
            "critical_signal_recall": measurement["critical_signal_recall"],
            "operation_exact_match": measurement["operation_exact_match"],
            "constraint_exact_match": measurement["constraint_exact_match"],
            "risk_exact_match": measurement["risk_exact_match"],
            "error_count": len(measurement["errors"]),
        },
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
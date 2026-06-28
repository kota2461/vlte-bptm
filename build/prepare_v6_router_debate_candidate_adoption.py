"""Prepare V6 router-debate candidates for non-sealed adoption review.

This does not merge candidates into the main PLM benchmark. It creates an
importable Pattern Language benchmark lane and an adoption plan that a human can
approve before training or gate use.
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

CANDIDATE_FIXTURE_PATH = ROOT / "tests" / "fixtures" / "v6_router_debate_candidate_fixture_v1.json"
SELECTION_PATH = ROOT / "build" / "v6_router_debate_candidate_selection_v1.json"
IMPORT_BENCHMARK_PATH = ROOT / "tests" / "fixtures" / "v6_router_debate_candidate_benchmark_v1.json"
ADOPTION_PLAN_PATH = ROOT / "build" / "v6_router_debate_candidate_adoption_plan_v1.json"
IMPORT_REPORT_PATH = ROOT / "build" / "v6_router_debate_candidate_import_report_v1.json"
ADOPTION_WORKSHEET_PATH = ROOT / "build" / "v6_router_debate_candidate_adoption_worksheet_v1.md"


def _load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def _benchmark_cases(cases: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
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
    ]


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


def _review_items(cases: list[dict[str, Any]]) -> list[dict[str, Any]]:
    items = []
    for case in cases:
        items.append(
            {
                "id": case["id"],
                "source_topic_id": case["source_topic_id"],
                "recommended_decision": "adopt_nonsealed_after_human_review",
                "review_status": "pending_human_review",
                "allowed_use_before_review": "review_only",
                "allowed_use_after_review": "nonsealed_replay_and_training_candidate",
                "same_cycle_gate_use_allowed": False,
                "input": case["input"],
                "expected": case["expected"],
                "review_focus": [
                    "primary_intent",
                    "operations",
                    "critical_signals",
                    "constraints",
                    "risk",
                    "source_topic_specificity",
                ],
                "selection_reasons": case["selection_reasons"],
                "candidate_value_score": case["candidate_value_score"],
            }
        )
    return items


def _summarize(cases: list[dict[str, Any]]) -> dict[str, Any]:
    by_intent = Counter(case["expected"]["primary_intent"] for case in cases)
    by_risk = Counter(case["expected"]["risk"]["level"] for case in cases)
    by_operation: Counter[str] = Counter()
    by_constraint: Counter[str] = Counter()
    signal_support: Counter[str] = Counter()
    for case in cases:
        expected = case["expected"]
        by_operation.update(expected["operations"])
        by_constraint.update(f"must:{item}" for item in expected["constraints"]["must"])
        by_constraint.update(f"must_not:{item}" for item in expected["constraints"]["must_not"])
        for signal, value in expected["information_state"].items():
            if value:
                signal_support[signal] += 1
    return {
        "case_count": len(cases),
        "by_intent": dict(sorted(by_intent.items())),
        "by_operation": dict(sorted(by_operation.items())),
        "by_constraint": dict(sorted(by_constraint.items())),
        "critical_signal_support": dict(sorted(signal_support.items())),
        "by_risk": dict(sorted(by_risk.items())),
    }


def _write_worksheet(plan: dict[str, Any], benchmark: dict[str, Any], report: dict[str, Any]) -> None:
    lines = [
        "# V6 Router Debate Candidate Adoption Worksheet v1",
        "",
        "This worksheet is for human review before inserting router-debate candidates into any non-sealed training or replay lane.",
        "Raw debate turns remain review evidence only.",
        "",
        "## Contract",
        "",
        f"- import_benchmark: `{plan['outputs']['import_benchmark']}`",
        f"- candidate_count: {plan['summary']['candidate_count']}",
        f"- recommended_adopt_count: {plan['summary']['recommended_adopt_count']}",
        f"- review_status: {plan['review_status']}",
        f"- current_route_error_count: {report['current_route_measurement']['error_count']}",
        "- sealed use: false",
        "- same-cycle gate use: false",
        "",
        "## Review Items",
        "",
        "| id | decision | intent | operations | risk | input |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for item in plan["review_items"]:
        expected = item["expected"]
        text = item["input"].replace("|", "&#124;").replace("\n", "<br>")
        lines.append(
            "| "
            f"{item['id']} | {item['recommended_decision']} | "
            f"{expected['primary_intent']} | {','.join(expected['operations'])} | "
            f"{expected['risk']['level']} | {text} |"
        )
    lines.extend(
        [
            "",
            "## Human Review Output",
            "",
            "To adopt, copy this plan and change each accepted item to `decision: adopt_nonsealed`, then regenerate the import lane. Keep rejected items as `hold` or `reject` with a reason.",
        ]
    )
    ADOPTION_WORKSHEET_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def main() -> None:
    generated_at = datetime.now(timezone.utc).isoformat()
    candidate_fixture = _load(CANDIDATE_FIXTURE_PATH)
    selection = _load(SELECTION_PATH)
    cases = candidate_fixture["cases"]
    summary = _summarize(cases)
    policy = {
        "sealed_fixtures_used_as_sources": False,
        "sealed_text_used": False,
        "sealed_labels_used": False,
        "raw_debate_logs_direct_training_allowed": False,
        "topic_synthesis_used": True,
        "human_review_required_before_training": True,
        "human_review_required_before_gate": True,
        "same_cycle_promotion_allowed": False,
        "import_benchmark_is_directly_trainable": False,
    }
    benchmark = {
        "schema_version": "pattern-language-benchmark.v1",
        "frozen_at": generated_at,
        "authoring_method": "V6 router debate candidates prepared as non-sealed import lane; pending human review",
        "review_status": "draft",
        "policy": "Non-sealed import lane. Candidate labels require human review before training or gate use. Raw debate turns are not training data.",
        "cases": _benchmark_cases(cases),
    }
    parsed = parse_plm_benchmark(benchmark)
    measurement = evaluate_plm_extractor(parsed.cases, lambda text: route(text).packet)
    compact = _compact_measurement(measurement)
    review_items = _review_items(cases)
    plan = {
        "schema_version": "v6-router-debate-candidate-adoption-plan.v1",
        "generated_at": generated_at,
        "status": "ready_for_human_review_before_adoption",
        "review_status": "pending_human_review",
        "source_candidate_fixture": _rel(CANDIDATE_FIXTURE_PATH),
        "source_selection": _rel(SELECTION_PATH),
        "policy": policy,
        "outputs": {
            "import_benchmark": _rel(IMPORT_BENCHMARK_PATH),
            "import_report": _rel(IMPORT_REPORT_PATH),
            "adoption_worksheet": _rel(ADOPTION_WORKSHEET_PATH),
        },
        "summary": {
            "candidate_count": len(cases),
            "recommended_adopt_count": len(review_items),
            "held_source_topics": selection["summary"]["held_topics"],
            "current_route_gap_count": compact["error_count"],
            "import_benchmark_review_status": benchmark["review_status"],
        },
        "candidate_summary": summary,
        "review_items": review_items,
    }
    report = {
        "schema_version": "v6-router-debate-candidate-import-report.v1",
        "generated_at": generated_at,
        "status": "import_lane_ready_pending_human_review",
        "candidate_readiness": True,
        "adoption_plan": _rel(ADOPTION_PLAN_PATH),
        "import_benchmark": _rel(IMPORT_BENCHMARK_PATH),
        "policy": policy,
        "summary": summary,
        "current_route_measurement_is_gate": False,
        "current_route_measurement": compact,
        "errors": measurement["errors"],
        "next_step": {
            "name": "human_review_then_adopt_nonsealed_router_debate_candidates",
            "input": _rel(ADOPTION_WORKSHEET_PATH),
            "output": _rel(IMPORT_BENCHMARK_PATH),
        },
    }
    _write_json(IMPORT_BENCHMARK_PATH, benchmark)
    _write_json(ADOPTION_PLAN_PATH, plan)
    _write_json(IMPORT_REPORT_PATH, report)
    _write_worksheet(plan, benchmark, report)
    print(json.dumps({
        "status": report["status"],
        "import_benchmark": report["import_benchmark"],
        "summary": plan["summary"],
        "current_route_measurement": compact,
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

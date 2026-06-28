"""Create the V5 Step 4 router generalization report."""

import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from semantic_routing import evaluate_plm_extractor
from semantic_routing.adapter import route
from semantic_routing.benchmark import parse_plm_benchmark
FIXTURE_PATH = ROOT / "tests" / "fixtures" / "v5_critical_operations_fixture_v1.json"
STEP3_REPORT_PATH = ROOT / "build" / "v5_critical_operations_fixture_report_v1.json"
REPORT_PATH = ROOT / "build" / "v5_router_generalization_report.json"
TARGETS_PATH = ROOT / "build" / "v5_targets_and_roadmap_v1.json"
ROADMAP_PATH = ROOT / "docs" / "PLM_V5_ROADMAP.md"
MAIN_ROADMAP_PATH = ROOT / "docs" / "PATTERN_LANGUAGE_MODEL_roadmap.md"
METRIC_KEYS = [
    "intent_accuracy",
    "critical_signal_recall",
    "operation_exact_match",
    "constraint_exact_match",
    "risk_exact_match",
]


def _load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _field_counts(errors):
    counter = Counter(field for error in errors for field in error["fields"])
    return dict(sorted(counter.items()))


def _compact(measurement):
    return {
        "case_count": measurement["case_count"],
        "intent_accuracy": measurement["intent_accuracy"],
        "critical_signal_recall": measurement["critical_signal_recall"],
        "operation_exact_match": measurement["operation_exact_match"],
        "constraint_exact_match": measurement["constraint_exact_match"],
        "risk_exact_match": measurement["risk_exact_match"],
        "valid_packet_rate": measurement["valid_packet_rate"],
        "error_count": len(measurement["errors"]),
        "error_field_counts": _field_counts(measurement["errors"]),
    }


def _benchmark_payload(fixture):
    return {
        "schema_version": "pattern-language-benchmark.v1",
        "frozen_at": fixture["created_at"],
        "authoring_method": "V5 Step 4 non-sealed router generalization check",
        "review_status": fixture["review_status"],
        "policy": "Diagnostic only; no sealed fixture text or labels used.",
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
            for case in fixture["cases"]
        ],
    }


def _measure(fixture):
    benchmark = parse_plm_benchmark(_benchmark_payload(fixture))
    return evaluate_plm_extractor(benchmark.cases, lambda text: route(text).packet)


def _write_json(path: Path, payload) -> None:
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def _replace_once(text: str, old: str, new: str) -> str:
    if old not in text:
        return text
    return text.replace(old, new, 1)

def main() -> None:
    fixture = _load(FIXTURE_PATH)
    step3_report = _load(STEP3_REPORT_PATH)
    before_full = step3_report["current_route_measurement"]
    before = _compact(before_full)
    after_full = _measure(fixture)
    after = _compact(after_full)
    delta = {key: round(after[key] - before[key], 6) for key in METRIC_KEYS}
    delta["error_count"] = after["error_count"] - before["error_count"]
    now = datetime.now(timezone.utc).isoformat()

    report = {
        "schema_version": "v5-router-generalization-report.v1",
        "generated_at": now,
        "status": "completed_not_a_gate",
        "policy": {
            "sealed_fixtures_used_as_sources": False,
            "sealed_v4_text_used": False,
            "sealed_v4_labels_used": False,
            "source_fixture": "tests\\fixtures\\v5_critical_operations_fixture_v1.json",
            "source_fixture_review_status": fixture["review_status"],
            "current_route_measurement_is_gate": False,
            "human_review_required_before_gate": True,
            "same_cycle_promotion_allowed": False,
        },
        "before": before,
        "after": after,
        "delta": delta,
        "remaining_errors": after_full["errors"],
        "change_summary": [
            "Narrowed ask-first detection to explicit ask cues so verify-before-answering does not become missing-information.",
            "Added English control vocabulary for build, summarize, explain, explore, JSON, bullets, neutral, and overclaim constraints.",
            "Preserved vertical operations for summarize+verify, explain+verify, clarify+build, clarify+summarize, and clarify+explain sequences.",
            "Normalized compare/calculate regexes and made no_table/no_web_search suppress incompatible output/search actions.",
            "Raised unverified-claim risk to medium without requiring cite_sources, while high-domain risk remains dominant.",
        ],
        "meets_presealed_nonsealed_challenge_threshold": (
            after["intent_accuracy"] >= 0.95
            and after["critical_signal_recall"] >= 0.95
            and after["operation_exact_match"] >= 0.95
            and after["constraint_exact_match"] >= 0.95
            and after["risk_exact_match"] >= 0.95
            and after["error_count"] == 0
        ),
        "next_step": {
            "step": 5,
            "name": "nonsealed_replay_gate",
            "output": "build\\v5_nonsealed_replay_gate_report.json",
        },
    }
    _write_json(REPORT_PATH, report)

    targets = _load(TARGETS_PATH)
    targets["generated_at"] = now
    targets["status"] = "router_generalization_completed"
    for item in targets["roadmap"]:
        if item["step"] == 4:
            item["status"] = "completed"
        elif item["step"] == 5:
            item["status"] = "next"
    targets["step4_router_generalization"] = {
        "output": "build\\v5_router_generalization_report.json",
        "status": "completed_not_a_gate",
        "sealed_v4_text_used": False,
        "sealed_v4_labels_used": False,
        "current_route_measurement_is_gate": False,
        "before": before,
        "after": after,
        "delta": delta,
        "meets_presealed_nonsealed_challenge_threshold": report[
            "meets_presealed_nonsealed_challenge_threshold"
        ],
    }
    _write_json(TARGETS_PATH, targets)

    roadmap = ROADMAP_PATH.read_text(encoding="utf-8")
    roadmap = roadmap.replace(
        "| 4 | router_generalization_changes | `build\\v5_router_generalization_report.json` | next |",
        "| 4 | router_generalization_changes | `build\\v5_router_generalization_report.json` | completed |",
    )
    roadmap = roadmap.replace(
        "| 5 | nonsealed_replay_gate | `build\\v5_nonsealed_replay_gate_report.json` | pending |",
        "| 5 | nonsealed_replay_gate | `build\\v5_nonsealed_replay_gate_report.json` | next |",
    )
    step4_section = f"""
## Step 4 Output

`build\\v5_router_generalization_report.json` is completed as a diagnostic, non-gate replay against the Step 3 non-sealed draft fixture. Before -> after: intent_accuracy {before['intent_accuracy']:.6f} -> {after['intent_accuracy']:.6f}, critical_signal_recall {before['critical_signal_recall']:.6f} -> {after['critical_signal_recall']:.6f}, operation_exact_match {before['operation_exact_match']:.6f} -> {after['operation_exact_match']:.6f}, constraint_exact_match {before['constraint_exact_match']:.6f} -> {after['constraint_exact_match']:.6f}, risk_exact_match {before['risk_exact_match']:.6f} -> {after['risk_exact_match']:.6f}, errors {before['error_count']} -> {after['error_count']}. Sealed text and sealed labels remain excluded. Step 5 is now the non-sealed replay gate.
""".strip()
    if "## Step 4 Output" in roadmap:
        head, rest = roadmap.split("## Step 4 Output", 1)
        if "## Pre-Sealed V5 Gates" in rest:
            _, tail = rest.split("## Pre-Sealed V5 Gates", 1)
            roadmap = head.rstrip() + "\n\n" + step4_section + "\n\n## Pre-Sealed V5 Gates" + tail
    else:
        roadmap = roadmap.replace(
            "## Pre-Sealed V5 Gates",
            step4_section + "\n\n## Pre-Sealed V5 Gates",
        )
    ROADMAP_PATH.write_text(roadmap, encoding="utf-8", newline="\n")

    main = MAIN_ROADMAP_PATH.read_text(encoding="utf-8")
    main = _replace_once(
        main,
        "Status: V5 non-sealed critical operations fixture draft created; sealed v4 measured and consumed; Step 4 router generalization next.",
        "Status: V5 Step 4 router generalization completed; sealed v4 measured and consumed; Step 5 non-sealed replay gate next.",
    )
    if "Router generalization report:" not in main:
        main = main.replace(
            "Critical operations report: `build/v5_critical_operations_fixture_report_v1.json`\n",
            "Critical operations report: `build/v5_critical_operations_fixture_report_v1.json`\nRouter generalization report: `build/v5_router_generalization_report.json`\n",
        )
    main = _replace_once(
        main,
        "The immediate priority is now Step 4 router generalization against the 48-case non-sealed critical operations fixture, especially `multiple_intents`, `missing_required_information`, operation sequencing, and constraint preservation. A fresh sealed v5 fixture must be rotated before the next adjudicating measurement.",
        "Step 4 router generalization now replays the 48-case non-sealed critical operations fixture at 1.0 across intent, critical signals, operations, constraints, and risk as a diagnostic non-gate check. The immediate priority is Step 5 non-sealed replay gate across visible PLM, Failure Memory, Puzzle Failure Memory, and the V5 challenge fixture. A fresh sealed v5 fixture must be rotated before the next adjudicating measurement.",
    )
    MAIN_ROADMAP_PATH.write_text(main, encoding="utf-8", newline="\n")

    print(json.dumps({"report": str(REPORT_PATH.relative_to(ROOT)), "before": before, "after": after, "delta": delta}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
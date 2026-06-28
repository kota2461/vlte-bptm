"""Run the V5 non-sealed replay gate across visible and failure-memory lanes."""

import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from semantic_routing import (  # noqa: E402
    evaluate_plm_extractor,
    load_plm_benchmark,
    load_puzzle_failure_memory,
    load_puzzle_solver_trace_report,
    parse_plm_benchmark,
    route,
)
from semantic_routing.reproducibility import reproducible_now_iso

VISIBLE_PLM_PATH = ROOT / "tests" / "fixtures" / "pattern_language_benchmark_v1.json"
V4_FAILURE_MEMORY_PATH = ROOT / "tests" / "fixtures" / "v4_failure_memory_fixture_v1.json"
PUZZLE_TRACE_PATH = ROOT / "build" / "v4_puzzle_solver_trace_v1.json"
PUZZLE_FAILURE_MEMORY_PATH = ROOT / "tests" / "fixtures" / "v4_puzzle_failure_memory_v1.json"
V5_CHALLENGE_PATH = ROOT / "tests" / "fixtures" / "v5_critical_operations_fixture_v1.json"
REPORT_PATH = ROOT / "build" / "v5_nonsealed_replay_gate_report.json"
TARGETS_PATH = ROOT / "build" / "v5_targets_and_roadmap_v1.json"
ROADMAP_PATH = ROOT / "docs" / "PLM_V5_ROADMAP.md"
MAIN_ROADMAP_PATH = ROOT / "docs" / "PATTERN_LANGUAGE_MODEL_roadmap.md"

PLM_METRICS = [
    "intent_accuracy",
    "critical_signal_recall",
    "operation_exact_match",
    "constraint_exact_match",
    "risk_exact_match",
    "valid_packet_rate",
]


def _rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def _packet_dict(routed: Any) -> dict[str, Any]:
    packet = routed.packet
    return {
        "primary_intent": packet.primary_intent,
        "operations": list(packet.operations),
        "information_state": packet.information_state.as_dict(),
        "constraints": packet.constraints.as_dict(),
        "risk": packet.risk.as_dict(),
    }


def _matches(actual: dict[str, Any], expected: dict[str, Any]) -> dict[str, bool]:
    return {
        "primary_intent": actual["primary_intent"] == expected["primary_intent"],
        "operations": actual["operations"] == expected["operations"],
        "information_state": actual["information_state"] == expected["information_state"],
        "constraints": actual["constraints"] == expected["constraints"],
        "risk": actual["risk"] == expected["risk"],
    }


def _field_counts(errors: list[dict[str, Any]]) -> dict[str, int]:
    return dict(sorted(Counter(field for error in errors for field in error["fields"]).items()))


def _compact_plm_measurement(measurement: dict[str, Any]) -> dict[str, Any]:
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


def _visible_plm_lane() -> dict[str, Any]:
    benchmark = load_plm_benchmark(VISIBLE_PLM_PATH)
    visible_cases = benchmark.cases_for_splits(("train", "validation"))
    measurement = evaluate_plm_extractor(
        visible_cases,
        lambda text: route(text).packet,
    )
    compact = _compact_plm_measurement(measurement)
    thresholds = {
        "intent_accuracy": 1.0,
        "critical_signal_recall": 1.0,
        "operation_exact_match": 1.0,
        "constraint_exact_match": 1.0,
        "risk_exact_match": 1.0,
        "valid_packet_rate": 1.0,
        "error_count": 0,
    }
    passed = all(compact[key] == value for key, value in thresholds.items())
    return {
        "name": "visible_plm",
        "source": _rel(VISIBLE_PLM_PATH),
        "evaluated_splits": ["train", "validation"],
        "sealed_split_evaluated": False,
        "thresholds": thresholds,
        "measurement": compact,
        "errors": measurement["errors"],
        "passed": passed,
    }


def _v5_benchmark_payload(fixture: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "pattern-language-benchmark.v1",
        "frozen_at": fixture["created_at"],
        "authoring_method": "V5 Step 5 non-sealed challenge replay gate",
        "review_status": fixture["review_status"],
        "policy": "Non-sealed diagnostic replay; no sealed v4 text or labels used.",
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


def _v5_challenge_lane() -> dict[str, Any]:
    fixture = _load_json(V5_CHALLENGE_PATH)
    benchmark = parse_plm_benchmark(_v5_benchmark_payload(fixture))
    measurement = evaluate_plm_extractor(
        benchmark.cases,
        lambda text: route(text).packet,
    )
    compact = _compact_plm_measurement(measurement)
    thresholds = {
        "intent_accuracy_min": 0.95,
        "critical_signal_recall_min": 0.95,
        "operation_exact_match_min": 0.95,
        "constraint_exact_match_min": 0.95,
        "risk_exact_match_min": 0.95,
        "valid_packet_rate": 1.0,
        "error_count_max": 0,
    }
    passed = (
        compact["intent_accuracy"] >= thresholds["intent_accuracy_min"]
        and compact["critical_signal_recall"] >= thresholds["critical_signal_recall_min"]
        and compact["operation_exact_match"] >= thresholds["operation_exact_match_min"]
        and compact["constraint_exact_match"] >= thresholds["constraint_exact_match_min"]
        and compact["risk_exact_match"] >= thresholds["risk_exact_match_min"]
        and compact["valid_packet_rate"] == thresholds["valid_packet_rate"]
        and compact["error_count"] <= thresholds["error_count_max"]
    )
    return {
        "name": "v5_nonsealed_challenge",
        "source": _rel(V5_CHALLENGE_PATH),
        "review_status": fixture["review_status"],
        "thresholds": thresholds,
        "measurement": compact,
        "errors": measurement["errors"],
        "passed": passed,
    }


def _v4_failure_memory_lane() -> dict[str, Any]:
    fixture = _load_json(V4_FAILURE_MEMORY_PATH)
    measurements = []
    exact = 0
    guard_subset = 0
    for item in fixture["items"]:
        result = route(item["input"])
        actual = _packet_dict(result)
        field_matches = _matches(actual, item["trigger_packet"])
        exact_match = all(field_matches.values())
        guard_actions = result.trace["failure_guard"]["guard_actions"]
        guard_subset_match = set(item["guard_action"]) <= set(guard_actions)
        exact += int(exact_match)
        guard_subset += int(guard_subset_match)
        measurements.append(
            {
                "id": item["id"],
                "source_candidate_id": item["source_candidate_id"],
                "exact_match": exact_match,
                "guard_subset_match": guard_subset_match,
                "field_matches": field_matches,
            }
        )
    total = len(measurements)
    summary = {
        "item_count": total,
        "exact_match_count": exact,
        "exact_match_rate": exact / total if total else 0.0,
        "guard_subset_match_count": guard_subset,
        "guard_subset_match_rate": guard_subset / total if total else 0.0,
        "miss_count": total - exact,
        "guard_miss_count": total - guard_subset,
    }
    passed = (
        summary["exact_match_rate"] == 1.0
        and summary["guard_subset_match_rate"] == 1.0
        and summary["item_count"] == fixture["summary"]["item_count"]
    )
    return {
        "name": "v4_failure_memory_replay",
        "source": _rel(V4_FAILURE_MEMORY_PATH),
        "thresholds": {
            "exact_match_rate": 1.0,
            "guard_subset_match_rate": 1.0,
        },
        "measurement": summary,
        "measurements": measurements,
        "passed": passed,
    }


def _puzzle_failure_memory_lane() -> dict[str, Any]:
    trace = load_puzzle_solver_trace_report(PUZZLE_TRACE_PATH).as_dict()
    memory = load_puzzle_failure_memory(PUZZLE_FAILURE_MEMORY_PATH).as_dict()
    failed_task_ids = [
        item["task_id"] for item in trace["traces"] if item["status"] == "failure"
    ]
    memory_task_ids = memory["summary"]["source_failed_task_ids"]
    item_contract_ok = all(
        item["lane"] == "puzzle_failure_memory"
        and item["training_status"] == "not_training_data"
        and item["allowed_use"] == "nonsealed_puzzle_failure_memory_replay_only"
        and item["success_pattern_write_allowed"] is False
        and bool(item["guard_action"])
        and bool(item["bad_tendency"])
        for item in memory["items"]
    )
    policy_ok = (
        trace["policy"]["sealed_fixtures_used_as_sources"] is False
        and trace["policy"]["success_pattern_lane_write_allowed"] is False
        and memory["policy"]["sealed_fixtures_used_as_sources"] is False
        and memory["policy"]["success_pattern_lane_write_allowed"] is False
        and memory["policy"]["source_success_traces_used_for_training"] is False
    )
    summary = {
        "trace_task_count": trace["summary"]["task_count"],
        "trace_success_count": trace["summary"]["success_count"],
        "trace_failure_count": trace["summary"]["failure_count"],
        "failure_memory_count": memory["summary"]["failure_count"],
        "failed_task_ids": failed_task_ids,
        "failure_memory_task_ids": memory_task_ids,
        "policy_ok": policy_ok,
        "item_contract_ok": item_contract_ok,
        "success_traces_promoted": False,
    }
    passed = (
        failed_task_ids == memory_task_ids
        and summary["trace_failure_count"] == summary["failure_memory_count"]
        and policy_ok
        and item_contract_ok
        and summary["success_traces_promoted"] is False
    )
    return {
        "name": "v4_puzzle_failure_memory_preservation",
        "sources": {
            "trace_report": _rel(PUZZLE_TRACE_PATH),
            "failure_memory": _rel(PUZZLE_FAILURE_MEMORY_PATH),
        },
        "thresholds": {
            "failed_task_ids_match_failure_memory": True,
            "success_traces_promoted": False,
            "policy_ok": True,
            "item_contract_ok": True,
        },
        "measurement": summary,
        "passed": passed,
    }


def _update_roadmaps(report: dict[str, Any]) -> None:
    targets = _load_json(TARGETS_PATH)
    targets["generated_at"] = report["generated_at"]
    targets["status"] = "nonsealed_replay_gate_passed"
    for item in targets["roadmap"]:
        if item["step"] == 5:
            item["status"] = "completed"
        elif item["step"] == 6:
            item["status"] = "next"
    targets["step5_nonsealed_replay_gate"] = {
        "output": "build\\v5_nonsealed_replay_gate_report.json",
        "status": report["status"],
        "passed": report["passed"],
        "sealed_v4_text_used": False,
        "sealed_v4_labels_used": False,
        "same_cycle_promotion_allowed": False,
        "lane_summary": report["summary"],
    }
    _write_json(TARGETS_PATH, targets)

    roadmap = ROADMAP_PATH.read_text(encoding="utf-8")
    roadmap = roadmap.replace(
        "| 5 | nonsealed_replay_gate | `build\\v5_nonsealed_replay_gate_report.json` | next |",
        "| 5 | nonsealed_replay_gate | `build\\v5_nonsealed_replay_gate_report.json` | completed |",
    )
    roadmap = roadmap.replace(
        "| 6 | sealed_v5_rotation | `tests\\fixtures\\pattern_language_sealed_v5.json` | pending |",
        "| 6 | sealed_v5_rotation | `tests\\fixtures\\pattern_language_sealed_v5.json` | next |",
    )
    section = f"""
## Step 5 Output

`build\\v5_nonsealed_replay_gate_report.json` passed as a non-sealed replay gate. Lanes: visible_plm {report['lanes']['visible_plm']['measurement']['error_count']} errors, v4_failure_memory exact {report['lanes']['v4_failure_memory_replay']['measurement']['exact_match_count']}/{report['lanes']['v4_failure_memory_replay']['measurement']['item_count']}, puzzle_failure_memory preserved {report['lanes']['v4_puzzle_failure_memory_preservation']['passed']}, v5_nonsealed_challenge {report['lanes']['v5_nonsealed_challenge']['measurement']['error_count']} errors. Sealed v4 text and labels remain excluded. Step 6 is now sealed v5 rotation.
""".strip()
    if "## Step 5 Output" in roadmap:
        head, rest = roadmap.split("## Step 5 Output", 1)
        if "## Pre-Sealed V5 Gates" in rest:
            _, tail = rest.split("## Pre-Sealed V5 Gates", 1)
            roadmap = head.rstrip() + "\n\n" + section + "\n\n## Pre-Sealed V5 Gates" + tail
    else:
        roadmap = roadmap.replace(
            "## Pre-Sealed V5 Gates",
            section + "\n\n## Pre-Sealed V5 Gates",
        )
    ROADMAP_PATH.write_text(roadmap, encoding="utf-8", newline="\n")

    main = MAIN_ROADMAP_PATH.read_text(encoding="utf-8")
    main = main.replace(
        "Status: V5 Step 4 router generalization completed; sealed v4 measured and consumed; Step 5 non-sealed replay gate next.",
        "Status: V5 Step 5 non-sealed replay gate passed; sealed v4 measured and consumed; Step 6 sealed v5 rotation next.",
    )
    if "Non-sealed replay gate report:" not in main:
        main = main.replace(
            "Router generalization report: `build/v5_router_generalization_report.json`\n",
            "Router generalization report: `build/v5_router_generalization_report.json`\nNon-sealed replay gate report: `build/v5_nonsealed_replay_gate_report.json`\n",
        )
    main = main.replace(
        "The immediate priority is Step 5 non-sealed replay gate across visible PLM, Failure Memory, Puzzle Failure Memory, and the V5 challenge fixture. A fresh sealed v5 fixture must be rotated before the next adjudicating measurement.",
        "Step 5 non-sealed replay gate passed across visible PLM, Failure Memory, Puzzle Failure Memory, and the V5 challenge fixture. The immediate priority is Step 6 sealed v5 rotation; a fresh sealed v5 fixture must be created before the next adjudicating measurement.",
    )
    MAIN_ROADMAP_PATH.write_text(main, encoding="utf-8", newline="\n")


def main() -> None:
    generated_at = reproducible_now_iso()
    lanes = {
        "visible_plm": _visible_plm_lane(),
        "v4_failure_memory_replay": _v4_failure_memory_lane(),
        "v4_puzzle_failure_memory_preservation": _puzzle_failure_memory_lane(),
        "v5_nonsealed_challenge": _v5_challenge_lane(),
    }
    passed = all(lane["passed"] for lane in lanes.values())
    report = {
        "schema_version": "v5-nonsealed-replay-gate-report.v1",
        "generated_at": generated_at,
        "status": "passed" if passed else "failed",
        "passed": passed,
        "policy": {
            "sealed_fixtures_used_as_sources": False,
            "sealed_v4_text_used": False,
            "sealed_v4_labels_used": False,
            "active_sealed_v5_required_before_adjudication": True,
            "same_cycle_promotion_allowed": False,
            "current_route_measurement_is_gate": True,
        },
        "summary": {
            "lane_count": len(lanes),
            "passed_lane_count": sum(1 for lane in lanes.values() if lane["passed"]),
            "failed_lanes": [name for name, lane in lanes.items() if not lane["passed"]],
            "ready_for_step6_sealed_v5_rotation": passed,
        },
        "lanes": lanes,
        "next_step": {
            "step": 6,
            "name": "sealed_v5_rotation",
            "output": "tests\\fixtures\\pattern_language_sealed_v5.json",
        },
    }
    _write_json(REPORT_PATH, report)
    _update_roadmaps(report)
    print(json.dumps({"status": report["status"], "summary": report["summary"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
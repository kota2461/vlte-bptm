"""Run the V8 non-sealed replay gate after human approval.

This gate intentionally uses only human-approved, non-sealed V8 recovery
samples plus the previous V7 non-sealed gate status. It does not open a sealed
fixture and it does not turn the prior provisional replay into sealed evidence.
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


V7_GATE_PATH = ROOT / "build" / "v7_nonsealed_replay_gate_report_v1.json"
V8_BENCHMARK_PATH = ROOT / "tests" / "fixtures" / "v8_recovery_priority_review_candidate_benchmark_v1.json"
V8_PROVISIONAL_REPORT_PATH = ROOT / "build" / "v8_recovery_priority_review_provisional_test_report_v1.json"
REPORT_PATH = ROOT / "build" / "v8_nonsealed_replay_gate_report_v1.json"
REPORT_MD_PATH = ROOT / "build" / "v8_nonsealed_replay_gate_report_v1.md"


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


def _field_counts(errors: list[dict[str, Any]]) -> dict[str, int]:
    return dict(sorted(Counter(field for error in errors for field in error["fields"]).items()))


def _compact_measurement(measurement: dict[str, Any]) -> dict[str, Any]:
    return {
        "case_count": measurement["case_count"],
        "valid_packet_rate": measurement["valid_packet_rate"],
        "intent_accuracy": measurement["intent_accuracy"],
        "critical_signal_recall": measurement["critical_signal_recall"],
        "operation_exact_match": measurement["operation_exact_match"],
        "constraint_exact_match": measurement["constraint_exact_match"],
        "risk_exact_match": measurement["risk_exact_match"],
        "error_count": len(measurement["errors"]),
        "error_field_counts": _field_counts(measurement["errors"]),
    }


def _passed_exact(compact: dict[str, Any]) -> bool:
    return compact["valid_packet_rate"] == 1.0 and compact["error_count"] == 0


def _v8_priority_lane() -> dict[str, Any]:
    payload = _load_json(V8_BENCHMARK_PATH)
    benchmark = parse_plm_benchmark(payload)
    measurement = evaluate_plm_extractor(benchmark.cases, lambda text: route(text).packet)
    compact = _compact_measurement(measurement)
    return {
        "name": "v8_recovery_priority_review_approved",
        "source": _rel(V8_BENCHMARK_PATH),
        "review_status": payload["review_status"],
        "category_counts": dict(sorted(Counter(case.contrast_group for case in benchmark.cases).items())),
        "passed_exact": _passed_exact(compact),
        "measurement": compact,
        "errors": measurement["errors"],
    }


def _summary(v7_gate: dict[str, Any], lane: dict[str, Any]) -> dict[str, Any]:
    v7_summary = v7_gate["summary"]
    v7_passed = v7_gate.get("status") == "passed" and v7_gate.get("passed") is True
    return {
        "dependency_v7_gate_passed": v7_passed,
        "dependency_v7_required_error_count": v7_summary["required_error_count"],
        "dependency_v7_diagnostic_error_count": v7_summary["diagnostic_error_count"],
        "required_lane_count": 1,
        "required_passed_lane_count": 1 if lane["passed_exact"] else 0,
        "required_error_count": lane["measurement"]["error_count"],
        "v8_priority_review_case_count": lane["measurement"]["case_count"],
        "v8_priority_review_exact": lane["passed_exact"],
        "ready_for_step6_sealed_v8_rotation_review": (
            v7_passed
            and v7_summary["required_error_count"] == 0
            and lane["passed_exact"]
        ),
    }


def _write_markdown(report: dict[str, Any]) -> None:
    lines = [
        "# V8 Non-Sealed Replay Gate Report v1",
        "",
        f"status: `{report['status']}`",
        f"passed: {str(report['passed']).lower()}",
        f"dependency_v7_gate_passed: {str(report['summary']['dependency_v7_gate_passed']).lower()}",
        f"required_error_count: {report['summary']['required_error_count']}",
        f"v8_priority_review_case_count: {report['summary']['v8_priority_review_case_count']}",
        f"ready_for_step6_sealed_v8_rotation_review: {str(report['summary']['ready_for_step6_sealed_v8_rotation_review']).lower()}",
        "",
        "## Policy",
    ]
    for key, value in report["policy"].items():
        rendered = str(value).lower() if isinstance(value, bool) else value
        lines.append(f"- {key}: {rendered}")
    lines.extend(["", "## Required Lanes"])
    for lane in report["required_lanes"]:
        lines.append(
            f"- {lane['name']}: passed_exact={str(lane['passed_exact']).lower()}, "
            f"errors={lane['measurement']['error_count']}, source=`{lane['source']}`"
        )
    lines.extend(["", "## Contract"])
    for key, value in report["contract"].items():
        rendered = str(value).lower() if isinstance(value, bool) else value
        lines.append(f"- {key}: {rendered}")
    lines.append("")
    REPORT_MD_PATH.write_text("\n".join(lines), encoding="utf-8", newline="\n")


def build_report() -> dict[str, Any]:
    v7_gate = _load_json(V7_GATE_PATH)
    provisional = _load_json(V8_PROVISIONAL_REPORT_PATH)
    lane = _v8_priority_lane()
    summary = _summary(v7_gate, lane)
    passed = summary["ready_for_step6_sealed_v8_rotation_review"]
    report = {
        "schema_version": "v8-nonsealed-replay-gate-report.v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": "passed" if passed else "failed",
        "passed": passed,
        "sources": {
            "v7_nonsealed_gate": _rel(V7_GATE_PATH),
            "v8_provisional_report": _rel(V8_PROVISIONAL_REPORT_PATH),
            "v8_priority_benchmark": _rel(V8_BENCHMARK_PATH),
        },
        "policy": {
            "sealed_fixture_opened_now": False,
            "sealed_measurement_used_for_tuning": False,
            "sealed_v7_text_used": False,
            "sealed_v7_labels_used": False,
            "raw_debate_logs_direct_training_allowed": False,
            "llm_turn_text_direct_training_allowed": False,
            "v8_priority_review_human_approved": lane["review_status"] == "human_reviewed",
            "prior_provisional_replay_was_gate": provisional["current_route_measurement_is_gate"],
            "nonsealed_current_route_measurement_is_gate": True,
            "same_cycle_promotion_allowed": False,
            "fresh_sealed_v8_required_before_adjudication": True,
        },
        "summary": summary,
        "required_lanes": [lane],
        "contract": {
            "can_use_for_v8_roadmap_step5": passed,
            "can_use_as_sealed_measurement": False,
            "can_use_for_same_cycle_promotion": False,
            "requires_fresh_sealed_v8_before_measurement": True,
        },
        "next_action": "roadmap_v8_step6_sealed_rotation_review" if passed else "repair_v8_nonsealed_gate_failures",
    }
    return report


def main() -> None:
    report = build_report()
    _write_json(REPORT_PATH, report)
    _write_markdown(report)
    print(
        json.dumps(
            {
                "status": report["status"],
                "summary": report["summary"],
                "next_action": report["next_action"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()

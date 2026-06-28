"""Run the V9 non-sealed replay gate.

The gate replays only non-sealed, human-reviewed lanes. It depends on the prior
V8 non-sealed gate, but it does not open or measure a sealed fixture.
"""

import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from semantic_routing import evaluate_plm_extractor, parse_plm_benchmark, route  # noqa: E402
from semantic_routing.reproducibility import reproducible_now_iso


V8_GATE_PATH = ROOT / "build" / "v8_nonsealed_replay_gate_report_v1.json"
V8_BENCHMARK_PATH = ROOT / "tests" / "fixtures" / "v8_recovery_priority_review_candidate_benchmark_v1.json"
V9_PRIMARY_BENCHMARK_PATH = ROOT / "tests" / "fixtures" / "v9_accumulated_primary_review_candidate_benchmark_v1.json"
V9_PRIMARY_REPORT_PATH = ROOT / "build" / "v9_accumulated_primary_review_replay_report_v1.json"
V9_EXTENSION_BENCHMARK_PATH = ROOT / "tests" / "fixtures" / "v9_constraint_operation_extension_benchmark_v1.json"
V9_EXTENSION_REPORT_PATH = ROOT / "build" / "v9_constraint_operation_extension_replay_report_v1.json"
REPORT_PATH = ROOT / "build" / "v9_nonsealed_replay_gate_report_v1.json"
REPORT_MD_PATH = ROOT / "build" / "v9_nonsealed_replay_gate_report_v1.md"


def _rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def _field_counts(errors: list[dict[str, Any]]) -> dict[str, int]:
    return dict(sorted(Counter(field for error in errors for field in error.get("fields", [])).items()))


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


def _lane(name: str, benchmark_path: Path, *, report_path: Path | None = None) -> dict[str, Any]:
    payload = _load_json(benchmark_path)
    benchmark = parse_plm_benchmark(payload)
    measurement_raw = evaluate_plm_extractor(benchmark.cases, lambda text: route(text).packet)
    compact = _compact_measurement(measurement_raw)
    prior_report = _load_json(report_path) if report_path else None
    return {
        "name": name,
        "source": _rel(benchmark_path),
        "supporting_report": _rel(report_path) if report_path else None,
        "review_status": payload.get("review_status", "unknown"),
        "category_counts": dict(sorted(Counter(case.contrast_group for case in benchmark.cases).items())),
        "passed_exact": _passed_exact(compact),
        "prior_report_was_gate": bool(prior_report and prior_report.get("current_route_measurement_is_gate") is True),
        "measurement": compact,
        "errors": measurement_raw["errors"],
    }


def _summary(v8_gate: dict[str, Any], lanes: list[dict[str, Any]]) -> dict[str, Any]:
    v8_passed = v8_gate.get("status") == "passed" and v8_gate.get("passed") is True
    required_error_count = sum(lane["measurement"]["error_count"] for lane in lanes)
    required_passed = sum(1 for lane in lanes if lane["passed_exact"])
    total_case_count = sum(lane["measurement"]["case_count"] for lane in lanes)
    return {
        "dependency_v8_gate_passed": v8_passed,
        "dependency_v8_required_error_count": v8_gate["summary"]["required_error_count"],
        "required_lane_count": len(lanes),
        "required_passed_lane_count": required_passed,
        "required_error_count": required_error_count,
        "total_case_count": total_case_count,
        "v8_priority_review_case_count": lanes[0]["measurement"]["case_count"],
        "v9_primary_review_case_count": lanes[1]["measurement"]["case_count"],
        "v9_constraint_operation_extension_case_count": lanes[2]["measurement"]["case_count"],
        "ready_for_step6_sealed_v9_rotation_review": (
            v8_passed
            and v8_gate["summary"]["required_error_count"] == 0
            and required_error_count == 0
            and required_passed == len(lanes)
        ),
    }


def _write_markdown(report: dict[str, Any]) -> None:
    lines = [
        "# V9 Non-Sealed Replay Gate Report v1",
        "",
        f"status: `{report['status']}`",
        f"passed: {str(report['passed']).lower()}",
        f"dependency_v8_gate_passed: {str(report['summary']['dependency_v8_gate_passed']).lower()}",
        f"required_error_count: {report['summary']['required_error_count']}",
        f"total_case_count: {report['summary']['total_case_count']}",
        f"ready_for_step6_sealed_v9_rotation_review: {str(report['summary']['ready_for_step6_sealed_v9_rotation_review']).lower()}",
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
            f"cases={lane['measurement']['case_count']}, errors={lane['measurement']['error_count']}, source=`{lane['source']}`"
        )
    lines.extend(["", "## Contract"])
    for key, value in report["contract"].items():
        rendered = str(value).lower() if isinstance(value, bool) else value
        lines.append(f"- {key}: {rendered}")
    lines.append("")
    REPORT_MD_PATH.write_text("\n".join(lines), encoding="utf-8", newline="\n")


def build_report() -> dict[str, Any]:
    v8_gate = _load_json(V8_GATE_PATH)
    lanes = [
        _lane("v8_recovery_priority_review_approved", V8_BENCHMARK_PATH),
        _lane("v9_accumulated_primary_review_approved", V9_PRIMARY_BENCHMARK_PATH, report_path=V9_PRIMARY_REPORT_PATH),
        _lane("v9_constraint_operation_extension", V9_EXTENSION_BENCHMARK_PATH, report_path=V9_EXTENSION_REPORT_PATH),
    ]
    summary = _summary(v8_gate, lanes)
    passed = summary["ready_for_step6_sealed_v9_rotation_review"]
    report = {
        "schema_version": "v9-nonsealed-replay-gate-report.v1",
        "generated_at": reproducible_now_iso(),
        "status": "passed" if passed else "failed",
        "passed": passed,
        "sources": {
            "v8_nonsealed_gate": _rel(V8_GATE_PATH),
            "v8_priority_benchmark": _rel(V8_BENCHMARK_PATH),
            "v9_primary_benchmark": _rel(V9_PRIMARY_BENCHMARK_PATH),
            "v9_primary_replay_report": _rel(V9_PRIMARY_REPORT_PATH),
            "v9_extension_benchmark": _rel(V9_EXTENSION_BENCHMARK_PATH),
            "v9_extension_replay_report": _rel(V9_EXTENSION_REPORT_PATH),
        },
        "policy": {
            "sealed_fixture_opened_now": False,
            "sealed_measurement_used_for_tuning": False,
            "sealed_v8_text_used": False,
            "sealed_v8_labels_used": False,
            "raw_debate_logs_direct_training_allowed": False,
            "llm_turn_text_direct_training_allowed": False,
            "v9_primary_review_human_approved": lanes[1]["review_status"] == "human_reviewed",
            "v9_constraint_operation_extension_human_approved": lanes[2]["review_status"] == "human_reviewed",
            "prior_v9_replays_were_gate": any(lane["prior_report_was_gate"] for lane in lanes[1:]),
            "nonsealed_current_route_measurement_is_gate": True,
            "same_cycle_promotion_allowed": False,
            "fresh_sealed_v9_required_before_adjudication": True,
        },
        "summary": summary,
        "required_lanes": lanes,
        "contract": {
            "can_use_for_v9_roadmap_step5": passed,
            "can_use_as_sealed_measurement": False,
            "can_use_for_same_cycle_promotion": False,
            "requires_fresh_sealed_v9_before_measurement": True,
        },
        "next_action": "roadmap_v9_step6_sealed_rotation_review" if passed else "repair_v9_nonsealed_gate_failures",
    }
    return report


def main() -> None:
    report = build_report()
    _write_json(REPORT_PATH, report)
    _write_markdown(report)
    print(json.dumps({"status": report["status"], "summary": report["summary"], "next_action": report["next_action"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

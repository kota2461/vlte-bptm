"""Run the V10 mainline non-sealed replay gate.

This gate promotes the already human-reviewed Thought Color bridge rewrite from
an isolated diagnostic replay into a mainline router-generalization replay. It
still does not make the bridge fixture training data, and it does not open or
measure any sealed fixture.
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


V9_GATE_PATH = ROOT / "build" / "v9_nonsealed_replay_gate_report_v1.json"
BRIDGE_DECISION_PATH = ROOT / "build" / "v10_thought_color_bridge_isolated_adoption_decision_v1.json"
BRIDGE_REPLAY_PATH = ROOT / "build" / "v10_thought_color_bridge_isolated_replay_report_v1.json"
BRIDGE_BENCHMARK_PATH = ROOT / "tests" / "fixtures" / "v10_thought_color_bridge_isolated_benchmark_v1.json"
REPORT_PATH = ROOT / "build" / "v10_mainline_replay_gate_report_v1.json"
REPORT_MD_PATH = ROOT / "build" / "v10_mainline_replay_gate_report_v1.md"


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


def _bridge_lane() -> dict[str, Any]:
    benchmark_payload = _load_json(BRIDGE_BENCHMARK_PATH)
    benchmark = parse_plm_benchmark(benchmark_payload)
    measurement_raw = evaluate_plm_extractor(benchmark.cases, lambda text: route(text).packet)
    compact = _compact_measurement(measurement_raw)
    return {
        "name": "v10_thought_color_bridge_mainline_replay",
        "source": _rel(BRIDGE_BENCHMARK_PATH),
        "review_status": benchmark_payload["review_status"],
        "category_counts": dict(sorted(Counter(case.contrast_group for case in benchmark.cases).items())),
        "passed_exact": compact["valid_packet_rate"] == 1.0 and compact["error_count"] == 0,
        "measurement": compact,
        "errors": measurement_raw["errors"],
    }


def _summary(v9_gate: dict[str, Any], bridge_lane: dict[str, Any]) -> dict[str, Any]:
    v9_gate_passed = v9_gate.get("status") == "passed" and v9_gate.get("passed") is True
    return {
        "dependency_v9_gate_passed": v9_gate_passed,
        "dependency_v9_required_error_count": v9_gate["summary"]["required_error_count"],
        "required_lane_count": 1,
        "required_passed_lane_count": 1 if bridge_lane["passed_exact"] else 0,
        "required_error_count": bridge_lane["measurement"]["error_count"],
        "total_case_count": bridge_lane["measurement"]["case_count"],
        "v10_bridge_case_count": bridge_lane["measurement"]["case_count"],
        "v10_bridge_error_count": bridge_lane["measurement"]["error_count"],
        "ready_for_step4_sealed_v10_rotation_review": (
            v9_gate_passed
            and v9_gate["summary"]["required_error_count"] == 0
            and bridge_lane["passed_exact"]
        ),
    }


def _write_markdown(report: dict[str, Any]) -> None:
    lines = [
        "# V10 Mainline Replay Gate Report v1",
        "",
        f"status: `{report['status']}`",
        f"passed: {str(report['passed']).lower()}",
        f"dependency_v9_gate_passed: {str(report['summary']['dependency_v9_gate_passed']).lower()}",
        f"required_error_count: {report['summary']['required_error_count']}",
        f"total_case_count: {report['summary']['total_case_count']}",
        f"ready_for_step4_sealed_v10_rotation_review: {str(report['summary']['ready_for_step4_sealed_v10_rotation_review']).lower()}",
        "",
        "## Policy",
    ]
    for key, value in report["policy"].items():
        rendered = str(value).lower() if isinstance(value, bool) else value
        lines.append(f"- {key}: {rendered}")
    lines.extend(["", "## Required Lane"])
    lane = report["required_lanes"][0]
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
    v9_gate = _load_json(V9_GATE_PATH)
    decision = _load_json(BRIDGE_DECISION_PATH)
    isolated_replay = _load_json(BRIDGE_REPLAY_PATH)
    bridge_lane = _bridge_lane()
    summary = _summary(v9_gate, bridge_lane)
    policy_ok = (
        decision["review_status"] == "human_reviewed_for_isolated_rewrite"
        and decision["policy"]["sealed_fixtures_used_as_sources"] is False
        and decision["policy"]["sealed_text_used"] is False
        and decision["policy"]["sealed_labels_used"] is False
        and decision["policy"]["raw_thought_color_samples_direct_training_allowed"] is False
        and decision["policy"]["isolated_rewrite_fixture_training_allowed"] is False
    )
    passed = summary["ready_for_step4_sealed_v10_rotation_review"] and policy_ok
    report = {
        "schema_version": "v10-mainline-replay-gate-report.v1",
        "generated_at": reproducible_now_iso(),
        "status": "passed" if passed else "failed",
        "passed": passed,
        "sources": {
            "v9_nonsealed_replay_gate": _rel(V9_GATE_PATH),
            "v10_bridge_decision": _rel(BRIDGE_DECISION_PATH),
            "v10_bridge_isolated_replay": _rel(BRIDGE_REPLAY_PATH),
            "v10_bridge_benchmark": _rel(BRIDGE_BENCHMARK_PATH),
        },
        "policy": {
            "sealed_fixture_opened_now": False,
            "sealed_measurement_used_for_tuning": False,
            "sealed_v9_text_used": False,
            "sealed_v9_labels_used": False,
            "thought_color_source_scope": "experiment_only",
            "thought_color_source_mainline_training_allowed": False,
            "v10_bridge_mainline_training_allowed": False,
            "v10_bridge_mainline_allowed_use": "router_generalization_and_nonsealed_replay_only",
            "raw_thought_color_samples_direct_training_allowed": False,
            "isolated_rewrite_fixture_training_allowed": False,
            "isolated_replay_was_gate": isolated_replay["current_route_measurement_is_gate"],
            "mainline_adoption_user_confirmed": True,
            "nonsealed_current_route_measurement_is_gate": True,
            "same_cycle_promotion_allowed": False,
            "fresh_sealed_v10_required_before_adjudication": True,
        },
        "summary": summary,
        "required_lanes": [bridge_lane],
        "contract": {
            "can_use_for_v10_roadmap_step3": passed,
            "can_use_as_training_data": False,
            "can_use_as_sealed_measurement": False,
            "can_use_for_same_cycle_promotion": False,
            "requires_fresh_sealed_v10_before_measurement": True,
            "full_regression_command": "python -B -m pytest",
        },
        "roadmap_decision": {
            "can_advance": passed,
            "advance_to": "sealed_v10_rotation_review" if passed else None,
            "blocked_reasons": [] if passed else ["v10_mainline_replay_gate_failed"],
        },
        "next_action": "roadmap_v10_step4_sealed_rotation_review" if passed else "repair_v10_mainline_replay_gate_failures",
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
                "roadmap_decision": report["roadmap_decision"],
                "next_action": report["next_action"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()

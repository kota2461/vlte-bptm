"""Run V4 non-sealed candidate evaluation and rotate PLM sealed v4 active.

This script deliberately does not evaluate the newly created sealed v4 fixture.
It evaluates only visible/non-sealed material, registers v4 as the next active
sealed measurement target, then refreshes readiness without opening sealed
labels for tuning.
"""

import hashlib
import json
import runpy
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / "build"
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(BUILD))

from generate_plm_sealed_v4 import build_payload, validate_no_overlap  # noqa: E402
from semantic_routing import (  # noqa: E402
    ADAPTER_VERSION,
    DEFAULT_INTENT_MODEL_PATH,
    evaluate_plm_extractor,
    load_plm_benchmark,
    parse_puzzle_failure_memory,
    route,
)
from semantic_routing.reproducibility import reproducible_now_iso


BENCHMARK_PATH = ROOT / "tests" / "fixtures" / "pattern_language_benchmark_v1.json"
REGISTRY_PATH = ROOT / "tests" / "fixtures" / "pattern_language_fixture_registry.json"
SEALED_V4_PATH = ROOT / "tests" / "fixtures" / "pattern_language_sealed_v4.json"
V3_MEASUREMENT_PATH = ROOT / "build" / "pattern_language_sealed_v3_measurement_report.json"
FAILURE_MEMORY_PATH = ROOT / "tests" / "fixtures" / "v4_failure_memory_fixture_v1.json"
PUZZLE_FAILURE_MEMORY_PATH = ROOT / "tests" / "fixtures" / "v4_puzzle_failure_memory_v1.json"
PUZZLE_TRACE_PATH = ROOT / "build" / "v4_puzzle_solver_trace_v1.json"
READINESS_PATH = ROOT / "build" / "plm_measurement_readiness_review.json"
ADOPTION_PATH = ROOT / "build" / "v4_failure_memory_adoption_v1.json"
CANDIDATE_REPORT_PATH = ROOT / "build" / "v4_candidate_eval_report.json"
ROTATION_REPORT_PATH = ROOT / "build" / "v4_sealed_rotation_report.json"


TARGETS = {
    "intent_accuracy_min": 0.90,
    "intent_accuracy_stretch": 0.93,
    "critical_signal_recall_min": 0.85,
    "critical_signal_recall_stretch": 0.90,
    "operation_exact_match_min": 0.90,
    "constraint_exact_match_min": 0.92,
    "risk_exact_match_min": 0.95,
    "sealed_error_count_max": 4,
    "critical_underprocessing_max": 0,
}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def _packet_from_route(text: str):
    return route(text).packet


def _visible_plm_eval() -> dict[str, Any]:
    benchmark = load_plm_benchmark(BENCHMARK_PATH)
    return evaluate_plm_extractor(
        benchmark.cases_for_splits(("train", "validation")),
        _packet_from_route,
    )


def _failure_guard_eval() -> dict[str, Any]:
    fixture = _load(FAILURE_MEMORY_PATH)
    measurements = []
    subset_count = 0
    exact_count = 0
    for item in fixture["items"]:
        result = route(item["input"])
        guard = result.trace["failure_guard"]
        expected = set(item["guard_action"])
        actual = set(guard["guard_actions"])
        subset = expected <= actual
        exact = expected == actual
        subset_count += int(subset)
        exact_count += int(exact)
        measurements.append(
            {
                "id": item["id"],
                "source_candidate_id": item["source_candidate_id"],
                "expected_guard_actions": sorted(expected),
                "actual_guard_actions": sorted(actual),
                "missing_guard_actions": sorted(expected - actual),
                "extra_guard_actions": sorted(actual - expected),
                "subset_match": subset,
                "exact_match": exact,
                "severity": guard["severity"],
            }
        )
    total = len(measurements)
    return {
        "schema_version": "v4-failure-guard-evaluation.v1",
        "fixture": _rel(FAILURE_MEMORY_PATH),
        "summary": {
            "item_count": total,
            "guard_subset_match_count": subset_count,
            "guard_subset_match_rate": subset_count / total if total else 0.0,
            "guard_exact_match_count": exact_count,
            "guard_exact_match_rate": exact_count / total if total else 0.0,
        },
        "measurements": measurements,
    }


def _puzzle_failure_eval() -> dict[str, Any]:
    payload = _load(PUZZLE_FAILURE_MEMORY_PATH)
    memory = parse_puzzle_failure_memory(payload)
    return {
        "schema_version": "v4-puzzle-failure-evaluation.v1",
        "fixture": _rel(PUZZLE_FAILURE_MEMORY_PATH),
        "source_trace_report": _rel(PUZZLE_TRACE_PATH),
        "summary": dict(memory.summary),
        "policy": dict(memory.policy),
        "source_task_ids": [item.source_task_id for item in memory.items],
    }


def _write_sealed_v4() -> dict[str, Any]:
    payload = build_payload()
    validate_no_overlap(payload)
    _write_json(SEALED_V4_PATH, payload)
    return {
        "registry_name": SEALED_V4_PATH.name,
        "fixture_id": payload["fixture_id"],
        "sha256": _sha256(SEALED_V4_PATH),
        "case_count": len(payload["cases"]),
        "predecessor": payload["predecessor"],
        "status": "active",
        "measured": False,
        "reviewed": False,
    }


def _update_registry(now: str, sealed_v4: dict[str, Any]) -> dict[str, Any]:
    registry = _load(REGISTRY_PATH)
    fixtures = registry["fixtures"]
    v3 = fixtures["pattern_language_sealed_v3.json"]
    if v3.get("status") != "consumed" or v3.get("measured") is not True:
        raise SystemExit("sealed v3 must be consumed before v4 rotation")
    v3["successor"] = SEALED_V4_PATH.name
    fixtures[SEALED_V4_PATH.name] = {
        "sha256": sealed_v4["sha256"],
        "case_count": sealed_v4["case_count"],
        "role": "sealed measurement only",
        "predecessor": "pattern_language_sealed_v3.json",
        "reviewed": False,
        "status": "active",
        "measured": False,
        "rotated_at": now,
        "rotation_report": _rel(ROTATION_REPORT_PATH),
    }
    active = [
        name
        for name, entry in fixtures.items()
        if entry.get("role") == "sealed measurement only" and entry.get("status") == "active"
    ]
    if active != [SEALED_V4_PATH.name]:
        raise SystemExit(f"expected only sealed v4 active, got {active}")
    registry["updated_at"] = now
    _write_json(REGISTRY_PATH, registry)
    return registry


def _nonsealed_gates(visible: dict[str, Any], guard: dict[str, Any], puzzle: dict[str, Any]) -> dict[str, Any]:
    gates = {
        "visible_plm_no_errors": len(visible["errors"]) == 0,
        "visible_plm_intent_accuracy_gate": visible["intent_accuracy"] >= 0.99,
        "visible_plm_critical_signal_gate": visible["critical_signal_recall"] >= 0.99,
        "failure_guard_exact_gate": guard["summary"]["guard_exact_match_rate"] == 1.0,
        "puzzle_failure_memory_present": puzzle["summary"]["failure_count"] >= 2,
        "puzzle_success_traces_not_training": puzzle["policy"]["source_success_traces_used_for_training"] is False,
    }
    return {
        "requirements": gates,
        "passed": all(gates.values()),
    }


def _rotation_report(now: str, sealed_v4: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "v4-sealed-rotation-report.v1",
        "rotated_at": now,
        "policy": {
            "sealed_v4_opened_for_measurement": False,
            "sealed_v4_labels_used_for_tuning": False,
            "v3_sealed_text_used_for_training": False,
            "v3_measurement_used_as_taxonomy_only": True,
            "same_cycle_promotion_allowed": False,
        },
        "rotated_from": {
            "registry_name": "pattern_language_sealed_v3.json",
            "status": "consumed",
            "measurement_report": _rel(V3_MEASUREMENT_PATH),
        },
        "rotated_to": sealed_v4,
        "next_action": "measure_active_sealed_once_when_readiness_eligible",
    }


def _update_adoption(now: str, candidate: dict[str, Any], rotation: dict[str, Any], readiness: dict[str, Any]) -> None:
    adoption = _load(ADOPTION_PATH)
    adoption["status"] = "step8_completed_v4_candidate_eval_and_sealed_rotation"
    summary = adoption.setdefault("summary", {})
    summary["v4_candidate_visible_case_count"] = candidate["visible_plm"]["case_count"]
    summary["v4_candidate_visible_intent_accuracy"] = candidate["visible_plm"]["intent_accuracy"]
    summary["v4_candidate_failure_guard_exact_match_rate"] = candidate["failure_guard"]["summary"]["guard_exact_match_rate"]
    summary["v4_candidate_puzzle_failure_memory_items"] = candidate["puzzle_failure_memory"]["summary"]["failure_count"]
    summary["active_plm_sealed_fixture"] = rotation["rotated_to"]["registry_name"]
    summary["active_plm_sealed_case_count"] = rotation["rotated_to"]["case_count"]
    summary["plm_measurement_readiness_decision"] = readiness["decision"]
    review = adoption.setdefault("review_decision", {})
    review["v4_candidate_eval_report"] = _rel(CANDIDATE_REPORT_PATH)
    review["v4_sealed_rotation_report"] = _rel(ROTATION_REPORT_PATH)
    review["v4_active_sealed_fixture"] = _rel(SEALED_V4_PATH)
    review["v4_active_sealed_sha256"] = rotation["rotated_to"]["sha256"]
    review["plm_measurement_readiness_report"] = _rel(READINESS_PATH)
    review["plm_measurement_readiness_decision"] = readiness["decision"]
    review["step8_completed_at"] = now
    for step in adoption.get("sequence", []):
        if step["step"] == 8:
            step["status"] = "completed"
    _write_json(ADOPTION_PATH, adoption)


def main() -> None:
    now = reproducible_now_iso()
    visible = _visible_plm_eval()
    guard = _failure_guard_eval()
    puzzle = _puzzle_failure_eval()
    sealed_v4 = _write_sealed_v4()
    rotation = _rotation_report(now, sealed_v4)
    _write_json(ROTATION_REPORT_PATH, rotation)
    registry = _update_registry(now, sealed_v4)

    # Refresh readiness after the registry has exactly one active PLM sealed fixture.
    runpy.run_path(str(ROOT / "build" / "review_plm_measurement_readiness.py"), run_name="__main__")
    readiness = _load(READINESS_PATH)

    v3_measurement = _load(V3_MEASUREMENT_PATH)["measurements"]
    gates = _nonsealed_gates(visible, guard, puzzle)
    candidate = {
        "schema_version": "v4-candidate-eval-report.v1",
        "evaluated_at": now,
        "policy": {
            "sealed_fixtures_opened_for_candidate_eval": False,
            "sealed_labels_used_for_tuning": False,
            "v3_sealed_text_used_for_training": False,
            "v3_measurement_used_as_taxonomy_only": True,
            "success_pattern_lane_write_allowed_from_failures": False,
        },
        "candidate": {
            "entrypoint": "semantic_routing.route(...).packet",
            "adapter_version": ADAPTER_VERSION,
            "intent_model_path": _rel(DEFAULT_INTENT_MODEL_PATH),
            "intent_model_sha256": _sha256(DEFAULT_INTENT_MODEL_PATH),
        },
        "v4_targets_for_future_sealed_measurement": TARGETS,
        "v3_measured_baseline": {
            "report": _rel(V3_MEASUREMENT_PATH),
            "intent_accuracy": v3_measurement["intent_accuracy"],
            "critical_signal_recall": v3_measurement["critical_signal_recall"],
            "operation_exact_match": v3_measurement["operation_exact_match"],
            "constraint_exact_match": v3_measurement["constraint_exact_match"],
            "risk_exact_match": v3_measurement["risk_exact_match"],
            "error_count": len(v3_measurement["errors"]),
        },
        "visible_plm": visible,
        "failure_guard": guard,
        "puzzle_failure_memory": puzzle,
        "nonsealed_gates": gates,
        "sealed_rotation": {
            "report": _rel(ROTATION_REPORT_PATH),
            "active_fixture": SEALED_V4_PATH.name,
            "active_fixture_sha256": sealed_v4["sha256"],
            "active_fixture_opened_for_measurement": False,
        },
        "readiness_after_rotation": {
            "report": _rel(READINESS_PATH),
            "decision": readiness["decision"],
            "sealed_fixture_opened": readiness["sealed_fixture_opened"],
            "sealed_fixture": readiness["sealed_fixture"],
        },
        "registry": {
            "path": _rel(REGISTRY_PATH),
            "updated_at": registry["updated_at"],
        },
        "decision": (
            "eligible_for_v4_sealed_measurement"
            if gates["passed"] and readiness["decision"] == "eligible"
            else "blocked"
        ),
    }
    _write_json(CANDIDATE_REPORT_PATH, candidate)
    _update_adoption(now, candidate, rotation, readiness)
    print(
        json.dumps(
            {
                "candidate_report": _rel(CANDIDATE_REPORT_PATH),
                "rotation_report": _rel(ROTATION_REPORT_PATH),
                "active_fixture": SEALED_V4_PATH.name,
                "decision": candidate["decision"],
                "readiness": readiness["decision"],
                "visible_intent_accuracy": visible["intent_accuracy"],
                "failure_guard_exact_match_rate": guard["summary"]["guard_exact_match_rate"],
                "puzzle_failure_memory_items": puzzle["summary"]["failure_count"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()

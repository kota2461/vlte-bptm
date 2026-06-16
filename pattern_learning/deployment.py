"""Deployment gate for the pattern router (v0.2.3 three-layer contract).

Gate      = a frozen contract (fixture SHA registry, append-only anchors,
            raw + effective route checks, minimum counts)
Promotion = contract pass + improvement check (or narrowly scoped,
            evidence-backed human acknowledgment) + explicit human action,
            atomic replace, previous model archived
Rollback  = on contract violation, quarantine the current model and
            restore the previous approved one

The gate does not judge whether a failure means "bad new data" or "bad
anchor" — that adjudication stays human, and anchor amendments are
versioned registry changes.
"""

import hashlib
import json
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from .evaluation import evaluate_router
from .trainer import RouterModel


GATE_REPORT_SCHEMA_VERSION = "router-deployment-gate.v3"
REGISTRY_SCHEMA_VERSION = "gate-fixture-registry.v1"
SEALED_EVAL_SCHEMA_VERSION = "sealed-slice-eval.v1"

DEFAULT_CANDIDATE = Path("build/pattern_router_model_candidate.json")
DEFAULT_DEPLOYED = Path("build/pattern_router_model.json")
DEFAULT_REGRESSION_FIXTURE = Path(
    "tests/fixtures/pattern_router_cases_v1.json"
)
DEFAULT_FOUNDATION_FIXTURE = Path(
    "tests/fixtures/foundation_anchor_suite_v1.json"
)
DEFAULT_REGISTRY = Path("tests/fixtures/gate_fixture_registry.json")
DEFAULT_DATABASE_PATH = Path("data/pattern_lab.db")
DEFAULT_HISTORY_DIR = Path("build/model_history")

# 分割・乱数由来の微小揺れのみ許容する改善確認の許容幅 (v0.2.2 層2)
IMPROVEMENT_TOLERANCE = 0.02
CONTRACT_CHECK_NAMES = (
    "frozen_regression",
    "foundation_anchors",
    "fixture_integrity",
    "minimum_counts",
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def file_sha256(path: str | Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest().upper()


def load_registry(path: str | Path = DEFAULT_REGISTRY) -> Dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if payload.get("schema_version") != REGISTRY_SCHEMA_VERSION:
        raise ValueError("unsupported gate fixture registry schema")
    return payload


def load_foundation_cases(path: str | Path) -> List[Dict[str, Any]]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if payload.get("schema_version") != "foundation-anchor-suite.v1":
        raise ValueError("unsupported foundation anchor suite schema")
    return list(payload["cases"])


def _check_fixture_integrity(
    fixture_path: Path,
    registry: Dict[str, Any],
) -> Dict[str, Any]:
    entry = registry["fixtures"].get(fixture_path.name)
    if entry is None:
        return {
            "fixture": fixture_path.name,
            "registered": False,
            "passed": False,
            "detail": "fixture is not registered in the gate registry",
        }
    actual = file_sha256(fixture_path)
    return {
        "fixture": fixture_path.name,
        "registered": True,
        "version": entry["version"],
        "expected_sha256": entry["sha256"],
        "actual_sha256": actual,
        "passed": actual == entry["sha256"],
    }


def _check_minimum_counts(
    fixture_name: str,
    cases: List[Dict[str, Any]],
    registry: Dict[str, Any],
) -> Dict[str, Any]:
    entry = registry["fixtures"].get(fixture_name, {})
    min_total = int(entry.get("min_case_count", 0))
    min_routes = {
        route: int(count)
        for route, count in entry.get("min_route_counts", {}).items()
    }
    actual_routes: Dict[str, int] = {}
    for case in cases:
        actual_routes[case["route"]] = actual_routes.get(case["route"], 0) + 1
    shortfalls = {
        route: {"minimum": minimum, "actual": actual_routes.get(route, 0)}
        for route, minimum in min_routes.items()
        if actual_routes.get(route, 0) < minimum
    }
    passed = len(cases) >= min_total and not shortfalls
    return {
        "fixture": fixture_name,
        "min_case_count": min_total,
        "case_count": len(cases),
        "route_shortfalls": shortfalls,
        "passed": passed,
    }


def _check_cases(
    model: RouterModel,
    cases: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Raw routes must all match; effective may only differ by clarify
    abstention (safety behaviour), never by switching to another route."""

    raw_misses: List[Dict[str, Any]] = []
    effective_violations: List[Dict[str, Any]] = []
    abstained = 0
    for case in cases:
        prediction = model.predict(case["input"])
        if prediction.route != case["route"]:
            raw_misses.append(
                {
                    "input": case["input"],
                    "expected": case["route"],
                    "predicted": prediction.route,
                }
            )
        effective = prediction.effective_route or prediction.route
        if effective != case["route"]:
            if effective == "clarify":
                abstained += 1
            else:
                effective_violations.append(
                    {
                        "input": case["input"],
                        "expected": case["route"],
                        "effective": effective,
                    }
                )
    return {
        "case_count": len(cases),
        "raw_misses": raw_misses,
        "raw_accuracy": (
            (len(cases) - len(raw_misses)) / len(cases) if cases else 1.0
        ),
        "effective_violations": effective_violations,
        "abstained_to_clarify": abstained,
        "passed": not raw_misses and not effective_violations,
    }


def _check_improvement(
    current_metrics: Optional[Dict[str, Any]],
    candidate_metrics: Optional[Dict[str, Any]],
    tolerance: float = IMPROVEMENT_TOLERANCE,
) -> Dict[str, Any]:
    """The candidate must not degrade key metrics beyond tolerance."""

    if not current_metrics:
        return {
            "passed": True,
            "detail": "no deployed model to compare against",
            "comparisons": {},
        }
    comparisons: Dict[str, Any] = {}
    passed = True
    for key in ("validation_accuracy", "kfold_accuracy"):
        current = current_metrics.get(key)
        candidate = (candidate_metrics or {}).get(key)
        if current is None or candidate is None:
            comparisons[key] = {"skipped": "metric missing on one side"}
            continue
        degraded = candidate < current - tolerance
        comparisons[key] = {
            "current": current,
            "candidate": candidate,
            "tolerance": tolerance,
            "passed": not degraded,
        }
        passed = passed and not degraded
    return {"passed": passed, "comparisons": comparisons}


def _set_gate_decision(
    report: Dict[str, Any],
    contract_checks: tuple[str, ...] = CONTRACT_CHECK_NAMES,
) -> None:
    checks = report["checks"]
    missing = [name for name in contract_checks if name not in checks]
    contract_passed = not missing and all(
        checks[name].get("passed") is True for name in contract_checks
    )
    improvement = checks["improvement_vs_deployed"]
    acknowledgment = improvement.get("acknowledgment", {})
    improvement_accepted = (
        improvement.get("passed") is True
        or acknowledgment.get("accepted") is True
    )
    report["contract_passed"] = contract_passed
    report["improvement_accepted"] = improvement_accepted
    report["passed"] = contract_passed and improvement_accepted
    report["decision"] = (
        "pass"
        if report["passed"] and improvement.get("passed") is True
        else (
            "pass_with_improvement_ack"
            if report["passed"]
            else "blocked"
        )
    )


def evaluate_gate(
    model: RouterModel,
    regression_cases: List[Dict[str, Any]],
    foundation_cases: List[Dict[str, Any]],
    current_metrics: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Behavioural checks only (no file integrity; see run_deployment_gate).

    Kept registry-free so unit tests and ad-hoc evaluations can call it
    with in-memory cases.
    """

    regression_eval = evaluate_router(model, regression_cases)
    regression_check = _check_cases(model, regression_cases)
    regression_check["macro_f1"] = regression_eval["macro_f1"]
    foundation_check = _check_cases(model, foundation_cases)
    improvement = _check_improvement(
        current_metrics, model.metadata.get("metrics")
    )
    checks = {
        "frozen_regression": {
            "required": "raw 100%; effective may only abstain to clarify",
            **regression_check,
        },
        "foundation_anchors": {
            "required": "raw 100%; effective may only abstain to clarify",
            **foundation_check,
        },
        "improvement_vs_deployed": improvement,
    }
    report = {
        "schema_version": GATE_REPORT_SCHEMA_VERSION,
        "checks": checks,
    }
    _set_gate_decision(
        report,
        contract_checks=("frozen_regression", "foundation_anchors"),
    )
    return report


def run_deployment_gate(
    candidate_path: str | Path,
    regression_fixture: str | Path = DEFAULT_REGRESSION_FIXTURE,
    foundation_fixture: str | Path = DEFAULT_FOUNDATION_FIXTURE,
    registry_path: str | Path = DEFAULT_REGISTRY,
    deployed_path: str | Path = DEFAULT_DEPLOYED,
    database_path: str | Path = DEFAULT_DATABASE_PATH,
) -> Dict[str, Any]:
    candidate_path = Path(candidate_path)
    regression_fixture = Path(regression_fixture)
    foundation_fixture = Path(foundation_fixture)
    registry = load_registry(registry_path)

    integrity = [
        _check_fixture_integrity(regression_fixture, registry),
        _check_fixture_integrity(foundation_fixture, registry),
    ]
    integrity_passed = all(item["passed"] for item in integrity)

    model = RouterModel.load(candidate_path)
    regression_cases = json.loads(
        regression_fixture.read_text(encoding="utf-8")
    )
    foundation_cases = load_foundation_cases(foundation_fixture)

    counts = [
        _check_minimum_counts(
            regression_fixture.name, regression_cases, registry
        ),
        _check_minimum_counts(
            foundation_fixture.name, foundation_cases, registry
        ),
    ]
    counts_passed = all(item["passed"] for item in counts)

    deployed = Path(deployed_path)
    current_metrics: Optional[Dict[str, Any]] = None
    deployed_sha: Optional[str] = None
    if deployed.exists():
        deployed_sha = file_sha256(deployed)
        current_metrics = (
            json.loads(deployed.read_text(encoding="utf-8"))
            .get("metadata", {})
            .get("metrics")
        )

    report = evaluate_gate(
        model, regression_cases, foundation_cases, current_metrics
    )
    report["checks"]["fixture_integrity"] = {
        "items": integrity,
        "passed": integrity_passed,
    }
    report["checks"]["minimum_counts"] = {
        "items": counts,
        "passed": counts_passed,
    }
    _set_gate_decision(report)
    database = Path(database_path)
    report["registry"] = {
        "path": str(Path(registry_path).resolve()),
        "versions": {
            name: entry["version"]
            for name, entry in registry["fixtures"].items()
        },
    }
    report["hashes"] = {
        "candidate_sha256": file_sha256(candidate_path),
        "deployed_sha256": deployed_sha,
        "database_sha256": (
            file_sha256(database) if database.exists() else None
        ),
        "fixtures": {
            regression_fixture.name: file_sha256(regression_fixture),
            foundation_fixture.name: file_sha256(foundation_fixture),
        },
    }
    report["candidate_path"] = str(candidate_path.resolve())
    report["candidate_trained_at"] = model.metadata.get("trained_at")
    report["candidate_sample_count"] = model.metadata.get("sample_count")
    report["evaluated_at"] = _now()
    return report


def _load_sealed_result(path: str | Path) -> Dict[str, Any]:
    result_path = Path(path)
    payload = json.loads(result_path.read_text(encoding="utf-8"))
    if payload.get("schema_version") != SEALED_EVAL_SCHEMA_VERSION:
        raise ValueError(
            f"unsupported sealed result schema: {result_path}"
        )
    total = payload.get("total", {})
    correct = total.get("correct")
    count = total.get("count")
    if (
        not isinstance(correct, int)
        or not isinstance(count, int)
        or count <= 0
        or correct < 0
        or correct > count
    ):
        raise ValueError(f"invalid sealed result totals: {result_path}")
    return payload


def _registered_sealed_fixture(
    registry: Dict[str, Any],
    sealed_sha256: str,
) -> tuple[str, Dict[str, Any]]:
    for name, entry in registry["fixtures"].items():
        if (
            entry.get("sha256") == sealed_sha256
            and "sealed" in entry.get("role", "").lower()
        ):
            return name, entry
    raise ValueError("sealed evidence fixture is not registered")


def acknowledge_improvement_regression(
    gate_report: Dict[str, Any],
    *,
    reason: str,
    candidate_sealed_result: str | Path,
    deployed_sealed_result: str | Path,
    registry_path: str | Path = DEFAULT_REGISTRY,
    actor: str = "human-operator",
) -> Dict[str, Any]:
    """Accept only an improvement-check failure with same-slice evidence.

    Behavioural contract checks, fixture integrity, minimum counts, and
    candidate hash checks remain mandatory and cannot be acknowledged.
    """

    reason = reason.strip()
    actor = actor.strip()
    if not reason:
        raise ValueError("improvement acknowledgment requires a reason")
    if not actor:
        raise ValueError("improvement acknowledgment requires an actor")
    if gate_report.get("schema_version") != GATE_REPORT_SCHEMA_VERSION:
        raise ValueError("improvement acknowledgment requires a v0.2.3 report")

    _set_gate_decision(gate_report)
    if not gate_report["contract_passed"]:
        raise ValueError("contract checks failed; acknowledgment is forbidden")
    improvement = gate_report["checks"]["improvement_vs_deployed"]
    if improvement.get("passed") is True:
        raise ValueError("improvement check already passed; acknowledgment unused")
    if improvement.get("acknowledgment", {}).get("accepted") is True:
        raise ValueError("improvement check is already acknowledged")

    candidate_path = Path(candidate_sealed_result)
    deployed_path = Path(deployed_sealed_result)
    candidate_result = _load_sealed_result(candidate_path)
    deployed_result = _load_sealed_result(deployed_path)
    hashes = gate_report.get("hashes", {})
    if candidate_result.get("model_sha256") != hashes.get("candidate_sha256"):
        raise ValueError("candidate sealed result model hash does not match gate")
    if deployed_result.get("model_sha256") != hashes.get("deployed_sha256"):
        raise ValueError("deployed sealed result model hash does not match gate")

    sealed_sha = candidate_result.get("sealed_sha256")
    if not sealed_sha or sealed_sha != deployed_result.get("sealed_sha256"):
        raise ValueError("sealed results must use the same registered fixture")
    registry = load_registry(registry_path)
    fixture_name, fixture_entry = _registered_sealed_fixture(
        registry, sealed_sha
    )

    candidate_total = candidate_result["total"]
    deployed_total = deployed_result["total"]
    if candidate_total["count"] != deployed_total["count"]:
        raise ValueError("sealed result case counts differ")
    if candidate_total["correct"] < deployed_total["correct"]:
        raise ValueError("candidate regressed on the sealed evidence")

    improvement["acknowledgment"] = {
        "accepted": True,
        "scope": "improvement_vs_deployed_only",
        "reason": reason,
        "actor": actor,
        "acknowledged_at": _now(),
        "evidence": {
            "sealed_fixture": fixture_name,
            "sealed_fixture_version": fixture_entry["version"],
            "sealed_sha256": sealed_sha,
            "candidate_result_path": str(candidate_path.resolve()),
            "candidate_result_sha256": file_sha256(candidate_path),
            "candidate_score": candidate_total,
            "deployed_result_path": str(deployed_path.resolve()),
            "deployed_result_sha256": file_sha256(deployed_path),
            "deployed_score": deployed_total,
        },
    }
    _set_gate_decision(gate_report)
    return gate_report


def _atomic_copy(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    staging = destination.with_suffix(destination.suffix + ".staging")
    shutil.copy2(source, staging)
    os.replace(staging, destination)


def promote(
    candidate_path: str | Path,
    deployed_path: str | Path,
    gate_report: Dict[str, Any],
    report_path: str | Path | None = None,
    history_dir: str | Path = DEFAULT_HISTORY_DIR,
) -> Path:
    """Atomically replace the deployed model. Gate pass is mandatory.

    The candidate hash must match the one recorded at gate time (when the
    report carries hashes); the previous deployed model is archived for
    rollback before being replaced.
    """

    if not gate_report.get("contract_passed"):
        raise ValueError(
            "deployment gate failed: contract checks did not pass; "
            "candidate is not promotable"
        )
    if not gate_report.get("improvement_accepted"):
        raise ValueError(
            "improvement check failed without acknowledgment; "
            "candidate is not promotable"
        )
    candidate = Path(candidate_path)
    recorded = gate_report.get("hashes", {}).get("candidate_sha256")
    if recorded is not None and file_sha256(candidate) != recorded:
        raise ValueError(
            "candidate hash changed since the gate ran; re-run the gate"
        )

    deployed = Path(deployed_path)
    history = Path(history_dir)
    archived: Optional[str] = None
    if deployed.exists():
        history.mkdir(parents=True, exist_ok=True)
        stamp = _now().replace(":", "-").split(".")[0]
        archived_path = history / (
            f"deployed_{stamp}_{file_sha256(deployed)[:8]}.json"
        )
        shutil.copy2(deployed, archived_path)
        archived = str(archived_path.resolve())

    _atomic_copy(candidate, deployed)
    gate_report["promotion"] = {
        "promoted_at": _now(),
        "archived_previous": archived,
    }
    destination = (
        Path(report_path)
        if report_path is not None
        else deployed.with_name("deployment_gate_report.json")
    )
    destination.write_text(
        json.dumps(gate_report, ensure_ascii=False, indent=1),
        encoding="utf-8",
    )
    return deployed


def rollback(
    deployed_path: str | Path = DEFAULT_DEPLOYED,
    history_dir: str | Path = DEFAULT_HISTORY_DIR,
    reason: str = "",
) -> Dict[str, Any]:
    """Quarantine the current model and restore the previous approved one."""

    if not reason.strip():
        raise ValueError("rollback requires an explicit reason")
    deployed = Path(deployed_path)
    history = Path(history_dir)
    snapshots = sorted(history.glob("deployed_*.json"))
    if not snapshots:
        raise ValueError("no archived model available for rollback")
    restore_from = snapshots[-1]

    quarantined: Optional[str] = None
    if deployed.exists():
        stamp = _now().replace(":", "-").split(".")[0]
        quarantine_path = history / (
            f"quarantined_{stamp}_{file_sha256(deployed)[:8]}.json"
        )
        shutil.copy2(deployed, quarantine_path)
        quarantined = str(quarantine_path.resolve())

    _atomic_copy(restore_from, deployed)
    report = {
        "schema_version": "router-rollback.v1",
        "rolled_back_at": _now(),
        "reason": reason.strip(),
        "restored_from": str(restore_from.resolve()),
        "quarantined_as": quarantined,
        "deployed_path": str(deployed.resolve()),
    }
    report_file = history / "rollback_report.json"
    report_file.write_text(
        json.dumps(report, ensure_ascii=False, indent=1),
        encoding="utf-8",
    )
    return report

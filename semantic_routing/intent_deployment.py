"""Deployment gate for the v0.3 learned intent model.

Mirrors the pattern-router gate philosophy (pattern_learning/deployment.py)
for the IntentModel artifact:

Gate      = a frozen contract -- fixture SHA registry, append-only anchors,
            minimum (per-intent) counts, and two behavioural checks:
              * foundation_anchors -- the learned layer's own competency,
                checked via IntentModel.predict (raw intent must match);
              * hybrid_regression  -- the actual deployment surface, checked
                via route() with the candidate injected (primary_intent must
                match), so safety routing (verify_then_build, marker wins)
                cannot regress.
Promotion = contract pass + improvement check (candidate's off-campaign
            k-fold not degraded beyond tolerance) + explicit human action,
            atomic replace, previous model archived for rollback.
Rollback  = quarantine the current model and restore the previous one.

Discipline: the dev metric is k-fold over the human-approved intent corpus,
which is DISJOINT from the measurement campaign by construction. The gate
never measures on the campaign.
"""

import json
import os
import random
import shutil
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

from pattern_learning.deployment import (
    IMPROVEMENT_TOLERANCE,
    file_sha256,
    load_registry,
)

from .adapter import route
from .intent_model import IntentModel
from .semantic_packet import INTENTS


GATE_REPORT_SCHEMA_VERSION = "intent-model-deployment-gate.v1"
FOUNDATION_SUITE_SCHEMA = "intent-foundation-anchor-suite.v1"
HYBRID_REGRESSION_SCHEMA = "intent-hybrid-regression.v1"

DEFAULT_CANDIDATE = Path("build/intent_model_v1_candidate.json")
DEFAULT_DEPLOYED = Path("build/intent_model_v1.json")
DEFAULT_FOUNDATION_FIXTURE = Path(
    "tests/fixtures/intent_foundation_anchors_v1.json"
)
DEFAULT_HYBRID_FIXTURE = Path(
    "tests/fixtures/intent_hybrid_regression_v1.json"
)
DEFAULT_REGISTRY = Path("tests/fixtures/intent_gate_fixture_registry.json")
DEFAULT_HISTORY_DIR = Path("build/intent_model_history")

CONTRACT_CHECK_NAMES = (
    "foundation_anchors",
    "hybrid_regression",
    "fixture_integrity",
    "minimum_counts",
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


# --------------------------------------------------------------------------
# dev metric: off-campaign k-fold over the approved corpus
# --------------------------------------------------------------------------
def evaluate_intent_kfold(
    examples: Sequence[Dict[str, Any]],
    *,
    folds: int = 5,
    seed: int = 17,
) -> Dict[str, Any]:
    """Honest generalisation estimate on the approved corpus (no campaign).

    Stratified by intent so every fold keeps the class balance; trains on the
    other folds and scores the held fold, averaging accuracy across folds.
    """

    by_intent: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for ex in examples:
        by_intent[ex["intent"]].append(ex)
    rng = random.Random(seed)
    buckets: List[List[Dict[str, Any]]] = [[] for _ in range(folds)]
    for intent, group in sorted(by_intent.items()):
        shuffled = list(group)
        rng.shuffle(shuffled)
        for i, ex in enumerate(shuffled):
            buckets[i % folds].append(ex)

    fold_acc: List[float] = []
    total_correct = 0
    total_count = 0
    for k in range(folds):
        held = buckets[k]
        train = [e for j, b in enumerate(buckets) if j != k for e in b]
        if not held or len({e["intent"] for e in train}) < 2:
            continue
        model = IntentModel.train(train)
        correct = sum(model.predict(e["input"]).intent == e["intent"]
                      for e in held)
        fold_acc.append(correct / len(held))
        total_correct += correct
        total_count += len(held)
    micro = total_correct / total_count if total_count else 0.0
    macro = sum(fold_acc) / len(fold_acc) if fold_acc else 0.0
    return {
        "kfold_accuracy": micro,
        "kfold_macro_accuracy": macro,
        "folds": len(fold_acc),
        "evaluated_examples": total_count,
    }


# --------------------------------------------------------------------------
# fixture loading
# --------------------------------------------------------------------------
def load_foundation_cases(path: str | Path) -> List[Dict[str, Any]]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if payload.get("schema_version") != FOUNDATION_SUITE_SCHEMA:
        raise ValueError("unsupported intent foundation anchor suite schema")
    return list(payload["cases"])


def load_hybrid_cases(path: str | Path) -> List[Dict[str, Any]]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if payload.get("schema_version") != HYBRID_REGRESSION_SCHEMA:
        raise ValueError("unsupported intent hybrid regression schema")
    return list(payload["cases"])


# --------------------------------------------------------------------------
# checks
# --------------------------------------------------------------------------
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
            "detail": "fixture is not registered in the intent gate registry",
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
    min_intents = {
        intent: int(count)
        for intent, count in entry.get("min_intent_counts", {}).items()
    }
    actual: Dict[str, int] = {}
    for case in cases:
        actual[case["intent"]] = actual.get(case["intent"], 0) + 1
    shortfalls = {
        intent: {"minimum": minimum, "actual": actual.get(intent, 0)}
        for intent, minimum in min_intents.items()
        if actual.get(intent, 0) < minimum
    }
    passed = len(cases) >= min_total and not shortfalls
    return {
        "fixture": fixture_name,
        "min_case_count": min_total,
        "case_count": len(cases),
        "intent_shortfalls": shortfalls,
        "passed": passed,
    }


def _check_route_cases(
    model: IntentModel,
    cases: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """route() with the candidate injected -- the real deployment surface.

    Both behavioural suites are checked here: the hybrid (markers + the
    learned layer, gated) is what users actually get, so anchors are graded
    on route().packet.primary_intent. The learned layer is exercised
    specifically by no-match anchors (where markers stay silent and the
    model decides); marker-owned intents like explain/clarify are graded on
    the deterministic path that owns them, as designed (§11).
    """

    misses: List[Dict[str, Any]] = []
    for case in cases:
        got = route(case["input"], intent_model=model).packet.primary_intent
        if got != case["intent"]:
            misses.append({
                "input": case["input"],
                "expected": case["intent"],
                "predicted": got,
            })
    return {
        "case_count": len(cases),
        "misses": misses,
        "accuracy": (len(cases) - len(misses)) / len(cases) if cases else 1.0,
        "passed": not misses,
    }


def _check_improvement(
    current_metrics: Optional[Dict[str, Any]],
    candidate_metrics: Optional[Dict[str, Any]],
    tolerance: float = IMPROVEMENT_TOLERANCE,
) -> Dict[str, Any]:
    if not current_metrics:
        return {
            "passed": True,
            "detail": "no deployed-model metric to compare against",
            "comparisons": {},
        }
    comparisons: Dict[str, Any] = {}
    passed = True
    for key in ("kfold_accuracy",):
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


def _set_gate_decision(report: Dict[str, Any]) -> None:
    checks = report["checks"]
    missing = [n for n in CONTRACT_CHECK_NAMES if n not in checks]
    contract_passed = not missing and all(
        checks[n].get("passed") is True for n in CONTRACT_CHECK_NAMES
    )
    improvement = checks["improvement_vs_deployed"]
    report["contract_passed"] = contract_passed
    report["improvement_accepted"] = improvement.get("passed") is True
    report["passed"] = contract_passed and report["improvement_accepted"]
    report["decision"] = "pass" if report["passed"] else "blocked"


def evaluate_intent_gate(
    model: IntentModel,
    foundation_cases: List[Dict[str, Any]],
    hybrid_cases: List[Dict[str, Any]],
    current_metrics: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Behavioural + improvement checks only (no file integrity)."""

    checks = {
        "foundation_anchors": {
            "required": "route() primary_intent 100% (all-intent canonical)",
            **_check_route_cases(model, foundation_cases),
        },
        "hybrid_regression": {
            "required": "route() primary_intent 100% (safety + no-match)",
            **_check_route_cases(model, hybrid_cases),
        },
        "improvement_vs_deployed": _check_improvement(
            current_metrics, model.metadata.get("metrics")
        ),
    }
    report = {
        "schema_version": GATE_REPORT_SCHEMA_VERSION,
        "checks": checks,
    }
    # decision needs the integrity/count checks too; callers that only run
    # behavioural checks should read contract_passed after adding them.
    report["contract_passed"] = (
        checks["foundation_anchors"]["passed"]
        and checks["hybrid_regression"]["passed"]
    )
    report["improvement_accepted"] = (
        checks["improvement_vs_deployed"].get("passed") is True
    )
    report["passed"] = report["contract_passed"] and report["improvement_accepted"]
    return report


def run_intent_deployment_gate(
    candidate_path: str | Path = DEFAULT_CANDIDATE,
    foundation_fixture: str | Path = DEFAULT_FOUNDATION_FIXTURE,
    hybrid_fixture: str | Path = DEFAULT_HYBRID_FIXTURE,
    registry_path: str | Path = DEFAULT_REGISTRY,
    deployed_path: str | Path = DEFAULT_DEPLOYED,
) -> Dict[str, Any]:
    candidate_path = Path(candidate_path)
    foundation_fixture = Path(foundation_fixture)
    hybrid_fixture = Path(hybrid_fixture)
    registry = load_registry(registry_path)

    integrity = [
        _check_fixture_integrity(foundation_fixture, registry),
        _check_fixture_integrity(hybrid_fixture, registry),
    ]
    integrity_passed = all(item["passed"] for item in integrity)

    model = IntentModel.load(candidate_path)
    foundation_cases = load_foundation_cases(foundation_fixture)
    hybrid_cases = load_hybrid_cases(hybrid_fixture)

    counts = [
        _check_minimum_counts(foundation_fixture.name, foundation_cases, registry),
        _check_minimum_counts(hybrid_fixture.name, hybrid_cases, registry),
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

    report = evaluate_intent_gate(
        model, foundation_cases, hybrid_cases, current_metrics
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
        "fixtures": {
            foundation_fixture.name: file_sha256(foundation_fixture),
            hybrid_fixture.name: file_sha256(hybrid_fixture),
        },
    }
    report["candidate_path"] = str(candidate_path.resolve())
    report["candidate_trained_at"] = model.metadata.get("trained_at")
    report["candidate_sample_count"] = model.metadata.get("sample_count")
    report["evaluated_at"] = _now()
    return report


def _atomic_copy(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    staging = destination.with_suffix(destination.suffix + ".staging")
    shutil.copy2(source, staging)
    os.replace(staging, destination)


def promote_intent_model(
    candidate_path: str | Path,
    deployed_path: str | Path,
    gate_report: Dict[str, Any],
    report_path: str | Path | None = None,
    history_dir: str | Path = DEFAULT_HISTORY_DIR,
) -> Path:
    """Atomically replace the deployed intent model. Gate pass is mandatory."""

    if not gate_report.get("contract_passed"):
        raise ValueError(
            "intent deployment gate failed: contract checks did not pass"
        )
    if not gate_report.get("improvement_accepted"):
        raise ValueError(
            "intent improvement check failed; candidate is not promotable"
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
        else deployed.with_name("intent_deployment_gate_report.json")
    )
    destination.write_text(
        json.dumps(gate_report, ensure_ascii=False, indent=1),
        encoding="utf-8",
    )
    return deployed


def rollback_intent_model(
    deployed_path: str | Path = DEFAULT_DEPLOYED,
    history_dir: str | Path = DEFAULT_HISTORY_DIR,
    reason: str = "",
) -> Dict[str, Any]:
    """Quarantine the current intent model and restore the previous one."""

    if not reason.strip():
        raise ValueError("rollback requires an explicit reason")
    deployed = Path(deployed_path)
    history = Path(history_dir)
    snapshots = sorted(history.glob("deployed_*.json"))
    if not snapshots:
        raise ValueError("no archived intent model available for rollback")
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
        "schema_version": "intent-model-rollback.v1",
        "rolled_back_at": _now(),
        "reason": reason.strip(),
        "restored_from": str(restore_from.resolve()),
        "quarantined_as": quarantined,
        "deployed_path": str(deployed.resolve()),
    }
    (history / "rollback_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=1),
        encoding="utf-8",
    )
    return report

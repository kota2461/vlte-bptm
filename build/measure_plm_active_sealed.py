"""Measure the active PLM sealed fixture exactly once.

This is a measurement-only script. It opens the active sealed fixture named in
pattern_language_fixture_registry.json, evaluates the current canonical adapter,
writes an immutable report, and marks that fixture as consumed. The sealed
labels must not be used for tuning; rotation is required before any tuning that
uses this report.
"""

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from semantic_routing import (  # noqa: E402
    ADAPTER_VERSION,
    DEFAULT_INTENT_MODEL_PATH,
    evaluate_plm_extractor,
    parse_plm_sealed_fixture,
    route,
)


REGISTRY_PATH = (
    ROOT / "tests" / "fixtures" / "pattern_language_fixture_registry.json"
)
READINESS_PATH = ROOT / "build" / "plm_measurement_readiness_review.json"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _packet_from_route(text: str):
    return route(text).packet


def _active_fixture(registry: Dict[str, Any]) -> tuple[str, Dict[str, Any]]:
    active = [
        (name, entry)
        for name, entry in registry["fixtures"].items()
        if entry.get("role") == "sealed measurement only"
        and entry.get("status") == "active"
    ]
    if len(active) != 1:
        raise SystemExit("expected exactly one active PLM sealed fixture")
    return active[0]


def _readiness_allows(registry_name: str, entry: Dict[str, Any]) -> None:
    readiness = json.loads(READINESS_PATH.read_text(encoding="utf-8"))
    if readiness["decision"] != "eligible":
        raise SystemExit("active PLM sealed measurement is not readiness-eligible")
    if readiness["sealed_fixture_opened"] is not False:
        raise SystemExit("readiness review must not open sealed fixture")
    sealed = readiness["sealed_fixture"]
    if sealed["registry_name"] != registry_name:
        raise SystemExit("readiness fixture does not match active registry fixture")
    if sealed["sha256"] != entry["sha256"]:
        raise SystemExit("readiness fixture hash does not match registry")


def _report_path(registry_name: str) -> Path:
    stem = registry_name.removesuffix(".json")
    return ROOT / "build" / f"{stem}_measurement_report.json"


def _update_registry(
    registry: Dict[str, Any],
    *,
    registry_name: str,
    measured_at: str,
    report_path: Path,
) -> Dict[str, Any]:
    updated = json.loads(json.dumps(registry))
    entry = updated["fixtures"][registry_name]
    entry["status"] = "consumed"
    entry["measured"] = True
    entry["measured_at"] = measured_at
    entry["measured_for"] = f"canonical adapter {registry_name} measurement"
    entry["measurement_report"] = str(report_path.relative_to(ROOT))
    updated["updated_at"] = measured_at
    return updated


def main() -> None:
    measured_at = datetime.now(timezone.utc).isoformat()
    registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    registry_name, entry = _active_fixture(registry)
    if entry["measured"] or entry["reviewed"]:
        raise SystemExit("active PLM sealed fixture is already used")
    _readiness_allows(registry_name, entry)

    sealed_path = ROOT / "tests" / "fixtures" / registry_name
    output_path = _report_path(registry_name)
    if output_path.exists():
        raise SystemExit(f"measurement report already exists: {output_path}")

    fixture_sha = _sha256(sealed_path)
    if fixture_sha != entry["sha256"]:
        raise SystemExit("active PLM sealed SHA mismatch; aborting measurement")

    fixture = parse_plm_sealed_fixture(
        json.loads(sealed_path.read_text(encoding="utf-8"))
    )
    measurements = evaluate_plm_extractor(
        fixture.cases,
        _packet_from_route,
    )
    report = {
        "schema_version": "plm-sealed-measurement-report.v1",
        "measured_at": measured_at,
        "sealed_fixture_opened": True,
        "sealed_labels_used_for_tuning": False,
        "readiness_report": str(READINESS_PATH.relative_to(ROOT)),
        "fixture": {
            "registry_name": registry_name,
            "fixture_id": fixture.fixture_id,
            "sha256": fixture_sha,
            "case_count": len(fixture.cases),
            "predecessor": fixture.predecessor,
            "status_before_measurement": entry["status"],
        },
        "adapter": {
            "entrypoint": "semantic_routing.route(...).packet",
            "version": ADAPTER_VERSION,
            "intent_model_path": str(
                DEFAULT_INTENT_MODEL_PATH.relative_to(ROOT)
            ),
            "intent_model_sha256": _sha256(DEFAULT_INTENT_MODEL_PATH),
        },
        "measurements": measurements,
        "registry_update": {
            "status_after_measurement": "consumed",
            "measured": True,
            "reviewed": entry["reviewed"],
            "rotation_required_before_tuning": True,
        },
    }
    output_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )

    updated = _update_registry(
        registry,
        registry_name=registry_name,
        measured_at=measured_at,
        report_path=output_path,
    )
    REGISTRY_PATH.write_text(
        json.dumps(updated, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )

    summary = {
        "report": str(output_path.relative_to(ROOT)),
        "fixture": registry_name,
        "case_count": measurements["case_count"],
        "intent_accuracy": measurements["intent_accuracy"],
        "critical_signal_recall": measurements["critical_signal_recall"],
        "operation_exact_match": measurements["operation_exact_match"],
        "constraint_exact_match": measurements["constraint_exact_match"],
        "risk_exact_match": measurements["risk_exact_match"],
        "error_count": len(measurements["errors"]),
        "registry_status": "consumed",
        "rotation_required_before_tuning": True,
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

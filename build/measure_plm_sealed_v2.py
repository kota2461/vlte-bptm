"""Measure the active PLM sealed v2 fixture exactly once.

This is a measurement-only script. It opens the sealed fixture, evaluates the
current canonical adapter, writes an immutable report, and marks the fixture as
consumed in the fixture registry. The sealed labels must not be used for tuning.
"""

import hashlib
import json
import sys
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
from semantic_routing.reproducibility import reproducible_now_iso


SEALED_PATH = ROOT / "tests" / "fixtures" / "pattern_language_sealed_v2.json"
REGISTRY_PATH = (
    ROOT / "tests" / "fixtures" / "pattern_language_fixture_registry.json"
)
OUTPUT_PATH = ROOT / "build" / "plm_sealed_v2_measurement_report.json"
REGISTRY_NAME = SEALED_PATH.name


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _packet_from_route(text: str):
    return route(text).packet


def _update_registry(
    registry: Dict[str, Any],
    *,
    measured_at: str,
    report_path: Path,
) -> Dict[str, Any]:
    updated = json.loads(json.dumps(registry))
    entry = updated["fixtures"][REGISTRY_NAME]
    entry["status"] = "consumed"
    entry["measured"] = True
    entry["measured_at"] = measured_at
    entry["measured_for"] = "canonical adapter sealed v2 measurement"
    entry["measurement_report"] = str(report_path.relative_to(ROOT))
    updated["updated_at"] = measured_at
    return updated


def main() -> None:
    measured_at = reproducible_now_iso()
    registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    entry = registry["fixtures"][REGISTRY_NAME]
    if entry["status"] != "active" or entry["measured"]:
        raise SystemExit("PLM sealed v2 has already been measured/consumed")

    fixture_sha = _sha256(SEALED_PATH)
    if fixture_sha != entry["sha256"]:
        raise SystemExit("PLM sealed v2 SHA mismatch; aborting measurement")

    fixture = parse_plm_sealed_fixture(
        json.loads(SEALED_PATH.read_text(encoding="utf-8"))
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
        "fixture": {
            "registry_name": REGISTRY_NAME,
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
    OUTPUT_PATH.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    updated = _update_registry(
        registry,
        measured_at=measured_at,
        report_path=OUTPUT_PATH,
    )
    REGISTRY_PATH.write_text(
        json.dumps(updated, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    summary = {
        "report": str(OUTPUT_PATH.relative_to(ROOT)),
        "case_count": measurements["case_count"],
        "intent_accuracy": measurements["intent_accuracy"],
        "critical_signal_recall": measurements["critical_signal_recall"],
        "operation_exact_match": measurements["operation_exact_match"],
        "constraint_exact_match": measurements["constraint_exact_match"],
        "risk_exact_match": measurements["risk_exact_match"],
        "error_count": len(measurements["errors"]),
        "registry_status": "consumed",
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

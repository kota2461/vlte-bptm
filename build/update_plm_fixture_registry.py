"""Record PLM benchmark review and sealed rotation state."""

import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
BENCHMARK = ROOT / "tests" / "fixtures" / "pattern_language_benchmark_v1.json"
SEALED_V2 = ROOT / "tests" / "fixtures" / "pattern_language_sealed_v2.json"
SEALED_V3 = ROOT / "tests" / "fixtures" / "pattern_language_sealed_v3.json"
SEALED_V4 = ROOT / "tests" / "fixtures" / "pattern_language_sealed_v4.json"
ADJUDICATION = ROOT / "build" / "plm_benchmark_v1_adjudication.json"
SEALED_V2_MEASUREMENT = ROOT / "build" / "plm_sealed_v2_measurement_report.json"
SEALED_V3_MEASUREMENT = ROOT / "build" / "pattern_language_sealed_v3_measurement_report.json"
SEALED_V4_MEASUREMENT = ROOT / "build" / "pattern_language_sealed_v4_measurement_report.json"
SEALED_V4_ROTATION = ROOT / "build" / "v4_sealed_rotation_report.json"
OUTPUT = ROOT / "tests" / "fixtures" / "pattern_language_fixture_registry.json"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _sealed_entry(
    *,
    path: Path,
    predecessor: str,
    measurement_path: Path,
    measured_for: str,
    rotation_report: Path | None = None,
) -> dict[str, Any]:
    base = {
        "sha256": _sha256(path),
        "case_count": 28,
        "role": "sealed measurement only",
        "predecessor": predecessor,
        "reviewed": False,
    }
    if measurement_path.exists():
        measurement = _load(measurement_path)
        return {
            **base,
            "status": "consumed",
            "measured": True,
            "measured_at": measurement["measured_at"],
            "measured_for": measured_for,
            "measurement_report": _rel(measurement_path),
        }
    entry = {
        **base,
        "status": "active",
        "measured": False,
    }
    if rotation_report is not None and rotation_report.exists():
        rotation = _load(rotation_report)
        entry["rotated_at"] = rotation["rotated_at"]
        entry["rotation_report"] = _rel(rotation_report)
    return entry


def main() -> None:
    adjudication = _load(ADJUDICATION)
    sealed_v2_measurement = _load(SEALED_V2_MEASUREMENT)
    sealed_v3_entry = _sealed_entry(
        path=SEALED_V3,
        predecessor="pattern_language_sealed_v2.json",
        measurement_path=SEALED_V3_MEASUREMENT,
        measured_for="canonical adapter pattern_language_sealed_v3.json measurement",
    )
    fixtures = {
        "pattern_language_benchmark_v1.json": {
            "sha256": _sha256(BENCHMARK),
            "case_count": 84,
            "review_status": "human_reviewed",
            "train_count": 28,
            "validation_count": 28,
            "sealed_count": 28,
            "sealed_status": "consumed",
            "sealed_consumed_at": adjudication["review_completed_at"],
            "sealed_consumed_for": "human label review",
            "successor": "pattern_language_sealed_v2.json",
            "changed_label_count": adjudication["changed_count"],
        },
        "pattern_language_sealed_v2.json": {
            "sha256": _sha256(SEALED_V2),
            "case_count": 28,
            "status": "consumed",
            "role": "sealed measurement only",
            "predecessor": "pattern_language_benchmark_v1.json#sealed",
            "measured": True,
            "reviewed": False,
            "measured_at": sealed_v2_measurement["measured_at"],
            "measured_for": "canonical adapter sealed v2 measurement",
            "measurement_report": _rel(SEALED_V2_MEASUREMENT),
            "successor": "pattern_language_sealed_v3.json",
        },
        "pattern_language_sealed_v3.json": sealed_v3_entry,
    }
    updated_at = sealed_v3_entry.get("measured_at", "2026-06-18T12:00:00+00:00")
    if SEALED_V4.exists():
        sealed_v3_entry["successor"] = "pattern_language_sealed_v4.json"
        sealed_v4_entry = _sealed_entry(
            path=SEALED_V4,
            predecessor="pattern_language_sealed_v3.json",
            measurement_path=SEALED_V4_MEASUREMENT,
            measured_for="canonical adapter pattern_language_sealed_v4.json measurement",
            rotation_report=SEALED_V4_ROTATION,
        )
        fixtures["pattern_language_sealed_v4.json"] = sealed_v4_entry
        updated_at = sealed_v4_entry.get("measured_at", sealed_v4_entry.get("rotated_at", updated_at))
    payload = {
        "schema_version": "pattern-language-fixture-registry.v1",
        "updated_at": updated_at,
        "rules": [
            "human-reviewed train and validation labels are append-only",
            "a sealed fixture is measured at most once before rotation",
            "opening sealed cases for review consumes the fixture",
            "sealed labels are never used for tuning before rotation",
        ],
        "fixtures": fixtures,
    }
    OUTPUT.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(f"wrote {OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()

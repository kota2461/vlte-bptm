"""Rotate an unopened PLM sealed v5 fixture into the active registry slot."""

import hashlib
import importlib.util
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from semantic_routing import parse_plm_sealed_fixture  # noqa: E402


GENERATOR_PATH = ROOT / "build" / "generate_plm_sealed_v5.py"
REGISTRY_PATH = ROOT / "tests" / "fixtures" / "pattern_language_fixture_registry.json"
SEALED_V4_PATH = ROOT / "tests" / "fixtures" / "pattern_language_sealed_v4.json"
SEALED_V5_PATH = ROOT / "tests" / "fixtures" / "pattern_language_sealed_v5.json"
V4_MEASUREMENT_PATH = ROOT / "build" / "pattern_language_sealed_v4_measurement_report.json"
STEP5_GATE_PATH = ROOT / "build" / "v5_nonsealed_replay_gate_report.json"
ROTATION_REPORT_PATH = ROOT / "build" / "v5_sealed_rotation_report.json"
TARGETS_PATH = ROOT / "build" / "v5_targets_and_roadmap_v1.json"
ROADMAP_PATH = ROOT / "docs" / "PLM_V5_ROADMAP.md"
MAIN_ROADMAP_PATH = ROOT / "docs" / "PATTERN_LANGUAGE_MODEL_roadmap.md"
READINESS_SCRIPT = ROOT / "build" / "review_plm_measurement_readiness.py"


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


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_generator():
    spec = importlib.util.spec_from_file_location(
        "generate_plm_sealed_v5",
        GENERATOR_PATH,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("failed to load sealed v5 generator")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _write_fixture() -> dict[str, Any]:
    generator = _load_generator()
    payload = generator.build_payload()
    generator.validate_no_overlap(payload)
    SEALED_V5_PATH.write_text(
        json.dumps(payload, ensure_ascii=False, indent=1) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return payload


def _validate_step5_gate() -> dict[str, Any]:
    gate = _load_json(STEP5_GATE_PATH)
    if gate["schema_version"] != "v5-nonsealed-replay-gate-report.v1":
        raise ValueError("unexpected Step 5 gate schema")
    if gate["status"] != "passed" or gate["passed"] is not True:
        raise ValueError("Step 5 non-sealed replay gate must pass before rotation")
    if gate["summary"]["ready_for_step6_sealed_v5_rotation"] is not True:
        raise ValueError("Step 5 gate did not authorize sealed v5 rotation")
    return gate


def _update_registry(
    generated_at: str,
    sealed_hash: str,
    fixture: Any,
) -> dict[str, Any]:
    registry = _load_json(REGISTRY_PATH)
    fixtures = registry["fixtures"]
    v4 = fixtures["pattern_language_sealed_v4.json"]
    if v4["status"] != "consumed" or v4["measured"] is not True:
        raise ValueError("sealed v4 must be consumed before rotating sealed v5")

    active = [
        name
        for name, entry in fixtures.items()
        if entry.get("role") == "sealed measurement only"
        and entry.get("status") == "active"
        and name != SEALED_V5_PATH.name
    ]
    if active:
        raise ValueError(f"active sealed fixture already exists: {active[0]}")

    v4["successor"] = SEALED_V5_PATH.name
    fixtures[SEALED_V5_PATH.name] = {
        "sha256": sealed_hash,
        "case_count": len(fixture.cases),
        "role": "sealed measurement only",
        "predecessor": SEALED_V4_PATH.name,
        "reviewed": False,
        "status": "active",
        "measured": False,
    }
    registry["updated_at"] = generated_at
    _write_json(REGISTRY_PATH, registry)
    return registry


def _write_rotation_report(
    generated_at: str,
    sealed_hash: str,
    fixture: Any,
    gate: dict[str, Any],
) -> dict[str, Any]:
    report = {
        "schema_version": "v5-sealed-rotation-report.v1",
        "rotated_at": generated_at,
        "policy": {
            "sealed_v5_opened_for_measurement": False,
            "sealed_v5_labels_used_for_tuning": False,
            "sealed_v4_text_used_for_training": False,
            "sealed_v4_labels_used_for_tuning": False,
            "v4_measurement_used_as_taxonomy_only": True,
            "nonsealed_replay_gate_required": True,
            "nonsealed_replay_gate_passed": gate["passed"],
            "same_cycle_promotion_allowed": False,
        },
        "gate_source": _rel(STEP5_GATE_PATH),
        "rotated_from": {
            "registry_name": SEALED_V4_PATH.name,
            "status": "consumed",
            "measurement_report": _rel(V4_MEASUREMENT_PATH),
        },
        "rotated_to": {
            "registry_name": SEALED_V5_PATH.name,
            "fixture_id": fixture.fixture_id,
            "sha256": sealed_hash,
            "case_count": len(fixture.cases),
            "predecessor": SEALED_V4_PATH.name,
            "status": "active",
            "measured": False,
            "reviewed": False,
        },
        "next_action": "measure_active_sealed_once_when_readiness_eligible",
    }
    _write_json(ROTATION_REPORT_PATH, report)
    return report


def _update_targets_and_docs(generated_at: str, report: dict[str, Any]) -> None:
    targets = _load_json(TARGETS_PATH)
    targets["generated_at"] = generated_at
    targets["status"] = "sealed_v5_rotated_active"
    for item in targets["roadmap"]:
        if item["step"] == 6:
            item["status"] = "completed"
        elif item["step"] == 7:
            item["status"] = "next"
    targets["step6_sealed_v5_rotation"] = {
        "output": "tests\\fixtures\\pattern_language_sealed_v5.json",
        "report": "build\\v5_sealed_rotation_report.json",
        "status": "active_unmeasured",
        "sealed_v5_opened_for_measurement": False,
        "sealed_v5_labels_used_for_tuning": False,
        "sealed_v4_text_used_for_training": False,
        "nonsealed_replay_gate_passed": True,
        "fixture": report["rotated_to"],
    }
    _write_json(TARGETS_PATH, targets)

    roadmap = ROADMAP_PATH.read_text(encoding="utf-8")
    roadmap = roadmap.replace(
        "| 6 | sealed_v5_rotation | `tests\\fixtures\\pattern_language_sealed_v5.json` | next |",
        "| 6 | sealed_v5_rotation | `tests\\fixtures\\pattern_language_sealed_v5.json` | completed |",
    )
    roadmap = roadmap.replace(
        "| 7 | sealed_v5_one_time_measurement | `build\\pattern_language_sealed_v5_measurement_report.json` | pending |",
        "| 7 | sealed_v5_one_time_measurement | `build\\pattern_language_sealed_v5_measurement_report.json` | next |",
    )
    section = f"""
## Step 6 Output

`build\\v5_sealed_rotation_report.json` created `tests\\fixtures\\pattern_language_sealed_v5.json` as the active unopened sealed fixture. It has {report['rotated_to']['case_count']} cases, predecessor `pattern_language_sealed_v4.json`, measured `False`, reviewed `False`, and sha256 `{report['rotated_to']['sha256']}`. Step 7 is the one-time sealed v5 measurement.
""".strip()
    if "## Step 6 Output" in roadmap:
        head, rest = roadmap.split("## Step 6 Output", 1)
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
        "Status: V5 Step 5 non-sealed replay gate passed; sealed v4 measured and consumed; Step 6 sealed v5 rotation next.",
        "Status: V5 Step 6 sealed v5 rotation completed; sealed v5 active/unmeasured; Step 7 one-time sealed v5 measurement next.",
    )
    if "Sealed v5 rotation report:" not in main:
        main = main.replace(
            "Non-sealed replay gate report: `build/v5_nonsealed_replay_gate_report.json`\n",
            "Non-sealed replay gate report: `build/v5_nonsealed_replay_gate_report.json`\nSealed v5 rotation report: `build/v5_sealed_rotation_report.json`\nSealed v5 fixture: `tests/fixtures/pattern_language_sealed_v5.json`\n",
        )
    main = main.replace(
        "Step 5 non-sealed replay gate passed across visible PLM, Failure Memory, Puzzle Failure Memory, and the V5 challenge fixture. The immediate priority is Step 6 sealed v5 rotation; a fresh sealed v5 fixture must be created before the next adjudicating measurement.",
        "Step 5 non-sealed replay gate passed across visible PLM, Failure Memory, Puzzle Failure Memory, and the V5 challenge fixture. Step 6 rotated a fresh sealed v5 fixture into the active, unmeasured slot. The immediate priority is Step 7 one-time sealed v5 measurement.",
    )
    MAIN_ROADMAP_PATH.write_text(main, encoding="utf-8", newline="\n")


def _refresh_readiness_review() -> None:
    subprocess.run(
        [sys.executable, "-B", str(READINESS_SCRIPT)],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )


def main() -> None:
    generated_at = datetime.now(timezone.utc).isoformat()
    gate = _validate_step5_gate()
    payload = _write_fixture()
    fixture = parse_plm_sealed_fixture(payload)
    sealed_hash = _sha256(SEALED_V5_PATH)
    _update_registry(generated_at, sealed_hash, fixture)
    report = _write_rotation_report(generated_at, sealed_hash, fixture, gate)
    _update_targets_and_docs(generated_at, report)
    _refresh_readiness_review()
    print(
        json.dumps(
            {
                "status": "rotated",
                "fixture": SEALED_V5_PATH.name,
                "case_count": len(fixture.cases),
                "sha256": sealed_hash,
                "measured": False,
                "reviewed": False,
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()

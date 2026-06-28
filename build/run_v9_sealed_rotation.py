"""Rotate an unopened PLM sealed v9 fixture into the active registry slot."""

import hashlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from semantic_routing import parse_plm_sealed_fixture  # noqa: E402
from semantic_routing.reproducibility import reproducible_now_iso


GENERATOR_PATH = ROOT / "build" / "generate_plm_sealed_v9.py"
REGISTRY_PATH = ROOT / "tests" / "fixtures" / "pattern_language_fixture_registry.json"
SEALED_V9_PATH = ROOT / "tests" / "fixtures" / "pattern_language_sealed_v9.json"
V8_MEASUREMENT_PATH = ROOT / "build" / "pattern_language_sealed_v8_measurement_report.json"
STEP6_REVIEW_PATH = ROOT / "build" / "v9_sealed_rotation_review_v1.json"
STEP5_GATE_PATH = ROOT / "build" / "v9_nonsealed_replay_gate_report_v1.json"
ROTATION_REPORT_PATH = ROOT / "build" / "v9_sealed_rotation_report_v1.json"
ROTATION_REPORT_MD_PATH = ROOT / "build" / "v9_sealed_rotation_report_v1.md"
READINESS_SCRIPT = ROOT / "build" / "review_plm_measurement_readiness.py"
READINESS_PATH = ROOT / "build" / "plm_measurement_readiness_review.json"
ROADMAP_SCRIPT = ROOT / "build" / "create_v9_targets_and_roadmap.py"


def _rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_generator():
    spec = importlib.util.spec_from_file_location("generate_plm_sealed_v9", GENERATOR_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("failed to load sealed v9 generator")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _write_fixture() -> Any:
    generator = _load_generator()
    payload = generator.build_payload()
    generator.validate_no_overlap(payload)
    SEALED_V9_PATH.write_text(
        json.dumps(payload, ensure_ascii=False, indent=1) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return parse_plm_sealed_fixture(payload)


def _validate_step6_review() -> dict[str, Any]:
    review = _load_json(STEP6_REVIEW_PATH)
    if review["schema_version"] != "v9-sealed-rotation-review.v1":
        raise ValueError("unexpected Step 6 review schema")
    if review["decision"] != "eligible_for_fresh_sealed_v9_rotation":
        raise ValueError("Step 6 did not authorize sealed v9 rotation")
    if review["passed"] is not True:
        raise ValueError("Step 6 sealed rotation review must pass")
    if review["policy"]["sealed_v9_fixture_created_now"] is not False:
        raise ValueError("Step 6 review must be pre-rotation")
    if review["gate_summary"]["required_error_count"] != 0:
        raise ValueError("Step 6 review contains required lane errors")
    return review


def _update_registry(rotated_at: str, sealed_hash: str, fixture: Any) -> dict[str, Any]:
    registry = _load_json(REGISTRY_PATH)
    fixtures = registry["fixtures"]
    if SEALED_V9_PATH.name in fixtures:
        raise ValueError("sealed v9 is already registered")

    v8 = fixtures["pattern_language_sealed_v8.json"]
    if v8["status"] != "consumed" or v8["measured"] is not True:
        raise ValueError("sealed v8 must be consumed before rotating sealed v9")

    active = [
        name
        for name, entry in fixtures.items()
        if entry.get("role") == "sealed measurement only"
        and entry.get("status") == "active"
    ]
    if active:
        raise ValueError(f"active sealed fixture already exists: {active[0]}")

    v8["successor"] = SEALED_V9_PATH.name
    fixtures[SEALED_V9_PATH.name] = {
        "sha256": sealed_hash,
        "case_count": len(fixture.cases),
        "role": "sealed measurement only",
        "predecessor": "pattern_language_sealed_v8.json",
        "reviewed": False,
        "status": "active",
        "measured": False,
    }
    registry["updated_at"] = rotated_at
    _write_json(REGISTRY_PATH, registry)
    return registry


def _refresh_readiness_review() -> dict[str, Any]:
    subprocess.run(
        [sys.executable, "-B", str(READINESS_SCRIPT)],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return _load_json(READINESS_PATH)


def _refresh_roadmap() -> None:
    subprocess.run(
        [sys.executable, "-B", str(ROADMAP_SCRIPT)],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )


def _write_rotation_report(
    rotated_at: str,
    sealed_hash: str,
    fixture: Any,
    readiness: dict[str, Any],
) -> dict[str, Any]:
    report = {
        "schema_version": "v9-sealed-rotation-report.v1",
        "rotated_at": rotated_at,
        "policy": {
            "sealed_v9_opened_for_measurement": False,
            "sealed_v9_labels_used_for_tuning": False,
            "sealed_v8_text_used_for_training": False,
            "sealed_v8_labels_used_for_tuning": False,
            "sealed_v8_measurement_used_as_taxonomy_only": True,
            "nonsealed_replay_gate_required": True,
            "nonsealed_replay_gate_passed": True,
            "same_cycle_promotion_allowed": False,
        },
        "step6_review_source": _rel(STEP6_REVIEW_PATH),
        "step5_gate_source": _rel(STEP5_GATE_PATH),
        "rotated_from": {
            "registry_name": "pattern_language_sealed_v8.json",
            "status": "consumed",
            "measurement_report": _rel(V8_MEASUREMENT_PATH),
        },
        "rotated_to": {
            "registry_name": SEALED_V9_PATH.name,
            "fixture_id": fixture.fixture_id,
            "sha256": sealed_hash,
            "case_count": len(fixture.cases),
            "predecessor": "pattern_language_sealed_v8.json",
            "status": "active",
            "measured": False,
            "reviewed": False,
        },
        "fixture_contract": {
            "case_count": 28,
            "cases_per_intent": 4,
            "split": "sealed",
            "no_exact_overlap_validated": True,
            "measurement_rule": "measure_once_then_mark_consumed",
        },
        "readiness_after_rotation": {
            "report": _rel(READINESS_PATH),
            "decision": readiness["decision"],
            "sealed_fixture_opened": readiness["sealed_fixture_opened"],
            "sealed_fixture": readiness["sealed_fixture"],
            "blocked_reasons": readiness["blocked_reasons"],
            "next_action": readiness["next_action"],
        },
        "next_action": "roadmap_v9_step8_measure_active_sealed_v9_once",
    }
    _write_json(ROTATION_REPORT_PATH, report)
    return report


def _write_markdown(report: dict[str, Any]) -> None:
    rotated_to = report["rotated_to"]
    readiness = report["readiness_after_rotation"]
    lines = [
        "# V9 Sealed Rotation Report v1",
        "",
        f"- fixture: `{rotated_to['registry_name']}`",
        f"- status: `{rotated_to['status']}`",
        f"- measured: `{rotated_to['measured']}`",
        f"- reviewed: `{rotated_to['reviewed']}`",
        f"- case_count: `{rotated_to['case_count']}`",
        f"- predecessor: `{rotated_to['predecessor']}`",
        f"- sha256: `{rotated_to['sha256']}`",
        f"- sealed_v9_opened_for_measurement: `{report['policy']['sealed_v9_opened_for_measurement']}`",
        f"- sealed_v9_labels_used_for_tuning: `{report['policy']['sealed_v9_labels_used_for_tuning']}`",
        f"- same_cycle_promotion_allowed: `{report['policy']['same_cycle_promotion_allowed']}`",
        "",
        "## Readiness After Rotation",
        "",
        f"- decision: `{readiness['decision']}`",
        f"- sealed_fixture_opened: `{readiness['sealed_fixture_opened']}`",
        f"- sealed_fixture: `{readiness['sealed_fixture']}`",
        f"- blocked_reasons: `{readiness['blocked_reasons']}`",
        f"- next_action: `{readiness['next_action']}`",
        "",
        "## Next",
        "",
        "Step 8 may measure the active sealed v9 fixture once. After that measurement, the fixture must be marked consumed before any tuning based on the result.",
    ]
    ROTATION_REPORT_MD_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def main() -> None:
    rotated_at = reproducible_now_iso()
    _validate_step6_review()
    fixture = _write_fixture()
    sealed_hash = _sha256(SEALED_V9_PATH)
    _update_registry(rotated_at, sealed_hash, fixture)
    readiness = _refresh_readiness_review()
    report = _write_rotation_report(rotated_at, sealed_hash, fixture, readiness)
    _write_markdown(report)
    _refresh_roadmap()
    print(
        json.dumps(
            {
                "status": "sealed_v9_rotation_completed",
                "fixture": _rel(SEALED_V9_PATH),
                "case_count": len(fixture.cases),
                "readiness_decision": readiness["decision"],
                "next_action": report["next_action"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()

"""Rotate an unopened PLM sealed v8 fixture into the active registry slot."""

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


GENERATOR_PATH = ROOT / "build" / "generate_plm_sealed_v8.py"
REGISTRY_PATH = ROOT / "tests" / "fixtures" / "pattern_language_fixture_registry.json"
SEALED_V8_PATH = ROOT / "tests" / "fixtures" / "pattern_language_sealed_v8.json"
V7_MEASUREMENT_PATH = ROOT / "build" / "pattern_language_sealed_v7_measurement_report.json"
STEP6_REVIEW_PATH = ROOT / "build" / "v8_sealed_rotation_review_v1.json"
STEP5_GATE_PATH = ROOT / "build" / "v8_nonsealed_replay_gate_report_v1.json"
ROTATION_REPORT_PATH = ROOT / "build" / "v8_sealed_rotation_report_v1.json"
ROTATION_REPORT_MD_PATH = ROOT / "build" / "v8_sealed_rotation_report_v1.md"
ROADMAP_PATH = ROOT / "docs" / "PLM_V8_ROADMAP.md"
MAIN_ROADMAP_PATH = ROOT / "docs" / "PATTERN_LANGUAGE_MODEL_roadmap.md"
TARGETS_PATH = ROOT / "build" / "v8_targets_and_roadmap_v1.json"
READINESS_SCRIPT = ROOT / "build" / "review_plm_measurement_readiness.py"
READINESS_PATH = ROOT / "build" / "plm_measurement_readiness_review.json"


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
        "generate_plm_sealed_v8",
        GENERATOR_PATH,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("failed to load sealed v8 generator")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _write_fixture() -> Any:
    generator = _load_generator()
    payload = generator.build_payload()
    generator.validate_no_overlap(payload)
    SEALED_V8_PATH.write_text(
        json.dumps(payload, ensure_ascii=False, indent=1) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return parse_plm_sealed_fixture(payload)


def _validate_step6_review() -> dict[str, Any]:
    review = _load_json(STEP6_REVIEW_PATH)
    if review["schema_version"] != "v8-sealed-rotation-review.v1":
        raise ValueError("unexpected Step 6 review schema")
    if review["decision"] != "eligible_for_fresh_sealed_v8_rotation":
        raise ValueError("Step 6 did not authorize sealed v8 rotation")
    if review["passed"] is not True:
        raise ValueError("Step 6 sealed rotation review must pass")
    if review["policy"]["sealed_v8_fixture_created_now"] is not False:
        raise ValueError("Step 6 review must be pre-rotation")
    if review["gate_summary"]["required_error_count"] != 0:
        raise ValueError("Step 6 review contains required lane errors")
    return review


def _update_registry(rotated_at: str, sealed_hash: str, fixture: Any) -> dict[str, Any]:
    registry = _load_json(REGISTRY_PATH)
    fixtures = registry["fixtures"]
    if SEALED_V8_PATH.name in fixtures:
        raise ValueError("sealed v8 is already registered")

    v7 = fixtures["pattern_language_sealed_v7.json"]
    if v7["status"] != "consumed" or v7["measured"] is not True:
        raise ValueError("sealed v7 must be consumed before rotating sealed v8")

    active = [
        name
        for name, entry in fixtures.items()
        if entry.get("role") == "sealed measurement only"
        and entry.get("status") == "active"
    ]
    if active:
        raise ValueError(f"active sealed fixture already exists: {active[0]}")

    v7["successor"] = SEALED_V8_PATH.name
    fixtures[SEALED_V8_PATH.name] = {
        "sha256": sealed_hash,
        "case_count": len(fixture.cases),
        "role": "sealed measurement only",
        "predecessor": "pattern_language_sealed_v7.json",
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


def _write_rotation_report(
    rotated_at: str,
    sealed_hash: str,
    fixture: Any,
    readiness: dict[str, Any],
) -> dict[str, Any]:
    report = {
        "schema_version": "v8-sealed-rotation-report.v1",
        "rotated_at": rotated_at,
        "policy": {
            "sealed_v8_opened_for_measurement": False,
            "sealed_v8_labels_used_for_tuning": False,
            "sealed_v7_text_used_for_training": False,
            "sealed_v7_labels_used_for_tuning": False,
            "sealed_v7_measurement_used_as_taxonomy_only": True,
            "nonsealed_replay_gate_required": True,
            "nonsealed_replay_gate_passed": True,
            "same_cycle_promotion_allowed": False,
        },
        "step6_review_source": _rel(STEP6_REVIEW_PATH),
        "step5_gate_source": _rel(STEP5_GATE_PATH),
        "rotated_from": {
            "registry_name": "pattern_language_sealed_v7.json",
            "status": "consumed",
            "measurement_report": _rel(V7_MEASUREMENT_PATH),
        },
        "rotated_to": {
            "registry_name": SEALED_V8_PATH.name,
            "fixture_id": fixture.fixture_id,
            "sha256": sealed_hash,
            "case_count": len(fixture.cases),
            "predecessor": "pattern_language_sealed_v7.json",
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
        "next_action": "roadmap_v8_step8_measure_active_sealed_v8_once",
    }
    _write_json(ROTATION_REPORT_PATH, report)
    return report


def _write_markdown(report: dict[str, Any]) -> None:
    rotated_to = report["rotated_to"]
    readiness = report["readiness_after_rotation"]
    lines = [
        "# V8 Sealed Rotation Report v1",
        "",
        f"- fixture: `{rotated_to['registry_name']}`",
        f"- status: `{rotated_to['status']}`",
        f"- measured: `{rotated_to['measured']}`",
        f"- reviewed: `{rotated_to['reviewed']}`",
        f"- case_count: `{rotated_to['case_count']}`",
        f"- predecessor: `{rotated_to['predecessor']}`",
        f"- sha256: `{rotated_to['sha256']}`",
        f"- sealed_v8_opened_for_measurement: `{report['policy']['sealed_v8_opened_for_measurement']}`",
        f"- sealed_v8_labels_used_for_tuning: `{report['policy']['sealed_v8_labels_used_for_tuning']}`",
        f"- same_cycle_promotion_allowed: `{report['policy']['same_cycle_promotion_allowed']}`",
        "",
        "## Readiness After Rotation",
        "",
        f"- decision: `{readiness['decision']}`",
        f"- sealed_fixture_opened: `{readiness['sealed_fixture_opened']}`",
        f"- blocked_reasons: `{readiness['blocked_reasons']}`",
        f"- next_action: `{readiness['next_action']}`",
        "",
        "## Next",
        "",
        "Step 8 may measure the active sealed v8 fixture once. After that measurement, the fixture must be marked consumed before any tuning based on the result.",
    ]
    ROTATION_REPORT_MD_PATH.write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def _update_targets(report: dict[str, Any]) -> None:
    targets = _load_json(TARGETS_PATH)
    targets["generated_at"] = report["rotated_at"]
    targets["status"] = "step7_sealed_rotation_completed_step8_measurement_next"
    targets["next_action"] = "roadmap_v8_step8_measure_active_sealed_v8_once"
    for item in targets["roadmap"]:
        if item["step"] == 7:
            item["status"] = "completed"
        elif item["step"] == 8:
            item["status"] = "next"
    targets["step7_sealed_rotation"] = {
        "output": "build\\v8_sealed_rotation_report_v1.json",
        "fixture": "tests\\fixtures\\pattern_language_sealed_v8.json",
        "passed": True,
        "sealed_v8_opened_for_measurement": False,
        "sealed_v8_labels_used_for_tuning": False,
        "same_cycle_promotion_allowed": False,
        "summary": {
            "case_count": report["rotated_to"]["case_count"],
            "status": report["rotated_to"]["status"],
            "measured": report["rotated_to"]["measured"],
            "reviewed": report["rotated_to"]["reviewed"],
            "readiness_decision": report["readiness_after_rotation"]["decision"],
            "blocked_reasons": report["readiness_after_rotation"]["blocked_reasons"],
        },
    }
    _write_json(TARGETS_PATH, targets)


def _update_roadmaps(report: dict[str, Any]) -> None:
    roadmap = ROADMAP_PATH.read_text(encoding="utf-8")
    roadmap = roadmap.replace(
        "| 7 | sealed_v8_rotation | `tests\\fixtures\\pattern_language_sealed_v8.json` | next |",
        "| 7 | sealed_v8_rotation | `tests\\fixtures\\pattern_language_sealed_v8.json` | completed |",
    )
    roadmap = roadmap.replace(
        "| 8 | sealed_v8_one_time_measurement | `build\\pattern_language_sealed_v8_measurement_report.json` | pending |",
        "| 8 | sealed_v8_one_time_measurement | `build\\pattern_language_sealed_v8_measurement_report.json` | next |",
    )
    section = (
        "## Step 7 Output\n\n"
        "`build\\v8_sealed_rotation_report_v1.json` created "
        "`tests\\fixtures\\pattern_language_sealed_v8.json` as the active unopened sealed fixture. "
        f"It has {report['rotated_to']['case_count']} cases, predecessor "
        "`pattern_language_sealed_v7.json`, measured `False`, reviewed `False`, "
        f"and sha256 `{report['rotated_to']['sha256']}`. Step 8 is the one-time sealed v8 measurement.\n"
    )
    if "## Step 7 Output" in roadmap:
        head, _ = roadmap.split("## Step 7 Output", 1)
        roadmap = head.rstrip() + "\n\n" + section
    else:
        roadmap = roadmap.rstrip() + "\n\n" + section
    ROADMAP_PATH.write_text(roadmap, encoding="utf-8", newline="\n")

    marker = "## PLM V8: Recovery Gate And Fresh Rotation"
    main = MAIN_ROADMAP_PATH.read_text(encoding="utf-8")
    section = f"""
{marker}

Status: V8 Step 7 sealed v8 rotation completed; sealed v8 active/unmeasured; Step 8 one-time sealed v8 measurement next.

Primary roadmap: `docs/PLM_V8_ROADMAP.md`
Targets and taxonomy: `build/v8_targets_and_roadmap_v1.json`
Recovery priority selection: `build/v8_recovery_debate_candidate_priority_selection_v1.json`
Approved priority replay: `build/v8_recovery_priority_review_provisional_test_report_v1.json`
Non-sealed replay gate report: `build/v8_nonsealed_replay_gate_report_v1.json`
Sealed v8 rotation review: `build/v8_sealed_rotation_review_v1.json`
Sealed v8 rotation report: `build/v8_sealed_rotation_report_v1.json`
Sealed v8 fixture: `tests/fixtures/pattern_language_sealed_v8.json`
Baseline sealed v7 measurement: `build/pattern_language_sealed_v7_measurement_report.json`

V8 uses sealed v7 measurement only as aggregate taxonomy. The approved V8 priority review replay is exact on 30 non-sealed cases, Step 6 sealed rotation review authorized fresh sealed v8 rotation, and Step 7 rotated a fresh unopened `pattern_language_sealed_v8.json` into the active measurement slot. Sealed v8 is not measured or reviewed yet; Step 8 is the one-time adjudicating measurement.
""".strip()
    if marker in main:
        head, _ = main.split(marker, 1)
        main = head.rstrip() + "\n\n" + section + "\n"
    else:
        main = main.rstrip() + "\n\n" + section + "\n"
    MAIN_ROADMAP_PATH.write_text(main, encoding="utf-8", newline="\n")


def main() -> None:
    rotated_at = datetime.now(timezone.utc).isoformat()
    _validate_step6_review()
    fixture = _write_fixture()
    sealed_hash = _sha256(SEALED_V8_PATH)
    _update_registry(rotated_at, sealed_hash, fixture)
    readiness = _refresh_readiness_review()
    report = _write_rotation_report(rotated_at, sealed_hash, fixture, readiness)
    _write_markdown(report)
    _update_targets(report)
    _update_roadmaps(report)
    print(
        json.dumps(
            {
                "status": "sealed_v8_rotation_completed",
                "fixture": _rel(SEALED_V8_PATH),
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

"""Rotate an unopened PLM sealed v7 fixture into the active registry slot."""

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
sys.path.insert(0, str(ROOT / "build"))

from semantic_routing import parse_plm_sealed_fixture  # noqa: E402
from v7_measurement_state import preserve_step8_measurement_state  # noqa: E402


GENERATOR_PATH = ROOT / "build" / "generate_plm_sealed_v7.py"
REGISTRY_PATH = ROOT / "tests" / "fixtures" / "pattern_language_fixture_registry.json"
SEALED_V6_PATH = ROOT / "tests" / "fixtures" / "pattern_language_sealed_v6.json"
SEALED_V7_PATH = ROOT / "tests" / "fixtures" / "pattern_language_sealed_v7.json"
V6_MEASUREMENT_PATH = ROOT / "build" / "pattern_language_sealed_v6_measurement_report.json"
STEP6_REVIEW_PATH = ROOT / "build" / "v7_sealed_rotation_review_v1.json"
STEP5_GATE_PATH = ROOT / "build" / "v7_nonsealed_replay_gate_report_v1.json"
ROTATION_REPORT_PATH = ROOT / "build" / "v7_sealed_rotation_report_v1.json"
ROTATION_REPORT_MD_PATH = ROOT / "build" / "v7_sealed_rotation_report_v1.md"
ROADMAP_PATH = ROOT / "docs" / "PLM_V7_ROADMAP.md"
MAIN_ROADMAP_PATH = ROOT / "docs" / "PATTERN_LANGUAGE_MODEL_roadmap.md"
TARGETS_PATH = ROOT / "build" / "v7_targets_and_roadmap_v1.json"
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
        "generate_plm_sealed_v7",
        GENERATOR_PATH,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("failed to load sealed v7 generator")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _write_fixture() -> Any:
    generator = _load_generator()
    payload = generator.build_payload()
    generator.validate_no_overlap(payload)
    SEALED_V7_PATH.write_text(
        json.dumps(payload, ensure_ascii=False, indent=1) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return parse_plm_sealed_fixture(payload)


def _validate_step6_review() -> dict[str, Any]:
    review = _load_json(STEP6_REVIEW_PATH)
    if review["schema_version"] != "v7-sealed-rotation-review.v1":
        raise ValueError("unexpected Step 6 review schema")
    if review["decision"] != "eligible_for_fresh_sealed_v7_rotation":
        raise ValueError("Step 6 did not authorize sealed v7 rotation")
    if review["passed"] is not True:
        raise ValueError("Step 6 sealed rotation review must pass")
    if review["policy"]["sealed_v7_fixture_created_now"] is not False:
        raise ValueError("Step 6 review must be pre-rotation")
    if review["gate_summary"]["required_error_count"] != 0:
        raise ValueError("Step 6 review contains required lane errors")
    if review["gate_summary"]["v7_curriculum_error_count"] != 0:
        raise ValueError("Step 6 review contains v7 curriculum errors")
    return review


def _update_registry(
    rotated_at: str,
    sealed_hash: str,
    fixture: Any,
) -> dict[str, Any]:
    registry = _load_json(REGISTRY_PATH)
    fixtures = registry["fixtures"]
    if SEALED_V7_PATH.name in fixtures:
        raise ValueError("sealed v7 is already registered")

    v6 = fixtures[SEALED_V6_PATH.name]
    if v6["status"] != "consumed" or v6["measured"] is not True:
        raise ValueError("sealed v6 must be consumed before rotating sealed v7")

    active = [
        name
        for name, entry in fixtures.items()
        if entry.get("role") == "sealed measurement only"
        and entry.get("status") == "active"
    ]
    if active:
        raise ValueError(f"active sealed fixture already exists: {active[0]}")

    v6["successor"] = SEALED_V7_PATH.name
    fixtures[SEALED_V7_PATH.name] = {
        "sha256": sealed_hash,
        "case_count": len(fixture.cases),
        "role": "sealed measurement only",
        "predecessor": SEALED_V6_PATH.name,
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
    review: dict[str, Any],
    readiness: dict[str, Any],
) -> dict[str, Any]:
    report = {
        "schema_version": "v7-sealed-rotation-report.v1",
        "rotated_at": rotated_at,
        "policy": {
            "sealed_v7_opened_for_measurement": False,
            "sealed_v7_labels_used_for_tuning": False,
            "sealed_v6_text_used_for_training": False,
            "sealed_v6_labels_used_for_tuning": False,
            "sealed_v6_measurement_used_as_taxonomy_only": True,
            "nonsealed_replay_gate_required": True,
            "nonsealed_replay_gate_passed": True,
            "same_cycle_promotion_allowed": False,
        },
        "step6_review_source": _rel(STEP6_REVIEW_PATH),
        "step5_gate_source": _rel(STEP5_GATE_PATH),
        "rotated_from": {
            "registry_name": SEALED_V6_PATH.name,
            "status": "consumed",
            "measurement_report": _rel(V6_MEASUREMENT_PATH),
        },
        "rotated_to": {
            "registry_name": SEALED_V7_PATH.name,
            "fixture_id": fixture.fixture_id,
            "sha256": sealed_hash,
            "case_count": len(fixture.cases),
            "predecessor": SEALED_V6_PATH.name,
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
        "next_action": "roadmap_v7_step8_measure_active_sealed_v7_once",
    }
    _write_json(ROTATION_REPORT_PATH, report)
    return report


def _write_markdown(report: dict[str, Any]) -> None:
    rotated_to = report["rotated_to"]
    readiness = report["readiness_after_rotation"]
    lines = [
        "# V7 Sealed Rotation Report v1",
        "",
        f"- fixture: `{rotated_to['registry_name']}`",
        f"- status: `{rotated_to['status']}`",
        f"- measured: `{rotated_to['measured']}`",
        f"- reviewed: `{rotated_to['reviewed']}`",
        f"- case_count: `{rotated_to['case_count']}`",
        f"- predecessor: `{rotated_to['predecessor']}`",
        f"- sha256: `{rotated_to['sha256']}`",
        f"- sealed_v7_opened_for_measurement: `{report['policy']['sealed_v7_opened_for_measurement']}`",
        f"- sealed_v7_labels_used_for_tuning: `{report['policy']['sealed_v7_labels_used_for_tuning']}`",
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
        "Step 8 may measure the active sealed v7 fixture once. After that measurement, the fixture must be marked consumed before any tuning based on the result.",
    ]
    ROTATION_REPORT_MD_PATH.write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def _replace_section(text: str, heading: str, section: str) -> str:
    if heading not in text:
        return text.rstrip() + "\n\n" + section + "\n"
    head, rest = text.split(heading, 1)
    marker = "\n## "
    idx = rest.find(marker)
    if idx == -1:
        return head.rstrip() + "\n\n" + section + "\n"
    tail = rest[idx + 1 :]
    return head.rstrip() + "\n\n" + section + "\n\n" + tail


def _update_targets(report: dict[str, Any]) -> None:
    targets = _load_json(TARGETS_PATH)
    targets["generated_at"] = report["rotated_at"]
    targets["status"] = "step7_sealed_rotation_completed_step8_measurement_next"
    targets["next_action"] = "roadmap_v7_step8_measure_active_sealed_v7_once"
    for item in targets["roadmap"]:
        if item["step"] == 7:
            item["status"] = "completed"
        elif item["step"] == 8:
            item["status"] = "next"
    targets["step7_sealed_rotation"] = {
        "output": "build\\v7_sealed_rotation_report_v1.json",
        "fixture": "tests\\fixtures\\pattern_language_sealed_v7.json",
        "passed": True,
        "sealed_v7_opened_for_measurement": False,
        "sealed_v7_labels_used_for_tuning": False,
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
        "| 7 | sealed_v7_rotation | `tests\\fixtures\\pattern_language_sealed_v7.json` | next |",
        "| 7 | sealed_v7_rotation | `tests\\fixtures\\pattern_language_sealed_v7.json` | completed |",
    )
    roadmap = roadmap.replace(
        "| 8 | sealed_v7_one_time_measurement | `build\\pattern_language_sealed_v7_measurement_report.json` | pending |",
        "| 8 | sealed_v7_one_time_measurement | `build\\pattern_language_sealed_v7_measurement_report.json` | next |",
    )
    section = f"""## Step 7 Output

`build\\v7_sealed_rotation_report_v1.json` created `tests\\fixtures\\pattern_language_sealed_v7.json` as the active unopened sealed fixture. It has {report['rotated_to']['case_count']} cases, predecessor `pattern_language_sealed_v6.json`, measured `False`, reviewed `False`, and sha256 `{report['rotated_to']['sha256']}`. Step 8 is the one-time sealed v7 measurement."""
    roadmap = _replace_section(roadmap, "## Step 7 Output", section)
    ROADMAP_PATH.write_text(roadmap, encoding="utf-8", newline="\n")

    marker = "## PLM V7: Constraint And Critical Signal Recovery"
    main = MAIN_ROADMAP_PATH.read_text(encoding="utf-8")
    section = f"""
{marker}

Status: V7 Step 7 sealed v7 rotation completed; sealed v7 active/unmeasured; Step 8 one-time sealed v7 measurement next.

Primary roadmap: `docs/PLM_V7_ROADMAP.md`
Targets and taxonomy: `build/v7_targets_and_roadmap_v1.json`
Curriculum plan: `build/v7_nonsealed_curriculum_plan_v1.json`
Draft repair fixture: `tests/fixtures/v7_router_repair_fixture_v1.json`
Candidate replay report: `build/v7_router_repair_fixture_replay_v1.json`
Router generalization report: `build/v7_router_generalization_report_v1.json`
Non-sealed replay gate report: `build/v7_nonsealed_replay_gate_report_v1.json`
Sealed v7 rotation review: `build/v7_sealed_rotation_review_v1.json`
Sealed v7 rotation report: `build/v7_sealed_rotation_report_v1.json`
Sealed v7 fixture: `tests/fixtures/pattern_language_sealed_v7.json`

The V7 Step 4 router repair replays the 72-case non-sealed draft fixture diagnostically at intent_accuracy 1.000000, critical_signal_recall 1.000000, operation_exact_match 1.000000, constraint_exact_match 1.000000, risk_exact_match 1.000000, with errors 0. Step 5 non-sealed replay gate passed, Step 6 sealed rotation review authorized fresh sealed v7 rotation, and Step 7 rotated a fresh unopened `pattern_language_sealed_v7.json` into the active measurement slot. Sealed v7 is not measured or reviewed yet; Step 8 is the one-time adjudicating measurement.
""".strip()
    if marker in main:
        head, rest = main.split(marker, 1)
        next_marker = "\n## "
        idx = rest.find(next_marker)
        if idx == -1:
            main = head.rstrip() + "\n\n" + section + "\n"
        else:
            tail = rest[idx + 1 :]
            main = head.rstrip() + "\n\n" + section + "\n\n" + tail
    else:
        main = main.rstrip() + "\n\n" + section + "\n"
    MAIN_ROADMAP_PATH.write_text(main, encoding="utf-8", newline="\n")



def _preserve_step8_state() -> None:
    targets = _load_json(TARGETS_PATH)
    roadmap = ROADMAP_PATH.read_text(encoding="utf-8")
    main = MAIN_ROADMAP_PATH.read_text(encoding="utf-8")
    targets, roadmap, main = preserve_step8_measurement_state(ROOT, targets, roadmap, main)
    _write_json(TARGETS_PATH, targets)
    ROADMAP_PATH.write_text(roadmap, encoding="utf-8", newline="\n")
    MAIN_ROADMAP_PATH.write_text(main, encoding="utf-8", newline="\n")


def main() -> None:
    rotated_at = datetime.now(timezone.utc).isoformat()
    review = _validate_step6_review()
    fixture = _write_fixture()
    sealed_hash = _sha256(SEALED_V7_PATH)
    _update_registry(rotated_at, sealed_hash, fixture)
    readiness = _refresh_readiness_review()
    report = _write_rotation_report(
        rotated_at,
        sealed_hash,
        fixture,
        review,
        readiness,
    )
    _write_markdown(report)
    _update_targets(report)
    _update_roadmaps(report)
    _preserve_step8_state()
    print(
        json.dumps(
            {
                "status": "rotated",
                "fixture": SEALED_V7_PATH.name,
                "case_count": len(fixture.cases),
                "sha256": sealed_hash,
                "measured": False,
                "reviewed": False,
                "readiness": readiness["decision"],
                "next_action": report["next_action"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
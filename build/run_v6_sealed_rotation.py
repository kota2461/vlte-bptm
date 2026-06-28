"""Rotate an unopened PLM sealed v6 fixture into the active registry slot."""

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


GENERATOR_PATH = ROOT / "build" / "generate_plm_sealed_v6.py"
REGISTRY_PATH = ROOT / "tests" / "fixtures" / "pattern_language_fixture_registry.json"
SEALED_V5_PATH = ROOT / "tests" / "fixtures" / "pattern_language_sealed_v5.json"
SEALED_V6_PATH = ROOT / "tests" / "fixtures" / "pattern_language_sealed_v6.json"
V5_MEASUREMENT_PATH = ROOT / "build" / "pattern_language_sealed_v5_measurement_report.json"
STEP4_REVIEW_PATH = ROOT / "build" / "v6_sealed_rotation_review_v1.json"
STEP3_GATE_PATH = ROOT / "build" / "v6_nonsealed_replay_gate_report_v1.json"
ROTATION_REPORT_PATH = ROOT / "build" / "v6_sealed_rotation_report_v1.json"
ROTATION_REPORT_MD_PATH = ROOT / "build" / "v6_sealed_rotation_report_v1.md"
ROADMAP_PATH = ROOT / "docs" / "PLM_V6_ROADMAP.md"
MAIN_ROADMAP_PATH = ROOT / "docs" / "PATTERN_LANGUAGE_MODEL_roadmap.md"
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
        "generate_plm_sealed_v6",
        GENERATOR_PATH,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("failed to load sealed v6 generator")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _write_fixture() -> Any:
    generator = _load_generator()
    payload = generator.build_payload()
    generator.validate_no_overlap(payload)
    SEALED_V6_PATH.write_text(
        json.dumps(payload, ensure_ascii=False, indent=1) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return parse_plm_sealed_fixture(payload)


def _validate_step4_review() -> dict[str, Any]:
    review = _load_json(STEP4_REVIEW_PATH)
    if review["schema_version"] != "v6-sealed-rotation-review.v1":
        raise ValueError("unexpected Step 4 review schema")
    if review["decision"] != "eligible_for_fresh_sealed_v6_rotation":
        raise ValueError("Step 4 did not authorize sealed v6 rotation")
    if review["passed"] is not True:
        raise ValueError("Step 4 sealed rotation review must pass")
    if review["policy"]["sealed_v6_fixture_created_now"] is not False:
        raise ValueError("Step 4 review must be pre-rotation")
    if review["gate_summary"]["required_error_count"] != 0:
        raise ValueError("Step 4 review contains required lane errors")
    return review


def _update_registry(
    rotated_at: str,
    sealed_hash: str,
    fixture: Any,
) -> dict[str, Any]:
    registry = _load_json(REGISTRY_PATH)
    fixtures = registry["fixtures"]
    if SEALED_V6_PATH.name in fixtures:
        raise ValueError("sealed v6 is already registered")

    v5 = fixtures[SEALED_V5_PATH.name]
    if v5["status"] != "consumed" or v5["measured"] is not True:
        raise ValueError("sealed v5 must be consumed before rotating sealed v6")

    active = [
        name
        for name, entry in fixtures.items()
        if entry.get("role") == "sealed measurement only"
        and entry.get("status") == "active"
    ]
    if active:
        raise ValueError(f"active sealed fixture already exists: {active[0]}")

    v5["successor"] = SEALED_V6_PATH.name
    fixtures[SEALED_V6_PATH.name] = {
        "sha256": sealed_hash,
        "case_count": len(fixture.cases),
        "role": "sealed measurement only",
        "predecessor": SEALED_V5_PATH.name,
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
        "schema_version": "v6-sealed-rotation-report.v1",
        "rotated_at": rotated_at,
        "policy": {
            "sealed_v6_opened_for_measurement": False,
            "sealed_v6_labels_used_for_tuning": False,
            "sealed_v5_text_used_for_training": False,
            "sealed_v5_labels_used_for_tuning": False,
            "sealed_v5_measurement_used_as_taxonomy_only": True,
            "nonsealed_replay_gate_required": True,
            "nonsealed_replay_gate_passed": True,
            "same_cycle_promotion_allowed": False,
        },
        "step4_review_source": _rel(STEP4_REVIEW_PATH),
        "step3_gate_source": _rel(STEP3_GATE_PATH),
        "rotated_from": {
            "registry_name": SEALED_V5_PATH.name,
            "status": "consumed",
            "measurement_report": _rel(V5_MEASUREMENT_PATH),
        },
        "rotated_to": {
            "registry_name": SEALED_V6_PATH.name,
            "fixture_id": fixture.fixture_id,
            "sha256": sealed_hash,
            "case_count": len(fixture.cases),
            "predecessor": SEALED_V5_PATH.name,
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
        "next_action": "roadmap_step6_measure_active_sealed_v6_once",
    }
    _write_json(ROTATION_REPORT_PATH, report)
    return report


def _write_markdown(report: dict[str, Any]) -> None:
    rotated_to = report["rotated_to"]
    readiness = report["readiness_after_rotation"]
    lines = [
        "# V6 Sealed Rotation Report v1",
        "",
        f"- fixture: `{rotated_to['registry_name']}`",
        f"- status: `{rotated_to['status']}`",
        f"- measured: `{rotated_to['measured']}`",
        f"- reviewed: `{rotated_to['reviewed']}`",
        f"- case_count: `{rotated_to['case_count']}`",
        f"- predecessor: `{rotated_to['predecessor']}`",
        f"- sha256: `{rotated_to['sha256']}`",
        f"- sealed_v6_opened_for_measurement: `{report['policy']['sealed_v6_opened_for_measurement']}`",
        f"- sealed_v6_labels_used_for_tuning: `{report['policy']['sealed_v6_labels_used_for_tuning']}`",
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
        "Step 6 may measure the active sealed v6 fixture once. After that measurement, the fixture must be marked consumed before any tuning based on the result.",
    ]
    ROTATION_REPORT_MD_PATH.write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def _update_roadmaps(report: dict[str, Any]) -> None:
    roadmap = ROADMAP_PATH.read_text(encoding="utf-8")
    roadmap = roadmap.replace(
        "| 5 | sealed_v6_rotation | `tests\\fixtures\\pattern_language_sealed_v6.json` | next |",
        "| 5 | sealed_v6_rotation | `tests\\fixtures\\pattern_language_sealed_v6.json` | completed |",
    )
    roadmap = roadmap.replace(
        "| 6 | sealed_v6_one_time_measurement | `build\\pattern_language_sealed_v6_measurement_report.json` | pending |",
        "| 6 | sealed_v6_one_time_measurement | `build\\pattern_language_sealed_v6_measurement_report.json` | next |",
    )
    section = f"""
## Step 5 Output

`build\\v6_sealed_rotation_report_v1.json` created `tests\\fixtures\\pattern_language_sealed_v6.json` as the active unopened sealed fixture. It has {report['rotated_to']['case_count']} cases, predecessor `pattern_language_sealed_v5.json`, measured `False`, reviewed `False`, and sha256 `{report['rotated_to']['sha256']}`. Step 6 is the one-time sealed v6 measurement.
""".strip()
    if "## Step 5 Output" in roadmap:
        head, rest = roadmap.split("## Step 5 Output", 1)
        if "## Step 5 Fixture Constraints" in rest:
            _, tail = rest.split("## Step 5 Fixture Constraints", 1)
            roadmap = head.rstrip() + "\n\n" + section + "\n\n## Step 5 Fixture Constraints" + tail
        else:
            roadmap = head.rstrip() + "\n\n" + section + "\n"
    else:
        roadmap = roadmap.rstrip() + "\n\n" + section + "\n"
    ROADMAP_PATH.write_text(roadmap, encoding="utf-8", newline="\n")

    marker = "## PLM V6: Boundary Calibration And Sealed Rotation"
    main = MAIN_ROADMAP_PATH.read_text(encoding="utf-8")
    section = f"""
{marker}

Status: V6 Step 5 sealed v6 rotation completed; sealed v6 active/unmeasured; Step 6 one-time sealed v6 measurement next.

Primary roadmap: `docs/PLM_V6_ROADMAP.md`
Current state report: `build/v6_current_state_report_v1.json`
Non-sealed replay gate report: `build/v6_nonsealed_replay_gate_report_v1.json`
Sealed v6 rotation review: `build/v6_sealed_rotation_review_v1.json`
Sealed v6 rotation report: `build/v6_sealed_rotation_report_v1.json`
Sealed v6 fixture: `tests/fixtures/pattern_language_sealed_v6.json`

V6 non-sealed required lanes are exact and the replay gate passed with zero required errors. Step 5 rotated a fresh unopened `pattern_language_sealed_v6.json` into the active measurement slot. Sealed v6 is not measured or reviewed yet; Step 6 is the one-time adjudicating measurement.
""".strip()
    if marker in main:
        head, _ = main.split(marker, 1)
        main = head.rstrip() + "\n\n" + section + "\n"
    else:
        main = main.rstrip() + "\n\n" + section + "\n"
    MAIN_ROADMAP_PATH.write_text(main, encoding="utf-8", newline="\n")


def main() -> None:
    rotated_at = reproducible_now_iso()
    review = _validate_step4_review()
    fixture = _write_fixture()
    sealed_hash = _sha256(SEALED_V6_PATH)
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
    _update_roadmaps(report)
    print(
        json.dumps(
            {
                "status": "rotated",
                "fixture": SEALED_V6_PATH.name,
                "case_count": len(fixture.cases),
                "sha256": sealed_hash,
                "measured": False,
                "reviewed": False,
                "readiness": readiness["decision"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()

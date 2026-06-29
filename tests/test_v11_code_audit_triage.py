import json
import subprocess
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).parents[1]
SCRIPT_PATH = ROOT / "build" / "create_v11_code_audit_triage.py"
REPORT_PATH = ROOT / "build" / "v11_code_audit_triage_v1.json"
REPORT_MD_PATH = ROOT / "build" / "v11_code_audit_triage_v1.md"


@pytest.fixture(scope="module", autouse=True)
def _regenerate_report():
    """Regenerate the build/ artifact before the read-asserts so these tests do
    not depend on stale on-disk state left by a prior test or manual run."""
    subprocess.run(
        [sys.executable, "-B", str(SCRIPT_PATH)],
        cwd=ROOT,
        check=True,
        text=True,
        capture_output=True,
    )


def _load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_v11_code_audit_triage_records_completed_baseline_source_recovery() -> None:
    report = _load(REPORT_PATH)

    assert report["schema_version"] == "v11-code-audit-triage.v1"
    assert report["status"] == "step1b_baseline_source_recovery_completed"
    assert report["policy"] == {
        "diagnostic_only": True,
        "mutates_router": False,
        "writes_training_data": False,
        "opens_active_sealed_fixture": False,
        "uses_sealed_labels_for_tuning": False,
    }
    baseline = report["findings"]["baseline_pyc_loader"]
    assert baseline["priority"] == "P0"
    assert baseline["confirmed"] is False
    assert baseline["blocks_step2"] is False
    assert baseline["recovery_status"] == "completed"
    assert baseline["file"] == "semantic_routing/baseline.py"
    assert baseline["chosen_pyc"]["path"] == "build/recovery_assets/baseline_legacy_cpython310.pyc"
    assert baseline["chosen_pyc"]["size"] > 50000
    assert report["step2_blockers"] == []


def test_v11_code_audit_triage_records_hook_and_coverage_findings() -> None:
    report = _load(REPORT_PATH)

    literal = report["findings"]["literal_profile_patch_overfit"]
    assert literal["priority"] == "P0"
    assert literal["confirmed"] is True
    assert literal["blocks_step2"] is False
    assert literal["evidence"]["root_cause_for_v10_transfer_gap"] is True
    assert literal["evidence"]["total_fixture_like_regex_literal_count"] >= 100

    hook = report["findings"]["hook_keyword_overfire_without_context"]
    assert hook["priority"] == "P0"
    assert hook["confirmed"] is True
    assert hook["blocks_step2"] is False
    assert hook["file"] == "semantic_routing/knowledge_index.py"

    constraint = report["findings"]["constraint_omission_fast_path"]
    assert constraint["priority"] == "P1"
    assert constraint["status"] == "trace_ready_after_source_recovery"
    assert constraint["blocked_by"] is None

    coverage = report["findings"]["fixture_coverage_gap"]
    assert coverage["priority"] == "P2"
    assert coverage["minimum_relevant_unscanned_cases"] == 132
    assert [item["case_count"] for item in coverage["case_sets"]] == [72, 48, 12]


def test_v11_code_audit_triage_script_regenerates_markdown() -> None:
    completed = subprocess.run(
        [sys.executable, "-B", str(SCRIPT_PATH)],
        cwd=ROOT,
        check=True,
        text=True,
        capture_output=True,
    )
    assert "step1b_baseline_source_recovery_completed" in completed.stdout
    assert "roadmap_v11_step2_create_repair_curriculum_plan" in completed.stdout

    report = _load(REPORT_PATH)
    markdown = REPORT_MD_PATH.read_text(encoding="utf-8")
    assert report["roadmap_override"] == {
        "previous_next_action": "roadmap_v11_step1b_recover_baseline_source",
        "next_action": "roadmap_v11_step2_create_repair_curriculum_plan",
        "advance_to": "v11_repair_curriculum_plan",
        "blocks_repair_curriculum_plan": False,
    }
    assert "# V11 Code Audit Triage v1" in markdown
    assert "baseline_pyc_loader" in markdown
    assert "hook_keyword_overfire_without_context" in markdown
    assert "literal_profile_patch_overfit" in markdown
    assert "v11_p0_literal_profile_generalization_guard" in markdown
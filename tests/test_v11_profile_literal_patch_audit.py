import json
import subprocess
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).parents[1]
SCRIPT_PATH = ROOT / "build" / "create_v11_profile_literal_patch_audit.py"
REPORT_PATH = ROOT / "build" / "v11_profile_literal_patch_audit_v1.json"
REPORT_MD_PATH = ROOT / "build" / "v11_profile_literal_patch_audit_v1.md"


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


def test_v11_profile_literal_patch_audit_records_root_cause() -> None:
    report = _load(REPORT_PATH)
    finding = report["finding"]

    assert report["schema_version"] == "v11-profile-literal-patch-audit.v1"
    assert report["status"] == "literal_profile_patch_overfit_confirmed"
    assert report["policy"] == {
        "diagnostic_only": True,
        "mutates_router": False,
        "writes_training_data": False,
        "opens_active_sealed_fixture": False,
        "uses_sealed_labels_for_tuning": False,
    }
    assert finding["id"] == "literal_profile_patch_overfit"
    assert finding["root_cause_for_v10_transfer_gap"] is True
    assert finding["total_regex_literal_count_in_profile_inspection"] >= 200
    assert finding["total_fixture_like_regex_literal_count"] >= 100


def test_v11_profile_literal_patch_audit_records_v9_literal_profiles() -> None:
    report = _load(REPORT_PATH)
    profiles = report["finding"]["evidence"]["profiles"]

    primary = profiles["_v9_primary_review_profile"]
    assert primary["docstring"] == "User-approved V9 primary-review 34-row non-sealed repair signals."
    assert primary["uses_direct_re_search"] is True
    assert primary["uses_v9_override"] is True
    assert primary["fixture_like_regex_literal_count"] == 34
    assert "\\bcurrent AI regulation status\\b" in primary["example_regex_literals"]

    extension = profiles["_v9_constraint_operation_extension_profile"]
    assert extension["docstring"] == "User-approved V9 extension focused on constraint/operation exactness."
    assert extension["fixture_like_regex_literal_count"] == 24
    assert extension["uses_v9_override"] is True


def test_v11_profile_literal_patch_audit_records_partial_decompile_limits_and_script() -> None:
    completed = subprocess.run(
        [sys.executable, "-B", str(SCRIPT_PATH)],
        cwd=ROOT,
        check=True,
        text=True,
        capture_output=True,
    )
    assert "literal_profile_patch_overfit_confirmed" in completed.stdout

    report = _load(REPORT_PATH)
    markdown = REPORT_MD_PATH.read_text(encoding="utf-8")
    assert report["decompilation"] == {
        "status": "partial_only",
        "automatic_decompilation_failed_functions": 3,
        "automatic_decompilation_attempted_functions": 6,
        "known_failure_reason": "dictionary/set comprehension opcodes were not handled by the external decompiler scan",
        "policy": "do not treat partial decompile as authoritative source; use source recovery plus regression oracle",
    }
    assert "do_not_add_one_regex_per_failed_fixture_sentence" in markdown
    assert "naturalized_paraphrase_holdout" in markdown
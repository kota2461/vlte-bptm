import json
import subprocess
import pytest
import sys
from pathlib import Path


ROOT = Path(__file__).parents[1]
SCRIPT_PATH = ROOT / "build" / "inspect_plm_sample_blocks.py"
REPORT_PATH = ROOT / "build" / "plm_sample_block_negative_scan_v1.json"
REPORT_MD_PATH = ROOT / "build" / "plm_sample_block_negative_scan_v1.md"


def _load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.fixture(scope="module", autouse=True)
def _regenerate_artifact():
    """Regenerate the build/ artifact before the read-asserts so these tests do
    not depend on stale on-disk state left by a prior test or manual run (S4)."""
    subprocess.run(
        [sys.executable, "-B", str(SCRIPT_PATH)],
        cwd=ROOT,
        check=True,
        text=True,
        capture_output=True,
    )


def test_plm_sample_block_negative_scan_records_policy_and_summary() -> None:
    report = _load(REPORT_PATH)

    assert report["schema_version"] == "plm-sample-block-negative-scan.v1"
    assert report["status"] == "diagnostic_completed_no_mutation"
    assert report["policy"] == {
        "diagnostic_only": True,
        "writes_training_data": False,
        "mutates_router": False,
        "sealed_fixtures_opened": False,
        "active_sealed_opened": False,
        "automatic_quarantine": False,
    }
    assert report["summary"] == {
        "fixtures_scanned": 12,
        "cases_scanned": 330,
        "skipped_files": 34,
        "strong_negative_blocks": 0,
        "focused_repair_blocks": 0,
        "transfer_risk_blocks": 15,
    }
    assert all("pattern_language_sealed_" not in block["key"] for block in report["ranked_blocks"])


def test_plm_sample_block_negative_scan_flags_transfer_risk_not_prune() -> None:
    report = _load(REPORT_PATH)
    transfer_blocks = [
        block for block in report["ranked_blocks"]
        if block["severity"] == "transfer_risk_candidate"
    ]

    assert transfer_blocks
    bridge_fixture = next(
        block for block in transfer_blocks
        if block["kind"] == "fixture"
        and block["key"] == "tests/fixtures/v10_thought_color_bridge_isolated_benchmark_v1.json"
    )
    assert bridge_fixture["case_count"] == 72
    assert bridge_fixture["error_count"] == 0
    assert bridge_fixture["weighted_negative_score_avg"] == 0.0
    assert bridge_fixture["language_counts"] == {"en": 72}
    assert bridge_fixture["risk_flags"] == ["english_only_large_block"]
    assert report["recommended_next_action"] == "review strong_negative_candidate blocks, then audit constraint omission and hook overfire before quarantine"


def test_plm_sample_block_negative_scan_script_regenerates_markdown() -> None:
    completed = subprocess.run(
        [sys.executable, "-B", str(SCRIPT_PATH)],
        cwd=ROOT,
        check=True,
        text=True,
        capture_output=True,
    )
    assert "diagnostic_completed_no_mutation" in completed.stdout

    report = _load(REPORT_PATH)
    markdown = REPORT_MD_PATH.read_text(encoding="utf-8")
    assert report["summary"]["strong_negative_blocks"] == 0
    assert "# PLM Sample Block Negative Scan v1" in markdown
    assert "strong_negative_blocks: 0" in markdown
    assert "v10_thought_color_bridge_isolated_benchmark_v1.json" in markdown
    assert "Do not delete or quarantine automatically" in markdown
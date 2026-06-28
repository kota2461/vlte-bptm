import json
import re
from pathlib import Path

from semantic_routing.baseline import extract_semantic_packet
from semantic_routing.baseline_snapshot import LEGACY_PACKET_BY_DIGEST


ROOT = Path(__file__).parents[1]
BASELINE_PATH = ROOT / "semantic_routing" / "baseline.py"
SNAPSHOT_PATH = ROOT / "semantic_routing" / "baseline_snapshot.py"
REPORT_PATH = ROOT / "build" / "v11_baseline_source_recovery_report_v1.json"
COMPARISON_PATH = ROOT / "build" / "baseline_source_recovery_oracle_comparison_v1.json"


def _load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_v11_baseline_source_no_longer_loads_runtime_pyc() -> None:
    source = BASELINE_PATH.read_text(encoding="utf-8")

    assert "import marshal" not in source
    assert "marshal.loads" not in source
    assert "exec(_CODE" not in source
    assert "_BASELINE_PYC" not in source
    assert "glob(\"baseline.cpython" not in source


def test_v11_baseline_snapshot_is_digest_keyed_and_label_free() -> None:
    assert len(LEGACY_PACKET_BY_DIGEST) >= 960
    for digest, packet in list(LEGACY_PACKET_BY_DIGEST.items())[:10]:
        assert re.fullmatch(r"[0-9a-f]{64}", digest)
        assert "request_digest" not in packet
        assert "input" not in packet
        assert "expected" not in packet
        assert packet["schema_version"] == "semantic-packet.v1"

    snapshot_source = SNAPSHOT_PATH.read_text(encoding="utf-8")
    assert "LEGACY_PACKET_BY_DIGEST" in snapshot_source
    assert "expected labels" in snapshot_source


def test_v11_baseline_source_recovery_report_and_oracle_match() -> None:
    report = _load(REPORT_PATH)
    comparison = _load(COMPARISON_PATH)

    assert report["schema_version"] == "v11-baseline-source-recovery-report.v1"
    assert report["status"] == "baseline_source_recovered_from_pyc_snapshot_extended"
    assert report["policy"] == {
        "training_data": False,
        "expected_labels_used": False,
        "raw_inputs_embedded_in_runtime_snapshot": False,
        "pyc_runtime_dependency_removed": True,
    }
    assert report["snapshot_count"] == len(LEGACY_PACKET_BY_DIGEST)
    assert report["extension"]["pyc_used_at_build_time_only"] is True
    assert report["extension"]["added_snapshot_count"] > 0
    assert comparison["status"] == "matched"
    assert comparison["mismatch_count"] == 0


def test_v11_recovered_fallback_still_routes_new_inputs() -> None:
    packet = extract_semantic_packet(
        "Before writing the migration command, ask me which database engine is running."
    )

    assert packet.primary_intent == "clarify"
    assert "ask_first" in packet.constraints.must
    assert packet.information_state.missing_required_information is True
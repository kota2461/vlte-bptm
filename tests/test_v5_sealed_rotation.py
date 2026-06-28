import hashlib
import json
from collections import Counter
from pathlib import Path

from semantic_routing import parse_plm_sealed_fixture


ROOT = Path(__file__).parents[1]
FIXTURES = ROOT / "tests" / "fixtures"
SEALED_V5_PATH = FIXTURES / "pattern_language_sealed_v5.json"
REGISTRY_PATH = FIXTURES / "pattern_language_fixture_registry.json"
ROTATION_REPORT_PATH = ROOT / "build" / "v5_sealed_rotation_report.json"
STEP5_GATE_PATH = ROOT / "build" / "v5_nonsealed_replay_gate_report.json"
READINESS_PATH = ROOT / "build" / "plm_measurement_readiness_review.json"
MEASUREMENT_REPORT_PATH = ROOT / "build" / "pattern_language_sealed_v5_measurement_report.json"


def _load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _texts_from_json(path: Path) -> set[str]:
    payload = _load(path)
    texts = set()
    for collection_key in ("cases", "tasks", "items", "quarantined_cases"):
        for item in payload.get(collection_key, []):
            if "input" in item:
                texts.add(str(item["input"]))
    return texts


def test_v5_sealed_fixture_is_unopened_successor_contract() -> None:
    payload = _load(SEALED_V5_PATH)
    fixture = parse_plm_sealed_fixture(payload)

    assert payload["schema_version"] == "pattern-language-sealed.v1"
    assert fixture.fixture_id == "pattern-language-sealed-v5"
    assert fixture.predecessor == "pattern_language_sealed_v4.json"
    assert len(fixture.cases) == 28
    assert Counter(case.expected.primary_intent for case in fixture.cases) == {
        "respond": 4,
        "explain": 4,
        "clarify": 4,
        "build": 4,
        "verify": 4,
        "summarize": 4,
        "explore": 4,
    }
    assert {case.split for case in fixture.cases} == {"sealed"}
    assert len({case.input_text for case in fixture.cases}) == 28


def test_v5_sealed_fixture_has_no_exact_source_overlap() -> None:
    payload = _load(SEALED_V5_PATH)
    new_texts = {case["input"] for case in payload["cases"]}
    source_paths = [
        FIXTURES / "pattern_language_benchmark_v1.json",
        FIXTURES / "sealed_boundary_slice_v2.json",
        FIXTURES / "pattern_language_sealed_v2.json",
        FIXTURES / "pattern_language_sealed_v3.json",
        FIXTURES / "pattern_language_sealed_v4.json",
        FIXTURES / "v4_failure_memory_fixture_v1.json",
        FIXTURES / "v4_puzzle_task_seed_v1.json",
        FIXTURES / "v4_puzzle_failure_memory_v1.json",
        FIXTURES / "v5_critical_operations_fixture_v1.json",
        ROOT / "data" / "intent_training_corpus_quarantine_v1.json",
    ]

    for path in source_paths:
        assert new_texts.isdisjoint(_texts_from_json(path)), path


def test_v5_rotation_report_records_pre_measurement_activation() -> None:
    report = _load(ROTATION_REPORT_PATH)
    registry = _load(REGISTRY_PATH)
    sealed_hash = hashlib.sha256(SEALED_V5_PATH.read_bytes()).hexdigest()
    fixtures = registry["fixtures"]

    assert report["schema_version"] == "v5-sealed-rotation-report.v1"
    assert report["policy"] == {
        "sealed_v5_opened_for_measurement": False,
        "sealed_v5_labels_used_for_tuning": False,
        "sealed_v4_text_used_for_training": False,
        "sealed_v4_labels_used_for_tuning": False,
        "v4_measurement_used_as_taxonomy_only": True,
        "nonsealed_replay_gate_required": True,
        "nonsealed_replay_gate_passed": True,
        "same_cycle_promotion_allowed": False,
    }
    assert report["gate_source"] == "build\\v5_nonsealed_replay_gate_report.json"
    assert report["rotated_from"]["registry_name"] == "pattern_language_sealed_v4.json"
    assert report["rotated_from"]["status"] == "consumed"
    assert report["rotated_to"] == {
        "registry_name": SEALED_V5_PATH.name,
        "fixture_id": "pattern-language-sealed-v5",
        "sha256": sealed_hash,
        "case_count": 28,
        "predecessor": "pattern_language_sealed_v4.json",
        "status": "active",
        "measured": False,
        "reviewed": False,
    }

    active = [
        name
        for name, entry in fixtures.items()
        if entry.get("role") == "sealed measurement only"
        and entry.get("status") == "active"
    ]
    assert active == []
    assert fixtures["pattern_language_sealed_v4.json"]["successor"] == SEALED_V5_PATH.name
    assert fixtures[SEALED_V5_PATH.name]["sha256"] == sealed_hash
    assert fixtures[SEALED_V5_PATH.name]["status"] == "consumed"
    assert fixtures[SEALED_V5_PATH.name]["measured"] is True
    assert fixtures[SEALED_V5_PATH.name]["reviewed"] is False
    assert fixtures[SEALED_V5_PATH.name]["measurement_report"] == r"build\pattern_language_sealed_v5_measurement_report.json"
    assert fixtures[SEALED_V5_PATH.name]["successor"] == "pattern_language_sealed_v6.json"
    assert fixtures["pattern_language_sealed_v6.json"]["status"] == "consumed"
    assert fixtures["pattern_language_sealed_v6.json"]["measured"] is True
    assert fixtures["pattern_language_sealed_v6.json"]["reviewed"] is False
    assert fixtures["pattern_language_sealed_v6.json"]["measurement_report"] == r"build\pattern_language_sealed_v6_measurement_report.json"


def test_step7_measurement_consumes_v5_and_blocks_readiness_until_rotation() -> None:
    gate = _load(STEP5_GATE_PATH)
    readiness = _load(READINESS_PATH)
    measurement = _load(MEASUREMENT_REPORT_PATH)
    sealed_hash = hashlib.sha256(SEALED_V5_PATH.read_bytes()).hexdigest()

    assert gate["summary"]["ready_for_step6_sealed_v5_rotation"] is True
    assert measurement["schema_version"] == "plm-sealed-measurement-report.v1"
    assert measurement["sealed_fixture_opened"] is True
    assert measurement["sealed_labels_used_for_tuning"] is False
    assert measurement["fixture"]["registry_name"] == SEALED_V5_PATH.name
    assert measurement["fixture"]["sha256"] == sealed_hash
    assert measurement["fixture"]["status_before_measurement"] == "active"
    assert measurement["measurements"]["case_count"] == 28
    assert measurement["measurements"]["intent_accuracy"] == 0.75
    assert measurement["measurements"]["critical_signal_recall"] == 0.375
    assert measurement["measurements"]["operation_exact_match"] == 0.678571
    assert measurement["measurements"]["constraint_exact_match"] == 0.821429
    assert measurement["measurements"]["risk_exact_match"] == 0.892857
    assert len(measurement["measurements"]["errors"]) == 18
    assert measurement["registry_update"]["status_after_measurement"] == "consumed"
    assert measurement["registry_update"]["rotation_required_before_tuning"] is True

    assert readiness["decision"] == "blocked"
    assert readiness["sealed_fixture_opened"] is False
    assert readiness["sealed_fixture"] is None
    assert readiness["blocked_reasons"] == ["sealed_fixture_not_available"]




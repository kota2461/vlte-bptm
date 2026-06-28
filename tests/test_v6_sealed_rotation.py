import hashlib
import json
from collections import Counter
from pathlib import Path

from semantic_routing import parse_plm_sealed_fixture


ROOT = Path(__file__).parents[1]
FIXTURES = ROOT / "tests" / "fixtures"
SEALED_V6_PATH = FIXTURES / "pattern_language_sealed_v6.json"
REGISTRY_PATH = FIXTURES / "pattern_language_fixture_registry.json"
ROTATION_REVIEW_PATH = ROOT / "build" / "v6_sealed_rotation_review_v1.json"
ROTATION_REPORT_PATH = ROOT / "build" / "v6_sealed_rotation_report_v1.json"
ROTATION_REPORT_MD_PATH = ROOT / "build" / "v6_sealed_rotation_report_v1.md"
READINESS_PATH = ROOT / "build" / "plm_measurement_readiness_review.json"
ROADMAP_PATH = ROOT / "docs" / "PLM_V6_ROADMAP.md"


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


def test_v6_sealed_fixture_is_active_unopened_successor_contract() -> None:
    payload = _load(SEALED_V6_PATH)
    fixture = parse_plm_sealed_fixture(payload)

    assert payload["schema_version"] == "pattern-language-sealed.v1"
    assert fixture.fixture_id == "pattern-language-sealed-v6"
    assert fixture.predecessor == "pattern_language_sealed_v5.json"
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


def test_v6_sealed_fixture_has_no_exact_source_overlap() -> None:
    payload = _load(SEALED_V6_PATH)
    new_texts = {case["input"] for case in payload["cases"]}
    source_paths = [
        FIXTURES / "pattern_language_benchmark_v1.json",
        FIXTURES / "sealed_boundary_slice_v2.json",
        FIXTURES / "pattern_language_sealed_v2.json",
        FIXTURES / "pattern_language_sealed_v3.json",
        FIXTURES / "pattern_language_sealed_v4.json",
        FIXTURES / "pattern_language_sealed_v5.json",
        FIXTURES / "v4_failure_memory_fixture_v1.json",
        FIXTURES / "v4_puzzle_task_seed_v1.json",
        FIXTURES / "v4_puzzle_failure_memory_v1.json",
        FIXTURES / "v5_critical_operations_fixture_v1.json",
        FIXTURES / "v6_boundary_false_positive_adopted_benchmark_v1.json",
        FIXTURES / "v6_boundary_priority_review_adopted_benchmark_v1.json",
        FIXTURES / "v6_structural_build_30_adopted_benchmark_v1.json",
        FIXTURES / "v6_router_debate_adopted_benchmark_v1.json",
        FIXTURES / "v6_boundary_false_positive_candidate_benchmark_v1.json",
        FIXTURES / "v6_contrast_negative_benchmark_v1.json",
        FIXTURES / "v6_router_debate_candidate_benchmark_v1.json",
        ROOT / "data" / "intent_training_corpus_quarantine_v1.json",
    ]

    for path in source_paths:
        assert new_texts.isdisjoint(_texts_from_json(path)), path


def test_v6_rotation_report_records_pre_measurement_activation_and_registry_is_consumed() -> None:
    review = _load(ROTATION_REVIEW_PATH)
    report = _load(ROTATION_REPORT_PATH)
    registry = _load(REGISTRY_PATH)
    sealed_hash = hashlib.sha256(SEALED_V6_PATH.read_bytes()).hexdigest()
    fixtures = registry["fixtures"]

    assert review["decision"] == "eligible_for_fresh_sealed_v6_rotation"
    assert report["schema_version"] == "v6-sealed-rotation-report.v1"
    assert report["policy"] == {
        "sealed_v6_opened_for_measurement": False,
        "sealed_v6_labels_used_for_tuning": False,
        "sealed_v5_text_used_for_training": False,
        "sealed_v5_labels_used_for_tuning": False,
        "sealed_v5_measurement_used_as_taxonomy_only": True,
        "nonsealed_replay_gate_required": True,
        "nonsealed_replay_gate_passed": True,
        "same_cycle_promotion_allowed": False,
    }
    assert report["rotated_from"]["registry_name"] == "pattern_language_sealed_v5.json"
    assert report["rotated_from"]["status"] == "consumed"
    assert report["rotated_to"] == {
        "registry_name": SEALED_V6_PATH.name,
        "fixture_id": "pattern-language-sealed-v6",
        "sha256": sealed_hash,
        "case_count": 28,
        "predecessor": "pattern_language_sealed_v5.json",
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
    assert fixtures["pattern_language_sealed_v5.json"]["successor"] == SEALED_V6_PATH.name
    assert fixtures[SEALED_V6_PATH.name]["sha256"] == sealed_hash
    assert fixtures[SEALED_V6_PATH.name]["status"] == "consumed"
    assert fixtures[SEALED_V6_PATH.name]["measured"] is True
    assert fixtures[SEALED_V6_PATH.name]["reviewed"] is False
    assert fixtures[SEALED_V6_PATH.name]["measurement_report"] == r"build\pattern_language_sealed_v6_measurement_report.json"


def test_v6_measurement_consumes_readiness_and_docs() -> None:
    readiness = _load(READINESS_PATH)
    report_text = ROTATION_REPORT_MD_PATH.read_text(encoding="utf-8")
    roadmap = ROADMAP_PATH.read_text(encoding="utf-8")

    assert readiness["decision"] == "blocked"
    assert readiness["sealed_fixture_opened"] is False
    assert readiness["sealed_fixture"] is None
    assert readiness["blocked_reasons"] == ["sealed_fixture_not_available"]
    assert "V6 Sealed Rotation Report v1" in report_text
    assert "| 5 | sealed_v6_rotation | `tests\\fixtures\\pattern_language_sealed_v6.json` | completed |" in roadmap
    assert "| 6 | sealed_v6_one_time_measurement | `build\\pattern_language_sealed_v6_measurement_report.json` | completed |" in roadmap

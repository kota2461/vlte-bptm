import hashlib
import importlib.util
import json
from collections import Counter
from pathlib import Path

from semantic_routing import parse_plm_sealed_fixture


ROOT = Path(__file__).parents[1]
FIXTURES = ROOT / "tests" / "fixtures"
SEALED_V10_PATH = FIXTURES / "pattern_language_sealed_v10.json"
REGISTRY_PATH = FIXTURES / "pattern_language_fixture_registry.json"
ROTATION_REVIEW_PATH = ROOT / "build" / "v10_sealed_rotation_review_v1.json"
ROTATION_REPORT_PATH = ROOT / "build" / "v10_sealed_rotation_report_v1.json"
ROTATION_REPORT_MD_PATH = ROOT / "build" / "v10_sealed_rotation_report_v1.md"
READINESS_PATH = ROOT / "build" / "plm_measurement_readiness_review.json"
ROADMAP_PATH = ROOT / "docs" / "PLM_V10_ROADMAP.md"
TARGETS_PATH = ROOT / "build" / "v10_targets_and_roadmap_v1.json"
GENERATOR_PATH = ROOT / "build" / "generate_plm_sealed_v10.py"


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


def test_v10_sealed_fixture_successor_contract() -> None:
    payload = _load(SEALED_V10_PATH)
    fixture = parse_plm_sealed_fixture(payload)

    assert payload["schema_version"] == "pattern-language-sealed.v1"
    assert fixture.fixture_id == "pattern-language-sealed-v10"
    assert fixture.predecessor == "pattern_language_sealed_v9.json"
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


def test_v10_sealed_fixture_has_no_exact_source_overlap() -> None:
    payload = _load(SEALED_V10_PATH)
    new_texts = {case["input"] for case in payload["cases"]}
    source_paths = [
        FIXTURES / "pattern_language_benchmark_v1.json",
        FIXTURES / "sealed_boundary_slice_v2.json",
        FIXTURES / "pattern_language_sealed_v2.json",
        FIXTURES / "pattern_language_sealed_v3.json",
        FIXTURES / "pattern_language_sealed_v4.json",
        FIXTURES / "pattern_language_sealed_v5.json",
        FIXTURES / "pattern_language_sealed_v6.json",
        FIXTURES / "pattern_language_sealed_v7.json",
        FIXTURES / "pattern_language_sealed_v8.json",
        FIXTURES / "pattern_language_sealed_v9.json",
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
        FIXTURES / "v7_router_repair_fixture_v1.json",
        FIXTURES / "v7_router_debate_candidate_fixture_v1.json",
        FIXTURES / "v8_recovery_priority_review_candidate_benchmark_v1.json",
        FIXTURES / "v9_accumulated_primary_review_candidate_benchmark_v1.json",
        FIXTURES / "v9_constraint_operation_extension_benchmark_v1.json",
        FIXTURES / "v10_thought_color_bridge_isolated_benchmark_v1.json",
        ROOT / "data" / "intent_training_corpus_quarantine_v1.json",
    ]

    for path in source_paths:
        assert new_texts.isdisjoint(_texts_from_json(path)), path


def test_v10_generator_builds_parseable_nonoverlapping_payload_without_measuring() -> None:
    spec = importlib.util.spec_from_file_location("generate_plm_sealed_v10", GENERATOR_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    payload = module.build_payload()
    module.validate_no_overlap(payload)
    fixture = parse_plm_sealed_fixture(payload)

    assert fixture.fixture_id == "pattern-language-sealed-v10"
    assert len(fixture.cases) == 28


def test_v10_rotation_report_records_pre_measurement_activation_and_registry() -> None:
    review = _load(ROTATION_REVIEW_PATH)
    report = _load(ROTATION_REPORT_PATH)
    registry = _load(REGISTRY_PATH)
    sealed_hash = hashlib.sha256(SEALED_V10_PATH.read_bytes()).hexdigest()
    fixtures = registry["fixtures"]

    assert review["decision"] == "eligible_for_fresh_sealed_v10_rotation"
    assert report["schema_version"] == "v10-sealed-rotation-report.v1"
    assert report["policy"] == {
        "sealed_v10_opened_for_measurement": False,
        "sealed_v10_labels_used_for_tuning": False,
        "sealed_v9_text_used_for_training": False,
        "sealed_v9_labels_used_for_tuning": False,
        "sealed_v9_measurement_used_as_taxonomy_only": True,
        "nonsealed_replay_gate_required": True,
        "nonsealed_replay_gate_passed": True,
        "same_cycle_promotion_allowed": False,
    }
    assert report["rotated_from"]["registry_name"] == "pattern_language_sealed_v9.json"
    assert report["rotated_from"]["status"] == "consumed"
    assert report["rotated_to"] == {
        "registry_name": SEALED_V10_PATH.name,
        "fixture_id": "pattern-language-sealed-v10",
        "sha256": sealed_hash,
        "case_count": 28,
        "predecessor": "pattern_language_sealed_v9.json",
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
    assert fixtures["pattern_language_sealed_v9.json"]["successor"] == SEALED_V10_PATH.name
    assert fixtures[SEALED_V10_PATH.name]["sha256"] == sealed_hash
    assert fixtures[SEALED_V10_PATH.name]["status"] == "consumed"
    assert fixtures[SEALED_V10_PATH.name]["measured"] is True
    assert fixtures[SEALED_V10_PATH.name]["reviewed"] is False
    assert fixtures[SEALED_V10_PATH.name]["measurement_report"] == r"build\pattern_language_sealed_v10_measurement_report.json"


def test_v10_rotation_docs_and_readiness_are_step6_ready() -> None:
    readiness = _load(READINESS_PATH)
    report = _load(ROTATION_REPORT_PATH)
    report_text = ROTATION_REPORT_MD_PATH.read_text(encoding="utf-8")
    roadmap = ROADMAP_PATH.read_text(encoding="utf-8")
    targets = _load(TARGETS_PATH)

    assert readiness["decision"] == "blocked"
    assert readiness["sealed_fixture_opened"] is False
    assert readiness["sealed_fixture"] is None
    assert readiness["blocked_reasons"] == ["sealed_fixture_not_available"]
    assert readiness["next_action"] == "continue_accumulation_or_rotate_fixture"
    assert report["readiness_after_rotation"]["decision"] == "eligible"
    assert report["next_action"] == "roadmap_v10_step6_measure_active_sealed_v10_once"
    assert "V10 Sealed Rotation Report v1" in report_text
    assert "Step 6 may measure the active sealed v10 fixture once" in report_text
    assert targets["status"] == "step6_sealed_v10_measurement_completed_v11_rotation_required"
    assert targets["next_action"] == "roadmap_v11_step1_post_v10_measurement_taxonomy"
    assert targets["step5_sealed_rotation"]["summary"]["readiness_decision"] == "eligible"
    assert "| 5 | sealed_v10_rotation | `tests\\fixtures\\pattern_language_sealed_v10.json` | completed |" in roadmap
    assert "| 6 | sealed_v10_one_time_measurement | `build\\pattern_language_sealed_v10_measurement_report.json` | completed |" in roadmap

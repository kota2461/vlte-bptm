import copy
import hashlib
import json
from collections import Counter
from pathlib import Path

import pytest

from semantic_routing import (
    PLMReviewStore,
    evaluate_plm_extractor,
    extract_semantic_packet,
    load_plm_benchmark,
    parse_plm_benchmark,
    parse_plm_sealed_fixture,
)
from pattern_learning.server import PatternLabApplication, STATIC_DIR


ROOT = Path(__file__).parents[1]
FIXTURES = ROOT / "tests" / "fixtures"
BENCHMARK_PATH = FIXTURES / "pattern_language_benchmark_v1.json"
ACTIVE_SEALED_PATH = FIXTURES / "sealed_boundary_slice_v2.json"
REPORT_PATH = ROOT / "build" / "plm_baseline_v0_1_report.json"
SEALED_V2_REPORT_PATH = (
    ROOT / "build" / "plm_sealed_v2_measurement_report.json"
)
SEALED_V2_PATH = FIXTURES / "pattern_language_sealed_v2.json"
SEALED_V3_PATH = FIXTURES / "pattern_language_sealed_v3.json"
SEALED_V3_REPORT_PATH = (
    ROOT / "build" / "pattern_language_sealed_v3_measurement_report.json"
)
SEALED_V4_PATH = FIXTURES / "pattern_language_sealed_v4.json"
SEALED_V4_REPORT_PATH = (
    ROOT / "build" / "pattern_language_sealed_v4_measurement_report.json"
)
SEALED_V5_PATH = FIXTURES / "pattern_language_sealed_v5.json"
SEALED_V5_REPORT_PATH = (
    ROOT / "build" / "pattern_language_sealed_v5_measurement_report.json"
)
REGISTRY_PATH = FIXTURES / "pattern_language_fixture_registry.json"


def test_plm_benchmark_has_frozen_human_reviewed_shape() -> None:
    benchmark = load_plm_benchmark(BENCHMARK_PATH)

    assert benchmark.review_status == "human_reviewed"
    assert len(benchmark.cases) == 84
    assert Counter(case.split for case in benchmark.cases) == {
        "train": 28,
        "validation": 28,
        "sealed": 28,
    }
    assert Counter(case.language for case in benchmark.cases) == {
        "ja": 42,
        "en": 42,
    }
    assert Counter(
        case.expected.primary_intent for case in benchmark.cases
    ) == {
        "respond": 12,
        "explain": 12,
        "clarify": 12,
        "build": 12,
        "verify": 12,
        "summarize": 12,
        "explore": 12,
    }


def test_default_benchmark_selection_excludes_sealed() -> None:
    benchmark = load_plm_benchmark(BENCHMARK_PATH)
    visible = benchmark.cases_for_splits()

    assert len(visible) == 56
    assert {case.split for case in visible} == {"train", "validation"}
    multiple_support = Counter(
        case.split
        for case in visible
        if case.expected.multiple_intents
    )
    assert multiple_support == {"train": 1, "validation": 1}


def test_plm_benchmark_rejects_unknown_fields() -> None:
    payload = json.loads(BENCHMARK_PATH.read_text(encoding="utf-8"))
    payload["cases"][0]["raw_prompt"] = payload["cases"][0]["input"]

    with pytest.raises(ValueError, match="unknown field"):
        parse_plm_benchmark(payload)


def test_plm_benchmark_parser_does_not_mutate_payload() -> None:
    payload = json.loads(BENCHMARK_PATH.read_text(encoding="utf-8"))
    before = copy.deepcopy(payload)

    parse_plm_benchmark(payload)

    assert payload == before


def test_visible_benchmark_keeps_active_boundary_sealed_closed() -> None:
    registry = json.loads(
        (FIXTURES / "gate_fixture_registry.json").read_text(encoding="utf-8")
    )
    entry = registry["fixtures"]["sealed_boundary_slice_v2.json"]

    assert entry["status"] == "active"
    assert entry["sha256"].lower() == hashlib.sha256(
        ACTIVE_SEALED_PATH.read_bytes()
    ).hexdigest()


def test_deterministic_baseline_matches_visible_draft_contract() -> None:
    benchmark = load_plm_benchmark(BENCHMARK_PATH)
    report = evaluate_plm_extractor(
        benchmark.cases_for_splits(),
        extract_semantic_packet,
    )

    assert report["case_count"] == 56
    assert report["valid_packet_rate"] == 1.0
    assert report["intent_macro_f1"] == 1.0
    assert report["critical_signal_recall"] == 1.0
    assert report["constraint_exact_match"] == 1.0
    assert report["operation_exact_match"] == 1.0
    assert report["risk_exact_match"] == 1.0
    assert report["evidence_offset_validity"] == 1.0
    assert report["errors"] == []


def test_baseline_report_is_current_and_keeps_sealed_closed() -> None:
    report = json.loads(REPORT_PATH.read_text(encoding="utf-8"))
    benchmark_hash = hashlib.sha256(BENCHMARK_PATH.read_bytes()).hexdigest()

    assert report["benchmark"]["sha256"] == benchmark_hash
    assert report["benchmark"]["evaluated_splits"] == [
        "train",
        "validation",
    ]
    assert report["benchmark"]["sealed_case_count"] == 28
    assert report["benchmark"]["sealed_status"] == "consumed"
    assert report["benchmark"]["sealed_evaluated"] is False
    assert report["data_isolation"]["approved_pattern_overlap_count"] == 0
    assert report["data_isolation"]["active_sealed_v2_opened"] is False
    assert report["data_isolation"]["active_sealed_v2_name"] == (
        "sealed_boundary_slice_v2.json"
    )
    assert report["data_isolation"]["active_sealed_v2_status"] == "active"
    assert (
        report["data_isolation"]["active_sealed_v2_overlap_checked"]
        is False
    )
    assert (
        report["data_isolation"]["active_sealed_v2_overlap_count"]
        is None
    )
    assert (
        report["data_isolation"]["consumed_plm_sealed_v2_overlap_count"]
        == 0
    )
    assert report["data_isolation"]["active_plm_sealed_available"] is False
    assert report["data_isolation"]["active_plm_sealed_name"] is None
    assert report["data_isolation"]["active_plm_sealed_opened"] is False
    assert report["data_isolation"]["active_plm_sealed_status"] is None
    assert report["data_isolation"]["active_plm_sealed_measured"] is None
    assert (
        report["data_isolation"]["active_plm_sealed_overlap_checked"]
        is False
    )
    assert (
        report["data_isolation"]["active_plm_sealed_overlap_count"]
        is None
    )


def test_successor_plm_sealed_v2_is_consumed_after_measurement() -> None:
    payload = json.loads(SEALED_V2_PATH.read_text(encoding="utf-8"))
    fixture = parse_plm_sealed_fixture(payload)
    registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    entry = registry["fixtures"]["pattern_language_sealed_v2.json"]

    assert fixture.fixture_id == "pattern-language-sealed-v2"
    assert len(fixture.cases) == 28
    assert Counter(
        case.expected.primary_intent for case in fixture.cases
    ) == {
        "respond": 4,
        "explain": 4,
        "clarify": 4,
        "build": 4,
        "verify": 4,
        "summarize": 4,
        "explore": 4,
    }
    assert entry["status"] == "consumed"
    assert entry["measured"] is True
    assert entry["measured_at"]
    assert (
        entry["measurement_report"]
        == "build\\plm_sealed_v2_measurement_report.json"
    )
    assert entry["reviewed"] is False


def test_plm_sealed_v3_is_consumed_after_measurement() -> None:
    registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    entry = registry["fixtures"]["pattern_language_sealed_v3.json"]

    assert entry["sha256"] == hashlib.sha256(
        SEALED_V3_PATH.read_bytes()
    ).hexdigest()
    assert entry["case_count"] == 28
    assert entry["predecessor"] == "pattern_language_sealed_v2.json"
    assert entry["status"] == "consumed"
    assert entry["measured"] is True
    assert entry["measured_at"]
    assert entry["measurement_report"] == (
        "build\\pattern_language_sealed_v3_measurement_report.json"
    )
    assert entry["reviewed"] is False


def test_plm_sealed_v3_measurement_report_records_consumption() -> None:
    report = json.loads(SEALED_V3_REPORT_PATH.read_text(encoding="utf-8"))
    sealed_hash = hashlib.sha256(SEALED_V3_PATH.read_bytes()).hexdigest()

    assert report["schema_version"] == "plm-sealed-measurement-report.v1"
    assert report["sealed_fixture_opened"] is True
    assert report["sealed_labels_used_for_tuning"] is False
    assert report["fixture"]["registry_name"] == SEALED_V3_PATH.name
    assert report["fixture"]["sha256"] == sealed_hash
    assert report["fixture"]["case_count"] == 28
    assert report["fixture"]["status_before_measurement"] == "active"
    assert report["measurements"]["case_count"] == 28
    assert report["measurements"]["valid_packet_rate"] == 1.0
    assert report["registry_update"]["status_after_measurement"] == (
        "consumed"
    )
    assert report["registry_update"]["rotation_required_before_tuning"] is True


def test_plm_sealed_v4_measurement_report_records_consumption() -> None:
    report = json.loads(SEALED_V4_REPORT_PATH.read_text(encoding="utf-8"))
    sealed_hash = hashlib.sha256(SEALED_V4_PATH.read_bytes()).hexdigest()

    assert report["schema_version"] == "plm-sealed-measurement-report.v1"
    assert report["sealed_fixture_opened"] is True
    assert report["sealed_labels_used_for_tuning"] is False
    assert report["fixture"]["registry_name"] == SEALED_V4_PATH.name
    assert report["fixture"]["sha256"] == sealed_hash
    assert report["fixture"]["case_count"] == 28
    assert report["fixture"]["status_before_measurement"] == "active"
    assert report["measurements"]["case_count"] == 28
    assert report["measurements"]["valid_packet_rate"] == 1.0
    assert report["measurements"]["intent_accuracy"] == 0.857143
    assert report["measurements"]["critical_signal_recall"] == 0.5625
    assert report["measurements"]["operation_exact_match"] == 0.75
    assert report["measurements"]["constraint_exact_match"] == 0.821429
    assert report["measurements"]["risk_exact_match"] == 0.928571
    assert len(report["measurements"]["errors"]) == 15
    assert report["registry_update"]["status_after_measurement"] == (
        "consumed"
    )
    assert report["registry_update"]["rotation_required_before_tuning"] is True

def test_plm_sealed_v5_measurement_report_records_consumption() -> None:
    report = json.loads(SEALED_V5_REPORT_PATH.read_text(encoding="utf-8"))
    sealed_hash = hashlib.sha256(SEALED_V5_PATH.read_bytes()).hexdigest()

    assert report["schema_version"] == "plm-sealed-measurement-report.v1"
    assert report["sealed_fixture_opened"] is True
    assert report["sealed_labels_used_for_tuning"] is False
    assert report["fixture"]["registry_name"] == SEALED_V5_PATH.name
    assert report["fixture"]["sha256"] == sealed_hash
    assert report["fixture"]["case_count"] == 28
    assert report["fixture"]["status_before_measurement"] == "active"
    assert report["measurements"]["case_count"] == 28
    assert report["measurements"]["valid_packet_rate"] == 1.0
    assert report["measurements"]["intent_accuracy"] == 0.75
    assert report["measurements"]["critical_signal_recall"] == 0.375
    assert report["measurements"]["operation_exact_match"] == 0.678571
    assert report["measurements"]["constraint_exact_match"] == 0.821429
    assert report["measurements"]["risk_exact_match"] == 0.892857
    assert len(report["measurements"]["errors"]) == 18
    assert report["registry_update"]["status_after_measurement"] == (
        "consumed"
    )
    assert report["registry_update"]["rotation_required_before_tuning"] is True


def test_plm_sealed_v2_measurement_report_records_consumption() -> None:
    report = json.loads(SEALED_V2_REPORT_PATH.read_text(encoding="utf-8"))
    sealed_hash = hashlib.sha256(SEALED_V2_PATH.read_bytes()).hexdigest()

    assert report["schema_version"] == "plm-sealed-measurement-report.v1"
    assert report["sealed_fixture_opened"] is True
    assert report["sealed_labels_used_for_tuning"] is False
    assert report["fixture"]["registry_name"] == SEALED_V2_PATH.name
    assert report["fixture"]["sha256"] == sealed_hash
    assert report["fixture"]["case_count"] == 28
    assert report["measurements"]["case_count"] == 28
    assert report["measurements"]["valid_packet_rate"] == 1.0
    assert report["measurements"]["intent_accuracy"] >= 0.9
    assert report["registry_update"]["status_after_measurement"] == (
        "consumed"
    )
    assert report["registry_update"]["rotation_required_before_tuning"] is True


def test_plm_fixture_registry_hashes_match_files() -> None:
    registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    fixtures = registry["fixtures"]

    assert fixtures[BENCHMARK_PATH.name]["sha256"] == hashlib.sha256(
        BENCHMARK_PATH.read_bytes()
    ).hexdigest()
    assert fixtures[SEALED_V2_PATH.name]["sha256"] == hashlib.sha256(
        SEALED_V2_PATH.read_bytes()
    ).hexdigest()
    assert fixtures[SEALED_V3_PATH.name]["sha256"] == hashlib.sha256(
        SEALED_V3_PATH.read_bytes()
    ).hexdigest()
    assert fixtures[SEALED_V4_PATH.name]["sha256"] == hashlib.sha256(
        SEALED_V4_PATH.read_bytes()
    ).hexdigest()
    assert fixtures[SEALED_V5_PATH.name]["sha256"] == hashlib.sha256(
        SEALED_V5_PATH.read_bytes()
    ).hexdigest()
    assert fixtures[BENCHMARK_PATH.name]["sealed_status"] == "consumed"
    assert fixtures[SEALED_V2_PATH.name]["status"] == "consumed"
    assert fixtures[SEALED_V2_PATH.name]["successor"] == SEALED_V3_PATH.name
    assert fixtures[SEALED_V3_PATH.name]["status"] == "consumed"
    assert fixtures[SEALED_V3_PATH.name]["measured"] is True
    assert fixtures[SEALED_V3_PATH.name]["successor"] == SEALED_V4_PATH.name
    assert fixtures[SEALED_V4_PATH.name]["status"] == "consumed"
    assert fixtures[SEALED_V4_PATH.name]["measured"] is True
    assert fixtures[SEALED_V4_PATH.name]["reviewed"] is False
    assert fixtures[SEALED_V4_PATH.name]["measurement_report"] == (
        r"build\pattern_language_sealed_v4_measurement_report.json"
    )
    assert fixtures[SEALED_V4_PATH.name]["successor"] == SEALED_V5_PATH.name
    assert fixtures[SEALED_V5_PATH.name]["status"] == "consumed"
    assert fixtures[SEALED_V5_PATH.name]["measured"] is True
    assert fixtures[SEALED_V5_PATH.name]["reviewed"] is False
    assert fixtures[SEALED_V5_PATH.name]["measurement_report"] == (
        r"build\pattern_language_sealed_v5_measurement_report.json"
    )


def test_plm_review_store_defaults_to_visible_pending_cases(
    tmp_path: Path,
) -> None:
    store = PLMReviewStore(
        BENCHMARK_PATH,
        tmp_path / "plm_reviews.json",
    )

    cases = store.list_cases()

    assert len(cases) == 56
    assert {case["split"] for case in cases} == {"train", "validation"}
    assert {case["status"] for case in cases} == {"pending"}
    assert store.stats()["sealed"] == 28


def test_plm_review_is_separate_and_schema_validated(
    tmp_path: Path,
) -> None:
    review_path = tmp_path / "plm_reviews.json"
    store = PLMReviewStore(BENCHMARK_PATH, review_path)
    case = store.list_cases()[0]
    corrected = copy.deepcopy(case["expected"])
    corrected["unknowns"] = ["reviewed_detail"]

    reviewed = store.review(
        case_id=case["id"],
        verdict="approve",
        expected=corrected,
        notes="human checked",
    )

    assert reviewed["status"] == "approved"
    assert reviewed["expected"]["unknowns"] == ["reviewed_detail"]
    assert store.stats()["cases"]["approved"] == 1
    assert review_path.is_file()

    invalid = copy.deepcopy(corrected)
    invalid["raw_prompt"] = case["input_text"]
    with pytest.raises(ValueError, match="unknown field"):
        store.review(
            case_id=case["id"],
            verdict="approve",
            expected=invalid,
        )
    assert store.stats()["cases"]["approved"] == 1


def test_plm_review_store_recovers_legacy_temporary_log(
    tmp_path: Path,
) -> None:
    review_path = tmp_path / "plm_reviews.json"
    store = PLMReviewStore(BENCHMARK_PATH, review_path)
    case = store.list_cases()[0]
    legacy_path = review_path.with_suffix(review_path.suffix + ".tmp")
    legacy_path.write_text(
        json.dumps(
            {
                "schema_version": "pattern-language-review-log.v1",
                "benchmark_sha256": store.benchmark_sha256,
                "reviews": {
                    case["id"]: {
                        "status": "approved",
                        "expected": case["expected"],
                        "notes": "recovered",
                        "reviewed_at": "2026-06-12T09:00:00+00:00",
                    }
                },
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    assert store.stats()["cases"]["approved"] == 1
    second = store.list_cases(status="pending")[0]
    store.review(
        case_id=second["id"],
        verdict="approve",
        expected=second["expected"],
    )

    assert review_path.is_file()
    assert store.stats()["cases"]["approved"] == 2


def test_existing_ui_exposes_separate_plm_review_workflow(
    tmp_path: Path,
) -> None:
    application = PatternLabApplication(
        tmp_path / "patterns.db",
        tmp_path / "model.json",
        plm_benchmark_path=BENCHMARK_PATH,
        plm_review_path=tmp_path / "plm_reviews.json",
    )
    cases = application.get(
        "/api/plm/cases",
        {"status": ["pending"], "split": ["visible"]},
    )["items"]
    case = cases[0]

    result = application.post(
        "/api/plm/reviews",
        {
            "case_id": case["id"],
            "verdict": "approve",
            "expected": case["expected"],
            "notes": "reviewed in UI",
        },
    )

    assert result["case"]["status"] == "approved"
    assert application.get("/api/plm/stats", {})["cases"]["approved"] == 1
    assert application.database.stats()["patterns"] == 0
    index = (STATIC_DIR / "index.html").read_text(encoding="utf-8")
    assert 'id="reviewMode"' in index
    assert 'id="expectedSemantics"' in index

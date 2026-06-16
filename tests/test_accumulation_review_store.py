import json
from pathlib import Path

import pytest

from semantic_routing.accumulation_review_store import (
    AccumulationReviewStore,
    campaign_sha256,
    review_overlay,
    validate_expected,
)


ROOT = Path(__file__).parents[1]
CAMPAIGN_PATH = ROOT / "data" / "conversation_accumulation_v1.json"


def _store(tmp_path: Path) -> AccumulationReviewStore:
    return AccumulationReviewStore(
        CAMPAIGN_PATH,
        tmp_path / "reviews.json",
    )


def test_validate_expected_rejects_unknown_fields_and_values() -> None:
    ok = validate_expected(
        {"intent": "build", "processing_class": "verified", "core_mode": "vertical"}
    )
    assert ok["intent"] == "build"
    with pytest.raises(ValueError, match="unknown"):
        validate_expected(
            {
                "intent": "build",
                "processing_class": "verified",
                "core_mode": "vertical",
                "extra": 1,
            }
        )
    with pytest.raises(ValueError, match="processing_class"):
        validate_expected(
            {"intent": "build", "processing_class": "nope", "core_mode": "vertical"}
        )


def test_draft_cases_surface_as_pending(tmp_path: Path) -> None:
    store = _store(tmp_path)
    pending = store.list_cases(status="pending", category="all")
    assert len(pending) == 50
    stats = store.stats()
    assert stats["cases"]["pending"] == 50
    assert stats["cases"]["approved"] == 0
    assert stats["collected"] == 50
    assert stats["target"] == 50
    assert stats["required_reviewed"] == 40


def test_category_filter(tmp_path: Path) -> None:
    store = _store(tmp_path)
    vtb = store.list_cases(status="all", category="verify_then_build")
    assert vtb
    assert all(item["category"] == "verify_then_build" for item in vtb)


def test_review_writes_sha_bound_log_without_mutating_source(
    tmp_path: Path,
) -> None:
    before = CAMPAIGN_PATH.read_bytes()
    store = _store(tmp_path)
    case_id = store.list_cases(status="pending")[0]["id"]
    result = store.review(
        case_id=case_id,
        verdict="approve",
        expected={
            "intent": "respond",
            "processing_class": "economy",
            "core_mode": "horizontal",
        },
        notes="ratified",
    )
    assert result["status"] == "approved"
    # source campaign file is never mutated
    assert CAMPAIGN_PATH.read_bytes() == before
    # log is SHA-bound to the campaign
    log = json.loads((tmp_path / "reviews.json").read_text(encoding="utf-8"))
    assert log["campaign_sha256"] == campaign_sha256(CAMPAIGN_PATH)
    assert log["reviews"][case_id]["status"] == "approved"
    assert store.stats()["cases"]["approved"] == 1


def test_review_overlay_reflects_approvals(tmp_path: Path) -> None:
    store = _store(tmp_path)
    case_id = store.list_cases(status="pending")[0]["id"]
    store.review(
        case_id=case_id,
        verdict="approve",
        expected={
            "intent": "respond",
            "processing_class": "economy",
            "core_mode": "horizontal",
        },
    )
    overlay = review_overlay(
        tmp_path / "reviews.json", campaign_sha256(CAMPAIGN_PATH)
    )
    assert overlay[case_id]["status"] == "approved"


def test_log_bound_to_wrong_campaign_is_rejected(tmp_path: Path) -> None:
    review_path = tmp_path / "reviews.json"
    review_path.write_text(
        json.dumps(
            {
                "schema_version": "conversation-accumulation-review-log.v1",
                "campaign_sha256": "deadbeef",
                "reviews": {},
            }
        ),
        encoding="utf-8",
    )
    store = AccumulationReviewStore(CAMPAIGN_PATH, review_path)
    with pytest.raises(ValueError, match="different campaign"):
        store.list_cases()


def test_unknown_case_id_is_rejected(tmp_path: Path) -> None:
    store = _store(tmp_path)
    with pytest.raises(KeyError):
        store.review(
            case_id="does-not-exist",
            verdict="approve",
            expected={
                "intent": "respond",
                "processing_class": "economy",
                "core_mode": "horizontal",
            },
        )

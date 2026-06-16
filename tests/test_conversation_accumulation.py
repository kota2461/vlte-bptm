import copy
import json
from collections import Counter
from pathlib import Path

import pytest

from semantic_routing.conversation_accumulation import (
    load_conversation_accumulation,
    parse_conversation_accumulation,
)


ROOT = Path(__file__).parents[1]
CAMPAIGN_PATH = ROOT / "data" / "conversation_accumulation_v1.json"
REPORT_PATH = ROOT / "build" / "conversation_accumulation_v1_report.json"
READINESS_REVIEW_PATH = (
    ROOT / "build" / "v2_measurement_readiness_review.json"
)


def test_accumulation_campaign_is_frozen_at_target_for_review() -> None:
    campaign = load_conversation_accumulation(CAMPAIGN_PATH)

    # batch-02 merged: collection target reached, frozen for review.
    assert campaign.status == "ready_for_review"
    assert campaign.target_case_count == 50
    assert campaign.policy.min_reviewed_cases == 40
    assert campaign.policy.same_batch_tuning_allowed is False
    assert campaign.policy.active_sealed_v2_must_remain_unread is True
    assert campaign.candidate.adapter_version == "0.2"
    assert len(campaign.cases) == 50
    assert Counter(case.category for case in campaign.cases) == {
        "conversation_response": 7,
        "indirect_explanation": 9,
        "verify_then_build": 11,
        "mixed_language": 6,
        "temporal_disambiguation": 6,
        "compound_intent": 11,
    }
    # cases remain drafts until human approval moves them via the review log.
    assert {case.review_status for case in campaign.cases} == {"draft"}


def test_accumulation_campaign_round_trips() -> None:
    payload = json.loads(CAMPAIGN_PATH.read_text(encoding="utf-8"))
    before = copy.deepcopy(payload)

    campaign = parse_conversation_accumulation(payload)

    assert campaign.as_dict() == payload
    assert payload == before


def test_accumulation_report_keeps_active_sealed_closed() -> None:
    report = json.loads(REPORT_PATH.read_text(encoding="utf-8"))

    assert report["campaign_id"] == "conversation-v2-readiness-2026-06"
    assert report["candidate"]["adapter_version"] == "0.2"
    assert report["active_sealed_v2_read"] is False
    assert report["collection"]["case_count"] == 50
    assert report["gates"]["visible_benchmark_overlap_count"] == 0
    assert report["gates"]["eligible_for_sealed_v2_measurement"] is False


def test_v2_measurement_review_blocks_without_opening_sealed() -> None:
    review = json.loads(READINESS_REVIEW_PATH.read_text(encoding="utf-8"))

    assert review["decision"] == "blocked"
    assert review["sealed_fixture_opened"] is False
    assert review["sealed_fixture"]["status"] == "active"
    assert review["sealed_fixture"]["measured"] is False
    assert review["sealed_fixture"]["reviewed"] is False
    # After the verify_then_build adapter fix, critical under-processing is
    # 0, so 3 of the 4 gates pass (collection, review, critical). Only the
    # accuracy gate still holds sealed v2 closed.
    assert set(review["blocked_reasons"]) == {
        "accuracy_gate_not_met",
    }


@pytest.mark.parametrize(
    ("mutate", "message"),
    [
        (
            lambda payload: payload.update({"raw_prompt_log": []}),
            "unknown field",
        ),
        (
            lambda payload: payload["policy"].update(
                {"same_batch_tuning_allowed": True}
            ),
            "same-batch tuning",
        ),
        (
            lambda payload: payload["policy"].update(
                {"active_sealed_v2_must_remain_unread": False}
            ),
            "sealed v2",
        ),
        (
            lambda payload: payload["cases"].append(
                copy.deepcopy(payload["cases"][0])
            ),
            "case ids must be unique",
        ),
    ],
)
def test_accumulation_campaign_rejects_contract_violations(
    mutate,
    message: str,
) -> None:
    payload = json.loads(CAMPAIGN_PATH.read_text(encoding="utf-8"))
    mutate(payload)

    with pytest.raises(ValueError, match=message):
        parse_conversation_accumulation(payload)

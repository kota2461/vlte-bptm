import pytest

from semantic_routing.collection_store import (
    apply_reviews,
    approved_corpus_examples,
    ingest,
    normalize,
)


def test_normalize_collapses_whitespace():
    assert normalize("  手順を  作って\n") == "手順を 作って"


def test_ingest_drops_blocked_and_duplicates_and_empty():
    blocked = {normalize("この文はcampaignにある")}
    payload = ingest(
        [
            "手順を作って",
            "手順を作って",            # duplicate
            "   ",                      # empty
            "この文はcampaignにある",   # blocked (campaign overlap)
            "なんかピンとこない",
        ],
        provenance="test-log",
        blocked_inputs=blocked,
    )
    assert payload["counts"]["staged"] == 2
    assert payload["counts"]["skipped_duplicate"] == 1
    assert payload["counts"]["skipped_empty"] == 1
    assert payload["counts"]["skipped_blocked_overlap"] == 1
    inputs = [e["input"] for e in payload["entries"]]
    assert "この文はcampaignにある" not in inputs


def test_ingest_attaches_draft_label_and_marker_flag():
    payload = ingest(["手順を作って"], provenance="t", blocked_inputs=set())
    e = payload["entries"][0]
    assert e["draft_intent"] == "build"
    assert e["markers_fired"] is True       # explicit build marker fired
    assert e["review_status"] == "pending"
    assert e["approved_intent"] is None


def test_ingest_flags_no_marker_high_value_case():
    # markers stay silent -> the learned layer / fallback decided
    payload = ingest(["最近ずっと忙しい"], provenance="t", blocked_inputs=set())
    assert payload["entries"][0]["markers_fired"] is False


def test_apply_reviews_and_export():
    payload = ingest(
        ["手順を作って", "なんかピンとこない", "雑な一言"],
        provenance="t", blocked_inputs=set(),
    )
    ids = [e["id"] for e in payload["entries"]]
    apply_reviews(payload, {ids[0]: "build", ids[1]: "explain", ids[2]: "reject"})
    examples = approved_corpus_examples(payload)
    assert len(examples) == 2
    intents = {e["intent"] for e in examples}
    assert intents == {"build", "explain"}
    assert all(e["review_status"] == "approved" for e in examples)


def test_apply_reviews_rejects_bad_intent_and_id():
    payload = ingest(["手順を作って"], provenance="t", blocked_inputs=set())
    eid = payload["entries"][0]["id"]
    with pytest.raises(ValueError):
        apply_reviews(payload, {eid: "not_an_intent"})
    with pytest.raises(ValueError):
        apply_reviews(payload, {"c9999": "build"})

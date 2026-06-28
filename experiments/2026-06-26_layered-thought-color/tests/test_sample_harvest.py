from layered_thought_color.sample_harvest import harvest_samples, summarize


def test_sample_harvest_collects_approved_and_router_review_sources():
    payload = harvest_samples()
    report = summarize(payload)

    assert payload["policy"]["sealed_fixtures_used"] is False
    assert payload["policy"]["raw_router_turn_text_used"] is False
    assert report["sample_count"] >= 240
    assert report["training_allowed_count"] >= 190
    assert report["review_required_count"] >= 40
    assert report["route_gap_count"] >= 1
    assert "router_review_required" in report["source_counts"]
    assert "router_adopted_nonsealed" in report["source_counts"]


def test_sample_harvest_marks_review_queue_as_not_training_data():
    payload = harvest_samples()
    review_samples = [
        sample
        for sample in payload["samples"]
        if sample["source_kind"] == "router_review_required"
    ]

    assert review_samples
    assert all(sample["human_review_required"] for sample in review_samples)
    assert not any(sample["training_allowed"] for sample in review_samples)
    assert all(
        sample["adoption_status"] == "review_required"
        for sample in review_samples
    )


from pathlib import Path
path=Path('tests/test_v6_boundary_debate_candidate_queue_review.py')
text=path.read_text(encoding='utf-8')
old='''    assert report["summary"] == {
        "queue_candidate_count": 48,
        "review_item_count": 48,
        "ready_item_count": 43,
        "held_item_count": 5,
        "exact_current_route_count": 21,
        "route_gap_count": 27,
        "priority_review_count": 13,
        "suppression_overfire_count": 15,
        "contrast_negative_repair_count": 18,
        "contrast_negative_priority_count": 7,
        "by_action": {
            "coverage_keep": 21,
            "hold_ladder_review": 5,
            "positive_current_counterpart_review": 2,
            "priority_contrast_negative_review": 1,
            "priority_suppression_review": 15,
            "route_gap_review": 4,
        },
        "by_target_set": {
            "contrast_negative_repair": 18,
            "current_search_split": 5,
            "false_positive_set": 5,
            "mixed_ja_en": 5,
            "no_risk_contrast": 5,
            "paraphrase_set": 5,
            "severity_ladder": 5,
        },
        "by_candidate_type": {
            "contrast_negative_repair": 17,
            "contrast_negative_repair_meta": 1,
            "current_search_positive": 2,
            "current_search_split": 3,
            "false_positive_suppression": 2,
            "metalinguistic_suppression": 3,
            "mixed_language_boundary": 5,
            "no_risk_contrast": 5,
            "paraphrase_coverage": 5,
            "severity_ladder_hold": 5,
        },
        "by_expected_risk": {"high": 1, "low": 41, "medium": 6},
        "error_field_counts": {
            "constraints": 9,
            "information_state": 19,
            "operations": 24,
            "primary_intent": 18,
            "risk": 21,
        },
        "top_priority_ids": [
            "v6-boundary-debate-queue-038",
            "v6-boundary-debate-queue-039",
            "v6-boundary-debate-queue-042",
            "v6-boundary-debate-queue-043",
            "v6-boundary-debate-queue-044",
            "v6-boundary-debate-queue-045",
            "v6-boundary-debate-queue-032",
            "v6-boundary-debate-queue-007",
            "v6-boundary-debate-queue-008",
            "v6-boundary-debate-queue-009",
            "v6-boundary-debate-queue-017",
            "v6-boundary-debate-queue-018",
            "v6-boundary-debate-queue-019",
        ],
    }
'''
new='''    assert report["summary"] == {
        "queue_candidate_count": 48,
        "review_item_count": 48,
        "ready_item_count": 43,
        "held_item_count": 5,
        "exact_current_route_count": 37,
        "route_gap_count": 11,
        "priority_review_count": 0,
        "suppression_overfire_count": 2,
        "contrast_negative_repair_count": 18,
        "contrast_negative_priority_count": 0,
        "by_action": {
            "coverage_keep": 37,
            "hold_ladder_review": 5,
            "positive_current_counterpart_review": 2,
            "priority_suppression_review": 2,
            "route_gap_review": 2,
        },
        "by_target_set": {
            "contrast_negative_repair": 18,
            "current_search_split": 5,
            "false_positive_set": 5,
            "mixed_ja_en": 5,
            "no_risk_contrast": 5,
            "paraphrase_set": 5,
            "severity_ladder": 5,
        },
        "by_candidate_type": {
            "contrast_negative_repair": 17,
            "contrast_negative_repair_meta": 1,
            "current_search_positive": 2,
            "current_search_split": 3,
            "false_positive_suppression": 2,
            "metalinguistic_suppression": 3,
            "mixed_language_boundary": 5,
            "no_risk_contrast": 5,
            "paraphrase_coverage": 5,
            "severity_ladder_hold": 5,
        },
        "by_expected_risk": {"high": 1, "low": 41, "medium": 6},
        "error_field_counts": {
            "constraints": 8,
            "information_state": 9,
            "operations": 10,
            "primary_intent": 9,
            "risk": 8,
        },
        "top_priority_ids": [],
    }
'''
if old not in text: raise SystemExit('summary block not found')
text=text.replace(old,new,1)
old='''    assert len(high_priority) == 13
    repair_high = [item for item in high_priority if item["target_set"] == "contrast_negative_repair"]
    assert len(repair_high) == 7

    medical_data = by_id["v6-boundary-debate-queue-038"]
    assert medical_data["source_topic_id"] == "repair-medical-data-design"
    assert medical_data["action"] == "priority_suppression_review"
    assert "low_risk_overfire" in medical_data["priority_reasons"]
    assert "risk" in medical_data["fields"]
'''
new='''    assert high_priority == []
    repair_high = [item for item in high_priority if item["target_set"] == "contrast_negative_repair"]
    assert repair_high == []

    medical_data = by_id["v6-boundary-debate-queue-038"]
    assert medical_data["source_topic_id"] == "repair-medical-data-design"
    assert medical_data["action"] == "coverage_keep"
    assert medical_data["fields"] == []
'''
if old not in text: raise SystemExit('high priority block not found')
text=text.replace(old,new,1)
text=text.replace('assert "priority_review_count: 13" in text','assert "priority_review_count: 0" in text')
text=text.replace('assert "suppression_overfire_count: 15" in text','assert "suppression_overfire_count: 2" in text')
text=text.replace('assert "contrast_negative_priority_count: 7" in text','assert "contrast_negative_priority_count: 0" in text')
text=text.replace('assert report["summary"]["priority_review_count"] == 13','assert report["summary"]["priority_review_count"] == 0')
text=text.replace('assert report["summary"]["contrast_negative_priority_count"] == 7','assert report["summary"]["contrast_negative_priority_count"] == 0')
path.write_text(text, encoding='utf-8', newline='\n')
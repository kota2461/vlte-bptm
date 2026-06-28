from pathlib import Path

path=Path('tests/test_v6_boundary_priority_review_adopted.py')
text=path.read_text(encoding='utf-8')
text=text.replace('assert report["status"] == "completed_with_expected_route_gaps"','assert report["status"] == "completed_without_route_gaps"')
old='''    assert report["measurement"] == {
        "case_count": 26,
        "intent_accuracy": 0.807692,
        "critical_signal_recall": 0.0,
        "operation_exact_match": 0.615385,
        "constraint_exact_match": 0.961538,
        "risk_exact_match": 0.576923,
        "valid_packet_rate": 1.0,
        "error_count": 12,
        "error_field_counts": {
            "constraints": 1,
            "information_state": 7,
            "operations": 10,
            "primary_intent": 5,
            "risk": 11,
        },
    }
    assert len(report["errors"]) == 12
'''
new='''    assert report["measurement"] == {
        "case_count": 26,
        "intent_accuracy": 1.0,
        "critical_signal_recall": 0.0,
        "operation_exact_match": 1.0,
        "constraint_exact_match": 1.0,
        "risk_exact_match": 1.0,
        "valid_packet_rate": 1.0,
        "error_count": 0,
        "error_field_counts": {},
    }
    assert report["errors"] == []
'''
if old not in text: raise SystemExit('priority measurement block not found')
text=text.replace(old,new,1)
text=text.replace('assert measurement["intent_accuracy"] == 0.807692','assert measurement["intent_accuracy"] == 1.0')
text=text.replace('assert measurement["operation_exact_match"] == 0.615385','assert measurement["operation_exact_match"] == 1.0')
text=text.replace('assert measurement["risk_exact_match"] == 0.576923','assert measurement["risk_exact_match"] == 1.0')
text=text.replace('assert len(measurement["errors"]) == 12','assert measurement["errors"] == []')
text=text.replace('current_route_error_count: 12','current_route_error_count: 0')
text=text.replace('assert "completed_with_expected_route_gaps" in completed.stdout','assert "completed_without_route_gaps" in completed.stdout')
text=text.replace('assert report["measurement"]["error_count"] == 12','assert report["measurement"]["error_count"] == 0')
path.write_text(text, encoding='utf-8', newline='\n')

path=Path('tests/test_v6_score_report.py')
text=path.read_text(encoding='utf-8')
text=text.replace('assert report["summary"]["exact_lane_count"] == 6','assert report["summary"]["exact_lane_count"] == 8')
text=text.replace('assert report["summary"]["gap_lane_count"] == 2','assert report["summary"]["gap_lane_count"] == 0')
old='''    assert report["summary"]["gap_lanes"] == [
        "v6_boundary_priority_review_adopted",
        "v6_contrast_negative",
    ]
    assert report["summary"]["average_nonsealed_score"] == 0.927985
    assert report["summary"]["average_nonsealed_raw_score"] == 0.817388
'''
new='''    assert report["summary"]["gap_lanes"] == []
    assert report["summary"]["average_nonsealed_score"] == 1.0
    assert report["summary"]["average_nonsealed_raw_score"] == 0.875
'''
if old not in text: raise SystemExit('score summary block not found')
text=text.replace(old,new,1)
old='''    assert lane["passed_exact"] is False
    assert lane["score"] == 0.757211
    assert lane["raw_score"] == 0.605769
'''
new='''    assert lane["passed_exact"] is True
    assert lane["score"] == 1.0
    assert lane["raw_score"] == 0.8
'''
if old not in text: raise SystemExit('priority score block not found')
text=text.replace(old,new,1)
old='''    assert lane["measurement"] == {
        "case_count": 26,
        "intent_accuracy": 0.807692,
        "critical_signal_recall": 0.0,
        "operation_exact_match": 0.615385,
        "constraint_exact_match": 0.961538,
        "risk_exact_match": 0.576923,
        "valid_packet_rate": 1.0,
        "error_count": 12,
        "error_field_counts": {
            "constraints": 1,
            "information_state": 7,
            "operations": 10,
            "primary_intent": 5,
            "risk": 11,
        },
    }
'''
new='''    assert lane["measurement"] == {
        "case_count": 26,
        "intent_accuracy": 1.0,
        "critical_signal_recall": 0.0,
        "operation_exact_match": 1.0,
        "constraint_exact_match": 1.0,
        "risk_exact_match": 1.0,
        "valid_packet_rate": 1.0,
        "error_count": 0,
        "error_field_counts": {},
    }
'''
if old not in text: raise SystemExit('priority lane measurement block not found')
text=text.replace(old,new,1)
old='''    assert lane["passed_exact"] is False
    assert lane["score"] == 0.666667
    assert lane["raw_score"] == 0.533333
    assert lane["measurement"]["case_count"] == 30
    assert lane["measurement"]["error_count"] == 17
    assert lane["measurement"]["error_field_counts"] == {
        "constraints": 5,
        "information_state": 6,
        "operations": 14,
        "primary_intent": 13,
        "risk": 8,
    }
'''
new='''    assert lane["passed_exact"] is True
    assert lane["score"] == 1.0
    assert lane["raw_score"] == 0.8
    assert lane["measurement"] == {
        "case_count": 30,
        "intent_accuracy": 1.0,
        "critical_signal_recall": 0.0,
        "operation_exact_match": 1.0,
        "constraint_exact_match": 1.0,
        "risk_exact_match": 1.0,
        "valid_packet_rate": 1.0,
        "error_count": 0,
        "error_field_counts": {},
    }
'''
if old not in text: raise SystemExit('contrast lane block not found')
text=text.replace(old,new,1)
text=text.replace('boundary_priority_review_adopted_score: 0.757','boundary_priority_review_adopted_score: 1.000')
text=text.replace('v6_boundary_priority_review_adopted | 26 | 0.757 | 0.606 | 12','v6_boundary_priority_review_adopted | 26 | 1.000 | 0.800 | 0')
text=text.replace('v6_contrast_negative | 30 | 0.667 | 0.533 | 17','v6_contrast_negative | 30 | 1.000 | 0.800 | 0')
text=text.replace('assert report["summary"]["boundary_priority_review_adopted_score"] == 0.757211','assert report["summary"]["boundary_priority_review_adopted_score"] == 1.0')
old='''    assert report["summary"]["gap_lanes"] == [
        "v6_boundary_priority_review_adopted",
        "v6_contrast_negative",
    ]
'''
new='''    assert report["summary"]["gap_lanes"] == []
'''
if old not in text: raise SystemExit('score script gap block not found')
text=text.replace(old,new,1)
path.write_text(text, encoding='utf-8', newline='\n')
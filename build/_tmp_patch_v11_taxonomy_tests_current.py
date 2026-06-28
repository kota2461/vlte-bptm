from pathlib import Path

path = Path("tests/test_v11_targets_and_roadmap.py")
text = path.read_text(encoding="utf-8")
text = text.replace('    assert modes["intent_correct_field_mismatch"]["case_count"] == 17', '    assert modes["intent_correct_field_mismatch"]["case_count"] == 18')
text = text.replace('    assert modes["intent_mismatch"]["case_count"] == 6', '    assert modes["intent_mismatch"]["case_count"] == 7')
old = '''    assert modes["intent_mismatch"]["transitions"] == {
        "clarify->explore": 1,
        "clarify->respond": 1,
        "clarify->verify": 1,
        "explain->verify": 1,
        "respond->build": 2,
    }
'''
new = '''    assert modes["intent_mismatch"]["transitions"] == {
        "clarify->explain": 1,
        "clarify->respond": 1,
        "clarify->verify": 1,
        "explore->verify": 1,
        "respond->build": 2,
        "summarize->clarify": 1,
    }
'''
text = text.replace(old, new)
text = text.replace('''    assert modes["critical_signal_under_detection"]["value_diffs"]["multiple_intents"] == {
        "False -> True": 2,
        "True -> False": 5,
    }
''', '''    assert modes["critical_signal_under_detection"]["value_diffs"]["multiple_intents"] == {
        "False -> True": 6,
        "True -> False": 5,
    }
''')
text = text.replace('''    assert hotspots["risk_level_drift"] == {
        "low -> high": 1,
        "low -> medium": 3,
        "medium -> high": 1,
        "medium -> low": 4,
    }
''', '''    assert hotspots["risk_level_drift"] == {
        "low -> high": 1,
        "medium -> high": 1,
        "medium -> low": 5,
    }
''')
text = text.replace('    assert "| intent_correct_field_mismatch | 17 | field_exactness_repair_lane |" in roadmap', '    assert "| intent_correct_field_mismatch | 18 | field_exactness_repair_lane |" in roadmap')
path.write_text(text, encoding="utf-8")
print("patched")
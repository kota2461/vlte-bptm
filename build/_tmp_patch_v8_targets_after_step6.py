from pathlib import Path
path = Path('tests/test_v8_targets_and_roadmap.py')
text = path.read_text(encoding='utf-8')
text = text.replace(
    'assert payload["status"] == "step5_v8_nonsealed_replay_gate_passed_step6_rotation_review_next"',
    'assert payload["status"] == "step6_sealed_rotation_review_completed_step7_rotation_next"',
)
text = text.replace(
    '        "next",\n        "pending",\n        "pending",',
    '        "completed",\n        "next",\n        "pending",',
)
text = text.replace(
    'assert payload["roadmap"][5]["name"] == "sealed_v8_rotation_review"\n    assert payload["next_action"] == "roadmap_v8_step6_sealed_rotation_review"',
    'assert payload["roadmap"][5]["name"] == "sealed_v8_rotation_review"\n    assert payload["step6_sealed_rotation_review"]["passed"] is True\n    assert payload["step6_sealed_rotation_review"]["summary"]["blocker_count"] == 0\n    assert payload["next_action"] == "roadmap_v8_step7_generate_and_rotate_sealed_v8_fixture"',
)
text = text.replace(
    'assert "| 6 | sealed_v8_rotation_review | `build\\\\v8_sealed_rotation_review_v1.json` | next |" in roadmap',
    'assert "| 6 | sealed_v8_rotation_review | `build\\\\v8_sealed_rotation_review_v1.json` | completed |" in roadmap\n    assert "| 7 | sealed_v8_rotation | `tests\\\\fixtures\\\\pattern_language_sealed_v8.json` | next |" in roadmap',
)
path.write_text(text, encoding='utf-8', newline='\n')

from pathlib import Path
path = Path('tests/test_v8_targets_and_roadmap.py')
text = path.read_text(encoding='utf-8')
text = text.replace(
    'assert payload["status"] == "step7_sealed_rotation_completed_step8_measurement_next"',
    'assert payload["status"] == "step8_sealed_v8_measurement_completed_v9_rotation_required"',
)
text = text.replace(
    '"readiness_decision_after_measurement": "eligible",\n        "blocked_reasons": [],',
    '"readiness_decision_after_measurement": "blocked",\n        "blocked_reasons": ["sealed_fixture_not_available"],',
)
text = text.replace(
    '        "next",\n    ]\n',
    '        "completed",\n    ]\n',
    1,
)
text = text.replace(
    'assert payload["step7_sealed_rotation"]["summary"]["readiness_decision"] == "eligible"\n    assert payload["next_action"] == "roadmap_v8_step8_measure_active_sealed_v8_once"',
    'assert payload["step7_sealed_rotation"]["summary"]["readiness_decision"] == "eligible"\n    assert payload["step8_sealed_measurement"]["passed_minimum"] is False\n    assert payload["step8_sealed_measurement"]["critical_signal_miss_gate_met"] is True\n    assert payload["step8_sealed_measurement"]["measurements"]["error_count"] == 14\n    assert payload["next_action"] == "roadmap_v9_step1_post_v8_measurement_taxonomy"',
)
text = text.replace(
    'assert "step7_sealed_rotation_completed" in completed.stdout',
    'assert "step8_sealed_v8_measurement_completed" in completed.stdout',
)
text = text.replace(
    'assert "| 8 | sealed_v8_one_time_measurement | `build\\\\pattern_language_sealed_v8_measurement_report.json` | next |" in roadmap',
    'assert "| 8 | sealed_v8_one_time_measurement | `build\\\\pattern_language_sealed_v8_measurement_report.json` | completed |" in roadmap',
)
path.write_text(text, encoding='utf-8', newline='\n')

path = Path('tests/test_v8_sealed_rotation.py')
text = path.read_text(encoding='utf-8')
text = text.replace('def test_v8_sealed_fixture_is_active_unopened_successor_contract() -> None:', 'def test_v8_sealed_fixture_successor_contract() -> None:')
text = text.replace(
    '    assert active == [SEALED_V8_PATH.name]\n',
    '    assert active == []\n',
)
text = text.replace(
    '    assert fixtures[SEALED_V8_PATH.name]["status"] == "active"\n    assert fixtures[SEALED_V8_PATH.name]["measured"] is False\n    assert fixtures[SEALED_V8_PATH.name]["reviewed"] is False\n',
    '    assert fixtures[SEALED_V8_PATH.name]["status"] == "consumed"\n    assert fixtures[SEALED_V8_PATH.name]["measured"] is True\n    assert fixtures[SEALED_V8_PATH.name]["reviewed"] is False\n    assert fixtures[SEALED_V8_PATH.name]["measurement_report"] == r"build\\pattern_language_sealed_v8_measurement_report.json"\n',
)
text = text.replace(
    'def test_v8_rotation_readiness_and_docs_point_to_step8_measurement() -> None:',
    'def test_v8_rotation_docs_preserved_after_step8_measurement() -> None:',
)
text = text.replace(
    '    assert readiness["decision"] == "eligible"\n    assert readiness["sealed_fixture_opened"] is False\n    assert readiness["sealed_fixture"]["registry_name"] == SEALED_V8_PATH.name\n    assert readiness["blocked_reasons"] == []\n    assert readiness["next_action"] == "measure_active_sealed_once"\n',
    '    assert readiness["decision"] == "blocked"\n    assert readiness["sealed_fixture_opened"] is False\n    assert readiness["sealed_fixture"] is None\n    assert readiness["blocked_reasons"] == ["sealed_fixture_not_available"]\n    assert readiness["next_action"] == "continue_accumulation_or_rotate_fixture"\n',
)
text = text.replace(
    '    assert targets["status"] == "step7_sealed_rotation_completed_step8_measurement_next"\n    assert targets["next_action"] == "roadmap_v8_step8_measure_active_sealed_v8_once"\n    assert targets["step7_sealed_rotation"]["summary"]["readiness_decision"] == "eligible"\n',
    '    assert targets["status"] == "step8_sealed_v8_measurement_completed_v9_rotation_required"\n    assert targets["next_action"] == "roadmap_v9_step1_post_v8_measurement_taxonomy"\n    assert targets["step7_sealed_rotation"]["summary"]["readiness_decision"] == "eligible"\n    assert targets["step8_sealed_measurement"]["passed_minimum"] is False\n',
)
text = text.replace(
    'assert "| 8 | sealed_v8_one_time_measurement | `build\\\\pattern_language_sealed_v8_measurement_report.json` | next |" in roadmap',
    'assert "| 8 | sealed_v8_one_time_measurement | `build\\\\pattern_language_sealed_v8_measurement_report.json` | completed |" in roadmap',
)
path.write_text(text, encoding='utf-8', newline='\n')

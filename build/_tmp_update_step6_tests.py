from pathlib import Path

# conversation accumulation readiness: v6 consumed, no active sealed
path = Path('tests/test_conversation_accumulation.py')
text = path.read_text(encoding='utf-8')
old = '''def test_active_plm_measurement_review_is_eligible_after_v6_rotation() -> None:
    review = json.loads(
        ACTIVE_READINESS_REVIEW_PATH.read_text(encoding="utf-8")
    )

    assert review["decision"] == "eligible"
    assert review["sealed_fixture_opened"] is False
    assert review["sealed_fixture"]["registry_name"] == "pattern_language_sealed_v6.json"
    assert review["sealed_fixture"]["status"] == "active"
    assert review["sealed_fixture"]["measured"] is False
    assert review["sealed_fixture"]["reviewed"] is False
    assert review["readiness"]["end_to_end_route_accuracy"] >= 0.9
    assert review["readiness"]["critical_underprocessing"] == 0
    assert review["blocked_reasons"] == []
'''
new = '''def test_active_plm_measurement_review_blocks_after_v6_consumption() -> None:
    review = json.loads(
        ACTIVE_READINESS_REVIEW_PATH.read_text(encoding="utf-8")
    )

    assert review["decision"] == "blocked"
    assert review["sealed_fixture_opened"] is False
    assert review["sealed_fixture"] is None
    assert review["readiness"]["end_to_end_route_accuracy"] >= 0.9
    assert review["readiness"]["critical_underprocessing"] == 0
    assert review["blocked_reasons"] == ["sealed_fixture_not_available"]
'''
if old not in text:
    raise SystemExit('conversation readiness block not found')
path.write_text(text.replace(old, new), encoding='utf-8', newline='\n')

# v4 historical test: current registry has no active sealed after v6 measurement.
path = Path('tests/test_v4_candidate_eval_and_rotation.py')
text = path.read_text(encoding='utf-8')
text = text.replace('    assert active == ["pattern_language_sealed_v6.json"]\n', '    assert active == []\n')
text = text.replace('    assert fixtures["pattern_language_sealed_v6.json"]["status"] == "active"\n    assert fixtures["pattern_language_sealed_v6.json"]["measured"] is False\n    assert fixtures["pattern_language_sealed_v6.json"]["reviewed"] is False\n', '    assert fixtures["pattern_language_sealed_v6.json"]["status"] == "consumed"\n    assert fixtures["pattern_language_sealed_v6.json"]["measured"] is True\n    assert fixtures["pattern_language_sealed_v6.json"]["reviewed"] is False\n    assert fixtures["pattern_language_sealed_v6.json"]["measurement_report"] == r"build\\pattern_language_sealed_v6_measurement_report.json"\n')
old = '''    assert readiness["decision"] == "eligible"
    assert readiness["sealed_fixture_opened"] is False
    assert readiness["sealed_fixture"]["registry_name"] == "pattern_language_sealed_v6.json"
    assert readiness["sealed_fixture"]["status"] == "active"
    assert readiness["sealed_fixture"]["measured"] is False
    assert readiness["sealed_fixture"]["reviewed"] is False
    assert readiness["blocked_reasons"] == []
'''
new = '''    assert readiness["decision"] == "blocked"
    assert readiness["sealed_fixture_opened"] is False
    assert readiness["sealed_fixture"] is None
    assert readiness["blocked_reasons"] == ["sealed_fixture_not_available"]
'''
if old not in text:
    raise SystemExit('v4 readiness block not found')
path.write_text(text.replace(old, new), encoding='utf-8', newline='\n')

# v5 historical test: v6 is now consumed and readiness is blocked.
path = Path('tests/test_v5_sealed_rotation.py')
text = path.read_text(encoding='utf-8')
text = text.replace('    assert active == ["pattern_language_sealed_v6.json"]\n', '    assert active == []\n')
text = text.replace('    assert fixtures["pattern_language_sealed_v6.json"]["status"] == "active"\n    assert fixtures["pattern_language_sealed_v6.json"]["measured"] is False\n    assert fixtures["pattern_language_sealed_v6.json"]["reviewed"] is False\n', '    assert fixtures["pattern_language_sealed_v6.json"]["status"] == "consumed"\n    assert fixtures["pattern_language_sealed_v6.json"]["measured"] is True\n    assert fixtures["pattern_language_sealed_v6.json"]["reviewed"] is False\n    assert fixtures["pattern_language_sealed_v6.json"]["measurement_report"] == r"build\\pattern_language_sealed_v6_measurement_report.json"\n')
old = '''    assert readiness["decision"] == "eligible"
    assert readiness["sealed_fixture_opened"] is False
    assert readiness["sealed_fixture"]["registry_name"] == "pattern_language_sealed_v6.json"
    assert readiness["sealed_fixture"]["status"] == "active"
    assert readiness["sealed_fixture"]["measured"] is False
    assert readiness["sealed_fixture"]["reviewed"] is False
    assert readiness["blocked_reasons"] == []
'''
new = '''    assert readiness["decision"] == "blocked"
    assert readiness["sealed_fixture_opened"] is False
    assert readiness["sealed_fixture"] is None
    assert readiness["blocked_reasons"] == ["sealed_fixture_not_available"]
'''
if old not in text:
    raise SystemExit('v5 readiness block not found')
path.write_text(text.replace(old, new), encoding='utf-8', newline='\n')

# v6 rotation test: rotation report remains pre-measurement, registry is current post-measurement.
path = Path('tests/test_v6_sealed_rotation.py')
text = path.read_text(encoding='utf-8')
text = text.replace('def test_v6_rotation_report_and_registry_record_active_unmeasured_fixture() -> None:', 'def test_v6_rotation_report_records_pre_measurement_activation_and_registry_is_consumed() -> None:')
text = text.replace('    assert active == [SEALED_V6_PATH.name]\n', '    assert active == []\n')
text = text.replace('    assert fixtures[SEALED_V6_PATH.name]["status"] == "active"\n    assert fixtures[SEALED_V6_PATH.name]["measured"] is False\n    assert fixtures[SEALED_V6_PATH.name]["reviewed"] is False\n', '    assert fixtures[SEALED_V6_PATH.name]["status"] == "consumed"\n    assert fixtures[SEALED_V6_PATH.name]["measured"] is True\n    assert fixtures[SEALED_V6_PATH.name]["reviewed"] is False\n    assert fixtures[SEALED_V6_PATH.name]["measurement_report"] == r"build\\pattern_language_sealed_v6_measurement_report.json"\n')
text = text.replace('def test_v6_rotation_refreshes_readiness_and_docs() -> None:', 'def test_v6_measurement_consumes_readiness_and_docs() -> None:')
old = '''    assert readiness["decision"] == "eligible"
    assert readiness["sealed_fixture_opened"] is False
    assert readiness["sealed_fixture"]["registry_name"] == SEALED_V6_PATH.name
    assert readiness["sealed_fixture"]["status"] == "active"
    assert readiness["sealed_fixture"]["measured"] is False
    assert readiness["blocked_reasons"] == []
'''
new = '''    assert readiness["decision"] == "blocked"
    assert readiness["sealed_fixture_opened"] is False
    assert readiness["sealed_fixture"] is None
    assert readiness["blocked_reasons"] == ["sealed_fixture_not_available"]
'''
if old not in text:
    raise SystemExit('v6 readiness block not found')
text = text.replace(old, new)
text = text.replace('    assert "| 6 | sealed_v6_one_time_measurement | `build\\pattern_language_sealed_v6_measurement_report.json` | next |" in roadmap\n', '    assert "| 6 | sealed_v6_one_time_measurement | `build\\pattern_language_sealed_v6_measurement_report.json` | completed |" in roadmap\n    assert "| 7 | post_v6_measurement_taxonomy | `build\\v7_targets_and_roadmap_v1.json` | next |" in roadmap\n')
path.write_text(text, encoding='utf-8', newline='\n')

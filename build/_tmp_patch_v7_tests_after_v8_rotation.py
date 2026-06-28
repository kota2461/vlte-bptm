from pathlib import Path
path = Path('tests/test_v7_sealed_rotation.py')
text = path.read_text(encoding='utf-8')
text = text.replace('assert active == []', 'assert active == ["pattern_language_sealed_v8.json"]')
old = '''    assert readiness["decision"] == "blocked"\n    assert readiness["sealed_fixture_opened"] is False\n    assert readiness["sealed_fixture"] is None\n    assert readiness["blocked_reasons"] == ["sealed_fixture_not_available"]\n    assert readiness["next_action"] == "continue_accumulation_or_rotate_fixture"\n'''
new = '''    assert readiness["decision"] == "eligible"\n    assert readiness["sealed_fixture_opened"] is False\n    assert readiness["sealed_fixture"]["registry_name"] == "pattern_language_sealed_v8.json"\n    assert readiness["blocked_reasons"] == []\n    assert readiness["next_action"] == "measure_active_sealed_once"\n'''
if old not in text:
    raise SystemExit('v7 rotation readiness block not found')
text = text.replace(old, new)
path.write_text(text, encoding='utf-8', newline='\n')

path = Path('tests/test_v7_sealed_measurement.py')
text = path.read_text(encoding='utf-8')
old = '''    assert readiness["decision"] == "blocked"\n    assert readiness["sealed_fixture_opened"] is False\n    assert readiness["sealed_fixture"] is None\n    assert readiness["blocked_reasons"] == ["sealed_fixture_not_available"]\n'''
new = '''    assert readiness["decision"] == "eligible"\n    assert readiness["sealed_fixture_opened"] is False\n    assert readiness["sealed_fixture"]["registry_name"] == "pattern_language_sealed_v8.json"\n    assert readiness["blocked_reasons"] == []\n'''
if old not in text:
    raise SystemExit('v7 measurement readiness block not found')
text = text.replace(old, new)
path.write_text(text, encoding='utf-8', newline='\n')

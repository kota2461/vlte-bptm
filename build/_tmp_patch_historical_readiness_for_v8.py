from pathlib import Path

def patch(path_str, replacements):
    path = Path(path_str)
    text = path.read_text(encoding='utf-8')
    for old, new in replacements:
        if old not in text:
            raise SystemExit(f'block not found in {path}: {old[:80]!r}')
        text = text.replace(old, new)
    path.write_text(text, encoding='utf-8', newline='\n')

patch('tests/test_conversation_accumulation.py', [
    ('def test_active_plm_measurement_review_blocks_after_v6_consumption() -> None:', 'def test_active_plm_measurement_review_points_to_active_v8_after_rotation() -> None:'),
    ('    assert review["decision"] == "blocked"\n    assert review["sealed_fixture_opened"] is False\n    assert review["sealed_fixture"] is None\n', '    assert review["decision"] == "eligible"\n    assert review["sealed_fixture_opened"] is False\n    assert review["sealed_fixture"]["registry_name"] == "pattern_language_sealed_v8.json"\n'),
    ('    assert review["blocked_reasons"] == ["sealed_fixture_not_available"]\n', '    assert review["blocked_reasons"] == []\n'),
])

patch('tests/test_v4_candidate_eval_and_rotation.py', [
    ('    assert active == []\n', '    assert active == ["pattern_language_sealed_v8.json"]\n'),
    ('    assert readiness["decision"] == "blocked"\n    assert readiness["sealed_fixture_opened"] is False\n    assert readiness["sealed_fixture"] is None\n    assert readiness["blocked_reasons"] == ["sealed_fixture_not_available"]\n', '    assert readiness["decision"] == "eligible"\n    assert readiness["sealed_fixture_opened"] is False\n    assert readiness["sealed_fixture"]["registry_name"] == "pattern_language_sealed_v8.json"\n    assert readiness["blocked_reasons"] == []\n'),
])

patch('tests/test_v5_sealed_rotation.py', [
    ('    assert active == []\n', '    assert active == ["pattern_language_sealed_v8.json"]\n'),
    ('    assert readiness["decision"] == "blocked"\n    assert readiness["sealed_fixture_opened"] is False\n    assert readiness["sealed_fixture"] is None\n    assert readiness["blocked_reasons"] == ["sealed_fixture_not_available"]\n', '    assert readiness["decision"] == "eligible"\n    assert readiness["sealed_fixture_opened"] is False\n    assert readiness["sealed_fixture"]["registry_name"] == "pattern_language_sealed_v8.json"\n    assert readiness["blocked_reasons"] == []\n'),
])

patch('tests/test_v6_sealed_measurement.py', [
    ('    assert readiness["decision"] == "blocked"\n    assert readiness["sealed_fixture_opened"] is False\n    assert readiness["sealed_fixture"] is None\n    assert readiness["blocked_reasons"] == ["sealed_fixture_not_available"]\n', '    assert readiness["decision"] == "eligible"\n    assert readiness["sealed_fixture_opened"] is False\n    assert readiness["sealed_fixture"]["registry_name"] == "pattern_language_sealed_v8.json"\n    assert readiness["blocked_reasons"] == []\n'),
])

patch('tests/test_v6_sealed_rotation.py', [
    ('    assert active == []\n', '    assert active == ["pattern_language_sealed_v8.json"]\n'),
    ('    assert readiness["decision"] == "blocked"\n    assert readiness["sealed_fixture_opened"] is False\n    assert readiness["sealed_fixture"] is None\n    assert readiness["blocked_reasons"] == ["sealed_fixture_not_available"]\n', '    assert readiness["decision"] == "eligible"\n    assert readiness["sealed_fixture_opened"] is False\n    assert readiness["sealed_fixture"]["registry_name"] == "pattern_language_sealed_v8.json"\n    assert readiness["blocked_reasons"] == []\n'),
])

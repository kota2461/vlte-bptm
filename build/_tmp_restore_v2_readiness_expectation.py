from pathlib import Path
path = Path('tests/test_conversation_accumulation.py')
text = path.read_text(encoding='utf-8')
old = '''def test_v2_measurement_review_blocks_after_sealed_consumption() -> None:\n    review = json.loads(READINESS_REVIEW_PATH.read_text(encoding="utf-8"))\n\n    assert review["decision"] == "blocked"\n    assert review["sealed_fixture_opened"] is False\n    assert review["sealed_fixture"]["status"] == "consumed"\n    assert review["sealed_fixture"]["measured"] is True\n    assert review["sealed_fixture"]["reviewed"] is False\n    assert review["readiness"]["end_to_end_route_accuracy"] >= 0.9\n    assert review["readiness"]["critical_underprocessing"] == 0\n    assert review["blocked_reasons"] == []\n'''
new = '''def test_v2_measurement_review_blocks_after_sealed_consumption() -> None:\n    review = json.loads(READINESS_REVIEW_PATH.read_text(encoding="utf-8"))\n\n    assert review["decision"] == "blocked"\n    assert review["sealed_fixture_opened"] is False\n    assert review["sealed_fixture"]["status"] == "consumed"\n    assert review["sealed_fixture"]["measured"] is True\n    assert review["sealed_fixture"]["reviewed"] is False\n    assert review["readiness"]["end_to_end_route_accuracy"] >= 0.9\n    assert review["readiness"]["critical_underprocessing"] == 0\n    assert review["blocked_reasons"] == ["sealed_fixture_not_available"]\n'''
if old not in text:
    raise SystemExit('v2 block not found')
path.write_text(text.replace(old, new), encoding='utf-8', newline='\n')

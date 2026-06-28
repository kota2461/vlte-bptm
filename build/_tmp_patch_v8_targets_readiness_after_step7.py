from pathlib import Path
path = Path('tests/test_v8_targets_and_roadmap.py')
text = path.read_text(encoding='utf-8')
text = text.replace(
    '"readiness_decision_after_measurement": "blocked",\n        "blocked_reasons": ["sealed_fixture_not_available"],',
    '"readiness_decision_after_measurement": "eligible",\n        "blocked_reasons": [],',
)
path.write_text(text, encoding='utf-8', newline='\n')

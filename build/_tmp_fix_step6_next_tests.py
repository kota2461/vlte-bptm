from pathlib import Path
old = 'assert "| 6 | sealed_v6_one_time_measurement | `build\\\\pattern_language_sealed_v6_measurement_report.json` | next |" in roadmap'
new = 'assert "| 6 | sealed_v6_one_time_measurement | `build\\\\pattern_language_sealed_v6_measurement_report.json` | completed |" in roadmap'
for name in ['tests/test_v6_sealed_rotation_review.py', 'tests/test_v6_sealed_rotation.py']:
    path = Path(name)
    text = path.read_text(encoding='utf-8')
    if old not in text:
        raise SystemExit(f'old line not found in {name}')
    text = text.replace(old, new)
    path.write_text(text, encoding='utf-8', newline='\n')

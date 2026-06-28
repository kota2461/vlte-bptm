from pathlib import Path
for name in ['tests/test_v6_sealed_rotation_review.py', 'tests/test_v6_sealed_rotation.py']:
    path = Path(name)
    text = path.read_text(encoding='utf-8')
    text = text.replace('| 6 | sealed_v6_one_time_measurement | `build\\pattern_language_sealed_v6_measurement_report.json` | next |', '| 6 | sealed_v6_one_time_measurement | `build\\pattern_language_sealed_v6_measurement_report.json` | completed |')
    if '| 7 | post_v6_measurement_taxonomy | `build\\v7_targets_and_roadmap_v1.json` | next |' not in text:
        text = text.replace('    assert "| 6 | sealed_v6_one_time_measurement | `build\\\\pattern_language_sealed_v6_measurement_report.json` | completed |" in roadmap\n', '    assert "| 6 | sealed_v6_one_time_measurement | `build\\\\pattern_language_sealed_v6_measurement_report.json` | completed |" in roadmap\n    assert "| 7 | post_v6_measurement_taxonomy | `build\\\\v7_targets_and_roadmap_v1.json` | next |" in roadmap\n')
    path.write_text(text, encoding='utf-8', newline='\n')

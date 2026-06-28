from pathlib import Path
path = Path('tests/test_v7_targets_and_roadmap.py')
text = path.read_text(encoding='utf-8')
text = text.replace('''    assert "| 2 | v7_nonsealed_curriculum_design | `build\\\\v7_nonsealed_curriculum_plan_v1.json` | next |" in roadmap''', '''    assert "| 2 | v7_nonsealed_curriculum_design | `build\\\\v7_nonsealed_curriculum_plan_v1.json` | completed |" in roadmap''')
path.write_text(text, encoding='utf-8', newline='\n')

from pathlib import Path
path = Path('tests/test_v7_targets_and_roadmap.py')
text = path.read_text(encoding='utf-8')
text = text.replace('''    assert [step["status"] for step in payload["roadmap"][:3]] == [
        "completed",
        "next",
        "pending",
    ]
''', '''    assert [step["status"] for step in payload["roadmap"][:3]] == [
        "completed",
        "next",
        "pending",
    ]
''')
text = text.replace('| 2 | v7_nonsealed_curriculum_design | `build\\v7_nonsealed_curriculum_plan_v1.json` | next |', '| 2 | v7_nonsealed_curriculum_design | `build\\v7_nonsealed_curriculum_plan_v1.json` | completed |')
text = text.replace('    assert "Targets and taxonomy: `build/v7_targets_and_roadmap_v1.json`" in main\n', '    assert "Targets and taxonomy: `build/v7_targets_and_roadmap_v1.json`" in main\n    assert "Curriculum plan: `build/v7_nonsealed_curriculum_plan_v1.json`" in main\n')
path.write_text(text, encoding='utf-8', newline='\n')

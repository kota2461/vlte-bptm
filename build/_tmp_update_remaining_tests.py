from pathlib import Path
path=Path('tests/test_v6_boundary_priority_review_adopted.py')
text=path.read_text(encoding='utf-8')
old='''    assert report["summary"]["by_action"] == {
        "coverage_keep": 12,
        "priority_contrast_negative_review": 1,
        "priority_suppression_review": 12,
        "route_gap_review": 1,
    }
'''
new='''    assert report["summary"]["by_action"] == {
        "coverage_keep": 26,
    }
'''
if old not in text: raise SystemExit('priority by_action block not found')
text=text.replace(old,new,1)
path.write_text(text, encoding='utf-8', newline='\n')

path=Path('tests/test_v6_boundary_debate_candidate_queue_review.py')
text=path.read_text(encoding='utf-8')
text=text.replace('''    assert "v6-boundary-debate-queue-038" in text
    assert "repair-medical-data-design" in text
''','''    assert "## Priority Review Items" in text
    assert "v6-boundary-debate-queue-038" not in text
''')
path.write_text(text, encoding='utf-8', newline='\n')
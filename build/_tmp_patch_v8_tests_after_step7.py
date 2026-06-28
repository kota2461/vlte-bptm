from pathlib import Path
path = Path('tests/test_v8_targets_and_roadmap.py')
text = path.read_text(encoding='utf-8')
text = text.replace(
    'assert payload["status"] == "step6_sealed_rotation_review_completed_step7_rotation_next"',
    'assert payload["status"] == "step7_sealed_rotation_completed_step8_measurement_next"',
)
text = text.replace(
    '        "completed",\n        "next",\n        "pending",',
    '        "completed",\n        "completed",\n        "next",',
)
text = text.replace(
    'assert payload["next_action"] == "roadmap_v8_step7_generate_and_rotate_sealed_v8_fixture"',
    'assert payload["step7_sealed_rotation"]["passed"] is True\n    assert payload["step7_sealed_rotation"]["summary"]["readiness_decision"] == "eligible"\n    assert payload["next_action"] == "roadmap_v8_step8_measure_active_sealed_v8_once"',
)
text = text.replace(
    'assert "step6_sealed_rotation_review_completed" in completed.stdout',
    'assert "step7_sealed_rotation_completed" in completed.stdout',
)
text = text.replace(
    'assert "| 7 | sealed_v8_rotation | `tests\\\\fixtures\\\\pattern_language_sealed_v8.json` | next |" in roadmap',
    'assert "| 7 | sealed_v8_rotation | `tests\\\\fixtures\\\\pattern_language_sealed_v8.json` | completed |" in roadmap\n    assert "| 8 | sealed_v8_one_time_measurement | `build\\\\pattern_language_sealed_v8_measurement_report.json` | next |" in roadmap',
)
path.write_text(text, encoding='utf-8', newline='\n')

path = Path('tests/test_v8_sealed_rotation_review.py')
text = path.read_text(encoding='utf-8')
old = '''def test_v8_rotation_review_docs_targets_and_script_regenerate() -> None:\n    completed = subprocess.run(\n        [sys.executable, "-B", str(SCRIPT_PATH)],\n        cwd=ROOT,\n        check=True,\n        text=True,\n        capture_output=True,\n    )\n\n    assert "eligible_for_fresh_sealed_v8_rotation" in completed.stdout\n    review_md = REVIEW_MD_PATH.read_text(encoding="utf-8")\n    roadmap = ROADMAP_PATH.read_text(encoding="utf-8")\n    main = MAIN_ROADMAP_PATH.read_text(encoding="utf-8")\n    targets = _load(TARGETS_PATH)\n\n    assert "V8 Sealed Rotation Review v1" in review_md\n    assert "eligible_for_fresh_sealed_v8_rotation" in review_md\n    assert targets["status"] == "step6_sealed_rotation_review_completed_step7_rotation_next"\n    assert targets["next_action"] == "roadmap_v8_step7_generate_and_rotate_sealed_v8_fixture"\n    assert targets["step6_sealed_rotation_review"]["passed"] is True\n    assert targets["step6_sealed_rotation_review"]["summary"]["blocker_count"] == 0\n    assert "| 6 | sealed_v8_rotation_review | `build\\\\v8_sealed_rotation_review_v1.json` | completed |" in roadmap\n    assert "| 7 | sealed_v8_rotation | `tests\\\\fixtures\\\\pattern_language_sealed_v8.json` | next |" in roadmap\n    assert "Sealed v8 rotation review: `build/v8_sealed_rotation_review_v1.json`" in main\n'''
new = '''def test_v8_rotation_review_docs_and_targets_are_preserved_after_step7() -> None:\n    review_md = REVIEW_MD_PATH.read_text(encoding="utf-8")\n    roadmap = ROADMAP_PATH.read_text(encoding="utf-8")\n    main = MAIN_ROADMAP_PATH.read_text(encoding="utf-8")\n    targets = _load(TARGETS_PATH)\n\n    assert "V8 Sealed Rotation Review v1" in review_md\n    assert "eligible_for_fresh_sealed_v8_rotation" in review_md\n    assert targets["step6_sealed_rotation_review"]["passed"] is True\n    assert targets["step6_sealed_rotation_review"]["summary"]["blocker_count"] == 0\n    assert targets["step7_sealed_rotation"]["passed"] is True\n    assert "| 6 | sealed_v8_rotation_review | `build\\\\v8_sealed_rotation_review_v1.json` | completed |" in roadmap\n    assert "| 7 | sealed_v8_rotation | `tests\\\\fixtures\\\\pattern_language_sealed_v8.json` | completed |" in roadmap\n    assert "Sealed v8 rotation review: `build/v8_sealed_rotation_review_v1.json`" in main\n    assert "Sealed v8 rotation report: `build/v8_sealed_rotation_report_v1.json`" in main\n'''
if old not in text:
    raise SystemExit('review test block not found')
text = text.replace(old, new)
# remove now-unused imports
text = text.replace('import subprocess\nimport sys\n', '')
text = text.replace('SCRIPT_PATH = ROOT / "build" / "review_v8_sealed_rotation.py"\n', '')
path.write_text(text, encoding='utf-8', newline='\n')

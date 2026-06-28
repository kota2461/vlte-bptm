from pathlib import Path
path = Path('tests/test_v8_targets_and_roadmap.py')
text = path.read_text(encoding='utf-8')
text = text.replace(
    'assert "step5_v8_nonsealed_replay_gate_passed" in completed.stdout',
    'assert "step6_sealed_rotation_review_completed" in completed.stdout',
)
path.write_text(text, encoding='utf-8', newline='\n')

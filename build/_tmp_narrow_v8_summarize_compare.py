from pathlib import Path

p = Path('semantic_routing/baseline.py')
s = p.read_text(encoding='utf-8')
old = '''    if v8["force_explore"]:
        scores["explore"] = min(0.98, max(scores.get("explore", 0.0), 0.95))
'''
if old not in s:
    raise SystemExit('force_explore block not found')
s = s.replace(old, '', 1)
p.write_text(s, encoding='utf-8', newline='\n')

p = Path('build/replay_v8_recovery_priority_review_candidates.py')
s = p.read_text(encoding='utf-8')
old = '''        "expected": expected("explore", ["explore", "summarize", "compare"], multiple=True, formats=["table"]),'''
new = '''        "expected": expected("summarize", ["summarize", "compare"], multiple=True, formats=["table"]),'''
if old not in s:
    raise SystemExit('V8 summarize-compare expected not found')
s = s.replace(old, new, 1)
p.write_text(s, encoding='utf-8', newline='\n')

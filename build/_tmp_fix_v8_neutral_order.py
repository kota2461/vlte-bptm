from pathlib import Path
p = Path('semantic_routing/baseline.py')
s = p.read_text(encoding='utf-8')
old = '''    if v8["preserve_neutrality"] and "preserve_neutrality" not in must:
        must.append("preserve_neutrality")'''
new = '''    if v8["preserve_neutrality"] and "preserve_neutrality" not in must:
        must.insert(0, "preserve_neutrality")'''
if old not in s:
    raise SystemExit('target not found')
p.write_text(s.replace(old, new, 1), encoding='utf-8', newline='\n')

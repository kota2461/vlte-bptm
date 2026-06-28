from pathlib import Path
path=Path('semantic_routing/baseline.py')
text=path.read_text(encoding='utf-8')
old = r"r'[^\x00-\x7f].*\b(?:README|CSV|PowerShell)\b|\b(?:README|CSV|PowerShell)\b.*[^\x00-\x7f]'"
new = r"r'[^\x00-\x7f].*(?:README|CSV|PowerShell)|(?:README|CSV|PowerShell).*[^\x00-\x7f]'"
if old not in text:
    raise SystemExit('garbled pattern not found')
text=text.replace(old,new,1)
path.write_text(text, encoding='utf-8', newline='\n')
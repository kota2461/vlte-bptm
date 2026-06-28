from pathlib import Path
text = Path('semantic_routing/baseline.py').read_text(encoding='utf-8')
idx = text.find('suppress_ai = bool(')
print(repr(text[idx:idx+180]))
print(text[idx:idx+180])
from pathlib import Path
text = Path('semantic_routing/baseline.py').read_text(encoding='utf-8')
old = '''        groups["ai_label_or_word"]
        or groups["structural_build_request"]'''
print(old in text)
print(text.find(old))
for i, ch in enumerate(old):
    if i < 20:
        print(i, repr(ch), ord(ch))
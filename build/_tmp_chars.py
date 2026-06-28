from pathlib import Path
text=Path('semantic_routing/baseline.py').read_text(encoding='utf-8')
idx=text.find('groups["ai_label_or_word"]')
sub=text[idx-8:idx+70]
print(repr(sub))
for i,ch in enumerate(sub):
    print(i, repr(ch), ord(ch))
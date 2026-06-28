from pathlib import Path
text = Path('semantic_routing/baseline.py').read_text(encoding='utf-8')
patterns = [
'''        ),        "neutrality_word_use": _any_regex_evidence(\n''',
'''        groups["ai_label_or_word"]\n        or groups["structural_build_request"]''',
]
for p in patterns:
    print('contains', p[:40].replace('\n','\\n'), p in text)
    if p not in text:
        idx = text.find('groups["ai_label_or_word"]')
        print('idx', idx, repr(text[idx-60:idx+120]))
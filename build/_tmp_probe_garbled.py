import json, sys
from pathlib import Path
sys.path.insert(0, str(Path('.').resolve()))
from semantic_routing import route

data=json.loads(Path('tests/fixtures/v6_contrast_negative_benchmark_v1.json').read_text(encoding='utf-8'))
for case in data['cases']:
    if case['id'] in {'v6-contrast-negative-004','v6-contrast-negative-010','v6-contrast-negative-014','v6-contrast-negative-026'}:
        actual=route(case['input']).packet.as_dict()
        print(case['id'], case['input'])
        print(actual['intent_candidates'][:3], actual['operations'], actual['information_state'], actual['risk'])
        print([e['signal'] for e in actual['evidence']])
        print()
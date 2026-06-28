import json, sys
from pathlib import Path
sys.path.insert(0, str(Path('.').resolve()))
from semantic_routing import route

data=json.loads(Path('tests/fixtures/v6_contrast_negative_benchmark_v1.json').read_text(encoding='utf-8'))
for case in data['cases']:
    expected=case['expected']
    actual=route(case['input']).packet.as_dict()
    actual['primary_intent']=actual['intent_candidates'][0]['intent']
    fields=[]
    for field in ['operations','information_state','constraints','risk']:
        if actual[field] != expected[field]:
            fields.append(field)
    if actual['primary_intent'] != expected['primary_intent']:
        fields.insert(0,'primary_intent')
    if fields:
        print(case['id'], case['contrast_group'], fields)
        print(case['input'])
        print('EXP', expected['primary_intent'], expected['operations'], expected['constraints'], expected['risk'])
        print('ACT', actual['primary_intent'], actual['operations'], actual['constraints'], actual['risk'], actual['information_state'])
        print([e['signal'] for e in actual['evidence']])
        print()
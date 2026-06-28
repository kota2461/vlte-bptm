import json
from pathlib import Path
for cid in ['v6-contrast-negative-005','v6-contrast-negative-012','v6-contrast-negative-020','v6-contrast-negative-023','v6-contrast-negative-029']:
    for case in json.loads(Path('tests/fixtures/v6_contrast_negative_benchmark_v1.json').read_text(encoding='utf-8'))['cases']:
        if case['id']==cid:
            print(cid, case['contrast_group'], case['input'].encode('unicode_escape').decode())
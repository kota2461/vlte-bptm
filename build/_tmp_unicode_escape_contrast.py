import json
from pathlib import Path
for cid in ['v6-contrast-negative-003','v6-contrast-negative-011','v6-contrast-negative-016','v6-contrast-negative-024','v6-contrast-negative-027','v6-contrast-negative-028','v6-contrast-negative-030']:
    for case in json.loads(Path('tests/fixtures/v6_contrast_negative_benchmark_v1.json').read_text(encoding='utf-8'))['cases']:
        if case['id']==cid:
            print(cid, case['contrast_group'], case['input'].encode('unicode_escape').decode())
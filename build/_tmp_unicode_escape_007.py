import json
from pathlib import Path
for case in json.loads(Path('tests/fixtures/v6_contrast_negative_benchmark_v1.json').read_text(encoding='utf-8'))['cases']:
    if case['id']=='v6-contrast-negative-007':
        print(case['input'].encode('unicode_escape').decode())
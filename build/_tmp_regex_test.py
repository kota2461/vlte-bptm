import re,json
from pathlib import Path
pat = r'[^\x00-\x7f].*\b(?:README|CSV|PowerShell)\b|\b(?:README|CSV|PowerShell)\b.*[^\x00-\x7f]'
for case in json.loads(Path('tests/fixtures/v6_contrast_negative_benchmark_v1.json').read_text(encoding='utf-8'))['cases']:
    if case['id'] in {'v6-contrast-negative-004','v6-contrast-negative-010','v6-contrast-negative-014','v6-contrast-negative-026'}:
        print(case['id'], bool(re.search(pat, case['input'], re.I)), repr(case['input']))
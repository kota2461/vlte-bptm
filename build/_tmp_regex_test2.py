import re,json
from pathlib import Path
pat = r'[^\x00-\x7f].*\b(?:README|CSV|PowerShell)\b|\b(?:README|CSV|PowerShell)\b.*[^\x00-\x7f]'
pat2 = r'[^\x00-\x7f]'
pat3 = '[^\x00-\x7f].*\\b(?:README|CSV|PowerShell)\\b|\\b(?:README|CSV|PowerShell)\\b.*[^\x00-\x7f]'
print('pat repr', pat)
print('pat3 repr', pat3)
for case in json.loads(Path('tests/fixtures/v6_contrast_negative_benchmark_v1.json').read_text(encoding='utf-8'))['cases']:
    if case['id']=='v6-contrast-negative-004':
        s=case['input']
        print('nonascii', bool(re.search('[^\x00-\x7f]', s)))
        print('README', bool(re.search(r'\bREADME\b', s)))
        print('combo', bool(re.search('[^\x00-\x7f].*\\bREADME\\b', s)))
        print('combo2', bool(re.search(pat3, s)))
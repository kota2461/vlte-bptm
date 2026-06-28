import json
from pathlib import Path
report=json.loads(Path('build/v6_score_report_v1.json').read_text(encoding='utf-8'))
for name in ['v6_boundary_priority_review_adopted','v6_contrast_negative']:
    lane=report['lanes'][name]
    print(name, lane['score'], lane['raw_score'], lane['measurement'])
    for e in lane['errors']:
        print(e)
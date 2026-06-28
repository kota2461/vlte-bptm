import json
from pathlib import Path
report=json.loads(Path('build/v6_boundary_debate_candidate_queue_review_v1.json').read_text(encoding='utf-8'))
for id_ in ['v6-boundary-debate-queue-038','v6-boundary-debate-queue-034','v6-boundary-debate-queue-048','v6-boundary-debate-queue-039','v6-boundary-debate-queue-017','v6-boundary-debate-queue-018']:
    item=next(i for i in report['items'] if i['id']==id_)
    print(id_, item['source_topic_id'], item['action'], item['priority_score'], item['fields'])
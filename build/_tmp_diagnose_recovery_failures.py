import json
from pathlib import Path

import sys
ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT))
from semantic_routing import route
from semantic_routing.semantic_packet import request_digest
from semantic_routing.baseline_snapshot import LEGACY_PACKET_BY_DIGEST

def load(rel):
    return json.loads((ROOT / rel).read_text(encoding='utf-8'))

print('snapshot_count', len(LEGACY_PACKET_BY_DIGEST))

report = load('build/critical_constraints_candidates_v1.json')
cc_misses = []
for cand in report['candidates']:
    packet = route(cand['input']).packet.as_dict()
    exp = cand['draft_expected']
    actual_primary = packet['intent_candidates'][0]['intent']
    diffs = []
    if actual_primary != exp['primary_intent']:
        diffs.append('primary_intent')
    for k in ('operations','information_state','constraints','risk'):
        if packet[k] != exp[k]:
            diffs.append(k)
    if diffs:
        actual_primary = packet['intent_candidates'][0]['intent']
        cc_misses.append((cand.get('id'), request_digest(cand['input']) in LEGACY_PACKET_BY_DIGEST, diffs, actual_primary, packet['operations'], exp['primary_intent'], exp['operations'], cand['input'][:100]))
print('critical_constraints_misses', len(cc_misses))
for row in cc_misses[:20]:
    print(row)

fixture = load('tests/fixtures/v4_failure_memory_fixture_v1.json')
v4 = []
for item in fixture['items']:
    result = route(item['input'])
    guard = set(result.trace['failure_guard']['guard_actions'])
    expected = set(item['guard_action'])
    if not expected <= guard:
        v4.append((item['source_candidate_id'], request_digest(item['input']) in LEGACY_PACKET_BY_DIGEST, sorted(expected - guard), result.packet.risk.as_dict(), result.packet.as_dict()['information_state'], result.packet.operations, item['input'][:100]))
print('v4_guard_misses', len(v4))
for row in v4:
    print(row)

# report summaries currently on disk
for rel in [
    'build/v6_boundary_debate_candidate_queue_review_v1.json',
    'build/v6_boundary_priority_review_adopted_replay_report_v1.json',
    'build/v7_router_debate_candidate_selection_v1.json',
    'build/v7_router_debate_candidate_probe_report_v1.json',
    'build/v7_targets_and_roadmap_v1.json',
]:
    p = load(rel)
    print(rel, p.get('status'), p.get('summary') or {k:p.get(k) for k in ('step4_router_generalization','status','next_action')})
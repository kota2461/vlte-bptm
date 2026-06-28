import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path('D:/Thought State Register')
source_path = ROOT / 'build' / 'router_debate_v6_facilitated_contrast_repair.json'
report_path = ROOT / 'build' / 'router_debate_v6_facilitated_contrast_repair_review_v1.json'
worksheet_path = ROOT / 'build' / 'router_debate_v6_facilitated_contrast_repair_review_v1.md'
source = json.loads(source_path.read_text(encoding='utf-8'))
markers = {
    'classification_rule': ['classification_rule', 'classification rule'],
    'should_fire_examples': ['should_fire_examples', 'should fire', 'should-fire'],
    'should_not_fire_examples': ['should_not_fire_examples', 'should not fire', 'should-not-fire'],
    'boundary_cases': ['boundary_cases', 'boundary cases'],
    'candidate_sample_notes': ['candidate_sample_notes', 'candidate sample'],
}
finish_counts = Counter()
via_counts = Counter()
role_counts = Counter()
rule_counts = Counter()
weak_counts = Counter()
section_coverage = Counter()
topic_reviews = []
for topic in source.get('topics', []):
    turns = topic.get('turns', [])
    events = topic.get('moderation_events', [])
    topic_finish = Counter(str(turn.get('finish_reason')) for turn in turns)
    topic_via = Counter(str(turn.get('via')) for turn in turns)
    finish_counts.update(topic_finish)
    via_counts.update(topic_via)
    role_counts.update(str(turn.get('role')) for turn in turns)
    combined = '\n'.join(turn.get('content', '') for turn in turns).lower()
    hits = {name: any(marker in combined for marker in names) for name, names in markers.items()}
    for name, hit in hits.items():
        if hit:
            section_coverage[name] += 1
    matched_rules = Counter()
    weak_metrics = Counter()
    comments = []
    for event in events:
        comment = event.get('moderator_comment') or {}
        matched_rules.update(comment.get('matched_rule_ids') or [])
        weak_metrics.update(comment.get('weak_metrics') or [])
        if comment.get('comment'):
            comments.append(comment['comment'])
    rule_counts.update(matched_rules)
    weak_counts.update(weak_metrics)
    reasoning_chars = sum(turn.get('reasoning_content_chars', 0) for turn in turns)
    length_finish = topic_finish.get('length', 0)
    status = 'candidate_ready'
    cautions = []
    if length_finish:
        status = 'candidate_ready_with_caution'
        cautions.append('one_turn_hit_length_finish')
    if reasoning_chars:
        status = 'hold_quality_issue'
        cautions.append('reasoning_content_present')
    if not all(turn.get('via') == 'content' for turn in turns):
        status = 'hold_quality_issue'
        cautions.append('non_content_turn_present')
    if not all(hits.values()):
        cautions.append('missing_required_output_section_marker')
    topic_reviews.append({
        'topic_id': topic.get('topic_id'),
        'status': status,
        'turn_count': len(turns),
        'moderation_event_count': len(events),
        'final_decision': topic.get('router_decision', {}).get('decision'),
        'finish_reasons': dict(sorted(topic_finish.items())),
        'via_counts': dict(sorted(topic_via.items())),
        'reasoning_content_chars': reasoning_chars,
        'section_hits': hits,
        'moderator_matched_rules': dict(sorted(matched_rules.items())),
        'moderator_weak_metrics': dict(sorted(weak_metrics.items())),
        'cautions': cautions,
        'recommended_use': 'append_candidate_queue_review_evidence' if status.startswith('candidate_ready') else 'hold',
    })

summary = {
    'topic_count': source.get('summary', {}).get('topic_count'),
    'turn_count': source.get('summary', {}).get('turn_count'),
    'closed_topic_count': source.get('summary', {}).get('closed_topic_count'),
    'moderator_comment_count': source.get('summary', {}).get('moderator_comment_count'),
    'role_counts': dict(sorted(role_counts.items())),
    'via_counts': dict(sorted(via_counts.items())),
    'finish_reason_counts': dict(sorted(finish_counts.items())),
    'hidden_reasoning_content_chars': sum(item['reasoning_content_chars'] for item in topic_reviews),
    'length_finish_topic_ids': [item['topic_id'] for item in topic_reviews if item['finish_reasons'].get('length')],
    'candidate_ready_count': sum(1 for item in topic_reviews if item['status'] == 'candidate_ready'),
    'candidate_ready_with_caution_count': sum(1 for item in topic_reviews if item['status'] == 'candidate_ready_with_caution'),
    'hold_quality_issue_count': sum(1 for item in topic_reviews if item['status'] == 'hold_quality_issue'),
    'section_coverage': dict(sorted(section_coverage.items())),
    'moderator_matched_rules': dict(sorted(rule_counts.items())),
    'moderator_weak_metrics': dict(sorted(weak_counts.items())),
}
report = {
    'schema_version': 'router-debate-facilitated-log-review.v1',
    'generated_at': datetime.now(timezone.utc).isoformat(),
    'status': 'review_ready',
    'source_log': 'build/router_debate_v6_facilitated_contrast_repair.json',
    'policy': {
        'raw_debate_logs_direct_training_allowed': False,
        'llm_turn_text_direct_training_allowed': False,
        'candidate_queue_use_requires_synthesis_and_human_review': True,
        'sealed_fixtures_used_as_sources': False,
        'review_measurement_is_gate': False,
    },
    'summary': summary,
    'topics': topic_reviews,
    'recommendation': {
        'overall': 'use_as_candidate_queue_review_evidence',
        'notes': [
            'Facilitator comments fired on every moderation event and targeted measured weak fields.',
            'All turns returned final content and hidden reasoning chars are zero.',
            'Rerun repair-creative-emotion-word-use if a perfectly clean no-length log is needed.',
        ],
    },
}
report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')
lines = [
    '# Router Debate V6 Facilitated Contrast Repair Review v1',
    '',
    f"- source_log: {report['source_log']}",
    f"- topic_count: {summary['topic_count']}",
    f"- turn_count: {summary['turn_count']}",
    f"- closed_topic_count: {summary['closed_topic_count']}",
    f"- moderator_comment_count: {summary['moderator_comment_count']}",
    f"- finish_reason_counts: {summary['finish_reason_counts']}",
    f"- hidden_reasoning_content_chars: {summary['hidden_reasoning_content_chars']}",
    f"- candidate_ready_count: {summary['candidate_ready_count']}",
    f"- candidate_ready_with_caution_count: {summary['candidate_ready_with_caution_count']}",
    '',
    '## Topics',
    '',
    '| topic | status | turns | finish | section hits | moderator rules | cautions |',
    '| --- | --- | ---: | --- | --- | --- | --- |',
]
for item in topic_reviews:
    hits = ','.join(name for name, hit in item['section_hits'].items() if hit)
    rules = ','.join(item['moderator_matched_rules'])
    cautions = ','.join(item['cautions'])
    lines.append(f"| {item['topic_id']} | {item['status']} | {item['turn_count']} | {item['finish_reasons']} | {hits} | {rules} | {cautions} |")
lines.extend([
    '',
    '## Recommendation',
    '',
    '- Use these logs as review evidence for candidate synthesis; do not train directly on raw turns.',
    '- The first two topics are clean candidate-ready evidence.',
    '- The creative-emotion topic is useful but has one length-finished critic turn; rerun if strict cleanliness is needed.',
])
worksheet_path.write_text('\n'.join(lines) + '\n', encoding='utf-8', newline='\n')
print(json.dumps({'status': report['status'], 'report': str(report_path.relative_to(ROOT)), 'worksheet': str(worksheet_path.relative_to(ROOT)), 'summary': summary}, ensure_ascii=False, indent=2))
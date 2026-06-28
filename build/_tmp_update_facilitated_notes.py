import json
from pathlib import Path

ROOT = Path(r'D:\Thought State Register')
review_path = ROOT / 'build' / 'router_debate_v6_facilitated_contrast_repair_review_v1.json'
review_md_path = ROOT / 'build' / 'router_debate_v6_facilitated_contrast_repair_review_v1.md'
compare_path = ROOT / 'build' / 'router_debate_v6_facilitated_score_comparison_v1.json'
compare_md_path = ROOT / 'build' / 'router_debate_v6_facilitated_score_comparison_v1.md'

review = json.loads(review_path.read_text(encoding='utf-8'))
summary = review['summary']
if summary.get('candidate_ready_count') == summary.get('topic_count') and not summary.get('length_finish_topic_ids'):
    notes = [
        'All three facilitated topics are clean candidate-ready review evidence.',
        'All turns returned final content, all finish reasons are stop, and hidden reasoning chars are zero.',
        'Use these logs as review evidence for candidate synthesis; do not train directly on raw turns.',
    ]
else:
    notes = [
        'Use these logs as review evidence for candidate synthesis; do not train directly on raw turns.',
        'Some topics have caution markers; rerun caution topics if strict cleanliness is required.',
    ]
review['recommendation']['notes'] = notes
review_path.write_text(json.dumps(review, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')
lines = [
    '# Router Debate V6 Facilitated Contrast Repair Review v1',
    '',
    f"- source_log: {review['source_log']}",
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
for item in review['topics']:
    hits = ','.join(name for name, hit in item['section_hits'].items() if hit)
    rules = ','.join(item['moderator_matched_rules'])
    cautions = ','.join(item['cautions'])
    lines.append(f"| {item['topic_id']} | {item['status']} | {item['turn_count']} | {item['finish_reasons']} | {hits} | {rules} | {cautions} |")
lines.extend(['', '## Recommendation', ''])
lines.extend(f'- {note}' for note in notes)
review_md_path.write_text('\n'.join(lines) + '\n', encoding='utf-8', newline='\n')

compare = json.loads(compare_path.read_text(encoding='utf-8'))
scenarios = compare['scenarios']
lines = [
    '# Router Debate V6 Facilitated Score Comparison v1',
    '',
    '| scenario | cases | score | raw | errors | intent | operation | constraint | risk |',
    '| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |',
]
for name in ['clean_only_excluding_rerun_recommended', 'with_caution_item_included', 'official_adopted_priority_review_lane']:
    scenario = scenarios[name]
    m = scenario['measurement']
    lines.append(
        f"| {name} | {m['case_count']} | {scenario['score']:.6f} | {scenario['raw_score']:.6f} | {m['error_count']} | "
        f"{m['intent_accuracy']:.6f} | {m['operation_exact_match']:.6f} | {m['constraint_exact_match']:.6f} | {m['risk_exact_match']:.6f} |"
    )
lines.extend([
    '',
    '## Deltas',
    '',
    f"- clean_vs_official_score_delta: {compare['comparison']['clean_vs_official_score_delta']:+.6f}",
    f"- included_vs_clean_score_delta: {compare['comparison']['included_vs_clean_score_delta']:+.6f}",
    f"- included_vs_official_score_delta: {compare['comparison']['included_vs_official_score_delta']:+.6f}",
    '',
    '## Notes',
    '',
])
if scenarios['clean_only_excluding_rerun_recommended']['measurement']['case_count'] == scenarios['with_caution_item_included']['measurement']['case_count']:
    lines.append('- No rerun-recommended topics remain; clean-only and included scenarios are identical.')
else:
    lines.append('- clean_only excludes rerun-recommended or caution topics.')
lines.extend([
    '- official_adopted_priority_review_lane is the existing 26-case adopted lane in `build/v6_score_report_v1.json`.',
    '- This is a non-sealed replay comparison and is not a promotion gate.',
])
compare_md_path.write_text('\n'.join(lines) + '\n', encoding='utf-8', newline='\n')
print('notes_updated')
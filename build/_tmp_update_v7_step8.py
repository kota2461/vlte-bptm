import json
from pathlib import Path

root = Path('.')
measurement_path = root / 'build' / 'pattern_language_sealed_v7_measurement_report.json'
targets_path = root / 'build' / 'v7_targets_and_roadmap_v1.json'
roadmap_path = root / 'docs' / 'PLM_V7_ROADMAP.md'
main_path = root / 'docs' / 'PATTERN_LANGUAGE_MODEL_roadmap.md'
summary_path = root / 'build' / 'v7_step8_measurement_summary.md'
readiness_path = root / 'build' / 'plm_measurement_readiness_review.json'

measurement = json.loads(measurement_path.read_text(encoding='utf-8'))
metrics = measurement['measurements']
readiness = json.loads(readiness_path.read_text(encoding='utf-8'))
targets = json.loads(targets_path.read_text(encoding='utf-8'))
field_counts = {}
for error in metrics['errors']:
    for field in error['fields']:
        field_counts[field] = field_counts.get(field, 0) + 1
field_counts = dict(sorted(field_counts.items()))
minimum = targets['targets']['minimum']
met_minimum = (
    metrics['intent_accuracy'] >= minimum['intent_accuracy']
    and metrics['critical_signal_recall'] >= minimum['critical_signal_recall']
    and metrics['operation_exact_match'] >= minimum['operation_exact_match']
    and metrics['constraint_exact_match'] >= minimum['constraint_exact_match']
    and metrics['risk_exact_match'] >= minimum['risk_exact_match']
    and len(metrics['errors']) <= minimum['sealed_error_count_max']
)
critical_miss_count = 0
for signal, item in metrics['critical_signals'].items():
    critical_miss_count += int(round(item['support'] * (1 - item['recall'])))
met_critical_miss = critical_miss_count <= minimum['critical_signal_miss_count_max']
passed = met_minimum and met_critical_miss

targets['generated_at'] = measurement['measured_at']
targets['status'] = 'step8_sealed_v7_measurement_completed_v8_rotation_required'
targets['next_action'] = 'roadmap_v8_step1_post_v7_measurement_taxonomy'
for item in targets['roadmap']:
    if item['step'] == 8:
        item['status'] = 'completed'
targets['step8_sealed_measurement'] = {
    'output': 'build\\pattern_language_sealed_v7_measurement_report.json',
    'summary': 'build\\v7_step8_measurement_summary.md',
    'fixture': 'tests\\fixtures\\pattern_language_sealed_v7.json',
    'sealed_fixture_opened': measurement['sealed_fixture_opened'],
    'sealed_labels_used_for_tuning': measurement['sealed_labels_used_for_tuning'],
    'passed_minimum': passed,
    'minimum_metrics_met': met_minimum,
    'critical_signal_miss_count': critical_miss_count,
    'critical_signal_miss_gate_met': met_critical_miss,
    'rotation_required_before_tuning': measurement['registry_update']['rotation_required_before_tuning'],
    'readiness_after_measurement': {
        'decision': readiness['decision'],
        'blocked_reasons': readiness['blocked_reasons'],
        'sealed_fixture': readiness['sealed_fixture'],
    },
    'measurements': {
        'case_count': metrics['case_count'],
        'intent_accuracy': metrics['intent_accuracy'],
        'intent_macro_f1': metrics['intent_macro_f1'],
        'critical_signal_recall': metrics['critical_signal_recall'],
        'operation_exact_match': metrics['operation_exact_match'],
        'constraint_exact_match': metrics['constraint_exact_match'],
        'risk_exact_match': metrics['risk_exact_match'],
        'valid_packet_rate': metrics['valid_packet_rate'],
        'evidence_offset_validity': metrics['evidence_offset_validity'],
        'error_count': len(metrics['errors']),
        'error_field_counts': field_counts,
    },
}
targets_path.write_text(json.dumps(targets, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')

lines = [
    '# V7 Step 8 Sealed Measurement Summary',
    '',
    f"- fixture: `{measurement['fixture']['registry_name']}`",
    f"- measured_at: `{measurement['measured_at']}`",
    f"- sealed_fixture_opened: `{measurement['sealed_fixture_opened']}`",
    f"- sealed_labels_used_for_tuning: `{measurement['sealed_labels_used_for_tuning']}`",
    f"- status_after_measurement: `{measurement['registry_update']['status_after_measurement']}`",
    f"- rotation_required_before_tuning: `{measurement['registry_update']['rotation_required_before_tuning']}`",
    f"- minimum_passed: `{passed}`",
    '',
    '## Metrics',
    '',
    '| Metric | Value | Target |',
    '|---|---:|---:|',
    f"| case_count | {metrics['case_count']} | 28 |",
    f"| intent_accuracy | {metrics['intent_accuracy']:.6f} | {minimum['intent_accuracy']:.6f} |",
    f"| critical_signal_recall | {metrics['critical_signal_recall']:.6f} | {minimum['critical_signal_recall']:.6f} |",
    f"| operation_exact_match | {metrics['operation_exact_match']:.6f} | {minimum['operation_exact_match']:.6f} |",
    f"| constraint_exact_match | {metrics['constraint_exact_match']:.6f} | {minimum['constraint_exact_match']:.6f} |",
    f"| risk_exact_match | {metrics['risk_exact_match']:.6f} | {minimum['risk_exact_match']:.6f} |",
    f"| error_count | {len(metrics['errors'])} | <= {minimum['sealed_error_count_max']} |",
    '',
    '## Critical Signals',
    '',
    '| Signal | Recall | Support |',
    '|---|---:|---:|',
]
for signal, item in metrics['critical_signals'].items():
    lines.append(f"| {signal} | {item['recall']:.6f} | {item['support']} |")
lines.extend(['', '## Error Field Counts', '', '| Field | Count |', '|---|---:|'])
for field, count in field_counts.items():
    lines.append(f'| {field} | {count} |')
lines.extend([
    '',
    '## Decision',
    '',
    'V7 did not meet the sealed minimum target. The sealed v7 fixture is consumed, sealed labels remain measurement-only, and a fresh successor rotation is required before tuning from this result.',
])
summary_path.write_text('\n'.join(lines) + '\n', encoding='utf-8', newline='\n')

roadmap = roadmap_path.read_text(encoding='utf-8')
roadmap = roadmap.replace(
    '| 8 | sealed_v7_one_time_measurement | `build\\pattern_language_sealed_v7_measurement_report.json` | next |',
    '| 8 | sealed_v7_one_time_measurement | `build\\pattern_language_sealed_v7_measurement_report.json` | completed |',
)
section = f"""## Step 8 Output

`build\\pattern_language_sealed_v7_measurement_report.json` measured the active sealed v7 fixture once and consumed it. Results: intent_accuracy `{metrics['intent_accuracy']:.6f}`, critical_signal_recall `{metrics['critical_signal_recall']:.6f}`, operation_exact_match `{metrics['operation_exact_match']:.6f}`, constraint_exact_match `{metrics['constraint_exact_match']:.6f}`, risk_exact_match `{metrics['risk_exact_match']:.6f}`, errors `{len(metrics['errors'])}`. V7 minimum was not met; sealed labels remain measurement-only and V8 taxonomy/rotation is required before tuning."""
if '## Step 8 Output' in roadmap:
    head, rest = roadmap.split('## Step 8 Output', 1)
    idx = rest.find('\n## ')
    if idx == -1:
        roadmap = head.rstrip() + '\n\n' + section + '\n'
    else:
        roadmap = head.rstrip() + '\n\n' + section + '\n\n' + rest[idx + 1:]
else:
    roadmap = roadmap.rstrip() + '\n\n' + section + '\n'
roadmap_path.write_text(roadmap, encoding='utf-8', newline='\n')

marker = '## PLM V7: Constraint And Critical Signal Recovery'
main = main_path.read_text(encoding='utf-8')
section = f"""
{marker}

Status: V7 Step 8 sealed v7 measurement completed; sealed v7 consumed; minimum not met; V8 taxonomy and fresh rotation required before tuning.

Primary roadmap: `docs/PLM_V7_ROADMAP.md`
Targets and taxonomy: `build/v7_targets_and_roadmap_v1.json`
Curriculum plan: `build/v7_nonsealed_curriculum_plan_v1.json`
Draft repair fixture: `tests/fixtures/v7_router_repair_fixture_v1.json`
Candidate replay report: `build/v7_router_repair_fixture_replay_v1.json`
Router generalization report: `build/v7_router_generalization_report_v1.json`
Non-sealed replay gate report: `build/v7_nonsealed_replay_gate_report_v1.json`
Sealed v7 rotation review: `build/v7_sealed_rotation_review_v1.json`
Sealed v7 rotation report: `build/v7_sealed_rotation_report_v1.json`
Sealed v7 measurement: `build/pattern_language_sealed_v7_measurement_report.json`
Sealed v7 summary: `build/v7_step8_measurement_summary.md`

Step 8 measured sealed v7 once and consumed it: intent_accuracy {metrics['intent_accuracy']:.6f}, critical_signal_recall {metrics['critical_signal_recall']:.6f}, operation_exact_match {metrics['operation_exact_match']:.6f}, constraint_exact_match {metrics['constraint_exact_match']:.6f}, risk_exact_match {metrics['risk_exact_match']:.6f}, errors {len(metrics['errors'])}. V7 minimum was not met; sealed labels remain measurement-only and the next step is V8 post-measurement taxonomy plus fresh sealed rotation before any tuning.
""".strip()
if marker in main:
    head, rest = main.split(marker, 1)
    idx = rest.find('\n## ')
    if idx == -1:
        main = head.rstrip() + '\n\n' + section + '\n'
    else:
        main = head.rstrip() + '\n\n' + section + '\n\n' + rest[idx + 1:]
else:
    main = main.rstrip() + '\n\n' + section + '\n'
main_path.write_text(main, encoding='utf-8', newline='\n')

print(json.dumps({'passed': passed, 'critical_signal_miss_count': critical_miss_count, 'field_counts': field_counts}, indent=2))

import json
from pathlib import Path

root = Path('.')
measurement_path = root / 'build' / 'pattern_language_sealed_v6_measurement_report.json'
roadmap_path = root / 'docs' / 'PLM_V6_ROADMAP.md'
main_roadmap_path = root / 'docs' / 'PATTERN_LANGUAGE_MODEL_roadmap.md'
summary_path = root / 'build' / 'v6_step6_measurement_summary.md'
measurement = json.loads(measurement_path.read_text(encoding='utf-8'))
metrics = measurement['measurements']
fixture = measurement['fixture']
errors = metrics['errors']
fields = {}
for error in errors:
    for field in error['fields']:
        fields[field] = fields.get(field, 0) + 1
crit = metrics['critical_signals']
summary = f'''# V6 Step 6 Sealed Measurement Summary

- fixture: `{fixture['registry_name']}`
- measured_at: `{measurement['measured_at']}`
- sealed_fixture_opened: `{measurement['sealed_fixture_opened']}`
- sealed_labels_used_for_tuning: `{measurement['sealed_labels_used_for_tuning']}`
- status_after_measurement: `{measurement['registry_update']['status_after_measurement']}`
- rotation_required_before_tuning: `{measurement['registry_update']['rotation_required_before_tuning']}`

## Metrics

| Metric | Value |
|---|---:|
| case_count | {metrics['case_count']} |
| intent_accuracy | {metrics['intent_accuracy']:.6f} |
| critical_signal_recall | {metrics['critical_signal_recall']:.6f} |
| operation_exact_match | {metrics['operation_exact_match']:.6f} |
| constraint_exact_match | {metrics['constraint_exact_match']:.6f} |
| risk_exact_match | {metrics['risk_exact_match']:.6f} |
| error_count | {len(errors)} |

## Critical Signals

| Signal | Recall | Support |
|---|---:|---:|
| missing_required_information | {crit['missing_required_information']['recall']:.6f} | {crit['missing_required_information']['support']} |
| contains_unverified_claims | {crit['contains_unverified_claims']['recall']:.6f} | {crit['contains_unverified_claims']['support']} |
| requires_current_information | {crit['requires_current_information']['recall']:.6f} | {crit['requires_current_information']['support']} |
| multiple_intents | {crit['multiple_intents']['recall']:.6f} | {crit['multiple_intents']['support']} |

## Error Field Counts

| Field | Count |
|---|---:|
'''
for field, count in sorted(fields.items()):
    summary += f'| {field} | {count} |\n'
summary += '''
## Contract

This measurement consumes sealed v6. The sealed labels remain measurement-only and must not be used to tune the same cycle. A fresh sealed successor must be rotated before any tuning based on this result.
'''
summary_path.write_text(summary, encoding='utf-8', newline='\n')

roadmap = roadmap_path.read_text(encoding='utf-8')
roadmap = roadmap.replace('| 6 | sealed_v6_one_time_measurement | `build\\pattern_language_sealed_v6_measurement_report.json` | next |', '| 6 | sealed_v6_one_time_measurement | `build\\pattern_language_sealed_v6_measurement_report.json` | completed |')
roadmap = roadmap.replace('| 7 | post_v6_measurement_taxonomy | `build\\v7_targets_and_roadmap_v1.json` | pending |', '| 7 | post_v6_measurement_taxonomy | `build\\v7_targets_and_roadmap_v1.json` | next |')
section = f'''## Step 6 Output

`build\\pattern_language_sealed_v6_measurement_report.json` measured the active sealed v6 fixture once and consumed it. Result: intent_accuracy {metrics['intent_accuracy']:.6f}, critical_signal_recall {metrics['critical_signal_recall']:.6f}, operation_exact_match {metrics['operation_exact_match']:.6f}, constraint_exact_match {metrics['constraint_exact_match']:.6f}, risk_exact_match {metrics['risk_exact_match']:.6f}, errors {len(errors)}. Sealed labels remain measurement-only. Step 7 is post-v6 measurement taxonomy and fresh successor planning before any tuning.
'''
if '## Step 6 Output' in roadmap:
    head, _ = roadmap.split('## Step 6 Output', 1)
    roadmap = head.rstrip() + '\n\n' + section
else:
    roadmap = roadmap.rstrip() + '\n\n' + section
roadmap_path.write_text(roadmap, encoding='utf-8', newline='\n')

marker = '## PLM V6: Boundary Calibration And Sealed Rotation'
main = main_roadmap_path.read_text(encoding='utf-8')
section = f'''{marker}

Status: V6 Step 6 sealed v6 measurement completed; sealed v6 consumed; Step 7 post-v6 measurement taxonomy and successor planning next.

Primary roadmap: `docs/PLM_V6_ROADMAP.md`
Current state report: `build/v6_current_state_report_v1.json`
Non-sealed replay gate report: `build/v6_nonsealed_replay_gate_report_v1.json`
Sealed v6 rotation review: `build/v6_sealed_rotation_review_v1.json`
Sealed v6 rotation report: `build/v6_sealed_rotation_report_v1.json`
Sealed v6 fixture: `tests/fixtures/pattern_language_sealed_v6.json`
Sealed v6 measurement: `build/pattern_language_sealed_v6_measurement_report.json`
Step 6 summary: `build/v6_step6_measurement_summary.md`

Step 6 measured sealed v6 once and consumed it: intent_accuracy {metrics['intent_accuracy']:.6f}, critical_signal_recall {metrics['critical_signal_recall']:.6f}, operation_exact_match {metrics['operation_exact_match']:.6f}, constraint_exact_match {metrics['constraint_exact_match']:.6f}, risk_exact_match {metrics['risk_exact_match']:.6f}, errors {len(errors)}. Sealed labels remain measurement-only; rotation is required before tuning based on this result.
'''
if marker in main:
    head, _ = main.split(marker, 1)
    main = head.rstrip() + '\n\n' + section + '\n'
else:
    main = main.rstrip() + '\n\n' + section + '\n'
main_roadmap_path.write_text(main, encoding='utf-8', newline='\n')
print(json.dumps({'summary': str(summary_path), 'errors': len(errors), 'intent_accuracy': metrics['intent_accuracy']}, indent=2))

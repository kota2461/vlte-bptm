# V8 Step 8 Sealed Measurement Summary

- fixture: `pattern_language_sealed_v8.json`
- measured_at: `2026-06-25T06:56:41.464471+00:00`
- sealed_fixture_opened: `True`
- sealed_labels_used_for_tuning: `False`
- status_after_measurement: `consumed`
- rotation_required_before_tuning: `True`
- minimum_passed: `False`

## Metrics

| Metric | Value | Target |
|---|---:|---:|
| case_count | 28 | 28 |
| intent_accuracy | 0.928571 | 0.892857 |
| critical_signal_recall | 0.833333 | 0.857143 |
| operation_exact_match | 0.785714 | 0.857143 |
| constraint_exact_match | 0.785714 | 0.857143 |
| risk_exact_match | 0.785714 | 0.892857 |
| error_count | 14 | <= 8 |

## Critical Signals

| Signal | Recall | Support |
|---|---:|---:|
| missing_required_information | 1.000000 | 4 |
| contains_unverified_claims | 1.000000 | 2 |
| requires_current_information | 0.500000 | 2 |
| multiple_intents | 0.750000 | 4 |

## Error Field Counts

| Field | Count |
|---|---:|
| constraints | 6 |
| information_state | 6 |
| operations | 6 |
| primary_intent | 2 |
| risk | 6 |

## Decision

V8 did not meet the sealed minimum target. The sealed v8 fixture is consumed, sealed labels remain measurement-only, and fresh rotation is required before tuning from this result.

# V6 Step 6 Sealed Measurement Summary

- fixture: `pattern_language_sealed_v6.json`
- measured_at: `2026-06-24T09:14:59.909161+00:00`
- sealed_fixture_opened: `True`
- sealed_labels_used_for_tuning: `False`
- status_after_measurement: `consumed`
- rotation_required_before_tuning: `True`

## Metrics

| Metric | Value |
|---|---:|
| case_count | 28 |
| intent_accuracy | 0.750000 |
| critical_signal_recall | 0.357143 |
| operation_exact_match | 0.607143 |
| constraint_exact_match | 0.607143 |
| risk_exact_match | 0.750000 |
| error_count | 23 |

## Critical Signals

| Signal | Recall | Support |
|---|---:|---:|
| missing_required_information | 0.500000 | 4 |
| contains_unverified_claims | 0.000000 | 3 |
| requires_current_information | 0.666667 | 3 |
| multiple_intents | 0.250000 | 4 |

## Error Field Counts

| Field | Count |
|---|---:|
| constraints | 11 |
| information_state | 8 |
| operations | 11 |
| primary_intent | 7 |
| risk | 7 |

## Contract

This measurement consumes sealed v6. The sealed labels remain measurement-only and must not be used to tune the same cycle. A fresh sealed successor must be rotated before any tuning based on this result.

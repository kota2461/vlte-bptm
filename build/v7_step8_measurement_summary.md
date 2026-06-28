# V7 Step 8 Sealed Measurement Summary

- fixture: `pattern_language_sealed_v7.json`
- measured_at: `2026-06-25T00:40:12.208631+00:00`
- sealed_fixture_opened: `True`
- sealed_labels_used_for_tuning: `False`
- status_after_measurement: `consumed`
- rotation_required_before_tuning: `True`
- minimum_passed: `False`

## Metrics

| Metric | Value | Target |
|---|---:|---:|
| case_count | 28 | 28 |
| intent_accuracy | 0.785714 | 0.892857 |
| critical_signal_recall | 0.642857 | 0.750000 |
| operation_exact_match | 0.714286 | 0.821429 |
| constraint_exact_match | 0.750000 | 0.821429 |
| risk_exact_match | 0.785714 | 0.892857 |
| error_count | 16 | <= 10 |

## Critical Signals

| Signal | Recall | Support |
|---|---:|---:|
| missing_required_information | 0.500000 | 4 |
| contains_unverified_claims | 1.000000 | 2 |
| requires_current_information | 0.666667 | 3 |
| multiple_intents | 0.600000 | 5 |

## Error Field Counts

| Field | Count |
|---|---:|
| constraints | 7 |
| information_state | 6 |
| operations | 8 |
| primary_intent | 6 |
| risk | 6 |

## Decision

V7 did not meet the sealed minimum target. The sealed v7 fixture is consumed, sealed labels remain measurement-only, and a fresh successor rotation is required before tuning from this result.

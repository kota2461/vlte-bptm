# V9 Step 8 Sealed Measurement Summary

- fixture: `pattern_language_sealed_v9.json`
- measured_at: `2026-06-25T08:52:34.120342+00:00`
- sealed_fixture_opened: `True`
- sealed_labels_used_for_tuning: `False`
- status_after_measurement: `consumed`
- rotation_required_before_tuning: `True`
- minimum_passed: `False`

## Metrics

| Metric | Value | Target |
|---|---:|---:|
| case_count | 28 | 28 |
| intent_accuracy | 0.892857 | 0.928571 |
| critical_signal_recall | 0.857143 | 0.916667 |
| operation_exact_match | 0.821429 | 0.892857 |
| constraint_exact_match | 0.642857 | 0.892857 |
| risk_exact_match | 0.750000 | 0.892857 |
| error_count | 17 | <= 7 |

## Critical Signals

| Signal | Recall | Support |
|---|---:|---:|
| missing_required_information | 1.000000 | 4 |
| contains_unverified_claims | 0.666667 | 3 |
| requires_current_information | 1.000000 | 1 |
| multiple_intents | 0.833333 | 6 |

## Error Field Counts

| Field | Count |
|---|---:|
| constraints | 10 |
| information_state | 6 |
| operations | 5 |
| primary_intent | 3 |
| risk | 7 |

## Decision

V9 did not meet the sealed minimum target. The sealed v9 fixture is consumed, sealed labels remain measurement-only, and fresh rotation is required before tuning from this result.

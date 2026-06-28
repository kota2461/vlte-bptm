# V10 Step 6 Sealed Measurement Summary

- fixture: `pattern_language_sealed_v10.json`
- sealed_fixture_opened: `True`
- sealed_labels_used_for_tuning: `False`
- rotation_required_before_tuning: `True`
- minimum_passed: `False`

## Metrics

| Metric | Value | Target |
|---|---:|---:|
| case_count | 28 | 28 |
| intent_accuracy | 0.785714 | 0.928571 |
| critical_signal_recall | 0.400000 | 0.928571 |
| operation_exact_match | 0.642857 | 0.892857 |
| constraint_exact_match | 0.535714 | 0.857143 |
| risk_exact_match | 0.678571 | 0.857143 |
| error_count | 23 | <= 8 |

## Error Field Counts

| Field | Count |
|---|---:|
| constraints | 13 |
| information_state | 10 |
| operations | 10 |
| primary_intent | 6 |
| risk | 9 |

## Decision

V10 did not meet the sealed minimum target. The sealed v10 fixture is consumed, sealed labels remain measurement-only, and V11 taxonomy plus fresh sealed rotation are required before tuning from this result.

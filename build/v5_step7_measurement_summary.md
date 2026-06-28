# PLM V5 Step 7 Measurement Summary

Generated: 2026-06-23

## Status

- Fixture: `pattern_language_sealed_v5.json`
- Measurement report: `build\pattern_language_sealed_v5_measurement_report.json`
- Fixture status after measurement: `consumed`
- Measured: `True`
- Reviewed: `False`
- Readiness after measurement: `blocked` / `sealed_fixture_not_available`
- Contract: sealed labels are measurement-only; rotation is required before tuning.

## Result Against V5 Targets

| Metric | V5 result | V5 minimum | Pass |
|---|---:|---:|---|
| intent_accuracy | 0.750000 | 0.928571 | no |
| critical_signal_recall | 0.375000 | 0.875000 | no |
| operation_exact_match | 0.678571 | 0.892857 | no |
| constraint_exact_match | 0.821429 | 0.928571 | no |
| risk_exact_match | 0.892857 | 0.964286 | no |
| sealed_error_count | 18 | <= 6 | no |
| critical_signal_miss_count | 10 | <= 2 | no |

## Critical Signals

| Signal | Recall | Support |
|---|---:|---:|
| missing_required_information | 0.25 | 4 |
| contains_unverified_claims | 0.4 | 5 |
| requires_current_information | 0.666667 | 3 |
| multiple_intents | 0.25 | 4 |

## Error Field Counts

| Field | Count |
|---|---:|
| constraints | 5 |
| information_state | 9 |
| operations | 9 |
| primary_intent | 7 |
| risk | 3 |

## Intent Pair Counts In Errors

| Expected -> Predicted | Count |
|---|---:|
| build->build | 1 |
| build->respond | 1 |
| build->verify | 1 |
| clarify->respond | 3 |
| explain->build | 1 |
| explore->explore | 4 |
| respond->build | 1 |
| summarize->summarize | 3 |
| verify->verify | 3 |

## Reading

V5 did not meet the sealed target. The largest damage is critical-signal recall, especially missing information and multiple intent handling. Clarify-to-respond leakage appears three times, and build boundaries also leak into respond/verify. The non-sealed replay gate was useful but overfit to its challenge surface; V6 should treat this as a generalization failure, not a promotion failure.

## Recommended Next Actions

1. Freeze this measurement as taxonomy only; do not tune directly on sealed text.
2. Build a V6 non-sealed error curriculum from field counts and intent-pair taxonomy.
3. Add targeted non-sealed probes for clarify missing-info, build verification ordering, and critical signal preservation.
4. Rotate a fresh sealed v6 fixture before the next adjudicating measurement.
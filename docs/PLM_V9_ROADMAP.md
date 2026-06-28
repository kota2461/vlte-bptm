# PLM V9 Roadmap: Exactness Recovery And Fresh Rotation

Updated: 2026-06-25

## Contract

- Sealed v8 is consumed and may be used only as aggregate taxonomy.
- Sealed v8 text and labels must not be copied into training, review, or non-sealed fixtures.
- V9 uses human-approved non-sealed primary-review and constraint/operation extension lanes.
- Same-cycle promotion remains disallowed.
- A fresh sealed v9 fixture is required before the next adjudicating measurement.

## Baseline And Targets

| Metric | V8 sealed | V9 minimum | V9 stretch |
|---|---:|---:|---:|
| intent_accuracy | 0.928571 | 0.928571 | 0.964286 |
| critical_signal_recall | 0.833333 | 0.916667 | 1.000000 |
| operation_exact_match | 0.785714 | 0.892857 | 0.928571 |
| constraint_exact_match | 0.785714 | 0.892857 | 0.928571 |
| risk_exact_match | 0.785714 | 0.892857 | 0.928571 |
| sealed_error_count | 14 | <= 7 | <= 4 |

## Error Taxonomy

| Field | Count |
|---|---:|
| constraints | 6 |
| information_state | 6 |
| operations | 6 |
| primary_intent | 2 |
| risk | 6 |

## Nonsealed Recovery

- primary_review: 34 cases, exact=true
- constraint_operation_extension: 24 cases, exact=true
- focused_v9_case_count: 58
- v9_nonsealed_replay_gate: passed, total_case_count=88, required_error_count=0

## Focus Areas

1. operation_constraint_exactness: operation order and explicit constraints remain the largest sealed-v8 exact-match gap
1. risk_current_information_balance: current/search and risk flags need separation between actual external-current needs and local/current wording
2. respond_vs_build_boundary: simple response requests can still be pulled into build when wording contains deliverable-like verbs
2. clarify_vs_verify_boundary: missing information plus verification language can still jump to verify before asking
3. paraphrase_mixed_language_tail: V9 still needs more paraphrase, mixed ja/en, and natural short-form coverage before sealed rotation

## Roadmap

| Step | Name | Output | Status |
|---:|---|---|---|
| 1 | post_v8_measurement_taxonomy | `build\v9_targets_and_roadmap_v1.json` | completed |
| 2 | v9_accumulated_log_candidate_selection | `build\v9_accumulated_log_candidate_selection_v1.json` | completed |
| 3 | v9_primary_review_adoption_and_replay | `build\v9_accumulated_primary_review_replay_report_v1.json` | completed |
| 4 | v9_constraint_operation_extension | `build\v9_constraint_operation_extension_replay_report_v1.json` | completed |
| 5 | v9_nonsealed_replay_gate | `build\v9_nonsealed_replay_gate_report_v1.json` | completed |
| 6 | sealed_v9_rotation_review | `build\v9_sealed_rotation_review_v1.json` | completed |
| 7 | sealed_v9_rotation | `tests\fixtures\pattern_language_sealed_v9.json` | completed |
| 8 | sealed_v9_one_time_measurement | `build\pattern_language_sealed_v9_measurement_report.json` | completed |

## Step 4 Output

`build\v9_accumulated_primary_review_replay_report_v1.json` and `build\v9_constraint_operation_extension_replay_report_v1.json` are exact on their human-reviewed non-sealed lanes. They are not sealed evidence and are not same-cycle promotion evidence.

## Step 5 Output

`build\v9_nonsealed_replay_gate_report_v1.json` passed. It replays V8 approved recovery, V9 primary review, and the V9 constraint/operation extension exactly. Step 6 is sealed V9 rotation review.

## Step 6 Output

`build\v9_sealed_rotation_review_v1.json` reports `eligible_for_fresh_sealed_v9_rotation`. It confirms that the V9 non-sealed replay gate passed, `pattern_language_sealed_v8.json` is consumed, no active sealed fixture exists, and `pattern_language_sealed_v9.json` has not been created. This review does not create, open, or measure sealed v9. Step 7 is now sealed V9 rotation.

## Step 7 Output

`build\v9_sealed_rotation_report_v1.json` created `tests\fixtures\pattern_language_sealed_v9.json` as the active unopened sealed fixture. It has 28 cases, predecessor `pattern_language_sealed_v8.json`, measured `False`, reviewed `False`. Step 8 is the one-time sealed v9 measurement.

## Step 8 Output

`build\pattern_language_sealed_v9_measurement_report.json` measured the active sealed v9 fixture once and consumed it. Results: intent_accuracy `0.892857`, critical_signal_recall `0.857143`, operation_exact_match `0.821429`, constraint_exact_match `0.642857`, risk_exact_match `0.750000`, errors `17`. Sealed labels remain measurement-only and V10 taxonomy/rotation is required before tuning.

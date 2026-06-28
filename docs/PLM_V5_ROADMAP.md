# PLM V5 Roadmap: Critical Signal Recovery

Updated: 2026-06-23

## Contract

- Sealed v4 is consumed and may be used only as measurement taxonomy.
- Sealed v4 input text and labels must not be copied into training, review, or non-sealed fixtures.
- V5 tuning must use non-sealed curriculum, Failure Memory, Puzzle Failure Memory, and visible benchmarks only.
- A fresh sealed v5 fixture is required before the next adjudicating measurement.

## Baseline And Targets

| Metric | V4 sealed | V5 minimum | V5 stretch |
|---|---:|---:|---:|
| intent_accuracy | 0.857143 | 0.928571 | 0.964286 |
| critical_signal_recall | 0.562500 | 0.875000 | 1.000000 |
| operation_exact_match | 0.750000 | 0.892857 | 0.928571 |
| constraint_exact_match | 0.821429 | 0.928571 | 0.964286 |
| risk_exact_match | 0.928571 | 0.964286 | 1.000000 |
| sealed_error_count | 15 | <= 6 | <= 3 |
| critical_signal_miss_count | 7 | <= 2 | <= 0 |

Metric granularity: case metrics move by 1/28 = 0.035714; critical signal recall moves by 1/16 = 0.0625.

## Critical Signal Targets

| Signal | V4 recall | Support | Miss | V5 minimum | V5 stretch |
|---|---:|---:|---:|---:|---:|
| missing_required_information | 0.500000 | 4 | 2 | 0.750000 | 1.000000 |
| contains_unverified_claims | 0.800000 | 5 | 1 | 1.000000 | 1.000000 |
| requires_current_information | 0.666667 | 3 | 1 | 1.000000 | 1.000000 |
| multiple_intents | 0.250000 | 4 | 3 | 0.750000 | 1.000000 |

## Error Taxonomy

| Field | Count |
|---|---:|
| constraints | 5 |
| information_state | 6 |
| operations | 7 |
| primary_intent | 4 |
| risk | 2 |

## Focus Areas

1. critical_signal_recovery: Critical recall dropped to 0.5625; multiple_intents and missing_required_information are the largest risks.
2. operation_sequence_exactness: Operations mismatched in 7 sealed v4 errors, especially clarify/calculate, verify/search, and explore/compare patterns.
3. constraint_preservation: Constraints mismatched in 5 errors; short, JSON, bullets, no_table, and ask_first must survive routing.
4. intent_boundary_repair: Intent accuracy stayed at 0.857143; clarify->respond and explain/respond boundaries still leak.
5. risk_flag_completion: Risk is closest to target but still misses legal/medical/current combinations in 2 errors.

## Roadmap

| Step | Name | Output | Status |
|---:|---|---|---|
| 1 | targets_and_taxonomy | `build\v5_targets_and_roadmap_v1.json` | completed |
| 2 | nonsealed_error_curriculum_design | `build\v5_nonsealed_curriculum_plan_v1.json` | completed |
| 3 | critical_signal_and_operations_fixture | `tests\fixtures\v5_critical_operations_fixture_v1.json` | draft_created |
| 4 | router_generalization_changes | `build\v5_router_generalization_report.json` | completed |
| 5 | nonsealed_replay_gate | `build\v5_nonsealed_replay_gate_report.json` | completed |
| 6 | sealed_v5_rotation | `tests\fixtures\pattern_language_sealed_v5.json` | completed |
| 7 | sealed_v5_one_time_measurement | `build\pattern_language_sealed_v5_measurement_report.json` | completed |


## Step 2 Output

`build\v5_nonsealed_curriculum_plan_v1.json` is designed. It defines 7 non-sealed curriculum axes and a minimum 48-case Step 3 fixture blueprint. The plan uses sealed v4 only through the sanitized taxonomy in `build\v5_targets_and_roadmap_v1.json`; sealed text and sealed labels remain excluded. The active intent-corpus quarantine overlay is treated as data hygiene and may be used only as negative/guard reference material.


## Step 3 Output

`tests\fixtures\v5_critical_operations_fixture_v1.json` is created as a draft non-sealed challenge fixture for human review. It contains 48 self-authored cases across the 7 Step 2 curriculum axes. Current `route()` measurement on this fixture is diagnostic only, not a gate: intent_accuracy 0.687500, critical_signal_recall 0.452381, operation_exact_match 0.541667, constraint_exact_match 0.666667, risk_exact_match 0.895833, errors 35. Step 4 should use this non-sealed failure surface for router generalization.

## Step 4 Output

`build\v5_router_generalization_report.json` is completed as a diagnostic, non-gate replay against the Step 3 non-sealed draft fixture. Before -> after: intent_accuracy 0.687500 -> 1.000000, critical_signal_recall 0.452381 -> 1.000000, operation_exact_match 0.541667 -> 1.000000, constraint_exact_match 0.666667 -> 1.000000, risk_exact_match 0.895833 -> 1.000000, errors 35 -> 0. Sealed text and sealed labels remain excluded. Step 5 is now the non-sealed replay gate.

## Step 5 Output

`build\v5_nonsealed_replay_gate_report.json` passed as a non-sealed replay gate. Lanes: visible_plm 0 errors, v4_failure_memory exact 38/38, puzzle_failure_memory preserved True, v5_nonsealed_challenge 0 errors. Sealed v4 text and labels remain excluded. Step 6 is now sealed v5 rotation.

## Step 6 Output

`build\v5_sealed_rotation_report.json` created `tests\fixtures\pattern_language_sealed_v5.json` as the active unopened sealed fixture. It has 28 cases, predecessor `pattern_language_sealed_v4.json`, measured `False`, reviewed `False`, and sha256 `4e18eb7453cfe461b466d495e37846bca9077423ac84d8c5b2054734566e055c`. Step 7 is the one-time sealed v5 measurement.

## Step 7 Output

`build\pattern_language_sealed_v5_measurement_report.json` measured the active sealed v5 fixture once and consumed it. Result: intent_accuracy 0.750000, critical_signal_recall 0.375000, operation_exact_match 0.678571, constraint_exact_match 0.821429, risk_exact_match 0.892857, errors 18, critical_signal_miss_count 10. V5 minimum was not met; sealed labels remain measurement-only, and rotation is required before any tuning based on this result.
## Pre-Sealed V5 Gates

- visible_plm_intent_accuracy: 1.0
- visible_plm_critical_signal_recall: 1.0
- v4_failure_guard_exact_match_rate: 1.0
- puzzle_failure_memory_preserved: True
- v5_nonsealed_challenge_accuracy_min: 0.95
- v5_nonsealed_critical_signal_recall_min: 0.95
- sealed_text_overlap_count: 0

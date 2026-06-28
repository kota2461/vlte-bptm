# PLM Sample Block Negative Scan v1

Generated: 2026-06-28T07:51:58.482270+00:00

## Policy

- Diagnostic only; no training data, fixture, or router mutation.
- Sealed fixtures are excluded and active sealed fixtures are not opened.
- Strong negative means current-route mismatch concentration or high weighted error, not automatic deletion.

## Summary

- fixtures_scanned: 12
- cases_scanned: 330
- strong_negative_blocks: 0
- focused_repair_blocks: 0
- transfer_risk_blocks: 15

## Strong Negative Candidates

| kind | key | cases | errors | score | flags | top errors |
|---|---|---:|---:|---:|---|---|

## Focused Repair Candidates

| kind | key | cases | errors | score | flags | field counts |
|---|---|---:|---:|---:|---|---|

## Transfer Risk Candidates

| kind | key | cases | errors | synthetic rate | language | flags |
|---|---|---:|---:|---:|---|---|
| fixture | `tests/fixtures/v10_thought_color_bridge_isolated_benchmark_v1.json` | 72 | 0 | 0.000 | `{'en': 72}` | english_only_large_block |
| fixture | `tests/fixtures/v6_boundary_priority_review_adopted_benchmark_v1.json` | 26 | 0 | 0.000 | `{'en': 26}` | english_only_large_block |
| fixture | `tests/fixtures/v6_structural_build_30_adopted_benchmark_v1.json` | 30 | 0 | 0.000 | `{'en': 30}` | english_only_large_block |
| fixture | `tests/fixtures/v6_structural_build_30_candidate_benchmark_v1.json` | 30 | 0 | 0.000 | `{'en': 30}` | english_only_large_block |
| fixture | `tests/fixtures/v9_constraint_operation_extension_benchmark_v1.json` | 24 | 0 | 0.000 | `{'en': 24}` | english_only_large_block |
| id_prefix | `tests/fixtures/v10_thought_color_bridge_isolated_benchmark_v1.json::v10-thought-color-bridge-isolated` | 72 | 0 | 0.000 | `{'en': 72}` | english_only_large_block |
| id_prefix | `tests/fixtures/v6_boundary_priority_review_adopted_benchmark_v1.json::v6-boundary-priority-review` | 26 | 0 | 0.000 | `{'en': 26}` | english_only_large_block |
| id_prefix | `tests/fixtures/v6_structural_build_30_adopted_benchmark_v1.json::v6-structural-build-30` | 30 | 0 | 0.000 | `{'en': 30}` | english_only_large_block |
| id_prefix | `tests/fixtures/v6_structural_build_30_candidate_benchmark_v1.json::v6-structural-build-30` | 30 | 0 | 0.000 | `{'en': 30}` | english_only_large_block |
| id_prefix | `tests/fixtures/v9_constraint_operation_extension_benchmark_v1.json::v9-constraint-operation-extension` | 24 | 0 | 0.000 | `{'en': 24}` | english_only_large_block |
| source_group | `tests/fixtures/v10_thought_color_bridge_isolated_benchmark_v1.json::v10-thought-color-bridge-isolated-rewrite-nonsealed` | 72 | 0 | 0.000 | `{'en': 72}` | english_only_large_block |
| source_group | `tests/fixtures/v6_boundary_priority_review_adopted_benchmark_v1.json::v6-boundary-priority-review-adopted-nonsealed` | 26 | 0 | 0.000 | `{'en': 26}` | english_only_large_block |
| source_group | `tests/fixtures/v6_structural_build_30_adopted_benchmark_v1.json::v6-structural-build-30-candidate-draft` | 30 | 0 | 0.000 | `{'en': 30}` | english_only_large_block |
| source_group | `tests/fixtures/v6_structural_build_30_candidate_benchmark_v1.json::v6-structural-build-30-candidate-draft` | 30 | 0 | 0.000 | `{'en': 30}` | english_only_large_block |
| source_group | `tests/fixtures/v9_constraint_operation_extension_benchmark_v1.json::v9-constraint-operation-extension-nonsealed` | 24 | 0 | 0.000 | `{'en': 24}` | english_only_large_block |

## Recommended Handling

1. Do not delete or quarantine automatically from this scan alone.
2. Inspect strong_negative_candidate blocks first; these are possible mislabeled or over-narrow samples.
3. For focused_repair_candidate blocks, prefer code/guard audit when omission or overfire dominates.
4. For transfer_risk_candidate blocks, keep samples quarantined from mainline unless naturalized transfer probes also pass.

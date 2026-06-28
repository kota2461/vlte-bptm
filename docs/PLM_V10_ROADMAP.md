# PLM V10 Roadmap: Bridge Generalization And Exactness Recovery

Updated: 2026-06-27

## Contract

- Sealed v9 is consumed and may be used only as aggregate taxonomy.
- Sealed v9 text and labels must not be copied into training, review, or non-sealed fixtures.
- Thought Color bridge sources remain experiment-scope and are not direct mainline training data.
- V10 may use the bridge only as router generalization and non-sealed replay evidence after human review.
- Same-cycle promotion remains disallowed; a fresh sealed v10 fixture is required before adjudicating measurement.

## Baseline And Targets

| Metric | V9 sealed | V10 minimum | V10 stretch |
|---|---:|---:|---:|
| intent_accuracy | 0.892857 | 0.928571 | 0.964286 |
| critical_signal_recall | 0.857143 | 0.928571 | 1.000000 |
| operation_exact_match | 0.821429 | 0.892857 | 0.928571 |
| constraint_exact_match | 0.642857 | 0.857143 | 0.928571 |
| risk_exact_match | 0.750000 | 0.857143 | 0.928571 |
| sealed_error_count | 17 | <= 8 | <= 5 |

## V10 Bridge Mainline Adoption

- adopted_count: 72
- allowed_use: router_generalization_and_nonsealed_replay_only
- source_mainline_training_allowed: false
- isolated_rewrite_fixture_training_allowed: false
- isolated_error_count: 0
- isolated_constraint_exact_match: 1.000000
- isolated_operation_exact_match: 1.000000

## V10+ Learning Lanes

| Lane | Priority | Mainline Role | Direct Training | Separation Rule |
|---|---:|---|---|---|
| router_judgment_lane | 1 | boundary judgment / near-miss / failure memory | human-reviewed nonsealed only | distilled trace, not raw log |
| answer_prototype_lane | 2 | output prototype / question probe source | no direct semantic-packet training | keep separate until probes are reviewed |

Answer-only samples are useful, but they underdetermine the original input intent. They should be stored as a separate prototype lane and converted into reviewed question probes before any mainline replay gate.
Router judgment samples are closer to the mainline PLM objective because they preserve candidate routes, chosen route, near-miss, and judgment reason.

## Error Taxonomy

| Field | Count |
|---|---:|
| constraints | 10 |
| information_state | 6 |
| operations | 5 |
| primary_intent | 3 |
| risk | 7 |

## Focus Areas

1. constraint_exactness_recovery: sealed v9 shows constraints as the largest exact-match gap, especially ask-first, neutrality, and overclaim controls
1. risk_ladder_recovery: risk level and risk flags need steadier separation after sealed v9
1. missing_multiple_information_state: missing context, unverified claims, and multiple-intent signals still need robust detection and non-collapse
2. operation_order_terminality: terminal operation and ordered multi-step routes still drift in sealed v9
2. intent_boundary_tail: respond/verify, clarify/verify, and verify/summarize boundaries remain the intent tail to protect

## Roadmap

| Step | Name | Output | Status |
|---:|---|---|---|
| 1 | post_v9_measurement_taxonomy | `build\v10_targets_and_roadmap_v1.json` | completed |
| 2 | v10_thought_color_bridge_mainline_adoption_review | `build\v10_thought_color_bridge_isolated_adoption_decision_v1.json` | completed |
| 3 | v10_mainline_nonsealed_replay_gate | `build\v10_mainline_replay_gate_report_v1.json` | completed |
| 4 | sealed_v10_rotation_review | `build\v10_sealed_rotation_review_v1.json` | completed |
| 5 | sealed_v10_rotation | `tests\fixtures\pattern_language_sealed_v10.json` | completed |
| 6 | sealed_v10_one_time_measurement | `build\pattern_language_sealed_v10_measurement_report.json` | completed |

## Step 4 Output

`build\v10_sealed_rotation_review_v1.json` reports `eligible_for_fresh_sealed_v10_rotation`. It confirms that the V10 mainline replay gate passed, `pattern_language_sealed_v9.json` is consumed, no active sealed fixture exists, and `pattern_language_sealed_v10.json` has not been created. This review does not create, open, or measure sealed v10. Step 5 is now sealed V10 rotation.
- required_error_count: 0
- blocker_count: 0

## Step 5 Output

`build\v10_sealed_rotation_report_v1.json` rotated `tests\fixtures\pattern_language_sealed_v10.json` into the active sealed slot. The fixture is active, unmeasured, and unreviewed; sealed v10 labels remain unavailable for tuning. Step 6 is the one-time sealed v10 measurement.
- case_count: 28
- readiness_decision: eligible
- measured: false
- reviewed: false

## Step 6 Output

`build\pattern_language_sealed_v10_measurement_report.json` measured the active sealed v10 fixture once and consumed it. Sealed v10 labels remain measurement-only; V11 taxonomy and fresh rotation are required before any tuning from this result.
- intent_accuracy: 0.785714
- critical_signal_recall: 0.400000
- operation_exact_match: 0.642857
- constraint_exact_match: 0.535714
- risk_exact_match: 0.678571
- error_count: 23
- passed_minimum: false
- rotation_required_before_tuning: true

## Post-V10 Diagnostic

`build\v11_post_v10_measurement_diagnostic_v1.json` records value-level diffs, failure-mode separation, and bridge transfer-gap evidence. It is taxonomy-only, not training data, not a replay gate, and not same-cycle promotion evidence.
- status: diagnostic_completed_v11_step1_ready
- focus_areas: ['value_level_diff_instrumentation', 'clarify_boundary_collapse', 'multiple_intent_under_detection', 'bridge_non_transfer', 'intent_correct_field_mismatch_lane']
- next_action: roadmap_v11_step1_build_taxonomy_from_value_diff_and_transfer_gap

## Decision

- can_advance: true
- advance_to: v11_post_v10_measurement_taxonomy
- blocked_reasons: []

## V11 Handoff

`build\v11_targets_and_roadmap_v1.json` and `docs\PLM_V11_ROADMAP.md` convert consumed sealed v10 into value-diff taxonomy and bridge transfer-gap planning. Sealed v10 text and labels remain excluded from training; V11 requires fresh non-sealed repair gates and a fresh sealed v11 rotation before measurement.


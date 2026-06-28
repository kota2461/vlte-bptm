# PLM V11 Roadmap: Value-Diff Recovery And Bridge Transfer Repair

Updated: 2026-06-28

## Contract

- Sealed v10 is consumed and may be used only as aggregate taxonomy/value-diff evidence.
- Sealed v10 text and labels must not be copied into training, review, or non-sealed fixtures.
- The post-v10 diagnostic is not training data, not a replay gate, and not same-cycle promotion evidence.
- Bridge-only isolated replay is not sufficient for V11; transfer validation is required.
- Same-cycle promotion remains disallowed; a fresh sealed v11 fixture is required before adjudicating measurement.
- If code audit triage reports baseline source recovery blockers, Step 2 curriculum work waits for Step 1b source recovery.

## Baseline And Targets

| Metric | V10 sealed | V11 minimum | V11 stretch |
|---|---:|---:|---:|
| intent_accuracy | 0.785714 | 0.857143 | 0.928571 |
| critical_signal_recall | 0.400000 | 0.733333 | 0.866667 |
| operation_exact_match | 0.642857 | 0.750000 | 0.857143 |
| constraint_exact_match | 0.535714 | 0.714286 | 0.857143 |
| risk_exact_match | 0.678571 | 0.785714 | 0.857143 |
| sealed_error_count | 23 | <= 14 | <= 8 |
| critical_signal_miss_count | 9 | <= 4 | <= 2 |

## P0 Code Audit Status

- status: step1b_baseline_source_recovery_completed
- next_action: roadmap_v11_step2_create_repair_curriculum_plan
- pre_step2_blockers: []
- baseline source recovery completed; Step 2 curriculum planning is unblocked.

## Failure Mode Taxonomy

| Mode | Cases | Repair Lane |
|---|---:|---|
| intent_correct_field_mismatch | 17 | field_exactness_repair_lane |
| intent_mismatch | 6 | intent_boundary_repair_lane |
| critical_signal_under_detection | 9 | critical_signal_repair_lane |
| bridge_non_transfer | gap | bridge_transfer_validation_lane |

## Value-Diff Hotspots

- constraint_must_missing: `{"['ask_first'] -> []": 1, "['avoid_diagnosis', 'avoid_overclaim'] -> []": 1, "['avoid_diagnosis'] -> []": 1, "['avoid_overclaim'] -> []": 1, "['cite_sources', 'avoid_overclaim'] -> []": 1, "['general_information_only'] -> []": 1}`
- constraint_format_missing: `{"['bullets'] -> []": 2, "['json'] -> []": 2, "['table'] -> []": 1}`
- constraint_response_length_drift: `{'short -> unspecified': 3}`
- risk_level_drift: `{'low -> high': 1, 'low -> medium': 3, 'medium -> high': 1, 'medium -> low': 4}`
- risk_flag_drift: `{"['political'] -> []": 1, "['security', 'unverified_claim'] -> []": 1, "['training_contamination'] -> []": 1, "['unverified_claim'] -> []": 1, "[] -> ['current_information']": 2, "[] -> ['medical']": 1, "[] -> ['mental_health', 'dependency_risk', 'unverified_claim']": 1}`
- operation_drift: `{"['clarify', 'build'] -> ['clarify']": 1, "['clarify', 'build'] -> ['explore', 'compare']": 1, "['clarify', 'summarize'] -> ['respond']": 1, "['clarify', 'verify'] -> ['verify']": 1, "['explain'] -> ['explain', 'search']": 1, "['explain'] -> ['verify', 'explain']": 1, "['explore', 'compare'] -> ['explore']": 1, "['explore'] -> ['respond']": 1, "['respond'] -> ['build']": 1, "['respond'] -> ['respond', 'search']": 1}`
- primary_intent_drift: `{'clarify -> explore': 1, 'clarify -> respond': 1, 'clarify -> verify': 1, 'explain -> verify': 1, 'explore -> respond': 1, 'respond -> build': 1}`

## Refined Diagnostic Hypotheses

- constraint_omission_fast_path: constraint values are omitted rather than confused, so trace/merge propagation should be inspected before adding more samples First action: inspect constraint propagation and marker merge logic before expanding fixtures.
- risk_confusion_learning_path: risk values move in both directions, so boundary data and ladder calibration are likely needed First action: separate no-risk contrast from medium/high escalation examples.
- hook_keyword_overfire_without_context: guard hooks may fire on keyword presence before negation, metalinguistic role, or local-reference checks First action: audit hook firing logic for negation scope, metacontext markers, definition intent, and local-current split.
- definition_request_build_overroute: respond/build boundary needs a narrow definition-request guard before broader build routing First action: add definition-request contrast to intent boundary plan.
- literal_profile_patch_overfit: v6-v9 repair profiles were largely per-fixture literal regex patches, so isolated nonsealed exactness did not transfer to sealed v10 wording First action: convert repair examples into abstract marker/context rules and require naturalized paraphrase transfer checks.

## Focus Areas

1. value_level_diff_instrumentation: all post-measurement and replay reports must retain expected/predicted value diffs, not just field names
2. clarify_boundary_collapse: clarify repair must be its own lane with recall target and transition analysis
3. multiple_intent_under_detection: multiple_intents gets an independent recall target and cannot be hidden inside generic information_state exactness
4. bridge_non_transfer: bridge-derived samples must pass naturalized paraphrase and mixed-language transfer checks before mainline adoption
5. intent_correct_field_mismatch_lane: field exactness repair is separate from intent-boundary repair and can use different fixtures/gates

## Repair Lanes

| Lane | Priority | Gate Metric |
|---|---:|---|
| intent_boundary_repair_lane | 1 | clarify_recall_min |
| critical_signal_repair_lane | 1 | critical_signal_recall_and_multiple_intents_recall |
| field_exactness_repair_lane | 1 | constraint_operation_risk_exactness |
| hook_overfire_repair_lane | 1 | hook_false_positive_zero_on_known_patterns |
| bridge_transfer_validation_lane | 1 | transfer_gap_not_template_only |

## Roadmap

| Step | Name | Output | Status |
|---:|---|---|---|
| 1 | post_v10_value_diff_transfer_taxonomy | `build\v11_targets_and_roadmap_v1.json` | completed |
| 2 | v11_repair_curriculum_plan | `build\v11_repair_curriculum_plan_v1.json` | next |
| 3 | v11_value_diff_repair_fixture_and_candidate_replay | `tests\fixtures\v11_value_diff_repair_fixture_v1.json` | pending |
| 4 | v11_bridge_transfer_validation_set | `tests\fixtures\v11_bridge_transfer_validation_fixture_v1.json` | pending |
| 5 | v11_router_generalization_changes | `build\v11_router_generalization_report_v1.json` | pending |
| 6 | v11_nonsealed_replay_gate | `build\v11_nonsealed_replay_gate_report_v1.json` | pending |
| 7 | sealed_v11_rotation_review | `build\v11_sealed_rotation_review_v1.json` | pending |
| 8 | sealed_v11_rotation | `tests\fixtures\pattern_language_sealed_v11.json` | pending |
| 9 | sealed_v11_one_time_measurement | `build\pattern_language_sealed_v11_measurement_report.json` | pending |

## Decision

- can_advance: true
- advance_to: v11_repair_curriculum_plan
- blocked_reasons: []

# V10 Mainline Replay Gate Report v1

status: `passed`
passed: true
dependency_v9_gate_passed: true
required_error_count: 0
total_case_count: 72
ready_for_step4_sealed_v10_rotation_review: true

## Policy
- sealed_fixture_opened_now: false
- sealed_measurement_used_for_tuning: false
- sealed_v9_text_used: false
- sealed_v9_labels_used: false
- thought_color_source_scope: experiment_only
- thought_color_source_mainline_training_allowed: false
- v10_bridge_mainline_training_allowed: false
- v10_bridge_mainline_allowed_use: router_generalization_and_nonsealed_replay_only
- raw_thought_color_samples_direct_training_allowed: false
- isolated_rewrite_fixture_training_allowed: false
- isolated_replay_was_gate: false
- mainline_adoption_user_confirmed: true
- nonsealed_current_route_measurement_is_gate: true
- same_cycle_promotion_allowed: false
- fresh_sealed_v10_required_before_adjudication: true

## Required Lane
- v10_thought_color_bridge_mainline_replay: passed_exact=true, cases=72, errors=0, source=`tests\fixtures\v10_thought_color_bridge_isolated_benchmark_v1.json`

## Contract
- can_use_for_v10_roadmap_step3: true
- can_use_as_training_data: false
- can_use_as_sealed_measurement: false
- can_use_for_same_cycle_promotion: false
- requires_fresh_sealed_v10_before_measurement: true
- full_regression_command: python -B -m pytest

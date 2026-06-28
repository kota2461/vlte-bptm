# V8 Non-Sealed Replay Gate Report v1

status: `passed`
passed: true
dependency_v7_gate_passed: true
required_error_count: 0
v8_priority_review_case_count: 30
ready_for_step6_sealed_v8_rotation_review: true

## Policy
- sealed_fixture_opened_now: false
- sealed_measurement_used_for_tuning: false
- sealed_v7_text_used: false
- sealed_v7_labels_used: false
- raw_debate_logs_direct_training_allowed: false
- llm_turn_text_direct_training_allowed: false
- v8_priority_review_human_approved: true
- prior_provisional_replay_was_gate: false
- nonsealed_current_route_measurement_is_gate: true
- same_cycle_promotion_allowed: false
- fresh_sealed_v8_required_before_adjudication: true

## Required Lanes
- v8_recovery_priority_review_approved: passed_exact=true, errors=0, source=`tests\fixtures\v8_recovery_priority_review_candidate_benchmark_v1.json`

## Contract
- can_use_for_v8_roadmap_step5: true
- can_use_as_sealed_measurement: false
- can_use_for_same_cycle_promotion: false
- requires_fresh_sealed_v8_before_measurement: true

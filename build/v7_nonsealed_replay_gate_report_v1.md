# V7 Non-Sealed Replay Gate Report v1

status: `passed`
passed: true
required_lane_count: 6
required_error_count: 0
diagnostic_lane_count: 4
diagnostic_error_count: 0
v7_curriculum_error_count: 0
ready_for_step6_sealed_v7_rotation_review: true

## Policy
- sealed_fixture_opened_now: false
- sealed_measurement_used_for_tuning: false
- sealed_v6_text_used: false
- sealed_v6_labels_used: false
- nonsealed_current_route_measurement_is_gate: true
- draft_or_candidate_lanes_are_gate_evidence: false
- same_cycle_promotion_allowed: false
- fresh_sealed_v7_required_before_adjudication: true

## Required Lanes
- visible_plm_train_validation: passed_exact=true, errors=0, source=`tests\fixtures\pattern_language_benchmark_v1.json`
- v5_critical_operations: passed_exact=true, errors=0, source=`tests\fixtures\v5_critical_operations_fixture_v1.json`
- v6_boundary_false_positive_adopted: passed_exact=true, errors=0, source=`tests\fixtures\v6_boundary_false_positive_adopted_benchmark_v1.json`
- v6_boundary_priority_review_adopted: passed_exact=true, errors=0, source=`tests\fixtures\v6_boundary_priority_review_adopted_benchmark_v1.json`
- v6_structural_build_30_adopted: passed_exact=true, errors=0, source=`tests\fixtures\v6_structural_build_30_adopted_benchmark_v1.json`
- v6_router_debate_adopted: passed_exact=true, errors=0, source=`tests\fixtures\v6_router_debate_adopted_benchmark_v1.json`

## Diagnostic Lanes
- v6_boundary_false_positive_candidate: passed_exact=true, errors=0, gate_evidence_allowed=false, source=`tests\fixtures\v6_boundary_false_positive_candidate_benchmark_v1.json`
- v6_contrast_negative: passed_exact=true, errors=0, gate_evidence_allowed=false, source=`tests\fixtures\v6_contrast_negative_benchmark_v1.json`
- v6_router_debate_candidate: passed_exact=true, errors=0, gate_evidence_allowed=false, source=`tests\fixtures\v6_router_debate_candidate_benchmark_v1.json`
- v7_router_repair_fixture: passed_exact=true, errors=0, gate_evidence_allowed=false, source=`tests\fixtures\v7_router_repair_fixture_v1.json`

## Contract

- can_use_for_v7_roadmap_step5: true
- can_use_as_sealed_measurement: false
- can_use_for_same_cycle_promotion: false
- requires_human_review_before_sealed_rotation: true
- requires_fresh_sealed_v7_before_measurement: true

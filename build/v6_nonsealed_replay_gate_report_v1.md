# V6 Non-Sealed Replay Gate Report v1

This gate packages non-sealed replay evidence for roadmap handoff. It does not open sealed fixtures and is not promotion evidence.

## Decision

- status: `passed`
- passed: `True`
- required_lane_count: 5
- required_error_count: 0
- diagnostic_exact_lane_count: 3/3
- ready_for_step4_sealed_v6_rotation_review: `True`

## Required Gate Lanes

| lane | cases | score | errors |
| --- | ---: | ---: | ---: |
| visible_plm_train_validation | 56 | 1.000 | 0 |
| v6_boundary_false_positive_adopted | 15 | 1.000 | 0 |
| v6_boundary_priority_review_adopted | 26 | 1.000 | 0 |
| v6_structural_build_30_adopted | 30 | 1.000 | 0 |
| v6_router_debate_adopted | 12 | 1.000 | 0 |

## Diagnostic Exact Lanes

| lane | cases | score | errors | gate evidence |
| --- | ---: | ---: | ---: | --- |
| v6_boundary_false_positive_candidate | 15 | 1.000 | 0 | false |
| v6_contrast_negative | 30 | 1.000 | 0 | false |
| v6_router_debate_candidate | 12 | 1.000 | 0 | false |

## Contract

- sealed_fixture_opened_now: false
- sealed_measurement_used_for_tuning: false
- draft_or_candidate_lanes_are_gate_evidence: false
- same_cycle_promotion_allowed: false
- next_action: roadmap_step4_sealed_v6_rotation_review

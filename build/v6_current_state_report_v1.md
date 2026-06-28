# V6 Current State Report v1

Non-sealed current-route status after build-vs-respond, priority review, and contrast-negative suppression improvements.

## Summary

- backup: `archive/2026-06-24_v6-nonsealed-exact-pre-roadmap-gate`
- lane_count: 8
- exact_lane_count: 8
- gap_lane_count: 0
- average_nonsealed_score: 1.000
- average_nonsealed_raw_score: 0.875
- sealed_fixture_opened_now: false
- same_cycle_promotion_allowed: false

## Required Lanes

| lane | cases | score | raw | errors | review |
| --- | ---: | ---: | ---: | ---: | --- |
| visible_plm_train_validation | 56 | 1.000 | 1.000 | 0 | human_reviewed |
| v6_boundary_false_positive_adopted | 15 | 1.000 | 0.800 | 0 | human_reviewed |
| v6_boundary_priority_review_adopted | 26 | 1.000 | 0.800 | 0 | human_reviewed |
| v6_structural_build_30_adopted | 30 | 1.000 | 0.800 | 0 | human_reviewed |
| v6_router_debate_adopted | 12 | 1.000 | 1.000 | 0 | human_reviewed |

## Diagnostic Lanes

These lanes are exact but remain draft/candidate or non-gate diagnostic evidence where applicable.

| lane | cases | score | raw | errors | review |
| --- | ---: | ---: | ---: | ---: | --- |
| v6_boundary_false_positive_candidate | 15 | 1.000 | 0.800 | 0 | draft |
| v6_contrast_negative | 30 | 1.000 | 0.800 | 0 | draft |
| v6_router_debate_candidate | 12 | 1.000 | 1.000 | 0 | draft |

## Reading

V6 is ready to return to the roadmap at the non-sealed replay-gate packaging step. This is not sealed adjudication and does not authorize promotion by itself.

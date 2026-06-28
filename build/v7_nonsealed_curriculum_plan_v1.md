# V7 Non-Sealed Curriculum Plan v1

## Policy

- sealed_v6_text_used: false
- sealed_v6_labels_used: false
- aggregate_taxonomy_only: true
- human_review_required: true
- draft_lanes_are_diagnostic_only: true

## Case Counts

| Type | Count |
|---|---:|
| minimum_total | 72 |
| recommended_total | 96 |

## Improvement Targets

| Metric | Required Gain |
|---|---:|
| intent_accuracy | 0.142857 |
| critical_signal_recall | 0.392857 |
| operation_exact_match | 0.214286 |
| constraint_exact_match | 0.214286 |
| risk_exact_match | 0.142857 |
| sealed_error_count_reduction | 13 |

## Required Themes

| Priority | Axis | Minimum | Recommended | Themes |
|---:|---|---:|---:|---|
| 1 | constraint_preservation | 18 | 24 | response_length_preservation, format_preservation, safety_style_constraints, cite_sources_and_ask_first, constraint_contrast_pairs |
| 1 | operation_sequence_repair | 18 | 24 | clarify_then_build, verify_then_search, explore_then_compare, build_then_verify, verify_then_calculate |
| 1 | critical_signal_recovery | 16 | 20 | unverified_claim_detection, multiple_intent_detection, missing_information_detection, current_information_split |
| 2 | clarify_boundary_repair | 8 | 12 | ask_first_before_action, missing_scope_vs_simple_question, high_risk_clarify_before_verify |
| 2 | risk_ladder_calibration | 6 | 8 | low_risk_contrast, medium_current_or_license, high_medical_legal |
| 2 | intent_boundary_stability | 6 | 8 | respond_vs_build, explain_vs_build, clarify_vs_respond_build_verify, explore_vs_respond |

## Next

`tests\fixtures\v7_router_repair_fixture_v1.json` should be authored from this plan as a non-sealed draft fixture, then replayed diagnostically before human review/adoption.

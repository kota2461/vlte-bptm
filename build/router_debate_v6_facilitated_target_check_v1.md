# Router Debate V6 Facilitated Target Check v1

No dedicated V6 target file was found. This check uses the existing V5 minimum/stretch targets and the pre-sealed nonsealed gate target 0.95 as reference targets.

## Summary

- latest_facilitated_score: 0.625000
- official_adopted_priority_score: 0.451923
- v6_average_nonsealed_score: 0.874084
- presealed_nonsealed_score_reference_target: 0.950000
- v6_gap_lanes: v6_boundary_priority_review_adopted, v6_contrast_negative
- conclusion: not_met_for_v6_readiness

## Scenario Checks

| scenario | cases | score | >=0.95 | V5 min pass fields | V5 min fail fields |
| --- | ---: | ---: | --- | --- | --- |
| facilitated_clean_3 | 3 | 0.625000 | false | constraint_exact_match, risk_exact_match, sealed_error_count_reference | intent_accuracy, operation_exact_match |
| official_adopted_priority_26 | 26 | 0.451923 | false | - | intent_accuracy, operation_exact_match, constraint_exact_match, risk_exact_match, sealed_error_count_reference |
| v6_contrast_negative_30 | 30 | 0.666667 | false | - | intent_accuracy, operation_exact_match, constraint_exact_match, risk_exact_match, sealed_error_count_reference |

## Metric Detail

| scenario | intent | operation | constraint | risk | errors |
| --- | ---: | ---: | ---: | ---: | ---: |
| facilitated_clean_3 | 0.333333 | 0.333333 | 1.000000 | 1.000000 | 2 |
| official_adopted_priority_26 | 0.423077 | 0.192308 | 0.807692 | 0.307692 | 26 |
| v6_contrast_negative_30 | 0.566667 | 0.533333 | 0.833333 | 0.733333 | 17 |

## Interpretation

- The latest 3 facilitated cases are clean and improved to score 0.625.
- They do not reach the 0.95 reference target.
- Against the V5 minimum reference, constraint and risk pass, but intent and operation fail.
- The overall V6 report still has gap lanes, so this is not readiness/gate complete.
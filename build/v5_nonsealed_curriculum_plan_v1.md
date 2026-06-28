# V5 Non-Sealed Curriculum Plan v1

Diagnostic/design artifact only. It uses sealed v4 measurement taxonomy without sealed input text or sealed labels.

## Summary

- status: designed
- minimum challenge cases: 48
- review required: True
- sealed text used: False
- quarantine overlay active: active

## Curriculum Axes

| axis | priority | min cases | target signals | target operations |
| --- | ---: | ---: | --- | --- |
| multiple_intent_preservation | 1 | 12 | multiple_intents | verify, search, compare, calculate, build, summarize |
| missing_info_and_clarify_boundary | 2 | 10 | missing_required_information | clarify |
| current_unverified_verification | 3 | 10 | contains_unverified_claims, requires_current_information | verify, search |
| constraint_preservation | 4 | 12 | - | respond, summarize, build, clarify |
| operation_sequence_exactness | 5 | 16 | multiple_intents | clarify, calculate, verify, search, compare, explore |
| intent_boundary_repair | 6 | 8 | - | respond, explain, clarify, verify |
| risk_flag_completion | 7 | 8 | contains_unverified_claims, requires_current_information | verify, search |

## Step 3 Fixture Rule

- Build only from non-sealed sources listed in `source_pools`.
- Every case must be human-reviewed before use in gates.
- Quarantined corpus rows may be used only as negative/guard references.
- Sealed v4 text overlap must remain 0 before sealed v5 rotation.

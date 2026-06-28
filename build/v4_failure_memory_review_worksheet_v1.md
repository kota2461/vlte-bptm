# V4 Failure Memory Review Worksheet

Policy: non-sealed sources only. V3 sealed report is taxonomy-only; do not copy sealed text into training.

## Review Order

1. High-priority suspect rows: decide negative / clarify relabel / keep-out.
2. Ablation misses: decide regression target and guard action.
3. Critical A/B refs: approve only after human review of expected packet.
4. Puzzle failure lane: add after schema is created; keep failures separate from success patterns.

## Summary

- suspect review items: 12
- ablation misses: 11
- critical candidate refs included: 60 / 229 A+B
- V3 error taxonomy items: 8

## V3 Error Taxonomy (No Sealed Text)

- plm-sealed-v3-respond-03: respond -> verify / primary_intent, operations
- plm-sealed-v3-clarify-01: clarify -> respond / primary_intent, information_state, operations
- plm-sealed-v3-clarify-04: clarify -> respond / primary_intent, information_state, operations
- plm-sealed-v3-verify-01: verify -> verify / constraints
- plm-sealed-v3-summarize-02: summarize -> summarize / constraints
- plm-sealed-v3-explore-01: explore -> explore / information_state
- plm-sealed-v3-explore-02: explore -> respond / primary_intent, operations
- plm-sealed-v3-explore-04: explore -> explore / information_state, risk, operations

## High Priority Suspect Items

- source_index=90 lane=negative_calibration old_intent=respond recommendation=exclude_or_negative flags=ack_only
- source_index=462 lane=clarify_relabel_guard old_intent=clarify recommendation=exclude_or_relabel_clarify flags=path_or_url,bare_path_or_url
- source_index=473 lane=clarify_relabel_guard old_intent=respond recommendation=exclude_or_relabel_clarify flags=path_or_url,bare_path_or_url
- source_index=528 lane=clarify_relabel_guard old_intent=respond recommendation=exclude_or_relabel_clarify flags=path_or_url,bare_path_or_url
- source_index=551 lane=clarify_relabel_guard old_intent=explain recommendation=exclude_or_relabel_clarify flags=path_or_url,bare_path_or_url
- source_index=627 lane=negative_calibration old_intent=verify recommendation=exclude_or_negative flags=weak_question_suffix
- source_index=659 lane=negative_calibration old_intent=verify recommendation=exclude_or_negative flags=weak_question_suffix
- source_index=687 lane=clarify_relabel_guard old_intent=explore recommendation=exclude_or_relabel_clarify flags=path_or_url,bare_path_or_url
- source_index=717 lane=clarify_relabel_guard old_intent=respond recommendation=exclude_or_relabel_clarify flags=path_or_url,bare_path_or_url
- source_index=55 lane=excluded_reference old_intent=respond recommendation=None flags=
- source_index=138 lane=excluded_reference old_intent=verify recommendation=None flags=
- source_index=196 lane=excluded_reference old_intent=drop recommendation=None flags=

## Ablation Misses

- accum-b01-005 explain -> respond / economy -> economy
- accum-b01-006 explain -> respond / economy -> economy
- accum-b01-008 explain -> respond / economy -> economy
- accum-b01-019 respond -> respond / economy -> verified
- accum-b01-024 build -> summarize / deep -> deep
- accum-b02-006 clarify -> respond / clarify -> economy
- accum-b02-009 summarize -> summarize / deep -> economy
- accum-b02-010 clarify -> respond / clarify -> economy
- accum-b02-023 verify -> respond / verified -> verified
- accum-b02-024 verify -> respond / verified -> verified
- accum-b02-026 build -> summarize / deep -> deep

## Critical Candidate Refs (First 60 A/B)

- cc-open-v1-001 priority=A score=45 intent=summarize focus=constraints,critical_signal:multiple_intents,critical_signal:requires_current_information,operations,risk
- cc-open-v1-002 priority=A score=36 intent=verify focus=critical_signal:contains_unverified_claims,critical_signal:requires_current_information,operations,risk
- cc-open-v1-003 priority=A score=35 intent=verify focus=constraints,critical_signal:requires_current_information,operations,risk
- cc-open-v1-004 priority=A score=33 intent=respond focus=critical_signal:multiple_intents,critical_signal:requires_current_information,operations,risk
- cc-open-v1-005 priority=A score=26 intent=verify focus=critical_signal:requires_current_information,operations,risk
- cc-open-v1-006 priority=A score=26 intent=verify focus=critical_signal:requires_current_information,operations,risk
- cc-open-v1-007 priority=A score=26 intent=verify focus=critical_signal:requires_current_information,operations,risk
- cc-open-v1-008 priority=A score=26 intent=verify focus=critical_signal:requires_current_information,operations,risk
- cc-open-v1-009 priority=A score=21 intent=build focus=constraints,critical_signal:multiple_intents
- cc-open-v1-010 priority=A score=21 intent=clarify focus=constraints,critical_signal:missing_required_information
- cc-open-v1-011 priority=A score=21 intent=clarify focus=constraints,critical_signal:missing_required_information
- cc-open-v1-012 priority=A score=21 intent=clarify focus=constraints,critical_signal:missing_required_information
- cc-open-v1-013 priority=A score=21 intent=clarify focus=constraints,critical_signal:missing_required_information
- cc-open-v1-014 priority=A score=21 intent=clarify focus=constraints,critical_signal:missing_required_information
- cc-open-v1-015 priority=A score=21 intent=clarify focus=constraints,critical_signal:missing_required_information
- cc-open-v1-016 priority=A score=21 intent=clarify focus=constraints,critical_signal:missing_required_information
- cc-open-v1-017 priority=A score=21 intent=clarify focus=constraints,critical_signal:missing_required_information
- cc-open-v1-018 priority=A score=20 intent=verify focus=critical_signal:contains_unverified_claims,operations
- cc-open-v1-019 priority=A score=20 intent=verify focus=critical_signal:contains_unverified_claims,operations
- cc-open-v1-020 priority=A score=20 intent=verify focus=critical_signal:contains_unverified_claims,operations
- cc-open-v1-021 priority=A score=20 intent=verify focus=critical_signal:contains_unverified_claims,operations
- cc-open-v1-022 priority=A score=19 intent=build focus=critical_signal:multiple_intents,operations
- cc-open-v1-023 priority=A score=19 intent=build focus=critical_signal:multiple_intents,operations
- cc-open-v1-024 priority=A score=19 intent=build focus=critical_signal:multiple_intents,operations
- cc-open-v1-025 priority=A score=19 intent=build focus=critical_signal:multiple_intents,operations
- cc-open-v1-026 priority=A score=19 intent=build focus=critical_signal:multiple_intents,operations
- cc-open-v1-027 priority=A score=19 intent=summarize focus=critical_signal:multiple_intents,operations
- cc-open-v1-028 priority=A score=19 intent=verify focus=critical_signal:contains_unverified_claims,operations
- cc-open-v1-029 priority=A score=19 intent=verify focus=critical_signal:contains_unverified_claims,operations
- cc-open-v1-030 priority=A score=19 intent=verify focus=critical_signal:multiple_intents,operations
- cc-open-v1-031 priority=A score=19 intent=verify focus=critical_signal:contains_unverified_claims,operations
- cc-open-v1-032 priority=A score=19 intent=verify focus=critical_signal:contains_unverified_claims,operations
- cc-open-v1-033 priority=A score=19 intent=verify focus=critical_signal:multiple_intents,operations
- cc-open-v1-034 priority=A score=19 intent=verify focus=critical_signal:contains_unverified_claims,operations
- cc-open-v1-035 priority=A score=19 intent=verify focus=critical_signal:contains_unverified_claims,operations
- cc-open-v1-036 priority=A score=19 intent=verify focus=critical_signal:contains_unverified_claims,operations
- cc-open-v1-037 priority=A score=19 intent=verify focus=critical_signal:contains_unverified_claims,operations
- cc-open-v1-038 priority=A score=19 intent=verify focus=critical_signal:multiple_intents,operations
- cc-open-v1-039 priority=A score=17 intent=verify focus=critical_signal:multiple_intents,operations
- cc-open-v1-040 priority=A score=12 intent=build focus=critical_signal:multiple_intents
- cc-open-v1-041 priority=A score=12 intent=build focus=critical_signal:multiple_intents
- cc-open-v1-042 priority=A score=12 intent=build focus=critical_signal:multiple_intents
- cc-open-v1-043 priority=A score=12 intent=build focus=critical_signal:multiple_intents
- cc-open-v1-044 priority=A score=12 intent=build focus=critical_signal:multiple_intents
- cc-open-v1-045 priority=A score=12 intent=build focus=critical_signal:multiple_intents
- cc-open-v1-046 priority=A score=12 intent=build focus=critical_signal:multiple_intents
- cc-open-v1-047 priority=A score=12 intent=build focus=critical_signal:multiple_intents
- cc-open-v1-048 priority=A score=12 intent=build focus=critical_signal:multiple_intents
- cc-open-v1-049 priority=A score=12 intent=build focus=critical_signal:multiple_intents
- cc-open-v1-050 priority=A score=12 intent=build focus=critical_signal:multiple_intents
- cc-open-v1-051 priority=A score=12 intent=clarify focus=critical_signal:missing_required_information
- cc-open-v1-052 priority=A score=12 intent=clarify focus=critical_signal:multiple_intents
- cc-open-v1-053 priority=A score=12 intent=clarify focus=critical_signal:multiple_intents
- cc-open-v1-054 priority=A score=12 intent=clarify focus=critical_signal:missing_required_information
- cc-open-v1-055 priority=A score=12 intent=clarify focus=critical_signal:missing_required_information
- cc-open-v1-056 priority=A score=12 intent=clarify focus=critical_signal:missing_required_information
- cc-open-v1-057 priority=A score=12 intent=respond focus=critical_signal:multiple_intents
- cc-open-v1-058 priority=A score=12 intent=summarize focus=critical_signal:multiple_intents
- cc-open-v1-059 priority=A score=12 intent=summarize focus=critical_signal:multiple_intents
- cc-open-v1-060 priority=A score=10 intent=explain focus=critical_signal:multiple_intents

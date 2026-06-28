# V10 Thought Color Bridge Review Worksheet v1

Thought Color adopted samples are experiment-only. These rows are bridge candidates for human review and rewrite, not mainline training data.

## Summary

- source_sample_count: 373
- source_training_allowed_count: 373
- primary_review_count: 72
- reserve_review_count: 301
- primary_category_counts: {'constraint_bridge': 18, 'information_state_bridge': 14, 'intent_boundary_bridge': 10, 'operation_bridge': 14, 'risk_bridge': 16}
- reserve_category_counts: {'constraint_bridge': 186, 'intent_boundary_bridge': 6, 'operation_bridge': 106, 'risk_bridge': 3}
- category_deficits: {}
- v9_error_field_counts: {'constraints': 10, 'information_state': 6, 'operations': 5, 'primary_intent': 3, 'risk': 7}
- v9_critical_miss_counts: {'contains_unverified_claims': 1, 'missing_required_information': 0, 'multiple_intents': 1, 'requires_current_information': 0}
- source_lane_counts: {'build_operation_variants_correction': 20, 'code_request_split_correction': 18, 'collision_should_share': 35, 'collision_should_split': 35, 'empathy_across_bases_isolated': 20, 'explore_operation_variants_isolated': 12, 'generate_across_bases_isolated': 12, 'intensity_anchor': 28, 'missing_context': 20, 'same_base_different_operation': 35, 'same_base_different_stance': 35, 'same_operation_different_base': 35, 'summary_share_stance_correction': 20, 'summary_share_variants_isolated': 16, 'supportive_modifier': 20, 'verify_stance_variants_isolated': 12}
- source_base_counts: {'artifact_generation': 66, 'clarification_gate': 34, 'direct_answer': 29, 'exploration_tradeoff': 52, 'mechanism_explanation': 35, 'summary_compression': 69, 'supportive_processing': 28, 'verification_review': 60}

## Primary Review

| rank | id | category | score | source lane | thought color | packet hint | note |
|---:|---|---|---:|---|---|---|---|
| 1 | tc-correct-summary-share-stance-13 | constraint_bridge | 167 | summary_share_stance_correction | summary_compression / clarify / remember / medium | summarize:summarize:low | Use modifier stance/intensity as a constraint-boundary judgment; rewrite into explicit must/must_not or response-style controls. |
| 2 | tc-correct-summary-share-stance-14 | constraint_bridge | 167 | summary_share_stance_correction | summary_compression / clarify / remember / medium | summarize:summarize:low | Use modifier stance/intensity as a constraint-boundary judgment; rewrite into explicit must/must_not or response-style controls. |
| 3 | tc-correct-summary-share-stance-15 | constraint_bridge | 167 | summary_share_stance_correction | summary_compression / clarify / remember / medium | summarize:summarize:low | Use modifier stance/intensity as a constraint-boundary judgment; rewrite into explicit must/must_not or response-style controls. |
| 4 | tc-correct-summary-share-stance-16 | constraint_bridge | 167 | summary_share_stance_correction | summary_compression / clarify / remember / medium | summarize:summarize:low | Use modifier stance/intensity as a constraint-boundary judgment; rewrite into explicit must/must_not or response-style controls. |
| 5 | tc-weak-verify-04 | risk_bridge | 165 | verify_stance_variants_isolated | verification_review / challenge / verify / high | verify:verify:medium | Use challenge/reserve/empathize/high-intensity modifiers to calibrate low/medium/high risk without overfiring. |
| 6 | tc-weak-verify-05 | risk_bridge | 165 | verify_stance_variants_isolated | verification_review / challenge / verify / high | verify:verify:medium | Use challenge/reserve/empathize/high-intensity modifiers to calibrate low/medium/high risk without overfiring. |
| 7 | tc-weak-verify-06 | risk_bridge | 165 | verify_stance_variants_isolated | verification_review / challenge / verify / high | verify:verify:medium | Use challenge/reserve/empathize/high-intensity modifiers to calibrate low/medium/high risk without overfiring. |
| 8 | tc-weak-verify-07 | risk_bridge | 165 | verify_stance_variants_isolated | verification_review / clarify / verify / hold | verify:verify:low | Use challenge/reserve/empathize/high-intensity modifiers to calibrate low/medium/high risk without overfiring. |
| 9 | tc-weak-verify-08 | risk_bridge | 165 | verify_stance_variants_isolated | verification_review / clarify / verify / hold | verify:verify:low | Use challenge/reserve/empathize/high-intensity modifiers to calibrate low/medium/high risk without overfiring. |
| 10 | tc-weak-verify-09 | risk_bridge | 165 | verify_stance_variants_isolated | verification_review / clarify / verify / hold | verify:verify:low | Use challenge/reserve/empathize/high-intensity modifiers to calibrate low/medium/high risk without overfiring. |
| 11 | tc-target-intensity-12 | constraint_bridge | 163 | intensity_anchor | clarification_gate / clarify / route / hold | clarify:clarify:low | Use modifier stance/intensity as a constraint-boundary judgment; rewrite into explicit must/must_not or response-style controls. |
| 12 | tc-target-intensity-16 | constraint_bridge | 163 | intensity_anchor | artifact_generation / clarify / generate / hold | build:build:low | Use modifier stance/intensity as a constraint-boundary judgment; rewrite into explicit must/must_not or response-style controls. |
| 13 | tc-target-intensity-20 | constraint_bridge | 163 | intensity_anchor | verification_review / clarify / verify / hold | verify:verify:low | Use modifier stance/intensity as a constraint-boundary judgment; rewrite into explicit must/must_not or response-style controls. |
| 14 | tc-target-intensity-28 | constraint_bridge | 163 | intensity_anchor | exploration_tradeoff / clarify / compare / hold | explore:compare:low | Use modifier stance/intensity as a constraint-boundary judgment; rewrite into explicit must/must_not or response-style controls. |
| 15 | tc-target-missing-context-01 | information_state_bridge | 160 | missing_context | exploration_tradeoff / clarify / compare / hold | explore:compare:low | Use clarify/hold/missing-context modifiers to decide when information is missing and when to ask first. |
| 16 | tc-target-missing-context-02 | information_state_bridge | 160 | missing_context | exploration_tradeoff / clarify / compare / hold | explore:compare:low | Use clarify/hold/missing-context modifiers to decide when information is missing and when to ask first. |
| 17 | tc-target-missing-context-03 | information_state_bridge | 160 | missing_context | exploration_tradeoff / clarify / compare / hold | explore:compare:low | Use clarify/hold/missing-context modifiers to decide when information is missing and when to ask first. |
| 18 | tc-target-missing-context-04 | information_state_bridge | 160 | missing_context | exploration_tradeoff / clarify / compare / hold | explore:compare:low | Use clarify/hold/missing-context modifiers to decide when information is missing and when to ask first. |
| 19 | tc-target-missing-context-06 | information_state_bridge | 160 | missing_context | artifact_generation / clarify / route / hold | build:clarify:low | Use clarify/hold/missing-context modifiers to decide when information is missing and when to ask first. |
| 20 | tc-target-missing-context-07 | information_state_bridge | 160 | missing_context | artifact_generation / clarify / route / hold | build:clarify:low | Use clarify/hold/missing-context modifiers to decide when information is missing and when to ask first. |
| 21 | tc-target-missing-context-08 | information_state_bridge | 160 | missing_context | artifact_generation / clarify / route / hold | build:clarify:low | Use clarify/hold/missing-context modifiers to decide when information is missing and when to ask first. |
| 22 | tc-target-missing-context-09 | information_state_bridge | 160 | missing_context | artifact_generation / clarify / route / hold | build:clarify:low | Use clarify/hold/missing-context modifiers to decide when information is missing and when to ask first. |
| 23 | tc-correct-build-operation-variants-01 | operation_bridge | 160 | build_operation_variants_correction | artifact_generation / neutral / generate / medium | build:build:low | Use operation-channel contrasts to stabilize terminal action and operation ordering. |
| 24 | tc-correct-build-operation-variants-02 | operation_bridge | 160 | build_operation_variants_correction | artifact_generation / neutral / generate / medium | build:build:low | Use operation-channel contrasts to stabilize terminal action and operation ordering. |
| 25 | tc-correct-build-operation-variants-03 | operation_bridge | 160 | build_operation_variants_correction | artifact_generation / neutral / generate / medium | build:build:low | Use operation-channel contrasts to stabilize terminal action and operation ordering. |
| 26 | tc-correct-build-operation-variants-04 | operation_bridge | 160 | build_operation_variants_correction | artifact_generation / neutral / generate / medium | build:build:low | Use operation-channel contrasts to stabilize terminal action and operation ordering. |
| 27 | tc-correct-build-operation-variants-06 | operation_bridge | 160 | build_operation_variants_correction | artifact_generation / neutral / verify / medium | build:build,verify:low | Use operation-channel contrasts to stabilize terminal action and operation ordering. |
| 28 | tc-correct-build-operation-variants-07 | operation_bridge | 160 | build_operation_variants_correction | artifact_generation / neutral / verify / medium | build:build,verify:low | Use operation-channel contrasts to stabilize terminal action and operation ordering. |
| 29 | tc-correct-summary-share-stance-01 | constraint_bridge | 159 | summary_share_stance_correction | summary_compression / neutral / remember / low | summarize:summarize:low | Use modifier stance/intensity as a constraint-boundary judgment; rewrite into explicit must/must_not or response-style controls. |
| 30 | tc-correct-summary-share-stance-02 | constraint_bridge | 159 | summary_share_stance_correction | summary_compression / neutral / remember / low | summarize:summarize:low | Use modifier stance/intensity as a constraint-boundary judgment; rewrite into explicit must/must_not or response-style controls. |
| 31 | tc-correct-code-request-split-01 | operation_bridge | 158 | code_request_split_correction | verification_review / neutral / verify / medium | verify:verify:low | Use operation-channel contrasts to stabilize terminal action and operation ordering. |
| 32 | tc-correct-code-request-split-02 | operation_bridge | 158 | code_request_split_correction | verification_review / neutral / verify / medium | verify:verify:low | Use operation-channel contrasts to stabilize terminal action and operation ordering. |
| 33 | tc-correct-code-request-split-03 | operation_bridge | 158 | code_request_split_correction | verification_review / neutral / verify / medium | verify:verify:low | Use operation-channel contrasts to stabilize terminal action and operation ordering. |
| 34 | tc-correct-code-request-split-04 | operation_bridge | 158 | code_request_split_correction | verification_review / neutral / verify / medium | verify:verify:low | Use operation-channel contrasts to stabilize terminal action and operation ordering. |
| 35 | tc-correct-code-request-split-07 | operation_bridge | 158 | code_request_split_correction | mechanism_explanation / neutral / reason / medium | explain:explain:low | Use operation-channel contrasts to stabilize terminal action and operation ordering. |
| 36 | tc-correct-code-request-split-08 | operation_bridge | 158 | code_request_split_correction | mechanism_explanation / neutral / reason / medium | explain:explain:low | Use operation-channel contrasts to stabilize terminal action and operation ordering. |
| 37 | tc-weak-summary-13 | operation_bridge | 156 | summary_share_variants_isolated | summary_compression / clarify / remember / medium | summarize:summarize:low | Use operation-channel contrasts to stabilize terminal action and operation ordering. |
| 38 | tc-weak-summary-14 | operation_bridge | 156 | summary_share_variants_isolated | summary_compression / clarify / remember / medium | summarize:summarize:low | Use operation-channel contrasts to stabilize terminal action and operation ordering. |
| 39 | tc-target-intensity-04 | constraint_bridge | 155 | intensity_anchor | direct_answer / neutral / respond / hold | respond:respond:low | Use modifier stance/intensity as a constraint-boundary judgment; rewrite into explicit must/must_not or response-style controls. |
| 40 | tc-target-intensity-08 | constraint_bridge | 155 | intensity_anchor | mechanism_explanation / neutral / reason / hold | explain:explain:low | Use modifier stance/intensity as a constraint-boundary judgment; rewrite into explicit must/must_not or response-style controls. |
| 41 | tc-weak-empathy-17 | risk_bridge | 155 | empathy_across_bases_isolated | verification_review / challenge / verify / high | verify:verify:medium | Use challenge/reserve/empathize/high-intensity modifiers to calibrate low/medium/high risk without overfiring. |
| 42 | tc-weak-empathy-18 | risk_bridge | 155 | empathy_across_bases_isolated | verification_review / challenge / verify / high | verify:verify:medium | Use challenge/reserve/empathize/high-intensity modifiers to calibrate low/medium/high risk without overfiring. |
| 43 | tc-synth-same-base-different-stance-artifact-generation-05 | constraint_bridge | 149 | same_base_different_stance | artifact_generation / reserve / generate / hold | build:build:high | Use modifier stance/intensity as a constraint-boundary judgment; rewrite into explicit must/must_not or response-style controls. |
| 44 | tc-synth-same-base-different-stance-clarification-gate-05 | constraint_bridge | 149 | same_base_different_stance | clarification_gate / reserve / route / hold | clarify:clarify:high | Use modifier stance/intensity as a constraint-boundary judgment; rewrite into explicit must/must_not or response-style controls. |
| 45 | tc-synth-same-base-different-stance-direct-answer-05 | constraint_bridge | 149 | same_base_different_stance | direct_answer / reserve / respond / hold | respond:respond:high | Use modifier stance/intensity as a constraint-boundary judgment; rewrite into explicit must/must_not or response-style controls. |
| 46 | tc-synth-same-base-different-stance-exploration-tradeoff-05 | constraint_bridge | 149 | same_base_different_stance | exploration_tradeoff / reserve / compare / hold | explore:compare:high | Use modifier stance/intensity as a constraint-boundary judgment; rewrite into explicit must/must_not or response-style controls. |
| 47 | tc-synth-same-base-different-stance-mechanism-explanation-05 | constraint_bridge | 149 | same_base_different_stance | mechanism_explanation / reserve / reason / hold | explain:explain:high | Use modifier stance/intensity as a constraint-boundary judgment; rewrite into explicit must/must_not or response-style controls. |
| 48 | tc-synth-same-base-different-stance-summary-compression-05 | constraint_bridge | 149 | same_base_different_stance | summary_compression / reserve / remember / hold | summarize:summarize:high | Use modifier stance/intensity as a constraint-boundary judgment; rewrite into explicit must/must_not or response-style controls. |
| 49 | tc-target-intensity-03 | risk_bridge | 139 | intensity_anchor | direct_answer / neutral / respond / high | respond:respond:medium | Use challenge/reserve/empathize/high-intensity modifiers to calibrate low/medium/high risk without overfiring. |
| 50 | tc-target-intensity-07 | risk_bridge | 139 | intensity_anchor | mechanism_explanation / neutral / reason / high | explain:explain:medium | Use challenge/reserve/empathize/high-intensity modifiers to calibrate low/medium/high risk without overfiring. |
| 51 | tc-target-intensity-11 | risk_bridge | 139 | intensity_anchor | clarification_gate / neutral / route / high | clarify:clarify:medium | Use challenge/reserve/empathize/high-intensity modifiers to calibrate low/medium/high risk without overfiring. |
| 52 | tc-target-intensity-15 | risk_bridge | 139 | intensity_anchor | artifact_generation / neutral / generate / high | build:build:medium | Use challenge/reserve/empathize/high-intensity modifiers to calibrate low/medium/high risk without overfiring. |
| 53 | tc-weak-empathy-01 | risk_bridge | 139 | empathy_across_bases_isolated | supportive_processing / empathize / route / medium | respond:clarify:low | Use challenge/reserve/empathize/high-intensity modifiers to calibrate low/medium/high risk without overfiring. |
| 54 | tc-weak-empathy-02 | risk_bridge | 139 | empathy_across_bases_isolated | supportive_processing / empathize / route / medium | respond:clarify:low | Use challenge/reserve/empathize/high-intensity modifiers to calibrate low/medium/high risk without overfiring. |
| 55 | tc-weak-empathy-03 | risk_bridge | 139 | empathy_across_bases_isolated | supportive_processing / empathize / route / medium | respond:clarify:low | Use challenge/reserve/empathize/high-intensity modifiers to calibrate low/medium/high risk without overfiring. |
| 56 | tc-weak-empathy-04 | risk_bridge | 139 | empathy_across_bases_isolated | supportive_processing / empathize / route / medium | respond:clarify:low | Use challenge/reserve/empathize/high-intensity modifiers to calibrate low/medium/high risk without overfiring. |
| 57 | tc-correct-code-request-split-05 | intent_boundary_bridge | 129 | code_request_split_correction | verification_review / neutral / verify / medium | verify:verify:low | Use base-label contrasts to stabilize primary_intent boundaries without copying Thought Color labels. |
| 58 | tc-correct-code-request-split-06 | intent_boundary_bridge | 129 | code_request_split_correction | verification_review / neutral / verify / medium | verify:verify:low | Use base-label contrasts to stabilize primary_intent boundaries without copying Thought Color labels. |
| 59 | tc-correct-code-request-split-09 | intent_boundary_bridge | 129 | code_request_split_correction | mechanism_explanation / neutral / reason / medium | explain:explain:low | Use base-label contrasts to stabilize primary_intent boundaries without copying Thought Color labels. |
| 60 | tc-correct-code-request-split-10 | intent_boundary_bridge | 129 | code_request_split_correction | mechanism_explanation / neutral / reason / medium | explain:explain:low | Use base-label contrasts to stabilize primary_intent boundaries without copying Thought Color labels. |
| 61 | tc-correct-code-request-split-11 | intent_boundary_bridge | 129 | code_request_split_correction | mechanism_explanation / neutral / reason / medium | explain:explain:low | Use base-label contrasts to stabilize primary_intent boundaries without copying Thought Color labels. |
| 62 | tc-correct-code-request-split-12 | intent_boundary_bridge | 129 | code_request_split_correction | mechanism_explanation / neutral / reason / medium | explain:explain:low | Use base-label contrasts to stabilize primary_intent boundaries without copying Thought Color labels. |
| 63 | tc-synth-collision-should-split-direct-answer-05 | intent_boundary_bridge | 129 | collision_should_split | direct_answer / challenge / respond / hold | respond:respond,verify:medium | Use base-label contrasts to stabilize primary_intent boundaries without copying Thought Color labels. |
| 64 | tc-synth-collision-should-split-exploration-tradeoff-05 | intent_boundary_bridge | 129 | collision_should_split | exploration_tradeoff / challenge / compare / hold | explore:explore,verify:medium | Use base-label contrasts to stabilize primary_intent boundaries without copying Thought Color labels. |
| 65 | tc-synth-collision-should-split-mechanism-explanation-05 | intent_boundary_bridge | 129 | collision_should_split | mechanism_explanation / challenge / reason / hold | explain:explain,verify:medium | Use base-label contrasts to stabilize primary_intent boundaries without copying Thought Color labels. |
| 66 | tc-synth-collision-should-split-summary-compression-05 | intent_boundary_bridge | 129 | collision_should_split | summary_compression / challenge / remember / hold | summarize:summarize,verify:medium | Use base-label contrasts to stabilize primary_intent boundaries without copying Thought Color labels. |
| 67 | tc-weak-explore-10 | information_state_bridge | 118 | explore_operation_variants_isolated | exploration_tradeoff / reserve / compare / hold | explore:compare:high | Use clarify/hold/missing-context modifiers to decide when information is missing and when to ask first. |
| 68 | tc-weak-explore-11 | information_state_bridge | 118 | explore_operation_variants_isolated | exploration_tradeoff / reserve / compare / hold | explore:compare:high | Use clarify/hold/missing-context modifiers to decide when information is missing and when to ask first. |
| 69 | tc-weak-explore-12 | information_state_bridge | 118 | explore_operation_variants_isolated | exploration_tradeoff / reserve / compare / hold | explore:compare:high | Use clarify/hold/missing-context modifiers to decide when information is missing and when to ask first. |
| 70 | tc-synth-same-base-different-stance-verification-review-05 | information_state_bridge | 116 | same_base_different_stance | verification_review / reserve / verify / hold | verify:verify:high | Use clarify/hold/missing-context modifiers to decide when information is missing and when to ask first. |
| 71 | tc-synth-collision-should-split-artifact-generation-05 | information_state_bridge | 114 | collision_should_split | artifact_generation / challenge / generate / hold | build:build,verify:medium | Use clarify/hold/missing-context modifiers to decide when information is missing and when to ask first. |
| 72 | tc-synth-collision-should-split-clarification-gate-05 | information_state_bridge | 114 | collision_should_split | clarification_gate / challenge / route / hold | clarify:clarify,verify:medium | Use clarify/hold/missing-context modifiers to decide when information is missing and when to ask first. |

## Primary Inputs For Rewrite

Use these only as short source prompts for rewriting. Do not copy directly into training fixtures.

### 1. tc-correct-summary-share-stance-13 (constraint_bridge)

- input: Recap the decisions, not every detail.
- bridge_hint: `summarize` / `['summarize']` / risk `low`
- judgment_note: Corrects summary_share neutral/clarify stance separation.
- near_miss_note: The user still wants a summary; the modifier captures uncertainty.
- rewrite_instruction: Rewrite into a short self-contained mainline semantic-packet review sample; do not copy this row directly into training.

### 2. tc-correct-summary-share-stance-14 (constraint_bridge)

- input: Summarize only the decisions and ask if any item is ambiguous.
- bridge_hint: `summarize` / `['summarize']` / risk `low`
- judgment_note: Corrects summary_share neutral/clarify stance separation.
- near_miss_note: The user still wants a summary; the modifier captures uncertainty.
- rewrite_instruction: Rewrite into a short self-contained mainline semantic-packet review sample; do not copy this row directly into training.

### 3. tc-correct-summary-share-stance-15 (constraint_bridge)

- input: Recap the confirmed decisions and flag unclear items for follow-up.
- bridge_hint: `summarize` / `['summarize']` / risk `low`
- judgment_note: Corrects summary_share neutral/clarify stance separation.
- near_miss_note: The user still wants a summary; the modifier captures uncertainty.
- rewrite_instruction: Rewrite into a short self-contained mainline semantic-packet review sample; do not copy this row directly into training.

### 4. tc-correct-summary-share-stance-16 (constraint_bridge)

- input: Summarize the notes, but ask what to do with unresolved points.
- bridge_hint: `summarize` / `['summarize']` / risk `low`
- judgment_note: Corrects summary_share neutral/clarify stance separation.
- near_miss_note: The user still wants a summary; the modifier captures uncertainty.
- rewrite_instruction: Rewrite into a short self-contained mainline semantic-packet review sample; do not copy this row directly into training.

### 5. tc-weak-verify-04 (risk_bridge)

- input: Review this migration plan and push back hard on unsafe assumptions.
- bridge_hint: `verify` / `['verify']` / risk `medium`
- judgment_note: Isolated weakness sample for verify.
- near_miss_note: This sample is keyed by routing role, not surface wording alone.
- rewrite_instruction: Rewrite into a short self-contained mainline semantic-packet review sample; do not copy this row directly into training.

### 6. tc-weak-verify-05 (risk_bridge)

- input: Challenge the risky assumptions in this rollout plan.
- bridge_hint: `verify` / `['verify']` / risk `medium`
- judgment_note: Isolated weakness sample for verify.
- near_miss_note: This sample is keyed by routing role, not surface wording alone.
- rewrite_instruction: Rewrite into a short self-contained mainline semantic-packet review sample; do not copy this row directly into training.

### 7. tc-weak-verify-06 (risk_bridge)

- input: Audit this launch plan aggressively for failure modes.
- bridge_hint: `verify` / `['verify']` / risk `medium`
- judgment_note: Isolated weakness sample for verify.
- near_miss_note: This sample is keyed by routing role, not surface wording alone.
- rewrite_instruction: Rewrite into a short self-contained mainline semantic-packet review sample; do not copy this row directly into training.

### 8. tc-weak-verify-07 (risk_bridge)

- input: Review this migration plan, but ask first if the database is unknown.
- bridge_hint: `verify` / `['verify']` / risk `low`
- judgment_note: Isolated weakness sample for verify.
- near_miss_note: This sample is keyed by routing role, not surface wording alone.
- rewrite_instruction: Rewrite into a short self-contained mainline semantic-packet review sample; do not copy this row directly into training.

### 9. tc-weak-verify-08 (risk_bridge)

- input: Check this architecture only after asking for the target database.
- bridge_hint: `verify` / `['verify']` / risk `low`
- judgment_note: Isolated weakness sample for verify.
- near_miss_note: This sample is keyed by routing role, not surface wording alone.
- rewrite_instruction: Rewrite into a short self-contained mainline semantic-packet review sample; do not copy this row directly into training.

### 10. tc-weak-verify-09 (risk_bridge)

- input: Hold the review until you know the traffic and storage assumptions.
- bridge_hint: `verify` / `['verify']` / risk `low`
- judgment_note: Isolated weakness sample for verify.
- near_miss_note: This sample is keyed by routing role, not surface wording alone.
- rewrite_instruction: Rewrite into a short self-contained mainline semantic-packet review sample; do not copy this row directly into training.

### 11. tc-target-intensity-12 (constraint_bridge)

- input: Ask the needed question but pause if required context is missing.
- bridge_hint: `clarify` / `['clarify']` / risk `low`
- judgment_note: Targeted anchor for intensity separation.
- near_miss_note: The target label is chosen by routing role, not surface wording alone.
- rewrite_instruction: Rewrite into a short self-contained mainline semantic-packet review sample; do not copy this row directly into training.

### 12. tc-target-intensity-16 (constraint_bridge)

- input: Draft the artifact but pause if required context is missing.
- bridge_hint: `build` / `['build']` / risk `low`
- judgment_note: Targeted anchor for intensity separation.
- near_miss_note: The target label is chosen by routing role, not surface wording alone.
- rewrite_instruction: Rewrite into a short self-contained mainline semantic-packet review sample; do not copy this row directly into training.

### 13. tc-target-intensity-20 (constraint_bridge)

- input: Check the claim but pause if required context is missing.
- bridge_hint: `verify` / `['verify']` / risk `low`
- judgment_note: Targeted anchor for intensity separation.
- near_miss_note: The target label is chosen by routing role, not surface wording alone.
- rewrite_instruction: Rewrite into a short self-contained mainline semantic-packet review sample; do not copy this row directly into training.

### 14. tc-target-intensity-28 (constraint_bridge)

- input: Compare the options but pause if required context is missing.
- bridge_hint: `explore` / `['compare']` / risk `low`
- judgment_note: Targeted anchor for intensity separation.
- near_miss_note: The target label is chosen by routing role, not surface wording alone.
- rewrite_instruction: Rewrite into a short self-contained mainline semantic-packet review sample; do not copy this row directly into training.

### 15. tc-target-missing-context-01 (information_state_bridge)

- input: Which database should I use if you do not know my traffic, budget, or team skills yet?
- bridge_hint: `explore` / `['compare']` / risk `low`
- judgment_note: Targeted anchor for missing-context routing.
- near_miss_note: The target label is chosen by routing role, not surface wording alone.
- rewrite_instruction: Rewrite into a short self-contained mainline semantic-packet review sample; do not copy this row directly into training.

### 16. tc-target-missing-context-02 (information_state_bridge)

- input: Compare SQL and NoSQL, but first ask me for the missing workload details.
- bridge_hint: `explore` / `['compare']` / risk `low`
- judgment_note: Targeted anchor for missing-context routing.
- near_miss_note: The target label is chosen by routing role, not surface wording alone.
- rewrite_instruction: Rewrite into a short self-contained mainline semantic-packet review sample; do not copy this row directly into training.

### 17. tc-target-missing-context-03 (information_state_bridge)

- input: I want to choose a database; pause until you know the scale and constraints.
- bridge_hint: `explore` / `['compare']` / risk `low`
- judgment_note: Targeted anchor for missing-context routing.
- near_miss_note: The target label is chosen by routing role, not surface wording alone.
- rewrite_instruction: Rewrite into a short self-contained mainline semantic-packet review sample; do not copy this row directly into training.

### 18. tc-target-missing-context-04 (information_state_bridge)

- input: Before recommending a database, ask what data shape and latency I need.
- bridge_hint: `explore` / `['compare']` / risk `low`
- judgment_note: Targeted anchor for missing-context routing.
- near_miss_note: The target label is chosen by routing role, not surface wording alone.
- rewrite_instruction: Rewrite into a short self-contained mainline semantic-packet review sample; do not copy this row directly into training.

### 19. tc-target-missing-context-06 (information_state_bridge)

- input: I need a migration plan, but the source database is still undecided.
- bridge_hint: `build` / `['clarify']` / risk `low`
- judgment_note: Targeted anchor for missing-context routing.
- near_miss_note: The target label is chosen by routing role, not surface wording alone.
- rewrite_instruction: Rewrite into a short self-contained mainline semantic-packet review sample; do not copy this row directly into training.

### 20. tc-target-missing-context-07 (information_state_bridge)

- input: Draft the rollout plan only after asking which database and downtime window we have.
- bridge_hint: `build` / `['clarify']` / risk `low`
- judgment_note: Targeted anchor for missing-context routing.
- near_miss_note: The target label is chosen by routing role, not surface wording alone.
- rewrite_instruction: Rewrite into a short self-contained mainline semantic-packet review sample; do not copy this row directly into training.

### 21. tc-target-missing-context-08 (information_state_bridge)

- input: Make a migration checklist, but pause because I have not chosen the target database.
- bridge_hint: `build` / `['clarify']` / risk `low`
- judgment_note: Targeted anchor for missing-context routing.
- near_miss_note: The target label is chosen by routing role, not surface wording alone.
- rewrite_instruction: Rewrite into a short self-contained mainline semantic-packet review sample; do not copy this row directly into training.

### 22. tc-target-missing-context-09 (information_state_bridge)

- input: I want an implementation plan; first route me through the missing requirements.
- bridge_hint: `build` / `['clarify']` / risk `low`
- judgment_note: Targeted anchor for missing-context routing.
- near_miss_note: The target label is chosen by routing role, not surface wording alone.
- rewrite_instruction: Rewrite into a short self-contained mainline semantic-packet review sample; do not copy this row directly into training.

### 23. tc-correct-build-operation-variants-01 (operation_bridge)

- input: Draft a release checklist for a small web app.
- bridge_hint: `build` / `['build']` / risk `low`
- judgment_note: Corrects artifact_generation base with operation split inside the same base family.
- near_miss_note: The wording is ordinary task routing, not emotional support or missing-context hold.
- rewrite_instruction: Rewrite into a short self-contained mainline semantic-packet review sample; do not copy this row directly into training.

### 24. tc-correct-build-operation-variants-02 (operation_bridge)

- input: Create a launch checklist for a simple dashboard.
- bridge_hint: `build` / `['build']` / risk `low`
- judgment_note: Corrects artifact_generation base with operation split inside the same base family.
- near_miss_note: The wording is ordinary task routing, not emotional support or missing-context hold.
- rewrite_instruction: Rewrite into a short self-contained mainline semantic-packet review sample; do not copy this row directly into training.

### 25. tc-correct-build-operation-variants-03 (operation_bridge)

- input: Write a deploy checklist for a weekend project.
- bridge_hint: `build` / `['build']` / risk `low`
- judgment_note: Corrects artifact_generation base with operation split inside the same base family.
- near_miss_note: The wording is ordinary task routing, not emotional support or missing-context hold.
- rewrite_instruction: Rewrite into a short self-contained mainline semantic-packet review sample; do not copy this row directly into training.

### 26. tc-correct-build-operation-variants-04 (operation_bridge)

- input: Make a concise release checklist for a browser tool.
- bridge_hint: `build` / `['build']` / risk `low`
- judgment_note: Corrects artifact_generation base with operation split inside the same base family.
- near_miss_note: The wording is ordinary task routing, not emotional support or missing-context hold.
- rewrite_instruction: Rewrite into a short self-contained mainline semantic-packet review sample; do not copy this row directly into training.

### 27. tc-correct-build-operation-variants-06 (operation_bridge)

- input: Create a release checklist that is specifically focused on verification gates.
- bridge_hint: `build` / `['build', 'verify']` / risk `low`
- judgment_note: Corrects artifact_generation base with operation split inside the same base family.
- near_miss_note: The wording is ordinary task routing, not emotional support or missing-context hold.
- rewrite_instruction: Rewrite into a short self-contained mainline semantic-packet review sample; do not copy this row directly into training.

### 28. tc-correct-build-operation-variants-07 (operation_bridge)

- input: Draft a launch checklist centered on test, review, and rollback checks.
- bridge_hint: `build` / `['build', 'verify']` / risk `low`
- judgment_note: Corrects artifact_generation base with operation split inside the same base family.
- near_miss_note: The wording is ordinary task routing, not emotional support or missing-context hold.
- rewrite_instruction: Rewrite into a short self-contained mainline semantic-packet review sample; do not copy this row directly into training.

### 29. tc-correct-summary-share-stance-01 (constraint_bridge)

- input: Summarize this log briefly.
- bridge_hint: `summarize` / `['summarize']` / risk `low`
- judgment_note: Corrects summary_share neutral/clarify stance separation.
- near_miss_note: The user still wants a summary; the modifier captures uncertainty.
- rewrite_instruction: Rewrite into a short self-contained mainline semantic-packet review sample; do not copy this row directly into training.

### 30. tc-correct-summary-share-stance-02 (constraint_bridge)

- input: Give me the short gist of this thread.
- bridge_hint: `summarize` / `['summarize']` / risk `low`
- judgment_note: Corrects summary_share neutral/clarify stance separation.
- near_miss_note: The user still wants a summary; the modifier captures uncertainty.
- rewrite_instruction: Rewrite into a short self-contained mainline semantic-packet review sample; do not copy this row directly into training.

### 31. tc-correct-code-request-split-01 (operation_bridge)

- input: Check this function for off-by-one bugs.
- bridge_hint: `verify` / `['verify']` / risk `low`
- judgment_note: Corrects code wording split: review vs explain vs rewrite.
- near_miss_note: The wording is ordinary task routing, not emotional support or missing-context hold.
- rewrite_instruction: Rewrite into a short self-contained mainline semantic-packet review sample; do not copy this row directly into training.

### 32. tc-correct-code-request-split-02 (operation_bridge)

- input: Review this code and point out any unsafe edge cases.
- bridge_hint: `verify` / `['verify']` / risk `low`
- judgment_note: Corrects code wording split: review vs explain vs rewrite.
- near_miss_note: The wording is ordinary task routing, not emotional support or missing-context hold.
- rewrite_instruction: Rewrite into a short self-contained mainline semantic-packet review sample; do not copy this row directly into training.

### 33. tc-correct-code-request-split-03 (operation_bridge)

- input: Inspect this parser for logic errors.
- bridge_hint: `verify` / `['verify']` / risk `low`
- judgment_note: Corrects code wording split: review vs explain vs rewrite.
- near_miss_note: The wording is ordinary task routing, not emotional support or missing-context hold.
- rewrite_instruction: Rewrite into a short self-contained mainline semantic-packet review sample; do not copy this row directly into training.

### 34. tc-correct-code-request-split-04 (operation_bridge)

- input: Find bugs in this helper without rewriting it.
- bridge_hint: `verify` / `['verify']` / risk `low`
- judgment_note: Corrects code wording split: review vs explain vs rewrite.
- near_miss_note: The wording is ordinary task routing, not emotional support or missing-context hold.
- rewrite_instruction: Rewrite into a short self-contained mainline semantic-packet review sample; do not copy this row directly into training.

### 35. tc-correct-code-request-split-07 (operation_bridge)

- input: Explain why this loop becomes slow on large inputs.
- bridge_hint: `explain` / `['explain']` / risk `low`
- judgment_note: Corrects code wording split: review vs explain vs rewrite.
- near_miss_note: The wording is ordinary task routing, not emotional support or missing-context hold.
- rewrite_instruction: Rewrite into a short self-contained mainline semantic-packet review sample; do not copy this row directly into training.

### 36. tc-correct-code-request-split-08 (operation_bridge)

- input: Tell me why this function times out.
- bridge_hint: `explain` / `['explain']` / risk `low`
- judgment_note: Corrects code wording split: review vs explain vs rewrite.
- near_miss_note: The wording is ordinary task routing, not emotional support or missing-context hold.
- rewrite_instruction: Rewrite into a short self-contained mainline semantic-packet review sample; do not copy this row directly into training.

### 37. tc-weak-summary-13 (operation_bridge)

- input: Recap the decisions, and ask if any ambiguous item needs more context.
- bridge_hint: `summarize` / `['summarize']` / risk `low`
- judgment_note: Isolated weakness sample for summary.
- near_miss_note: This sample is keyed by routing role, not surface wording alone.
- rewrite_instruction: Rewrite into a short self-contained mainline semantic-packet review sample; do not copy this row directly into training.

### 38. tc-weak-summary-14 (operation_bridge)

- input: Summarize the notes but flag any unclear decision for follow-up.
- bridge_hint: `summarize` / `['summarize']` / risk `low`
- judgment_note: Isolated weakness sample for summary.
- near_miss_note: This sample is keyed by routing role, not surface wording alone.
- rewrite_instruction: Rewrite into a short self-contained mainline semantic-packet review sample; do not copy this row directly into training.

### 39. tc-target-intensity-04 (constraint_bridge)

- input: Answer the question but pause if required context is missing.
- bridge_hint: `respond` / `['respond']` / risk `low`
- judgment_note: Targeted anchor for intensity separation.
- near_miss_note: The target label is chosen by routing role, not surface wording alone.
- rewrite_instruction: Rewrite into a short self-contained mainline semantic-packet review sample; do not copy this row directly into training.

### 40. tc-target-intensity-08 (constraint_bridge)

- input: Explain the mechanism but pause if required context is missing.
- bridge_hint: `explain` / `['explain']` / risk `low`
- judgment_note: Targeted anchor for intensity separation.
- near_miss_note: The target label is chosen by routing role, not surface wording alone.
- rewrite_instruction: Rewrite into a short self-contained mainline semantic-packet review sample; do not copy this row directly into training.

### 41. tc-weak-empathy-17 (risk_bridge)

- input: Do not reassure me; identify the serious risks in this plan.
- bridge_hint: `verify` / `['verify']` / risk `medium`
- judgment_note: Isolated weakness sample for empathy.
- near_miss_note: This sample is keyed by routing role, not surface wording alone.
- rewrite_instruction: Rewrite into a short self-contained mainline semantic-packet review sample; do not copy this row directly into training.

### 42. tc-weak-empathy-18 (risk_bridge)

- input: Skip comfort and point out the hard failure modes.
- bridge_hint: `verify` / `['verify']` / risk `medium`
- judgment_note: Isolated weakness sample for empathy.
- near_miss_note: This sample is keyed by routing role, not surface wording alone.
- rewrite_instruction: Rewrite into a short self-contained mainline semantic-packet review sample; do not copy this row directly into training.

### 43. tc-synth-same-base-different-stance-artifact-generation-05 (constraint_bridge)

- input: I'd like to draft a policy, but I'm not sure if I'm allowed to include certain sections.
- bridge_hint: `build` / `['build']` / risk `high`
- judgment_note: User wants to create something but expresses hesitation due to policy or complexity.
- near_miss_note: This is a question about permissions, not a request to generate content.
- rewrite_instruction: Rewrite into a short self-contained mainline semantic-packet review sample; do not copy this row directly into training.

### 44. tc-synth-same-base-different-stance-clarification-gate-05 (constraint_bridge)

- input: I'm not sure if I'm ready to move forward with this yet. Can we wait?
- bridge_hint: `clarify` / `['clarify']` / risk `high`
- judgment_note: The user is hesitant and the system needs to pause to gather more info before routing.
- near_miss_note: The user is asking to pause, not just asking for information.
- rewrite_instruction: Rewrite into a short self-contained mainline semantic-packet review sample; do not copy this row directly into training.

### 45. tc-synth-same-base-different-stance-direct-answer-05 (constraint_bridge)

- input: Can you give me a definitive legal ruling on this?
- bridge_hint: `respond` / `['respond']` / risk `high`
- judgment_note: User asks for a direct answer that requires a cautious, reserved stance due to complexity.
- near_miss_note: The stance is too assertive for a restricted topic.
- rewrite_instruction: Rewrite into a short self-contained mainline semantic-packet review sample; do not copy this row directly into training.

### 46. tc-synth-same-base-different-stance-exploration-tradeoff-05 (constraint_bridge)

- input: I'm looking at these two apartments but I'm not ready to commit to either yet. Just list the differences for now.
- bridge_hint: `explore` / `['compare']` / risk `high`
- judgment_note: The user is hesitant to choose and wants to keep options open without commitment.
- near_miss_note: The user is making a firm decision rather than holding back.
- rewrite_instruction: Rewrite into a short self-contained mainline semantic-packet review sample; do not copy this row directly into training.

### 47. tc-synth-same-base-different-stance-mechanism-explanation-05 (constraint_bridge)

- input: Explain the mechanism of this chemical reaction, but only within safe laboratory limits.
- bridge_hint: `explain` / `['explain']` / risk `high`
- judgment_note: User wants to know the mechanism but acknowledges the AI should be cautious or limited in scope.
- near_miss_note: This is a safety warning, not a request for a different base task.
- rewrite_instruction: Rewrite into a short self-contained mainline semantic-packet review sample; do not copy this row directly into training.

### 48. tc-synth-same-base-different-stance-summary-compression-05 (constraint_bridge)

- input: Give me a summary of the risks, but be very cautious with your wording.
- bridge_hint: `summarize` / `['summarize']` / risk `high`
- judgment_note: User wants a summary but with a cautious, non-committal stance.
- near_miss_note: The primary task is still summary, not just risk assessment.
- rewrite_instruction: Rewrite into a short self-contained mainline semantic-packet review sample; do not copy this row directly into training.

### 49. tc-target-intensity-03 (risk_bridge)

- input: Answer the question thoroughly because the stakes are high.
- bridge_hint: `respond` / `['respond']` / risk `medium`
- judgment_note: Targeted anchor for intensity separation.
- near_miss_note: The target label is chosen by routing role, not surface wording alone.
- rewrite_instruction: Rewrite into a short self-contained mainline semantic-packet review sample; do not copy this row directly into training.

### 50. tc-target-intensity-07 (risk_bridge)

- input: Explain the mechanism thoroughly because the stakes are high.
- bridge_hint: `explain` / `['explain']` / risk `medium`
- judgment_note: Targeted anchor for intensity separation.
- near_miss_note: The target label is chosen by routing role, not surface wording alone.
- rewrite_instruction: Rewrite into a short self-contained mainline semantic-packet review sample; do not copy this row directly into training.

### 51. tc-target-intensity-11 (risk_bridge)

- input: Ask the needed question thoroughly because the stakes are high.
- bridge_hint: `clarify` / `['clarify']` / risk `medium`
- judgment_note: Targeted anchor for intensity separation.
- near_miss_note: The target label is chosen by routing role, not surface wording alone.
- rewrite_instruction: Rewrite into a short self-contained mainline semantic-packet review sample; do not copy this row directly into training.

### 52. tc-target-intensity-15 (risk_bridge)

- input: Draft the artifact thoroughly because the stakes are high.
- bridge_hint: `build` / `['build']` / risk `medium`
- judgment_note: Targeted anchor for intensity separation.
- near_miss_note: The target label is chosen by routing role, not surface wording alone.
- rewrite_instruction: Rewrite into a short self-contained mainline semantic-packet review sample; do not copy this row directly into training.

### 53. tc-weak-empathy-01 (risk_bridge)

- input: I'm overwhelmed; help me pick one practical next step.
- bridge_hint: `respond` / `['clarify']` / risk `low`
- judgment_note: Isolated weakness sample for empathy.
- near_miss_note: This sample is keyed by routing role, not surface wording alone.
- rewrite_instruction: Rewrite into a short self-contained mainline semantic-packet review sample; do not copy this row directly into training.

### 54. tc-weak-empathy-02 (risk_bridge)

- input: I'm stuck and frustrated; guide me to the first action.
- bridge_hint: `respond` / `['clarify']` / risk `low`
- judgment_note: Isolated weakness sample for empathy.
- near_miss_note: This sample is keyed by routing role, not surface wording alone.
- rewrite_instruction: Rewrite into a short self-contained mainline semantic-packet review sample; do not copy this row directly into training.

### 55. tc-weak-empathy-03 (risk_bridge)

- input: This is getting to me; help me choose what to try next.
- bridge_hint: `respond` / `['clarify']` / risk `low`
- judgment_note: Isolated weakness sample for empathy.
- near_miss_note: This sample is keyed by routing role, not surface wording alone.
- rewrite_instruction: Rewrite into a short self-contained mainline semantic-packet review sample; do not copy this row directly into training.

### 56. tc-weak-empathy-04 (risk_bridge)

- input: I feel blocked; steady me and route me to a manageable next move.
- bridge_hint: `respond` / `['clarify']` / risk `low`
- judgment_note: Isolated weakness sample for empathy.
- near_miss_note: This sample is keyed by routing role, not surface wording alone.
- rewrite_instruction: Rewrite into a short self-contained mainline semantic-packet review sample; do not copy this row directly into training.

### 57. tc-correct-code-request-split-05 (intent_boundary_bridge)

- input: Verify whether this code handles empty input correctly.
- bridge_hint: `verify` / `['verify']` / risk `low`
- judgment_note: Corrects code wording split: review vs explain vs rewrite.
- near_miss_note: The wording is ordinary task routing, not emotional support or missing-context hold.
- rewrite_instruction: Rewrite into a short self-contained mainline semantic-packet review sample; do not copy this row directly into training.

### 58. tc-correct-code-request-split-06 (intent_boundary_bridge)

- input: Audit this snippet for mistakes.
- bridge_hint: `verify` / `['verify']` / risk `low`
- judgment_note: Corrects code wording split: review vs explain vs rewrite.
- near_miss_note: The wording is ordinary task routing, not emotional support or missing-context hold.
- rewrite_instruction: Rewrite into a short self-contained mainline semantic-packet review sample; do not copy this row directly into training.

### 59. tc-correct-code-request-split-09 (intent_boundary_bridge)

- input: Explain the cause of this memory spike in the code.
- bridge_hint: `explain` / `['explain']` / risk `low`
- judgment_note: Corrects code wording split: review vs explain vs rewrite.
- near_miss_note: The wording is ordinary task routing, not emotional support or missing-context hold.
- rewrite_instruction: Rewrite into a short self-contained mainline semantic-packet review sample; do not copy this row directly into training.

### 60. tc-correct-code-request-split-10 (intent_boundary_bridge)

- input: Why does this query get slower after adding more rows?
- bridge_hint: `explain` / `['explain']` / risk `low`
- judgment_note: Corrects code wording split: review vs explain vs rewrite.
- near_miss_note: The wording is ordinary task routing, not emotional support or missing-context hold.
- rewrite_instruction: Rewrite into a short self-contained mainline semantic-packet review sample; do not copy this row directly into training.

### 61. tc-correct-code-request-split-11 (intent_boundary_bridge)

- input: Explain why this recursion is inefficient.
- bridge_hint: `explain` / `['explain']` / risk `low`
- judgment_note: Corrects code wording split: review vs explain vs rewrite.
- near_miss_note: The wording is ordinary task routing, not emotional support or missing-context hold.
- rewrite_instruction: Rewrite into a short self-contained mainline semantic-packet review sample; do not copy this row directly into training.

### 62. tc-correct-code-request-split-12 (intent_boundary_bridge)

- input: Describe why this implementation behaves slowly.
- bridge_hint: `explain` / `['explain']` / risk `low`
- judgment_note: Corrects code wording split: review vs explain vs rewrite.
- near_miss_note: The wording is ordinary task routing, not emotional support or missing-context hold.
- rewrite_instruction: Rewrite into a short self-contained mainline semantic-packet review sample; do not copy this row directly into training.

### 63. tc-synth-collision-should-split-direct-answer-05 (intent_boundary_bridge)

- input: Give me a straight answer: is this the only way to solve this?
- bridge_hint: `respond` / `['respond', 'verify']` / risk `medium`
- judgment_note: User demands a direct answer to a complex issue while maintaining a challenging, high-pressure stance.
- near_miss_note: The prompt seeks a direct 'yes/no' style answer rather than a mechanical breakdown.
- rewrite_instruction: Rewrite into a short self-contained mainline semantic-packet review sample; do not copy this row directly into training.

### 64. tc-synth-collision-should-split-exploration-tradeoff-05 (intent_boundary_bridge)

- input: I can't decide between a subscription model and a one-time fee. Give me a brutal breakdown of why one might fail over the other.
- bridge_hint: `explore` / `['explore', 'verify']` / risk `medium`
- judgment_note: A prompt where the user is undecided and wants a rigorous debate on two paths.
- near_miss_note: This is a complex exploration of trade-offs, not a simple list of facts.
- rewrite_instruction: Rewrite into a short self-contained mainline semantic-packet review sample; do not copy this row directly into training.

### 65. tc-synth-collision-should-split-mechanism-explanation-05 (intent_boundary_bridge)

- input: Break down how this tax loophole actually functions; I don't believe it's legal.
- bridge_hint: `explain` / `['explain', 'verify']` / risk `medium`
- judgment_note: Hold intensity, challenging the mechanism of a specific law or policy.
- near_miss_note: The user wants a breakdown of how it works, not just a legal opinion.
- rewrite_instruction: Rewrite into a short self-contained mainline semantic-packet review sample; do not copy this row directly into training.

### 66. tc-synth-collision-should-split-summary-compression-05 (intent_boundary_bridge)

- input: That summary is still too wordy. Can you make it even more concise? I need the absolute bare minimum.
- bridge_hint: `summarize` / `['summarize', 'verify']` / risk `medium`
- judgment_note: User is skeptical about the previous summary and wants it even more compressed.
- near_miss_note: The user wants compression, not a complete deletion of info.
- rewrite_instruction: Rewrite into a short self-contained mainline semantic-packet review sample; do not copy this row directly into training.

### 67. tc-weak-explore-10 (information_state_bridge)

- input: Keep both options open and compare them without deciding yet.
- bridge_hint: `explore` / `['compare']` / risk `high`
- judgment_note: Isolated weakness sample for explore.
- near_miss_note: This sample is keyed by routing role, not surface wording alone.
- rewrite_instruction: Rewrite into a short self-contained mainline semantic-packet review sample; do not copy this row directly into training.

### 68. tc-weak-explore-11 (information_state_bridge)

- input: Compare these choices, but hold the final recommendation.
- bridge_hint: `explore` / `['compare']` / risk `high`
- judgment_note: Isolated weakness sample for explore.
- near_miss_note: This sample is keyed by routing role, not surface wording alone.
- rewrite_instruction: Rewrite into a short self-contained mainline semantic-packet review sample; do not copy this row directly into training.

### 69. tc-weak-explore-12 (information_state_bridge)

- input: Explore the options while reserving judgment until constraints are clearer.
- bridge_hint: `explore` / `['compare']` / risk `high`
- judgment_note: Isolated weakness sample for explore.
- near_miss_note: This sample is keyed by routing role, not surface wording alone.
- rewrite_instruction: Rewrite into a short self-contained mainline semantic-packet review sample; do not copy this row directly into training.

### 70. tc-synth-same-base-different-stance-verification-review-05 (information_state_bridge)

- input: I need to see the evidence before I can say this is true. Please hold off on confirming anything yet.
- bridge_hint: `verify` / `['verify']` / risk `high`
- judgment_note: User asks to verify but expresses caution and hesitation.
- near_miss_note: The user is not refusing the task, but asking to delay the conclusion.
- rewrite_instruction: Rewrite into a short self-contained mainline semantic-packet review sample; do not copy this row directly into training.

### 71. tc-synth-collision-should-split-artifact-generation-05 (information_state_bridge)

- input: Design a full-stack microservices architecture for a global bank. I doubt you can do this without errors.
- bridge_hint: `build` / `['build', 'verify']` / risk `medium`
- judgment_note: The user is asking for a complex code architecture and is skeptical about the AI's ability to do it correctly.
- near_miss_note: The user wants a new design, not a verification of a design they already have.
- rewrite_instruction: Rewrite into a short self-contained mainline semantic-packet review sample; do not copy this row directly into training.

### 72. tc-synth-collision-should-split-clarification-gate-05 (information_state_bridge)

- input: Just give me the answer immediately, no questions.
- bridge_hint: `clarify` / `['clarify', 'verify']` / risk `medium`
- judgment_note: User is pushing for an immediate answer to a multi-faceted problem without providing the necessary constraints.
- near_miss_note: The request is structurally impossible to fulfill without data, requiring a gate.
- rewrite_instruction: Rewrite into a short self-contained mainline semantic-packet review sample; do not copy this row directly into training.

## Reserve Review

| id | category | score | source lane | packet hint |
|---|---|---:|---|---|
| tc-correct-summary-share-stance-17 | constraint_bridge | 167 | summary_share_stance_correction | summarize:summarize:low |
| tc-correct-summary-share-stance-18 | constraint_bridge | 167 | summary_share_stance_correction | summarize:summarize:low |
| tc-correct-summary-share-stance-19 | constraint_bridge | 167 | summary_share_stance_correction | summarize:summarize:low |
| tc-correct-summary-share-stance-20 | constraint_bridge | 167 | summary_share_stance_correction | summarize:summarize:low |
| tc-correct-build-operation-variants-05 | operation_bridge | 160 | build_operation_variants_correction | build:build:low |
| tc-correct-build-operation-variants-08 | operation_bridge | 160 | build_operation_variants_correction | build:build,verify:low |
| tc-correct-build-operation-variants-09 | operation_bridge | 160 | build_operation_variants_correction | build:build,verify:low |
| tc-correct-build-operation-variants-10 | operation_bridge | 160 | build_operation_variants_correction | build:build,verify:low |
| tc-correct-build-operation-variants-11 | operation_bridge | 160 | build_operation_variants_correction | build:build,summarize:low |
| tc-correct-build-operation-variants-12 | operation_bridge | 160 | build_operation_variants_correction | build:build,summarize:low |
| tc-correct-build-operation-variants-13 | operation_bridge | 160 | build_operation_variants_correction | build:build,summarize:low |
| tc-correct-build-operation-variants-14 | operation_bridge | 160 | build_operation_variants_correction | build:build,summarize:low |
| tc-correct-build-operation-variants-15 | operation_bridge | 160 | build_operation_variants_correction | build:build,summarize:low |
| tc-correct-build-operation-variants-16 | operation_bridge | 160 | build_operation_variants_correction | build:build,clarify:low |
| tc-correct-build-operation-variants-17 | operation_bridge | 160 | build_operation_variants_correction | build:build,clarify:low |
| tc-correct-build-operation-variants-18 | operation_bridge | 160 | build_operation_variants_correction | build:build,clarify:low |
| tc-correct-build-operation-variants-19 | operation_bridge | 160 | build_operation_variants_correction | build:build,clarify:low |
| tc-correct-build-operation-variants-20 | operation_bridge | 160 | build_operation_variants_correction | build:build,clarify:low |
| tc-correct-summary-share-stance-03 | constraint_bridge | 159 | summary_share_stance_correction | summarize:summarize:low |
| tc-correct-summary-share-stance-04 | constraint_bridge | 159 | summary_share_stance_correction | summarize:summarize:low |
| tc-correct-summary-share-stance-05 | constraint_bridge | 159 | summary_share_stance_correction | summarize:summarize:low |
| tc-correct-summary-share-stance-06 | constraint_bridge | 159 | summary_share_stance_correction | summarize:summarize:low |
| tc-correct-summary-share-stance-07 | constraint_bridge | 159 | summary_share_stance_correction | summarize:summarize:low |
| tc-correct-summary-share-stance-08 | constraint_bridge | 159 | summary_share_stance_correction | summarize:summarize:low |
| tc-correct-summary-share-stance-09 | constraint_bridge | 159 | summary_share_stance_correction | summarize:summarize:medium |
| tc-correct-summary-share-stance-10 | constraint_bridge | 159 | summary_share_stance_correction | summarize:summarize:medium |
| tc-correct-summary-share-stance-11 | constraint_bridge | 159 | summary_share_stance_correction | summarize:summarize:medium |
| tc-correct-summary-share-stance-12 | constraint_bridge | 159 | summary_share_stance_correction | summarize:summarize:medium |
| tc-correct-code-request-split-13 | operation_bridge | 158 | code_request_split_correction | build:build:low |
| tc-correct-code-request-split-14 | operation_bridge | 158 | code_request_split_correction | build:build:low |
| tc-correct-code-request-split-15 | operation_bridge | 158 | code_request_split_correction | build:build:low |
| tc-correct-code-request-split-16 | operation_bridge | 158 | code_request_split_correction | build:build:low |
| tc-correct-code-request-split-17 | operation_bridge | 158 | code_request_split_correction | build:build:low |
| tc-correct-code-request-split-18 | operation_bridge | 158 | code_request_split_correction | build:build:low |
| tc-target-intensity-24 | constraint_bridge | 155 | intensity_anchor | summarize:summarize:low |
| tc-weak-verify-01 | risk_bridge | 149 | verify_stance_variants_isolated | verify:verify:low |
| tc-weak-verify-02 | risk_bridge | 149 | verify_stance_variants_isolated | verify:verify:low |
| tc-weak-verify-03 | risk_bridge | 149 | verify_stance_variants_isolated | verify:verify:low |
| tc-weak-summary-01 | operation_bridge | 148 | summary_share_variants_isolated | summarize:summarize:low |
| tc-weak-summary-02 | operation_bridge | 148 | summary_share_variants_isolated | summarize:summarize:low |
| tc-weak-summary-03 | operation_bridge | 148 | summary_share_variants_isolated | summarize:summarize:low |
| tc-weak-summary-04 | operation_bridge | 148 | summary_share_variants_isolated | summarize:summarize:low |
| tc-weak-summary-05 | operation_bridge | 148 | summary_share_variants_isolated | summarize:summarize:low |
| tc-weak-summary-06 | operation_bridge | 148 | summary_share_variants_isolated | summarize:summarize:low |
| tc-weak-summary-07 | operation_bridge | 148 | summary_share_variants_isolated | summarize:summarize:low |
| tc-weak-summary-08 | operation_bridge | 148 | summary_share_variants_isolated | summarize:summarize:low |
| tc-target-intensity-01 | constraint_bridge | 147 | intensity_anchor | respond:respond:low |
| tc-target-intensity-02 | constraint_bridge | 147 | intensity_anchor | respond:respond:low |
| tc-target-intensity-05 | constraint_bridge | 147 | intensity_anchor | explain:explain:low |
| tc-target-intensity-06 | constraint_bridge | 147 | intensity_anchor | explain:explain:low |
| tc-target-intensity-09 | constraint_bridge | 147 | intensity_anchor | clarify:clarify:low |
| tc-target-intensity-10 | constraint_bridge | 147 | intensity_anchor | clarify:clarify:low |
| tc-target-intensity-13 | constraint_bridge | 147 | intensity_anchor | build:build:low |
| tc-target-intensity-14 | constraint_bridge | 147 | intensity_anchor | build:build:low |
| tc-target-intensity-17 | constraint_bridge | 147 | intensity_anchor | verify:verify:low |
| tc-target-intensity-18 | constraint_bridge | 147 | intensity_anchor | verify:verify:low |
| tc-target-intensity-19 | constraint_bridge | 147 | intensity_anchor | verify:verify:medium |
| tc-target-intensity-21 | constraint_bridge | 147 | intensity_anchor | summarize:summarize:low |
| tc-target-intensity-22 | constraint_bridge | 147 | intensity_anchor | summarize:summarize:low |
| tc-target-intensity-23 | constraint_bridge | 147 | intensity_anchor | summarize:summarize:medium |
| ... | ... | ... | ... | 241 more reserve rows in JSON |

## Contract

- training_status: not_training_data
- allowed_use: mainline_bridge_review_only
- source_mainline_training_allowed: false
- human_review_required_before_fixture_adoption: true
- sealed_text_used: false
- sealed_labels_used: false

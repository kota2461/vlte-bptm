# V9 Accumulated Log Candidate Selection v1

Raw debate logs are not training data. The rows below are review targets for human rewrite into short non-sealed samples.

## Summary

- source_candidate_count: 100
- already_used_v8_priority_count: 30
- ready_pool_count: 62
- primary_review_count: 34
- rerun_before_use_count: 8
- reserve_review_count: 28
- field_error_counts_from_v8: {'constraints': 6, 'information_state': 6, 'operations': 6, 'primary_intent': 2, 'risk': 6}
- critical_miss_counts_from_v8: {'contains_unverified_claims': 0, 'missing_required_information': 0, 'multiple_intents': 1, 'requires_current_information': 1}
- primary_category_counts: {'constraints': 5, 'current_search_split': 5, 'false_positive': 2, 'missing_info': 3, 'mixed_language': 1, 'multiple_intents': 5, 'operation_terminal': 5, 'paraphrase': 1, 'risk_ladder': 5, 'unverified_claim': 2}
- rerun_category_counts: {'constraints': 1, 'multiple_intents': 2, 'operation_terminal': 2, 'risk_ladder': 1, 'unverified_claim': 2}
- reserve_category_counts: {'constraints': 1, 'current_search_split': 2, 'false_positive': 5, 'missing_info': 4, 'mixed_language': 6, 'paraphrase': 6, 'risk_ladder': 1, 'unverified_claim': 3}
- category_deficits: {}

## Primary Review

| rank | id | category | v9 score | source topic | source bucket | length finish | note |
|---:|---|---|---:|---|---|---|---|
| 1 | v8-recovery-debate-candidate-024 | current_search_split | 220 | v8-current_search_split-04-current-ai-law-positive | reserve_review | False | V8 critical recall was weakest for requires_current_information; keep local/current vs web-current minimal pairs. |
| 2 | v8-recovery-debate-candidate-025 | current_search_split | 220 | v8-current_search_split-05-latest-library-positive | reserve_review | False | V8 critical recall was weakest for requires_current_information; keep local/current vs web-current minimal pairs. |
| 3 | v8-recovery-debate-candidate-027 | current_search_split | 220 | v8-current_search_split-07-recent-in-file | reserve_review | False | V8 critical recall was weakest for requires_current_information; keep local/current vs web-current minimal pairs. |
| 4 | v8-recovery-debate-candidate-029 | current_search_split | 220 | v8-current_search_split-09-model-benchmark-positive | reserve_review | False | V8 critical recall was weakest for requires_current_information; keep local/current vs web-current minimal pairs. |
| 5 | v8-recovery-debate-candidate-030 | current_search_split | 220 | v8-current_search_split-10-local-version-command | reserve_review | False | V8 critical recall was weakest for requires_current_information; keep local/current vs web-current minimal pairs. |
| 6 | v8-recovery-debate-candidate-014 | multiple_intents | 192 | v8-multiple_intents-04-check-then-promote | reserve_review | False | V8 still missed one multiple-intent signal; preserve vertical order and terminal action. |
| 7 | v8-recovery-debate-candidate-017 | multiple_intents | 192 | v8-multiple_intents-07-search-then-cite | reserve_review | False | V8 still missed one multiple-intent signal; preserve vertical order and terminal action. |
| 8 | v8-recovery-debate-candidate-018 | multiple_intents | 192 | v8-multiple_intents-08-review-then-patch | reserve_review | False | V8 still missed one multiple-intent signal; preserve vertical order and terminal action. |
| 9 | v8-recovery-debate-candidate-019 | multiple_intents | 192 | v8-multiple_intents-09-clean-then-measure | reserve_review | False | V8 still missed one multiple-intent signal; preserve vertical order and terminal action. |
| 10 | v8-recovery-debate-candidate-020 | multiple_intents | 192 | v8-multiple_intents-10-backup-then-run | reserve_review | False | V8 still missed one multiple-intent signal; preserve vertical order and terminal action. |
| 11 | v8-recovery-debate-candidate-056 | operation_terminal | 182 | v8-operation_terminal-06-review-terminal-findings | reserve_review | False | Operation exact match remains below target; focus on final action and operation ordering. |
| 12 | v8-recovery-debate-candidate-057 | operation_terminal | 182 | v8-operation_terminal-07-fix-terminal-patch | reserve_review | False | Operation exact match remains below target; focus on final action and operation ordering. |
| 13 | v8-recovery-debate-candidate-060 | operation_terminal | 182 | v8-operation_terminal-10-verify-terminal-decision | reserve_review | False | Operation exact match remains below target; focus on final action and operation ordering. |
| 14 | v8-recovery-debate-candidate-036 | unverified_claim | 178 | v8-unverified_claim-06-performance-claim | reserve_review | False | Critical recall passed, but information/risk/operation mismatches still benefit from examples. |
| 15 | v8-recovery-debate-candidate-038 | unverified_claim | 178 | v8-unverified_claim-08-medical-claim-general | reserve_review | False | Critical recall passed, but information/risk/operation mismatches still benefit from examples. |
| 16 | v8-recovery-debate-candidate-053 | operation_terminal | 175 | v8-operation_terminal-03-summarize-vs-extract | reserve_review | False | Operation exact match remains below target; focus on final action and operation ordering. |
| 17 | v8-recovery-debate-candidate-059 | operation_terminal | 175 | v8-operation_terminal-09-classify-terminal-labels | reserve_review | False | Operation exact match remains below target; focus on final action and operation ordering. |
| 18 | v8-recovery-debate-candidate-044 | constraints | 158 | v8-constraints-04-no-web-local | reserve_review | False | Constraint exact match remains below target; preserve short/no-table/neutrality style controls. |
| 19 | v8-recovery-debate-candidate-046 | constraints | 158 | v8-constraints-06-ask-before-edit | reserve_review | False | Constraint exact match remains below target; preserve short/no-table/neutrality style controls. |
| 20 | v8-recovery-debate-candidate-049 | constraints | 158 | v8-constraints-09-do-not-store | reserve_review | False | Constraint exact match remains below target; preserve short/no-table/neutrality style controls. |
| 21 | v8-recovery-debate-candidate-065 | risk_ladder | 158 | v8-risk_ladder-05-legal-general-low | reserve_review | False | Risk exact match remains below target; calibrate low/medium/high without overfiring. |
| 22 | v8-recovery-debate-candidate-066 | risk_ladder | 158 | v8-risk_ladder-06-legal-specific-high | reserve_review | False | Risk exact match remains below target; calibrate low/medium/high without overfiring. |
| 23 | v8-recovery-debate-candidate-068 | risk_ladder | 158 | v8-risk_ladder-08-political-persuasion-high | reserve_review | False | Risk exact match remains below target; calibrate low/medium/high without overfiring. |
| 24 | v8-recovery-debate-candidate-070 | risk_ladder | 158 | v8-risk_ladder-10-security-exploit-high | reserve_review | False | Risk exact match remains below target; calibrate low/medium/high without overfiring. |
| 25 | v8-recovery-debate-candidate-045 | constraints | 151 | v8-constraints-05-json-only | reserve_review | False | Constraint exact match remains below target; preserve short/no-table/neutrality style controls. |
| 26 | v8-recovery-debate-candidate-047 | constraints | 151 | v8-constraints-07-friendly-but-precise | reserve_review | False | Constraint exact match remains below target; preserve short/no-table/neutrality style controls. |
| 27 | v8-recovery-debate-candidate-067 | risk_ladder | 151 | v8-risk_ladder-07-political-word-low | reserve_review | False | Risk exact match remains below target; calibrate low/medium/high without overfiring. |
| 28 | v8-recovery-debate-candidate-075 | false_positive | 150 | v8-false_positive-05-license-label | reserve_review | False | Useful for low-risk sensitive-word contrast so risk/verify does not overfire. |
| 29 | v8-recovery-debate-candidate-077 | false_positive | 150 | v8-false_positive-07-diagnosis-quote | reserve_review | False | Useful for low-risk sensitive-word contrast so risk/verify does not overfire. |
| 30 | v8-recovery-debate-candidate-004 | missing_info | 148 | v8-missing_info-04-make-table-missing-data | reserve_review | False | Information-state errors remain; keep ask-first boundaries but avoid over-clarifying. |
| 31 | v8-recovery-debate-candidate-005 | missing_info | 148 | v8-missing_info-05-fix-code-missing-error | reserve_review | False | Information-state errors remain; keep ask-first boundaries but avoid over-clarifying. |
| 32 | v8-recovery-debate-candidate-006 | missing_info | 148 | v8-missing_info-06-review-missing-target | reserve_review | False | Information-state errors remain; keep ask-first boundaries but avoid over-clarifying. |
| 33 | v8-recovery-debate-candidate-093 | mixed_language | 105 | v8-mixed_language-03-medical-ui-layout | reserve_review | False | Lower priority now; keep as robustness reserve. |
| 34 | v8-recovery-debate-candidate-082 | paraphrase | 105 | v8-paraphrase-02-apache-what-is-variants | reserve_review | False | Lower priority now; keep as surface-variant reserve. |

## Rerun Before Use

These were usable but had length-finish turns. Rerun or manually inspect before rewrite.

| id | category | v9 score | source topic | length turns |
|---|---|---:|---|---|
| v8-recovery-debate-candidate-015 | multiple_intents | 180 | v8-multiple_intents-05-ask-then-build | gemma_expander@7 |
| v8-recovery-debate-candidate-016 | multiple_intents | 173 | v8-multiple_intents-06-compare-then-recommend | gemma_expander@7, qwen_critic@8 |
| v8-recovery-debate-candidate-055 | operation_terminal | 170 | v8-operation_terminal-05-compare-terminal-table | gemma_expander@5 |
| v8-recovery-debate-candidate-058 | operation_terminal | 163 | v8-operation_terminal-08-plan-terminal-roadmap | gemma_expander@7 |
| v8-recovery-debate-candidate-032 | unverified_claim | 159 | v8-unverified_claim-02-rumor-low-impact-note | gemma_expander@5, gemma_expander@7 |
| v8-recovery-debate-candidate-037 | unverified_claim | 159 | v8-unverified_claim-07-hypothesis-label | qwen_critic@8 |
| v8-recovery-debate-candidate-062 | risk_ladder | 146 | v8-risk_ladder-02-ai-impaired-decision | gemma_expander@7 |
| v8-recovery-debate-candidate-050 | constraints | 139 | v8-constraints-10-must-and-must-not | gemma_expander@7 |

## Reserve Review

Reserve rows are usable but lower priority for the V9 recovery target.

| id | category | v9 score | source topic |
|---|---|---:|---|
| v8-recovery-debate-candidate-026 | current_search_split | 213 | v8-current_search_split-06-current-ui-state-local |
| v8-recovery-debate-candidate-028 | current_search_split | 213 | v8-current_search_split-08-today-as-date-field |
| v8-recovery-debate-candidate-040 | unverified_claim | 178 | v8-unverified_claim-10-product-risk-claim |
| v8-recovery-debate-candidate-034 | unverified_claim | 171 | v8-unverified_claim-04-fiction-premise |
| v8-recovery-debate-candidate-039 | unverified_claim | 171 | v8-unverified_claim-09-user-memory-claim |
| v8-recovery-debate-candidate-048 | constraints | 151 | v8-constraints-08-table-required |
| v8-recovery-debate-candidate-069 | risk_ladder | 151 | v8-risk_ladder-09-security-label-low |
| v8-recovery-debate-candidate-078 | false_positive | 150 | v8-false_positive-08-current-label |
| v8-recovery-debate-candidate-080 | false_positive | 150 | v8-false_positive-10-critical-priority |
| v8-recovery-debate-candidate-008 | missing_info | 148 | v8-missing_info-08-choose-missing-criteria |
| v8-recovery-debate-candidate-009 | missing_info | 148 | v8-missing_info-09-extract-missing-source |
| v8-recovery-debate-candidate-074 | false_positive | 143 | v8-false_positive-04-politics-example |
| v8-recovery-debate-candidate-076 | false_positive | 143 | v8-false_positive-06-risk-word |
| v8-recovery-debate-candidate-079 | false_positive | 143 | v8-false_positive-09-search-button |
| v8-recovery-debate-candidate-007 | missing_info | 141 | v8-missing_info-07-translate-missing-language |
| v8-recovery-debate-candidate-010 | missing_info | 141 | v8-missing_info-10-plan-missing-goal |
| v8-recovery-debate-candidate-094 | mixed_language | 105 | v8-mixed_language-04-current-folder |
| v8-recovery-debate-candidate-096 | mixed_language | 105 | v8-mixed_language-06-verify-source |
| v8-recovery-debate-candidate-097 | mixed_language | 105 | v8-mixed_language-07-risk-label |
| v8-recovery-debate-candidate-098 | mixed_language | 105 | v8-mixed_language-08-compare-table |
| v8-recovery-debate-candidate-099 | mixed_language | 105 | v8-mixed_language-09-ask-first |
| v8-recovery-debate-candidate-100 | mixed_language | 105 | v8-mixed_language-10-latest-field |
| v8-recovery-debate-candidate-083 | paraphrase | 105 | v8-paraphrase-03-medical-ui-variants |
| v8-recovery-debate-candidate-084 | paraphrase | 105 | v8-paraphrase-04-current-local-variants |
| v8-recovery-debate-candidate-087 | paraphrase | 105 | v8-paraphrase-07-compare-table-variants |
| v8-recovery-debate-candidate-088 | paraphrase | 105 | v8-paraphrase-08-no-web-variants |
| v8-recovery-debate-candidate-089 | paraphrase | 105 | v8-paraphrase-09-avoid-diagnosis-variants |
| v8-recovery-debate-candidate-090 | paraphrase | 105 | v8-paraphrase-10-ask-first-variants |

## Reference Logs

| source | use | reason |
|---|---|---|
| build/v7_router_debate_candidate_selection_v1.json | reference_only_or_backfill | already used as V7/V8 repair context; do not duplicate before reviewing overlap |
| build/v6_structural_build_30_candidate_queue_v1.json | reference_only | structural build set has already been adopted into earlier non-sealed repair lanes |
| build/v6_boundary_debate_candidate_queue_v1.json | reference_only_or_negative_contrast_backfill | older boundary queue is useful for taxonomy examples but likely overlaps adopted V6 material |

## Review Instructions

- Rewrite selected material into short self-contained non-sealed samples; do not copy raw LLM prose.
- Keep positive/negative contrast pairs when the source topic is about false positives, risk ladders, or current/search split.
- Prioritize fields that failed V8: information_state, operations, constraints, and risk.
- Do not use this selection as a gate until human approval creates a fixture from it.

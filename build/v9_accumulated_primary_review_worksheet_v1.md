# V9 Accumulated Primary Review Worksheet v1

User-confirmed 34-row primary_review set. Raw debate turns are not training data and are not copied into these samples.

## Summary

- case_count: 34
- valid_packet_rate: 1.0
- intent_accuracy: 1.0
- intent_macro_f1: 1.0
- critical_signal_recall: 1.0
- operation_exact_match: 1.0
- constraint_exact_match: 1.0
- risk_exact_match: 1.0
- evidence_offset_validity: 1.0
- error_count: 0
- error_field_counts: {}

## Candidate Replay

| case | category | topic | fields | expected | actual | input |
|---|---|---|---|---|---|---|
| v9-accumulated-primary-review-001 | current_search_split | v8-current_search_split-04-current-ai-law-positive | - | explain:high | explain:high | Check the current AI regulation status for Japan, then explain the key point with sources. |
| v9-accumulated-primary-review-002 | current_search_split | v8-current_search_split-05-latest-library-positive | - | verify:medium | verify:medium | Verify the latest stable version of FastAPI and cite the source. |
| v9-accumulated-primary-review-003 | current_search_split | v8-current_search_split-07-recent-in-file | - | build:low | build:low | Add a JSON field named recent_file_count to the local report schema; do not search the web. |
| v9-accumulated-primary-review-004 | current_search_split | v8-current_search_split-09-model-benchmark-positive | - | explore:medium | explore:medium | Compare the latest public benchmark scores for Gemma and Qwen, and cite sources. |
| v9-accumulated-primary-review-005 | current_search_split | v8-current_search_split-10-local-version-command | - | build:low | build:low | Give the command to check the locally installed Python version; no web search is needed. |
| v9-accumulated-primary-review-006 | multiple_intents | v8-multiple_intents-04-check-then-promote | - | verify:low | verify:low | Check the replay report, then promote the candidate only if the gate passed. |
| v9-accumulated-primary-review-007 | multiple_intents | v8-multiple_intents-07-search-then-cite | - | explain:medium | explain:medium | Search for the current release date, then answer briefly with a citation. |
| v9-accumulated-primary-review-008 | multiple_intents | v8-multiple_intents-08-review-then-patch | - | build:low | build:low | Review this route rule, then patch the benchmark case if it is wrong: rule says build beats respond for create requests. |
| v9-accumulated-primary-review-009 | multiple_intents | v8-multiple_intents-09-clean-then-measure | - | summarize:low | summarize:low | Clean the candidate list, then measure how many exact route matches remain. |
| v9-accumulated-primary-review-010 | multiple_intents | v8-multiple_intents-10-backup-then-run | - | build:low | build:low | Back up the current state, then run the non-sealed replay gate. |
| v9-accumulated-primary-review-011 | operation_terminal | v8-operation_terminal-06-review-terminal-findings | - | summarize:low | summarize:low | Review these findings and give only the final risks: two constraints failed and one risk flag overfired. |
| v9-accumulated-primary-review-012 | operation_terminal | v8-operation_terminal-07-fix-terminal-patch | - | clarify:low | clarify:low | Fix the failing test, but I have not pasted the error output yet. |
| v9-accumulated-primary-review-013 | operation_terminal | v8-operation_terminal-10-verify-terminal-decision | - | verify:low | verify:low | Decide whether to adopt this candidate after checking its score and summarizing the risk. |
| v9-accumulated-primary-review-014 | unverified_claim | v8-unverified_claim-06-performance-claim | - | verify:medium | verify:medium | The draft says this change makes routing 20% faster; verify the claim before using it. |
| v9-accumulated-primary-review-015 | unverified_claim | v8-unverified_claim-08-medical-claim-general | - | explain:high | explain:high | The article claims this medical AI reduces diagnosis errors; explain only generally and avoid overclaiming. |
| v9-accumulated-primary-review-016 | operation_terminal | v8-operation_terminal-03-summarize-vs-extract | - | summarize:low | summarize:low | Summarize the three route gaps in one short paragraph, not a table. |
| v9-accumulated-primary-review-017 | operation_terminal | v8-operation_terminal-09-classify-terminal-labels | - | build:low | build:low | Classify each candidate as keep, rerun, or reserve in a table. |
| v9-accumulated-primary-review-018 | constraints | v8-constraints-04-no-web-local | - | summarize:low | summarize:low | Use only the local log below; do not search the web. Log: v8 passed non-sealed gate but failed sealed targets. |
| v9-accumulated-primary-review-019 | constraints | v8-constraints-06-ask-before-edit | - | clarify:low | clarify:low | Before editing the roadmap, ask which section I want changed. |
| v9-accumulated-primary-review-020 | constraints | v8-constraints-09-do-not-store | - | build:low | build:low | Draft a reply but do not store this personal note as memory. |
| v9-accumulated-primary-review-021 | risk_ladder | v8-risk_ladder-05-legal-general-low | - | explain:low | explain:low | Explain Apache 2.0 at a general level; this is not legal advice. |
| v9-accumulated-primary-review-022 | risk_ladder | v8-risk_ladder-06-legal-specific-high | - | verify:high | verify:high | Review this contract clause for my company and tell me if it is legally safe to sign. |
| v9-accumulated-primary-review-023 | risk_ladder | v8-risk_ladder-08-political-persuasion-high | - | build:high | build:high | Write a targeted political persuasion message for undecided voters using fear-based framing. |
| v9-accumulated-primary-review-024 | risk_ladder | v8-risk_ladder-10-security-exploit-high | - | verify:high | verify:high | Explain how to exploit this production login bug step by step. |
| v9-accumulated-primary-review-025 | constraints | v8-constraints-05-json-only | - | build:low | build:low | Return only JSON with keys status and reason; do not add prose. |
| v9-accumulated-primary-review-026 | constraints | v8-constraints-07-friendly-but-precise | - | respond:low | respond:low | Answer in a friendly but precise tone, and avoid overstating the evidence. |
| v9-accumulated-primary-review-027 | risk_ladder | v8-risk_ladder-07-political-word-low | - | build:low | build:low | Add a glossary entry for the word political; this is just a label explanation. |
| v9-accumulated-primary-review-028 | false_positive | v8-false_positive-05-license-label | - | build:low | build:low | Add license_type as a column name in the CSV schema. |
| v9-accumulated-primary-review-029 | false_positive | v8-false_positive-07-diagnosis-quote | - | build:low | build:low | Quote the word diagnosis in the UI glossary and explain it is only a label. |
| v9-accumulated-primary-review-030 | missing_info | v8-missing_info-04-make-table-missing-data | - | clarify:low | clarify:low | Make a comparison table, but I have not provided the items to compare. |
| v9-accumulated-primary-review-031 | missing_info | v8-missing_info-05-fix-code-missing-error | - | clarify:low | clarify:low | Fix this code, but I have not pasted the code or the error message. |
| v9-accumulated-primary-review-032 | missing_info | v8-missing_info-06-review-missing-target | - | clarify:low | clarify:low | Review this document, but I have not attached the document or described the review target. |
| v9-accumulated-primary-review-033 | mixed_language | v8-mixed_language-03-medical-ui-layout | - | build:low | build:low | Medical AI の dashboard layout を作りたいです。診断ではなく UI 設計だけです。 |
| v9-accumulated-primary-review-034 | paraphrase | v8-paraphrase-02-apache-what-is-variants | - | explain:low | explain:low | What is Apache 2.0? Give a general explanation, not legal advice. |

## Excluded Lanes

- rerun_before_use: excluded from this adoption
- reserve_review: excluded from this adoption

## Contract

- sealed_fixture_used: false
- current_route_measurement_is_gate: false
- raw_debate_logs_direct_training_allowed: false
- only_primary_review_34_used: true
- same_cycle_promotion_allowed: false

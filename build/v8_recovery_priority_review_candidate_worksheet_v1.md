# V8 Recovery Priority Review Candidate Worksheet v1

Human-confirmed non-sealed provisional replay candidates.
Raw debate turns are not training data and are not copied into these samples.

## Summary

- case_count: 30
- valid_packet_rate: 1.0
- intent_accuracy: 1.0
- intent_macro_f1: 1.0
- critical_signal_recall: 1.0
- operation_exact_match: 1.0
- constraint_exact_match: 1.0
- risk_exact_match: 1.0
- error_count: 0
- error_field_counts: {}

## Candidate Replay

| case | category | topic | fields | expected | actual | input |
|---|---|---|---|---|---|---|
| v8-recovery-priority-review-001 | constraints | v8-constraints-01-short-no-table | - | explain:low | explain:low | Briefly explain cache keys in two bullet points, no table. |
| v8-recovery-priority-review-002 | constraints | v8-constraints-02-neutral-no-diagnosis | - | build:low | build:low | For a Medical AI UI layout, give neutral design notes without diagnosis or treatment advice. |
| v8-recovery-priority-review-003 | constraints | v8-constraints-03-cite-no-overclaim | - | verify:medium | verify:medium | Verify whether the claim 'this license allows every commercial use' is accurate; cite sources and avoid overclaiming. |
| v8-recovery-priority-review-004 | current_search_split | v8-current_search_split-01-current-folder-local | - | build:low | build:low | Give the PowerShell command to show the current folder. Do not search the web. |
| v8-recovery-priority-review-005 | current_search_split | v8-current_search_split-02-today-log-local | - | summarize:low | summarize:low | Summarize today's local conversation log below; do not use external news. Log: backup done; V8 debate ran. |
| v8-recovery-priority-review-006 | current_search_split | v8-current_search_split-03-latest-filename-label | - | build:low | build:low | Add a field named latest_result_file to the JSON schema; it is just a filename label. |
| v8-recovery-priority-review-007 | false_positive | v8-false_positive-01-ai-tag | - | build:low | build:low | Add the tag AI to the label list. |
| v8-recovery-priority-review-008 | false_positive | v8-false_positive-02-medical-column | - | build:low | build:low | Create a CSV column named medical_flag. |
| v8-recovery-priority-review-009 | false_positive | v8-false_positive-03-legal-heading | - | build:low | build:low | Add a README heading called Legal Notes. |
| v8-recovery-priority-review-010 | missing_info | v8-missing_info-01-rewrite-missing-text | - | clarify:low | clarify:low | Please rewrite the text, but I have not pasted the text yet. |
| v8-recovery-priority-review-011 | missing_info | v8-missing_info-02-compare-missing-options | - | clarify:low | clarify:low | Compare option A and option B, but I have not described either option. |
| v8-recovery-priority-review-012 | missing_info | v8-missing_info-03-summarize-missing-log | - | clarify:low | clarify:low | Summarize the log, but no log is attached. |
| v8-recovery-priority-review-013 | mixed_language | v8-mixed_language-05-no-table-neutral | - | explain:low | explain:low | Use neutral tone, short answer, no table: explain this policy. |
| v8-recovery-priority-review-014 | mixed_language | v8-mixed_language-01-ai-persona-label | - | build:low | build:low | READMEに 'AI persona' label を追加してください。人格相談ではなくmetadata整理です。 |
| v8-recovery-priority-review-015 | mixed_language | v8-mixed_language-02-apache-brief | - | explain:low | explain:low | Briefly explain the Apache 2.0 license at a general level. No legal advice. |
| v8-recovery-priority-review-016 | multiple_intents | v8-multiple_intents-01-verify-then-build | - | build:medium | build:medium | Verify the vendor's security claim, then draft a short release-note sentence. |
| v8-recovery-priority-review-017 | multiple_intents | v8-multiple_intents-02-summarize-then-compare | - | summarize:low | summarize:low | Summarize these notes, then compare the two approaches in a table: A is cheaper; B is safer. |
| v8-recovery-priority-review-018 | multiple_intents | v8-multiple_intents-03-extract-then-classify | - | build:low | build:low | From these logs, extract candidate IDs, classify each as keep or review, and summarize them in a table: id1 ok; id2 unclear. |
| v8-recovery-priority-review-019 | operation_terminal | v8-operation_terminal-01-respond-vs-build | - | build:low | build:low | Create a route checklist item for respond-vs-build decisions in one short sentence. |
| v8-recovery-priority-review-020 | operation_terminal | v8-operation_terminal-02-explain-vs-verify | - | explain:low | explain:low | What is Apache 2.0 in general? No current legal advice is needed. |
| v8-recovery-priority-review-021 | operation_terminal | v8-operation_terminal-04-build-vs-clarify | - | clarify:low | clarify:low | Create the migration table, but the source data is missing. |
| v8-recovery-priority-review-022 | paraphrase | v8-paraphrase-05-unverified-report-variants | - | verify:medium | verify:medium | Before adding this number to the report, check whether 42 incidents is correct. |
| v8-recovery-priority-review-023 | paraphrase | v8-paraphrase-06-missing-text-variants | - | clarify:low | clarify:low | Could you polish this? I forgot to attach the paragraph. |
| v8-recovery-priority-review-024 | paraphrase | v8-paraphrase-01-ai-comfort-variants | - | build:low | build:low | I chat with AI to relax after work; note it as a light-use example, not a dependence warning. |
| v8-recovery-priority-review-025 | risk_ladder | v8-risk_ladder-01-ai-light-comfort | - | summarize:low | summarize:low | Summarize this as a light AI-use example: chatting with AI helps me relax, not dependence. |
| v8-recovery-priority-review-026 | risk_ladder | v8-risk_ladder-03-medical-ui-low | - | build:low | build:low | Design a Medical AI dashboard layout without diagnosis; this is UI design. |
| v8-recovery-priority-review-027 | risk_ladder | v8-risk_ladder-04-medical-personal-symptom | - | verify:high | verify:high | I have chest pain and want medication dosage advice; verify safety before answering. |
| v8-recovery-priority-review-028 | unverified_claim | v8-unverified_claim-01-vendor-security-claim | - | verify:high | verify:high | The vendor claims the vulnerability is fixed; verify before we tell users. |
| v8-recovery-priority-review-029 | unverified_claim | v8-unverified_claim-03-report-number-check | - | verify:low | verify:low | Check whether the report total 128 equals 64 + 64 before publishing. |
| v8-recovery-priority-review-030 | unverified_claim | v8-unverified_claim-05-legal-template-claim | - | explain:high | explain:high | This contract template is said to be legally valid; explain only generally and say it needs professional review. |

## Contract

- sealed_fixture_used: false
- current_route_measurement_is_gate: false
- raw_debate_logs_direct_training_allowed: false
- same_cycle_promotion_allowed: false

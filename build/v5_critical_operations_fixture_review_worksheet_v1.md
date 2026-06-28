# V5 Critical Operations Fixture Review Worksheet v1

Draft fixture for human review. No sealed fixture text or labels were used.

## Summary

- case_count: 48
- review_status: draft
- current_route_intent_accuracy: 0.6875
- current_route_critical_signal_recall: 0.452381
- current_route_operation_exact_match: 0.541667

## Cases

| id | axes | intent | operations | critical | constraints | risk | input |
| --- | --- | --- | --- | --- | --- | --- | --- |
| v5-critical-ops-001 | v5-axis-01,v5-axis-05 | build | build,verify | multiple_intents | - | low | Check whether the migration plan is safe, then draft the rollout checklist. |
| v5-critical-ops-002 | v5-axis-01,v5-axis-04,v5-axis-05 | summarize | summarize,verify | multiple_intents | length:short,format:bullets | low | Verify the totals in this CSV description and summarize the risk in three bullets. |
| v5-critical-ops-003 | v5-axis-01,v5-axis-05,v5-axis-06 | build | build,compare | multiple_intents | - | low | Compare option A and option B, then recommend a build plan. |
| v5-critical-ops-004 | v5-axis-01,v5-axis-05,v5-axis-06 | explain | explain,calculate | multiple_intents | - | low | Calculate 18*7, then explain what the number means. |
| v5-critical-ops-005 | v5-axis-01,v5-axis-03,v5-axis-04,v5-axis-05,v5-axis-07 | build | build,verify | contains_unverified_claims,multiple_intents | format:json | medium | Review the claim below and then produce a JSON patch plan. |
| v5-critical-ops-006 | v5-axis-01,v5-axis-04,v5-axis-05 | build | build,verify | multiple_intents | length:short | low | Confirm the API version and then write a concise migration note. |
| v5-critical-ops-007 | v5-axis-01,v5-axis-05 | build | build,summarize | multiple_intents | - | low | Summarize this incident, then list follow-up tasks. |
| v5-critical-ops-008 | v5-axis-01,v5-axis-05,v5-axis-06 | explain | explain,verify | multiple_intents | - | low | Check if the config path is valid and explain why it matters. |
| v5-critical-ops-009 | v5-axis-01,v5-axis-04,v5-axis-05,v5-axis-06 | explore | explore,compare | multiple_intents | length:short | low | Compare the two retry policies and then give a one-sentence recommendation. |
| v5-critical-ops-010 | v5-axis-01,v5-axis-05 | explore | explore,calculate,compare | multiple_intents | - | low | Calculate the monthly cost from 12*49, then compare it with the budget. |
| v5-critical-ops-011 | v5-axis-01,v5-axis-03,v5-axis-05,v5-axis-07 | summarize | summarize,verify,search | requires_current_information,multiple_intents | - | medium | Verify the premise, search if needed, and summarize the current status. |
| v5-critical-ops-012 | v5-axis-01,v5-axis-02,v5-axis-04,v5-axis-05,v5-axis-06 | clarify | clarify,build | missing_required_information,multiple_intents | must:ask_first | low | Ask which environment this is for, then draft the deployment command. |
| v5-critical-ops-013 | v5-axis-02,v5-axis-04,v5-axis-06 | clarify | clarify | missing_required_information | must:ask_first | low | Before answering, ask me which database engine is in use. |
| v5-critical-ops-014 | v5-axis-02,v5-axis-06 | clarify | clarify | missing_required_information | must:ask_first | low | I have an error but did not share the log; ask for what you need first. |
| v5-critical-ops-015 | v5-axis-02,v5-axis-06 | clarify | clarify | missing_required_information | - | low | Can you fix it? I have not said which file is failing. |
| v5-critical-ops-016 | v5-axis-02,v5-axis-04,v5-axis-05,v5-axis-06 | clarify | clarify,calculate | missing_required_information,multiple_intents | must:ask_first | low | The numbers look wrong; ask me for the spreadsheet before calculating. |
| v5-critical-ops-017 | v5-axis-02,v5-axis-04,v5-axis-06 | clarify | clarify | missing_required_information | must:ask_first | low | Before recommending a path, ask whether this is production or staging. |
| v5-critical-ops-018 | v5-axis-02,v5-axis-05,v5-axis-06 | clarify | clarify,build | missing_required_information,multiple_intents | - | low | I want a migration plan, but the target database is not stated. |
| v5-critical-ops-019 | v5-axis-02,v5-axis-04,v5-axis-05,v5-axis-06 | clarify | clarify,explain | missing_required_information,multiple_intents | must:ask_first | low | Please ask which API version I mean before you explain the change. |
| v5-critical-ops-020 | v5-axis-02,v5-axis-06 | clarify | clarify | missing_required_information | - | low | We need to decide, but the success metric is not provided. |
| v5-critical-ops-021 | v5-axis-02,v5-axis-04,v5-axis-05,v5-axis-06 | clarify | clarify,summarize | missing_required_information,multiple_intents | must:ask_first | low | Ask me which user group this policy affects before summarizing it. |
| v5-critical-ops-022 | v5-axis-02,v5-axis-04,v5-axis-06 | clarify | clarify | missing_required_information | must:ask_first | low | I only wrote 'make it better'; ask for the artifact first. |
| v5-critical-ops-023 | v5-axis-03,v5-axis-04,v5-axis-07 | verify | verify,search | requires_current_information | must:cite_sources | medium | Check the latest Node.js LTS version and cite sources. |
| v5-critical-ops-024 | v5-axis-03,v5-axis-07 | verify | verify,search | requires_current_information | - | medium | Verify today's exchange rate before answering. |
| v5-critical-ops-025 | v5-axis-03,v5-axis-04,v5-axis-07 | verify | verify | contains_unverified_claims | must:cite_sources | medium | The vendor claims the patch fixes CVE-1234; verify it with sources. |
| v5-critical-ops-026 | v5-axis-03,v5-axis-04,v5-axis-07 | verify | verify | contains_unverified_claims | must:avoid_overclaim | medium | Review the reported figures and avoid overclaiming a winner. |
| v5-critical-ops-027 | v5-axis-03,v5-axis-07 | verify | verify,search | requires_current_information | - | medium | Is this still the recommended API as of today? |
| v5-critical-ops-028 | v5-axis-03,v5-axis-07 | verify | verify,search | requires_current_information | - | high | For the current tax rule, verify before giving guidance. |
| v5-critical-ops-029 | v5-axis-03,v5-axis-07 | verify | verify | contains_unverified_claims | - | high | Medical dosage advice was proposed in the note; verify and warn me if uncertain. |
| v5-critical-ops-030 | v5-axis-01,v5-axis-03,v5-axis-05,v5-axis-07 | summarize | summarize,verify | contains_unverified_claims,multiple_intents | - | high | The security report says credentials leaked; confirm before summarizing. |
| v5-critical-ops-031 | v5-axis-03,v5-axis-07 | verify | verify,search | requires_current_information | - | medium | Use the latest release notes to check whether this bug is fixed. |
| v5-critical-ops-032 | v5-axis-03,v5-axis-04,v5-axis-06,v5-axis-07 | explain | explain | - | must_not:no_web_search | low | Do not search; just explain what 'current context' means in this chat. |
| v5-critical-ops-033 | v5-axis-04,v5-axis-06 | respond | respond | - | length:short | low | Answer in one sentence. |
| v5-critical-ops-034 | v5-axis-04 | summarize | summarize | - | format:json | low | Summarize the tradeoffs as JSON. |
| v5-critical-ops-035 | v5-axis-04 | respond | respond | - | format:bullets,must_not:no_table | low | Give bullet points, no table. |
| v5-critical-ops-036 | v5-axis-04,v5-axis-06 | build | build | - | must_not:no_code | low | Draft a checklist without code. |
| v5-critical-ops-037 | v5-axis-04,v5-axis-05,v5-axis-06 | explore | explore,compare | - | must:preserve_neutrality | low | Compare the options without endorsing either side. |
| v5-critical-ops-038 | v5-axis-04,v5-axis-06 | explain | explain | - | length:short,must:avoid_overclaim | low | Explain briefly and avoid overclaiming. |
| v5-critical-ops-039 | v5-axis-04,v5-axis-05,v5-axis-06 | clarify | clarify,build | missing_required_information,multiple_intents | format:json,must:ask_first | low | Ask me first, then provide a JSON template. |
| v5-critical-ops-040 | v5-axis-04 | summarize | summarize | - | length:short,format:bullets,must:cite_sources | low | Summarize in three bullets and cite sources. |
| v5-critical-ops-041 | v5-axis-04,v5-axis-06 | build | build | - | format:code | low | Prepare a migration plan in a code block. |
| v5-critical-ops-042 | v5-axis-04,v5-axis-06 | explain | explain | - | length:long,must_not:no_code | low | Give a long detailed explanation, but no code. |
| v5-critical-ops-043 | v5-axis-04,v5-axis-05,v5-axis-06 | explore | explore,compare | - | format:table | low | Respond with a table comparing pros and cons. |
| v5-critical-ops-044 | v5-axis-04,v5-axis-06 | respond | respond | - | length:short,must:preserve_neutrality,must_not:no_table | low | Keep it concise, neutral, and no table. |
| v5-critical-ops-045 | v5-axis-05,v5-axis-06 | verify | verify,calculate | - | - | low | Does 0.5 equal 1/2? calculate and verify. |
| v5-critical-ops-046 | v5-axis-01,v5-axis-05,v5-axis-06 | explain | explain,compare | multiple_intents | - | low | Compare these two approaches, then explain the deciding factor. |
| v5-critical-ops-047 | v5-axis-05,v5-axis-06 | explore | explore,compare | - | - | low | Explore alternatives and compare their failure modes. |
| v5-critical-ops-048 | v5-axis-04,v5-axis-05,v5-axis-06 | respond | respond,calculate | - | length:short | low | Calculate 3+5 and return only the result. |

# V7 Router Debate Candidate Review Worksheet v1

This worksheet is for human review before any V7 router-debate candidate is inserted into non-sealed training or replay lanes.
Raw Gemma/Qwen turns remain review evidence only.

## Contract

- source_log: `build/v7_router_repair_debate_run.json`
- selected_candidates: 18
- source_topics: 5
- caution_topics: 1
- current_route_error_count: 0
- provisional_pass_count: 18
- provisional_repair_gap_count: 0
- sealed use: false
- raw turn direct training: false
- same-cycle gate use: false

## Review Items

| id | provisional | source_topic | type | intent | operations | risk | score | input | review_focus |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| v7-router-debate-candidate-001 | passes_current_route | v7-ambiguous-clarify-vs-build | should_fire_clarify | clarify | clarify | low | 10 | Please make this sound better. I have not provided the target text yet. | Undefined object should ask for the missing artifact instead of guessing a build target. |
| v7-router-debate-candidate-002 | passes_current_route | v7-ambiguous-clarify-vs-build | should_not_fire_clarify | build | build | low | 9 | Please make this sentence short and businesslike: The meeting is tomorrow and the deck is not ready. | Defined object plus vague style is enough to build without a follow-up. |
| v7-router-debate-candidate-003 | passes_current_route | v7-ambiguous-clarify-vs-build | boundary_case | clarify | clarify,build | low | 8 | Make the earlier proposal shorter. If there are multiple proposals, ask which one first. | History-dependent object should clarify if there may be multiple prior artifacts. |
| v7-router-debate-candidate-004 | passes_current_route | v7-current-search-split-local-vs-web | should_not_fire_current_search | build | build | low | 10 | Show a PowerShell command to check the current working folder. Do not search the web. | Current local folder is local context, not web-current information. |
| v7-router-debate-candidate-005 | passes_current_route | v7-current-search-split-local-vs-web | should_fire_current_search | verify | verify,search | medium | 10 | Check the latest Node.js LTS from official sources and answer with citations. | Latest external version needs freshness and sources. |
| v7-router-debate-candidate-006 | passes_current_route | v7-current-search-split-local-vs-web | metalinguistic_suppression | build | build | low | 9 | Add a CSV column named latest_config. This is not a request to check latest news. | The word latest used as a column name should not trigger search/current routing. |
| v7-router-debate-candidate-007 | passes_current_route | v7-current-search-split-local-vs-web | current_local_contrast | summarize | summarize | low | 8 | Summarize today's conversation log briefly. No external current information is needed. | Today can refer to local conversation history and should not require external search. |
| v7-router-debate-candidate-008 | passes_current_route | v7-unverified-claim-strength | should_fire_verify | verify | verify,search | high | 10 | The vendor says this patch fixed the vulnerability. Check it with sources. | Security remediation claim should be verified with sources before use. |
| v7-router-debate-candidate-009 | passes_current_route | v7-unverified-claim-strength | should_not_fire_verify | build | build | low | 8 | For a story premise, assume a patch saved the world and write the opening paragraph. | Fictional assumptions should not become factual verification tasks. |
| v7-router-debate-candidate-010 | passes_current_route | v7-unverified-claim-strength | should_fire_verify | verify | verify | medium | 8 | I heard this number is correct; please check it before I put it in the report. | A claim intended for a report should be checked before inclusion. |
| v7-router-debate-candidate-011 | passes_current_route | v7-unverified-claim-strength | should_not_fire_verify | build | build | low | 9 | Record the sentence 'the vendor says it is safe' as a hypothesis note. Do not verify it yet. | A note-recording task can preserve an unverified statement without validating it yet. |
| v7-router-debate-candidate-012 | passes_current_route | v7-constraint-stacking | constraint_stack | explain | explain | low | 10 | Explain medical AI UI cautions briefly, with no table, neutral tone, and no diagnosis. | Formatting and safety constraints should be preserved without turning UI design into diagnosis advice. |
| v7-router-debate-candidate-013 | passes_current_route | v7-constraint-stacking | medical_word_low_risk | explain | explain | low | 8 | Explain common causes of fatigue in bullet points. Do not give diagnosis or treatment advice. | General information with no diagnosis or treatment request should preserve avoid_diagnosis but not high-risk routing. |
| v7-router-debate-candidate-014 | passes_current_route | v7-constraint-stacking | positive_fire_source_requirement | verify | verify,search | medium | 8 | Check what Article 58 says and explain it with citations. | Specific legal article requests should verify sources even if phrased briefly. |
| v7-router-debate-candidate-015 | passes_current_route | v7-terminal-action-boundary | terminal_action_summary | summarize | summarize | low | 9 | Summarize the risks in this README. Do not search externally. | Risk wording in local context should summarize rather than force search or high-risk verification. |
| v7-router-debate-candidate-016 | passes_current_route | v7-terminal-action-boundary | vertical_stack_terminal_build | build | build,verify | low | 9 | Check the risks first, then create a fix checklist. | The final artifact is a checklist, with risk verification as a preceding step. |
| v7-router-debate-candidate-017 | passes_current_route | v7-terminal-action-boundary | terminal_action_table | build | build,compare | low | 9 | Compare the two designs and make a pros/cons table. | The terminal artifact is a table, while compare is the preceding operation. |
| v7-router-debate-candidate-018 | passes_current_route | v7-terminal-action-boundary | vertical_stack_terminal_table | build | build,summarize,compare | low | 10 | Summarize first, then compare. End with a comparison table, not a conclusion. | The route should keep summarize->compare ordering and end in a comparison table, not a generic conclusion. |

## Human Review Output

Accepted items should be copied into a separate adoption plan with explicit `decision: adopt_nonsealed`. Held items must keep their reason. This file itself is not training data.

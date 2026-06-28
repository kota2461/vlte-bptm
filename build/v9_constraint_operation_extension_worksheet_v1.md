# V9 Constraint/Operation Extension Worksheet v1

## Summary

- case_count: 24
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

## Coverage

- constraints cases: 12
- operation_terminal cases: 12
- target fields: {'constraints': 19, 'information_state': 6, 'operations': 12, 'risk': 3}

## Candidate Replay

| case | category | topic | fields | expected | actual | input |
|---|---|---|---|---|---|---|
| v9-constraint-operation-extension-001 | constraints | short_bullets_no_table | ok | summarize / ['summarize'] / {'response_length': 'short', 'formats': ['bullets'], 'must': [], 'must_not': ['no_table']} | summarize / ['summarize'] / {'response_length': 'short', 'formats': ['bullets'], 'must': [], 'must_not': ['no_table']} | Briefly list three deployment risks as bullet points, no table. |
| v9-constraint-operation-extension-002 | constraints | json_only | ok | build / ['build'] / {'response_length': 'unspecified', 'formats': ['json'], 'must': [], 'must_not': []} | build / ['build'] / {'response_length': 'unspecified', 'formats': ['json'], 'must': [], 'must_not': []} | Return only JSON with keys action and reason; do not add prose. |
| v9-constraint-operation-extension-003 | constraints | ask_first_before_edit | ok | clarify / ['clarify'] / {'response_length': 'unspecified', 'formats': [], 'must': ['ask_first'], 'must_not': []} | clarify / ['clarify'] / {'response_length': 'unspecified', 'formats': [], 'must': ['ask_first'], 'must_not': []} | Before editing the README, ask which section I want changed. |
| v9-constraint-operation-extension-004 | constraints | do_not_store_memory | ok | build / ['build'] / {'response_length': 'unspecified', 'formats': [], 'must': [], 'must_not': ['do_not_store']} | build / ['build'] / {'response_length': 'unspecified', 'formats': [], 'must': [], 'must_not': ['do_not_store']} | Draft the reply but do not store this personal note as memory. |
| v9-constraint-operation-extension-005 | constraints | cite_and_avoid_overclaim | ok | verify / ['verify'] / {'response_length': 'unspecified', 'formats': [], 'must': ['cite_sources', 'avoid_overclaim'], 'must_not': []} | verify / ['verify'] / {'response_length': 'unspecified', 'formats': [], 'must': ['cite_sources', 'avoid_overclaim'], 'must_not': []} | Verify this vendor claim with sources and avoid overclaiming: the router is 30% more accurate. |
| v9-constraint-operation-extension-006 | constraints | general_legal_explanation | ok | explain / ['explain'] / {'response_length': 'unspecified', 'formats': [], 'must': ['general_information_only'], 'must_not': []} | explain / ['explain'] / {'response_length': 'unspecified', 'formats': [], 'must': ['general_information_only'], 'must_not': []} | Explain Apache 2.0 as general information only; this is not legal advice. |
| v9-constraint-operation-extension-007 | constraints | medical_ui_no_diagnosis | ok | build / ['build'] / {'response_length': 'unspecified', 'formats': [], 'must': ['avoid_diagnosis'], 'must_not': []} | build / ['build'] / {'response_length': 'unspecified', 'formats': [], 'must': ['avoid_diagnosis'], 'must_not': []} | Design a medical AI screen layout without diagnosis or treatment advice. |
| v9-constraint-operation-extension-008 | constraints | tone_avoid_overclaim | ok | respond / ['respond'] / {'response_length': 'unspecified', 'formats': [], 'must': ['avoid_overclaim'], 'must_not': []} | respond / ['respond'] / {'response_length': 'unspecified', 'formats': [], 'must': ['avoid_overclaim'], 'must_not': []} | Answer in a friendly but precise tone and avoid overstating the evidence. |
| v9-constraint-operation-extension-009 | constraints | local_notes_no_web | ok | summarize / ['summarize'] / {'response_length': 'unspecified', 'formats': [], 'must': [], 'must_not': ['no_web_search']} | summarize / ['summarize'] / {'response_length': 'unspecified', 'formats': [], 'must': [], 'must_not': ['no_web_search']} | Use only the local notes below; no web search is needed. Notes: v9 repair passed. |
| v9-constraint-operation-extension-010 | constraints | table_required | ok | build / ['build'] / {'response_length': 'unspecified', 'formats': ['table'], 'must': [], 'must_not': []} | build / ['build'] / {'response_length': 'unspecified', 'formats': ['table'], 'must': [], 'must_not': []} | Create a comparison table for these options: A is cheaper, B is safer. |
| v9-constraint-operation-extension-011 | constraints | one_short_sentence | ok | explain / ['explain'] / {'response_length': 'short', 'formats': [], 'must': [], 'must_not': []} | explain / ['explain'] / {'response_length': 'short', 'formats': [], 'must': [], 'must_not': []} | Give exactly one short sentence explaining the result. |
| v9-constraint-operation-extension-012 | constraints | neutral_summary | ok | summarize / ['summarize'] / {'response_length': 'unspecified', 'formats': [], 'must': ['preserve_neutrality'], 'must_not': []} | summarize / ['summarize'] / {'response_length': 'unspecified', 'formats': [], 'must': ['preserve_neutrality'], 'must_not': []} | Summarize both sides neutrally without choosing a winner. |
| v9-constraint-operation-extension-013 | operation_terminal | summarize_only | ok | summarize / ['summarize'] / {'response_length': 'unspecified', 'formats': [], 'must': [], 'must_not': []} | summarize / ['summarize'] / {'response_length': 'unspecified', 'formats': [], 'must': [], 'must_not': []} | Summarize the failure list into three key points. |
| v9-constraint-operation-extension-014 | operation_terminal | classify_table | ok | build / ['build'] / {'response_length': 'unspecified', 'formats': ['table'], 'must': [], 'must_not': []} | build / ['build'] / {'response_length': 'unspecified', 'formats': ['table'], 'must': [], 'must_not': []} | Classify each log row as keep or review in a table. |
| v9-constraint-operation-extension-015 | operation_terminal | clarify_before_table_build | ok | clarify / ['clarify', 'build'] / {'response_length': 'unspecified', 'formats': ['table'], 'must': ['ask_first'], 'must_not': []} | clarify / ['clarify', 'build'] / {'response_length': 'unspecified', 'formats': ['table'], 'must': ['ask_first'], 'must_not': []} | Make a migration table, but the source columns are not provided. |
| v9-constraint-operation-extension-016 | operation_terminal | verify_then_release_note | ok | build / ['build', 'verify'] / {'response_length': 'short', 'formats': [], 'must': [], 'must_not': []} | build / ['build', 'verify'] / {'response_length': 'short', 'formats': [], 'must': [], 'must_not': []} | Verify the security claim, then write a short release note. |
| v9-constraint-operation-extension-017 | operation_terminal | explain_general | ok | explain / ['explain'] / {'response_length': 'unspecified', 'formats': [], 'must': ['general_information_only'], 'must_not': []} | explain / ['explain'] / {'response_length': 'unspecified', 'formats': [], 'must': ['general_information_only'], 'must_not': []} | Explain what Apache 2.0 means at a general level. |
| v9-constraint-operation-extension-018 | operation_terminal | compare_recommend | ok | explore / ['explore', 'compare'] / {'response_length': 'unspecified', 'formats': [], 'must': [], 'must_not': []} | explore / ['explore', 'compare'] / {'response_length': 'unspecified', 'formats': [], 'must': [], 'must_not': []} | Compare the two router designs and recommend one. |
| v9-constraint-operation-extension-019 | operation_terminal | calculate_verify | ok | verify / ['verify', 'calculate'] / {'response_length': 'unspecified', 'formats': [], 'must': [], 'must_not': []} | verify / ['verify', 'calculate'] / {'response_length': 'unspecified', 'formats': [], 'must': [], 'must_not': []} | Calculate whether 42 + 58 equals 100. |
| v9-constraint-operation-extension-020 | operation_terminal | current_search_cite | ok | verify / ['verify', 'search'] / {'response_length': 'unspecified', 'formats': [], 'must': ['cite_sources', 'avoid_overclaim'], 'must_not': []} | verify / ['verify', 'search'] / {'response_length': 'unspecified', 'formats': [], 'must': ['cite_sources', 'avoid_overclaim'], 'must_not': []} | Search for the latest Node.js LTS version and cite the source. |
| v9-constraint-operation-extension-021 | operation_terminal | build_checklist | ok | build / ['build'] / {'response_length': 'unspecified', 'formats': ['bullets'], 'must': [], 'must_not': []} | build / ['build'] / {'response_length': 'unspecified', 'formats': ['bullets'], 'must': [], 'must_not': []} | Build a checklist of fixes for the route gaps. |
| v9-constraint-operation-extension-022 | operation_terminal | review_then_terminal_summary | ok | summarize / ['summarize', 'verify'] / {'response_length': 'unspecified', 'formats': [], 'must': ['avoid_overclaim'], 'must_not': []} | summarize / ['summarize', 'verify'] / {'response_length': 'unspecified', 'formats': [], 'must': ['avoid_overclaim'], 'must_not': []} | Review the draft and summarize only the blocking issues. |
| v9-constraint-operation-extension-023 | operation_terminal | checked_json_plan | ok | build / ['build', 'verify'] / {'response_length': 'unspecified', 'formats': ['json'], 'must': [], 'must_not': []} | build / ['build', 'verify'] / {'response_length': 'unspecified', 'formats': ['json'], 'must': [], 'must_not': []} | Create the JSON patch plan after checking the assumptions. |
| v9-constraint-operation-extension-024 | operation_terminal | extract_classify_summarize_counts | ok | build / ['build', 'summarize', 'calculate'] / {'response_length': 'unspecified', 'formats': [], 'must': [], 'must_not': []} | build / ['build', 'summarize', 'calculate'] / {'response_length': 'unspecified', 'formats': [], 'must': [], 'must_not': []} | Extract candidate IDs, classify each as keep or rerun, and summarize counts. |

## Contract

- sealed_fixture_used: false
- current_route_measurement_is_gate: false
- raw_debate_logs_direct_training_allowed: false
- same_cycle_promotion_allowed: false

# V7 Router Repair Fixture Review Worksheet v1

Draft non-sealed fixture for human review. No sealed fixture text or labels were used.

## Summary

- case_count: 72
- review_status: draft
- current_route_intent_accuracy: 0.736111
- current_route_critical_signal_recall: 0.476923
- current_route_operation_exact_match: 0.611111
- current_route_constraint_exact_match: 0.680556
- current_route_risk_exact_match: 0.763889

## Cases

| id | axis | theme | lang | intent | operations | critical | constraints | risk | input |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| v7-router-repair-001 | constraint_preservation | response_length_preservation | en | respond | respond | - | length:short | low | Answer in exactly one short sentence: what is a cache key? |
| v7-router-repair-002 | constraint_preservation | response_length_preservation | en | explain | explain | - | length:long | low | Give a long explanation of why retry backoff helps overloaded services. |
| v7-router-repair-003 | constraint_preservation | response_length_preservation | ja | summarize | summarize | - | length:short,format:bullets | low | この会議メモを3つの箇条書きで短く要約してください。 |
| v7-router-repair-004 | constraint_preservation | response_length_preservation | mixed | explain | explain | - | length:medium,must_not:no_table | low | Keep it medium length and explain the trade-off without a table. |
| v7-router-repair-005 | constraint_preservation | format_preservation | en | summarize | summarize | - | format:json | low | Summarize the incident as JSON with keys impact and next_steps. |
| v7-router-repair-006 | constraint_preservation | format_preservation | en | build | build | - | format:bullets | low | Draft a release checklist as bullet points only. |
| v7-router-repair-007 | constraint_preservation | format_preservation | mixed | explore | explore,compare | - | format:table,must:preserve_neutrality | low | Compare the options in a table, but do not pick a winner. |
| v7-router-repair-008 | constraint_preservation | format_preservation | ja | summarize | summarize | - | length:short,must_not:no_table | low | 時系列ログを表にせず短くまとめてください。 |
| v7-router-repair-009 | constraint_preservation | safety_style_constraints | en | summarize | summarize | - | must:preserve_neutrality | medium | Give a neutral summary of this policy dispute without choosing a side. |
| v7-router-repair-010 | constraint_preservation | safety_style_constraints | en | explore | explore | - | must:avoid_overclaim | medium | Discuss future adoption scenarios without overclaiming certainty. |
| v7-router-repair-011 | constraint_preservation | safety_style_constraints | ja | explain | explain | - | must:general_information_only | low | Apache 2.0の概要を一般情報として説明してください。法的助言は不要です。 |
| v7-router-repair-012 | constraint_preservation | safety_style_constraints | ja | explain | explain | - | must:avoid_diagnosis | low | 医療AIダッシュボード設計の注意点を、診断助言なしで説明してください。 |
| v7-router-repair-013 | constraint_preservation | cite_sources_and_ask_first | en | verify | verify,search | requires_current_information | must:cite_sources | medium | Check the latest Python release and cite official sources. |
| v7-router-repair-014 | constraint_preservation | cite_sources_and_ask_first | en | clarify | clarify,build | missing_required_information,multiple_intents | must:ask_first | low | Before drafting the migration plan, ask which service is in scope. |
| v7-router-repair-015 | constraint_preservation | cite_sources_and_ask_first | mixed | explain | explain | - | must_not:no_web_search | low | The term latest_status is only a column name; explain the naming without web search. |
| v7-router-repair-016 | constraint_preservation | cite_sources_and_ask_first | en | verify | verify,search | contains_unverified_claims,requires_current_information | must:cite_sources | medium | Use sources to verify whether the vendor claim is still true. |
| v7-router-repair-017 | constraint_preservation | constraint_contrast_pairs | en | summarize | summarize | - | format:bullets,must_not:no_table | low | Summarize this note in bullets, no table. |
| v7-router-repair-018 | constraint_preservation | constraint_contrast_pairs | en | summarize | summarize | - | - | low | Summarize this note normally. |
| v7-router-repair-019 | operation_sequence_repair | clarify_then_build | en | clarify | clarify,build | missing_required_information,multiple_intents | - | low | Create a CSV export template, but the required columns are missing. |
| v7-router-repair-020 | operation_sequence_repair | clarify_then_build | ja | clarify | clarify,build | missing_required_information,multiple_intents | must:ask_first | low | 移行計画を書きたいですが、対象サービスが未定です。先に確認してください。 |
| v7-router-repair-021 | operation_sequence_repair | clarify_then_build | mixed | clarify | clarify,build | missing_required_information,multiple_intents | must:ask_first | low | Make a rollout checklist after asking which environment this applies to. |
| v7-router-repair-022 | operation_sequence_repair | clarify_then_build | en | clarify | clarify,build | missing_required_information,multiple_intents | must:ask_first | low | Draft the onboarding email, but ask who the audience is first. |
| v7-router-repair-023 | operation_sequence_repair | verify_then_search | en | verify | verify,search | requires_current_information | must:cite_sources | medium | Verify the current Node.js LTS version with sources. |
| v7-router-repair-024 | operation_sequence_repair | verify_then_search | ja | verify | verify,search | requires_current_information | must:cite_sources | medium | 今日時点の公式リリース情報を確認してから答えてください。 |
| v7-router-repair-025 | operation_sequence_repair | verify_then_search | en | verify | verify,search | requires_current_information | must:cite_sources | medium | Check whether this license permission is still documented and cite sources. |
| v7-router-repair-026 | operation_sequence_repair | verify_then_search | mixed | verify | verify,search | requires_current_information | - | medium | Verify if the latest API deprecation note applies to this SDK. |
| v7-router-repair-027 | operation_sequence_repair | explore_then_compare | en | explore | explore,compare | multiple_intents | - | low | Brainstorm three storage strategies and compare their trade-offs. |
| v7-router-repair-028 | operation_sequence_repair | explore_then_compare | ja | explore | explore,compare | multiple_intents | - | low | ルーター改善案を複数出して、それぞれの弱点を比較してください。 |
| v7-router-repair-029 | operation_sequence_repair | explore_then_compare | en | explore | explore,compare | - | must:avoid_overclaim | low | Compare two approaches without claiming either is always best. |
| v7-router-repair-030 | operation_sequence_repair | explore_then_compare | mixed | explore | explore,compare | multiple_intents | - | low | Explore alternatives for Knowledge Index and compare retrieval costs. |
| v7-router-repair-031 | operation_sequence_repair | build_then_verify | en | build | build,verify | contains_unverified_claims,multiple_intents | length:short | low | Check the assumptions, then draft a short migration checklist. |
| v7-router-repair-032 | operation_sequence_repair | build_then_verify | ja | build | build,verify | contains_unverified_claims,multiple_intents | - | low | 議論ログを軽く検証してから、候補レビュー表を作ってください。 |
| v7-router-repair-033 | operation_sequence_repair | build_then_verify | en | build | build,verify | contains_unverified_claims,multiple_intents | format:json | low | Validate the inputs and create a JSON import plan. |
| v7-router-repair-034 | operation_sequence_repair | verify_then_calculate | en | verify | verify,calculate | contains_unverified_claims | - | low | Check whether 24 * 18 equals 432 before adding it to the report. |
| v7-router-repair-035 | operation_sequence_repair | verify_then_calculate | ja | verify | verify,calculate | contains_unverified_claims | - | low | 請求額が小計と税額の合計に合うか計算して確認してください。 |
| v7-router-repair-036 | operation_sequence_repair | verify_then_calculate | mixed | verify | verify,calculate | contains_unverified_claims | - | low | Verify the error budget burn rate from 7/28 before summarizing. |
| v7-router-repair-037 | critical_signal_recovery | unverified_claim_detection | en | verify | verify | contains_unverified_claims | - | medium | The proposal supposedly removes all outage risk; verify before accepting it. |
| v7-router-repair-038 | critical_signal_recovery | unverified_claim_detection | ja | verify | verify | contains_unverified_claims | - | medium | この設定で必ず安全になると言われました。根拠を確認してください。 |
| v7-router-repair-039 | critical_signal_recovery | unverified_claim_detection | en | verify | verify,search | contains_unverified_claims | must:cite_sources | high | A note claims the patch fixed the vulnerability; check it with sources. |
| v7-router-repair-040 | critical_signal_recovery | unverified_claim_detection | mixed | verify | verify | contains_unverified_claims | must:avoid_diagnosis | high | The draft says medical advice is safe; verify and avoid diagnosis. |
| v7-router-repair-041 | critical_signal_recovery | unverified_claim_detection | en | verify | verify | contains_unverified_claims | - | medium | The vendor says this is compliant; do not assume it is true. |
| v7-router-repair-042 | critical_signal_recovery | multiple_intent_detection | en | build | build,verify | contains_unverified_claims,multiple_intents | length:short | low | Verify the claim, then write a short response for the release note. |
| v7-router-repair-043 | critical_signal_recovery | multiple_intent_detection | ja | explore | explore,summarize,compare | multiple_intents | - | low | ログを要約してから、改善案を比較してください。 |
| v7-router-repair-044 | critical_signal_recovery | multiple_intent_detection | mixed | clarify | clarify,calculate | missing_required_information,multiple_intents | must:ask_first | low | Ask what data is missing, then calculate the estimate. |
| v7-router-repair-045 | critical_signal_recovery | multiple_intent_detection | en | build | build,summarize | multiple_intents | format:bullets | low | Summarize the feedback and create a checklist of fixes. |
| v7-router-repair-046 | critical_signal_recovery | multiple_intent_detection | ja | summarize | summarize,verify,search | requires_current_information,multiple_intents | must:preserve_neutrality | medium | 最新情報を確認してから、中立的に要約してください。 |
| v7-router-repair-047 | critical_signal_recovery | missing_information_detection | en | clarify | clarify,calculate | missing_required_information | - | low | Estimate the monthly cost, but the usage volume is not provided. |
| v7-router-repair-048 | critical_signal_recovery | missing_information_detection | ja | clarify | clarify,build | missing_required_information,multiple_intents | - | low | 移行手順を作りたいですが、対象DBが分かりません。 |
| v7-router-repair-049 | critical_signal_recovery | missing_information_detection | en | clarify | clarify,verify | missing_required_information | - | high | Check contract validity, but the jurisdiction is missing. |
| v7-router-repair-050 | critical_signal_recovery | current_information_split | en | verify | verify,search | requires_current_information | must:cite_sources | medium | What is the latest stable Rust version today? Cite sources. |
| v7-router-repair-051 | critical_signal_recovery | current_information_split | ja | explain | explain | - | must_not:no_web_search | low | 現在の作業フォルダ名を説明してください。Web検索は不要です。 |
| v7-router-repair-052 | critical_signal_recovery | current_information_split | mixed | build | build | - | - | low | Add the label latest_release to the local tracking table. |
| v7-router-repair-053 | clarify_boundary_repair | ask_first_before_action | en | clarify | clarify,build | missing_required_information,multiple_intents | must:ask_first | low | Before writing the runbook, ask which cluster it is for. |
| v7-router-repair-054 | clarify_boundary_repair | ask_first_before_action | ja | clarify | clarify | missing_required_information | must:ask_first | low | 回答前に、対象ユーザー層を確認してください。 |
| v7-router-repair-055 | clarify_boundary_repair | ask_first_before_action | mixed | clarify | clarify,build | missing_required_information,multiple_intents | must:ask_first | low | Ask which tenant should be migrated before drafting commands. |
| v7-router-repair-056 | clarify_boundary_repair | missing_scope_vs_simple_question | en | respond | respond | - | - | low | What does TTL mean in caching? |
| v7-router-repair-057 | clarify_boundary_repair | missing_scope_vs_simple_question | en | clarify | clarify,build | missing_required_information,multiple_intents | - | low | Create a TTL policy, but the service tier is not stated. |
| v7-router-repair-058 | clarify_boundary_repair | missing_scope_vs_simple_question | ja | clarify | clarify | missing_required_information | must:ask_first | low | どのログを対象にするか未指定なので先に確認してください。 |
| v7-router-repair-059 | clarify_boundary_repair | high_risk_clarify_before_verify | en | clarify | clarify,verify | missing_required_information,requires_current_information | - | high | Check current contract legality, but the country is not specified. |
| v7-router-repair-060 | clarify_boundary_repair | high_risk_clarify_before_verify | ja | clarify | clarify,verify | missing_required_information | - | high | 医療助言が安全か確認したいですが、状況説明がありません。 |
| v7-router-repair-061 | risk_ladder_calibration | low_risk_contrast | en | build | build | - | - | low | Use the word medical_warning as a UI label in the mockup. |
| v7-router-repair-062 | risk_ladder_calibration | low_risk_contrast | ja | build | build | - | - | low | AI依存という列名をレビュー表に追加してください。 |
| v7-router-repair-063 | risk_ladder_calibration | medium_current_or_license | en | verify | verify,search | - | must:cite_sources | medium | Verify whether Apache 2.0 allows commercial use and cite sources. |
| v7-router-repair-064 | risk_ladder_calibration | medium_current_or_license | ja | verify | verify,search | requires_current_information | - | medium | 今日の公式リリース状況を確認してください。 |
| v7-router-repair-065 | risk_ladder_calibration | high_medical_legal | en | verify | verify | contains_unverified_claims | - | high | Verify whether this medical dosage advice is safe before answering. |
| v7-router-repair-066 | risk_ladder_calibration | high_medical_legal | ja | verify | verify,search | requires_current_information | - | high | 現在の法律でこの契約条項が有効か確認してください。 |
| v7-router-repair-067 | intent_boundary_stability | respond_vs_build | en | respond | respond | - | - | low | What is a routing tag? |
| v7-router-repair-068 | intent_boundary_stability | respond_vs_build | en | build | build | - | - | low | Add a routing tag called review_needed to the checklist. |
| v7-router-repair-069 | intent_boundary_stability | explain_vs_build | ja | explain | explain | - | - | low | なぜ非sealedデータで練習するのか説明してください。 |
| v7-router-repair-070 | intent_boundary_stability | clarify_vs_respond_build_verify | en | clarify | clarify | missing_required_information | - | low | Can you make it safer? I have not said what component this refers to. |
| v7-router-repair-071 | intent_boundary_stability | clarify_vs_respond_build_verify | mixed | build | build,verify | contains_unverified_claims,multiple_intents | - | low | Verify the config checksum and then update the note. |
| v7-router-repair-072 | intent_boundary_stability | explore_vs_respond | ja | explore | explore,compare | multiple_intents | - | medium | 複数の改善ルートを出して、それぞれのリスクを比較してください。 |

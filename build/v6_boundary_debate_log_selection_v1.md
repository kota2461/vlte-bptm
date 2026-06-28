# V6 Boundary Debate Log Selection v1

Raw LLM debate turns are review evidence only. This worksheet selects logs for later human rewriting/review; it does not make any item training-ready.

## Summary

- source_topic_count: 18
- source_turn_count: 144
- selected_primary_count: 15
- selected_secondary_count: 3
- held_ladder_count: 0
- quality_issue_count: 0
- immediate_focus_match_count: 10

## Decisions

| topic | target_set | decision | score | immediate | reason |
| --- | --- | --- | ---: | --- | --- |
| fp-ai-light-chat-healing | false_positive_set | select_primary_review | 8 | true | High-priority false-positive/paraphrase/no-risk calibration topic. |
| fp-ai-task-support-not-dependency | false_positive_set | select_primary_review | 8 | true | High-priority false-positive/paraphrase/no-risk calibration topic. |
| fp-ai-persona-heading-only | false_positive_set | select_primary_review | 6 | false | High-priority false-positive/paraphrase/no-risk calibration topic. |
| fp-legal-risk-column-name | false_positive_set | select_primary_review | 6 | false | High-priority false-positive/paraphrase/no-risk calibration topic. |
| fp-neutrality-example-sentence | false_positive_set | select_primary_review | 6 | false | High-priority false-positive/paraphrase/no-risk calibration topic. |
| paraphrase-ai-light-support | paraphrase_set | select_primary_review | 8 | true | High-priority false-positive/paraphrase/no-risk calibration topic. |
| paraphrase-apache-general-question | paraphrase_set | select_primary_review | 8 | true | High-priority false-positive/paraphrase/no-risk calibration topic. |
| paraphrase-medical-ui-design | paraphrase_set | select_primary_review | 8 | true | High-priority false-positive/paraphrase/no-risk calibration topic. |
| paraphrase-current-local-context | paraphrase_set | select_primary_review | 6 | false | High-priority false-positive/paraphrase/no-risk calibration topic. |
| paraphrase-metalinguistic-mention | paraphrase_set | select_primary_review | 6 | false | High-priority false-positive/paraphrase/no-risk calibration topic. |
| contrast-ai-word-only-low-risk | no_risk_contrast | select_primary_review | 8 | true | High-priority false-positive/paraphrase/no-risk calibration topic. |
| contrast-politics-word-only-low-risk | no_risk_contrast | select_primary_review | 6 | false | High-priority false-positive/paraphrase/no-risk calibration topic. |
| contrast-medical-word-only-low-risk | no_risk_contrast | select_primary_review | 8 | true | High-priority false-positive/paraphrase/no-risk calibration topic. |
| contrast-license-word-only-low-risk | no_risk_contrast | select_primary_review | 8 | true | High-priority false-positive/paraphrase/no-risk calibration topic. |
| contrast-future-word-only-low-risk | no_risk_contrast | select_primary_review | 6 | false | High-priority false-positive/paraphrase/no-risk calibration topic. |
| mixed-ai-persona-label-ja-en | mixed_ja_en | select_secondary_review | 5 | false | Useful medium-priority mixed-language or current/search split topic. |
| mixed-apache-general-ja-en | mixed_ja_en | select_secondary_review | 7 | true | Useful medium-priority mixed-language or current/search split topic. |
| mixed-medical-ui-ja-en | mixed_ja_en | select_secondary_review | 7 | true | Useful medium-priority mixed-language or current/search split topic. |

## Immediate Focus Matches

| topic | target_set | axes | theme |
| --- | --- | --- | --- |
| fp-ai-light-chat-healing | false_positive_set | false_positive, ai_light_use, dependency_suppression, low_risk_contrast | AIと雑談して癒やされているだけの軽い利用を、依存リスクや心理相談として過剰判定しない境界を議論する。 |
| fp-ai-task-support-not-dependency | false_positive_set | false_positive, negated_scope, ai_task_support, dependency_suppression | AIに毎日の予定整理を手伝ってもらうケースを、依存の話ではなくタスク管理相談として扱う条件を議論する。 |
| paraphrase-ai-light-support | paraphrase_set | paraphrase, ai_light_use, low_risk_contrast, common_features | 『AIと雑談して癒やされている』系の軽症例を5通りに言い換え、どれも低リスクとして扱うための共通特徴を議論する。 |
| paraphrase-apache-general-question | paraphrase_set | paraphrase, license_general, legal_suppression, current_suppression | 『Apache 2.0とは何ですか？』系の一般説明質問を複数表現に言い換え、high legal/currentにしない条件を議論する。 |
| paraphrase-medical-ui-design | paraphrase_set | paraphrase, medical_ui_design, diagnosis_suppression, boundary_review | 『医療AIのUI設計を考えたい』系の診断ではない設計相談を複数表現に言い換え、clarify/highにしない条件を議論する。 |
| contrast-ai-word-only-low-risk | no_risk_contrast | no_risk_contrast, ai_word_only, positive_negative_pair, risk_boundary | 『AI』という語があるだけではrisk/verifyにしないno-risk contrast例と、実際にAI安全境界が必要な例の違いを議論する。 |
| contrast-medical-word-only-low-risk | no_risk_contrast | no_risk_contrast, medical_word_only, diagnosis_suppression, risk_boundary | 『薬』『片頭痛』『医療』などの単語説明や翻訳を、診断相談やmedical high riskにしない条件を議論する。 |
| contrast-license-word-only-low-risk | no_risk_contrast | no_risk_contrast, license_word_only, legal_suppression, source_boundary | 『ライセンス』という語の一般説明やタグ保存を、法的助言やcurrent source要求にしない条件を議論する。 |
| mixed-apache-general-ja-en | mixed_ja_en | mixed_ja_en, license_general, brief_explain, legal_suppression | 『Apache 2.0 license の概要を日本語でbriefに説明』を、high legal/currentではなく一般説明として扱う条件を議論する。 |
| mixed-medical-ui-ja-en | mixed_ja_en | mixed_ja_en, medical_ui_design, diagnosis_suppression, boundary_review | 『medical AI UI layoutを考えたい』という日英混在設計相談を、診断相談と区別する条件を議論する。 |

## Contract

- training_allowed: false
- gate_use_allowed: false
- raw_debate_logs_direct_training_allowed: false
- next step: human review, then synthesize short self-contained candidate samples if accepted

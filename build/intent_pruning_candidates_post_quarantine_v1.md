# Intent Pruning Candidates Post Quarantine v1

Diagnostic only. No corpus or quarantine file is modified.

## Summary

- active quarantine entries: 9
- active baseline examples: 730
- remaining suspect candidates: 38
- high priority candidates: 21
- rewrite/anonymize path candidates: 13
- weak question candidates: 8

## Scenario Ablations

| scenario | action | count | gate | kfold delta | route delta | failed delta | label |
|---|---|---:|---|---:|---:|---:|---|
| rewrite_or_anonymize_path | rewrite_or_anonymize_path_then_retest | 13 | pass | -0.005961 | +0.000000 | +0 | keep_until_more_evidence |
| weak_question_holdout | holdout_or_failure_memory_review | 8 | pass | -0.020263 | +0.000000 | +0 | keep_until_more_evidence |
| very_short_anchor_control | do_not_bulk_prune | 17 | pass | -0.049915 | +0.000000 | +0 | keep_until_more_evidence |
| all_high_priority_remaining | review_before_prune_or_rewrite | 21 | pass | -0.043588 | -0.020000 | +1 | keep_until_more_evidence |

## High Priority Rows

| score | index | action | intent | flags | evidence | kfold delta | input |
|---:|---:|---|---|---|---|---:|---|
| 64 | 490 | rewrite_or_anonymize_path_then_retest | respond | path_or_url | keep_until_more_evidence | -0.030629 | 昨日の続きからの前にcodexのレポートです。/D:/pseudo personality/inverse_hybrid_ai/README.md |
| 64 | 530 | rewrite_or_anonymize_path_then_retest | explore | path_or_url | keep_until_more_evidence | -0.029258 | ollama経由だとモデル落とせなかったので、すでにインストールしていたLMStudioのgemma4を "D:\models\gemma-4-E4B-it-GGUF"にコピーしましたllamaで使えると思うのですがど… |
| 64 | 575 | rewrite_or_anonymize_path_then_retest | respond | path_or_url | keep_until_more_evidence | -0.029258 | "D:\Hybrid_PC_AI\start_ui.bat"start uiはこちらからしてます |
| 64 | 658 | rewrite_or_anonymize_path_then_retest | verify | path_or_url | keep_until_more_evidence | -0.029258 | D:/Thought State Register/docs/EXTERNAL_REVIEW_REPORT_2026-06-11.md v1.6まで進めたので確認と調査をお願いします |
| 64 | 725 | rewrite_or_anonymize_path_then_retest | explore | path_or_url | keep_until_more_evidence | -0.023771 | "D:\Hybrid_PC_AI" "D:\nichijo_jissou" D:\Core5_Project\core_review 導入候補としてこちらがあるのですが順位付けお願いします |
| 64 | 726 | rewrite_or_anonymize_path_then_retest | respond | path_or_url | keep_until_more_evidence | -0.025142 | nichijo_jissouからまずは導入行きましょう。その前にもう一つ候補がありまして、そちらは確か、メインＬＬＭがsubに司令を出す形でさらに海馬LLMを載せた物になります。D:\keywordmodel 多分これ… |
| 60 | 422 | rewrite_or_anonymize_path_then_retest | build | path_or_url | keep_until_more_evidence | -0.012797 | 03_instructions/precursor_tasks_v0.1.mdこちらを読んでもらってから続き行きましょう！ |
| 60 | 428 | rewrite_or_anonymize_path_then_retest | build | path_or_url | keep_until_more_evidence | -0.033373 | "D:\pseudo personality\02_design\Inverse_Hybrid_AI_Design_v1.5.md"続きからお願いします！ |
| 60 | 479 | rewrite_or_anonymize_path_then_retest | build | path_or_url | keep_until_more_evidence | -0.036116 | @"D:\nichijo_jissou\03_instructions\7day_chat_test_preflight_checklist_2026-06-01.md" test前の |
| 60 | 542 | rewrite_or_anonymize_path_then_retest | build | path_or_url | keep_until_more_evidence | -0.027886 | "D:\pseudo personality\CLAUDE.md"を読み実装を進めてください！ |
| 60 | 570 | rewrite_or_anonymize_path_then_retest | build | path_or_url | keep_until_more_evidence | -0.052577 | なるほどありがとうございます！それでは、 直近のこちらをお願いしたいです以下ログです Claude Code 側で docs/auto_log_review_2026-05-08.md + CLAUDE.md + do… |
| 60 | 571 | rewrite_or_anonymize_path_then_retest | explain | path_or_url | keep_until_more_evidence | -0.026514 | @D:\Hybrid_PC_AI\docs\auto_log_review_2026-05-08.md これで読めますか |
| 60 | 651 | rewrite_or_anonymize_path_then_retest | build | path_or_url | keep_until_more_evidence | -0.032001 | server起動.batとUI.batが欲しいです！D:\Topic packagingこちらにお願いします |
| 49 | 418 | holdout_or_failure_memory_review | explore | weak_question_suffix | keep_until_more_evidence | -0.030629 | subをollama使って、別モデルでテストとかできますか？ |
| 49 | 500 | holdout_or_failure_memory_review | explore | weak_question_suffix | keep_until_more_evidence | -0.023771 | 本命(中期)に感情による問い返しや反論を混ぜるというのはどうでしょう |
| 49 | 599 | holdout_or_failure_memory_review | explore | weak_question_suffix | keep_until_more_evidence | -0.037488 | Aはコストがかかりそうなので、B、Cを片付けてから行く方向でどうでしょう |
| 49 | 737 | holdout_or_failure_memory_review | explore | weak_question_suffix | keep_until_more_evidence | -0.014168 | こちら使えますか！ |
| 45 | 481 | holdout_or_failure_memory_review | explain | weak_question_suffix | keep_until_more_evidence | -0.023771 | ログの確認できますか？ |
| 45 | 525 | holdout_or_failure_memory_review | build | weak_question_suffix | keep_until_more_evidence | -0.041603 | EXL2がまだ出回って内容なので、圧縮をお願いできますか |
| 45 | 569 | holdout_or_failure_memory_review | explain | weak_question_suffix | keep_until_more_evidence | -0.022399 | つまり、project側でdocsに書き込んでそれをcode側で読み取ってコーディングというイメージで合ってますか |
| 45 | 719 | holdout_or_failure_memory_review | explain | weak_question_suffix | keep_until_more_evidence | -0.026514 | Claudeさん側で足りない部分を補う事はできますか |

## Review Rule

- `strong_prune_or_rewrite_candidate`: review first, then quarantine or rewrite/anonymize and retest.
- `rewrite_candidate_not_delete_yet`: prefer anonymized/relabelled replacement over deletion.
- `review_candidate_neutral_safe`: safe-looking but low evidence; hold for more samples.
- `keep_until_more_evidence`: do not prune now.
- Very short anchors should generally stay unless they have strong negative ablation evidence.

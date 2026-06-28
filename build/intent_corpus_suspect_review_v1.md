# Intent Corpus Suspect Review v1

Diagnostic only. No corpus/model/sealed files are modified.

## Summary

- corpus examples: 739
- suspect examples: 47
- high-priority review: 9
- by recommendation: {'exclude_or_negative': 3, 'exclude_or_relabel_clarify': 6, 'keep_if_directive_but_anonymize_path': 13, 'keep_if_intent_is_unambiguous': 17, 'review': 8}
- by flag: {'ack_only': 1, 'bare_path_or_url': 6, 'path_or_url': 19, 'very_short_le_8': 17, 'weak_question_suffix': 10}

## Excluded Reference Check

- harvest#55 respond/rejected calibration_exclude=None :: どうでしょう
- harvest#138 verify/rejected calibration_exclude=None :: こちらであってるでしょうか
- harvest#196 drop/pending calibration_exclude=True :: https://news.yahoo.co.jp/articles/514385b06980812ee2f4ef3dfec35a5be1d66388

## High-Priority Review

- corpus#90 [respond / pattern-db-remap] exclude_or_negative flags=ack_only :: ありがとうございます
- corpus#462 [clarify / claudelog-harvest] exclude_or_relabel_clarify flags=path_or_url,bare_path_or_url :: きました！ありがとうございます。ここで質問するのもなんですが、"D:\Thought State Register"側のサンプル集めに、どの様な種類の質問が良いでしょう。
- corpus#473 [respond / claudelog-harvest] exclude_or_relabel_clarify flags=path_or_url,bare_path_or_url :: "D:\nichijo_jissou\05_post_impl\handoff_to_code_2026-05-30.md" mypyベースライン109errorsも環境による物以外修正済みです
- corpus#528 [respond / claudelog-harvest] exclude_or_relabel_clarify flags=path_or_url,bare_path_or_url :: すみませんフォルダが重なってたので短縮しました。D:\models\gemma-4-12B-it
- corpus#551 [explain / claudelog-harvest] exclude_or_relabel_clarify flags=path_or_url,bare_path_or_url :: 質問です！__D:\Topic packaging\backend\app\domain\enums.pyここを取り入れてるってことは、topic packaging内の学習データを利用可能ってことですよね？__ だとしたら、そちらも近いうちにUIまで仕上げて学習させるのがよさそうですね
- corpus#627 [verify / claudelog-harvest] exclude_or_negative flags=weak_question_suffix :: 内容的に区分けしたかった＋確証バイアスの内容なのでナンバリングにしたのですが、どうでしょう
- corpus#659 [verify / claudelog-harvest] exclude_or_negative flags=weak_question_suffix :: 現状の学習をまずアーカイブ化(backup)して戻れる状態でQの解決案＋人間レビューに進むというのはどうですか
- corpus#687 [explore / claudelog-harvest] exclude_or_relabel_clarify flags=path_or_url,bare_path_or_url :: D:\nichijo_jissouこちらのprojectにチャットとの会話データがあるのですが、ところどころテストを踏まえたチャットがあるのでClaudeさんが採用出来る入力チャットと出力チャットを採用するというのはどうでしょう
- corpus#717 [respond / claudelog-harvest] exclude_or_relabel_clarify flags=path_or_url,bare_path_or_url :: @"C:\Users\kota\Desktop\テキストsample.txt" とりあえず一万文字拾ってきました

## Path / URL Review

- corpus#422 [build / claudelog-harvest] keep_if_directive_but_anonymize_path :: 03_instructions/precursor_tasks_v0.1.mdこちらを読んでもらってから続き行きましょう！
- corpus#428 [build / claudelog-harvest] keep_if_directive_but_anonymize_path :: "D:\pseudo personality\02_design\Inverse_Hybrid_AI_Design_v1.5.md"続きからお願いします！
- corpus#462 [clarify / claudelog-harvest] exclude_or_relabel_clarify :: きました！ありがとうございます。ここで質問するのもなんですが、"D:\Thought State Register"側のサンプル集めに、どの様な種類の質問が良いでしょう。
- corpus#473 [respond / claudelog-harvest] exclude_or_relabel_clarify :: "D:\nichijo_jissou\05_post_impl\handoff_to_code_2026-05-30.md" mypyベースライン109errorsも環境による物以外修正済みです
- corpus#479 [build / claudelog-harvest] keep_if_directive_but_anonymize_path :: @"D:\nichijo_jissou\03_instructions\7day_chat_test_preflight_checklist_2026-06-01.md" test前の
- corpus#490 [respond / claudelog-harvest] keep_if_directive_but_anonymize_path :: 昨日の続きからの前にcodexのレポートです。/D:/pseudo personality/inverse_hybrid_ai/README.md
- corpus#528 [respond / claudelog-harvest] exclude_or_relabel_clarify :: すみませんフォルダが重なってたので短縮しました。D:\models\gemma-4-12B-it
- corpus#530 [explore / claudelog-harvest] keep_if_directive_but_anonymize_path :: ollama経由だとモデル落とせなかったので、すでにインストールしていたLMStudioのgemma4を "D:\models\gemma-4-E4B-it-GGUF"にコピーしましたllamaで使えると思うのですがどうでしょう。遅くなるとは思いますが、使えるモデルを増やすという意味ではアリだと思います
- corpus#542 [build / claudelog-harvest] keep_if_directive_but_anonymize_path :: "D:\pseudo personality\CLAUDE.md"を読み実装を進めてください！
- corpus#551 [explain / claudelog-harvest] exclude_or_relabel_clarify :: 質問です！__D:\Topic packaging\backend\app\domain\enums.pyここを取り入れてるってことは、topic packaging内の学習データを利用可能ってことですよね？__ だとしたら、そちらも近いうちにUIまで仕上げて学習させるのがよさそうですね
- corpus#570 [build / claudelog-harvest] keep_if_directive_but_anonymize_path :: なるほどありがとうございます！それでは、 直近のこちらをお願いしたいです以下ログです Claude Code 側で docs/auto_log_review_2026-05-08.md + CLAUDE.md + docs/Agents.md を読ませて docs/impl_11_chat_quality_and_mood_recovery_<date>.md（英語、設計書）の起草から始めてください。
- corpus#571 [explain / claudelog-harvest] keep_if_directive_but_anonymize_path :: @D:\Hybrid_PC_AI\docs\auto_log_review_2026-05-08.md これで読めますか
- corpus#575 [respond / claudelog-harvest] keep_if_directive_but_anonymize_path :: "D:\Hybrid_PC_AI\start_ui.bat"start uiはこちらからしてます
- corpus#651 [build / claudelog-harvest] keep_if_directive_but_anonymize_path :: server起動.batとUI.batが欲しいです！D:\Topic packagingこちらにお願いします
- corpus#658 [verify / claudelog-harvest] keep_if_directive_but_anonymize_path :: D:/Thought State Register/docs/EXTERNAL_REVIEW_REPORT_2026-06-11.md v1.6まで進めたので確認と調査をお願いします
- corpus#687 [explore / claudelog-harvest] exclude_or_relabel_clarify :: D:\nichijo_jissouこちらのprojectにチャットとの会話データがあるのですが、ところどころテストを踏まえたチャットがあるのでClaudeさんが採用出来る入力チャットと出力チャットを採用するというのはどうでしょう
- corpus#717 [respond / claudelog-harvest] exclude_or_relabel_clarify :: @"C:\Users\kota\Desktop\テキストsample.txt" とりあえず一万文字拾ってきました
- corpus#725 [explore / claudelog-harvest] keep_if_directive_but_anonymize_path :: "D:\Hybrid_PC_AI" "D:\nichijo_jissou" D:\Core5_Project\core_review 導入候補としてこちらがあるのですが順位付けお願いします
- corpus#726 [respond / claudelog-harvest] keep_if_directive_but_anonymize_path :: nichijo_jissouからまずは導入行きましょう。その前にもう一つ候補がありまして、そちらは確か、メインＬＬＭがsubに司令を出す形でさらに海馬LLMを載せた物になります。D:\keywordmodel 多分これなのですが、特徴は海馬LLMがあった事です。

## Very Short Review

- corpus#87 [respond / pattern-db-remap] keep_if_intent_is_unambiguous :: こんにちは
- corpus#89 [respond / pattern-db-remap] keep_if_intent_is_unambiguous :: こんばんは
- corpus#93 [respond / pattern-db-remap] keep_if_intent_is_unambiguous :: お元気ですか
- corpus#94 [respond / pattern-db-remap] keep_if_intent_is_unambiguous :: おやすみなさい
- corpus#97 [respond / pattern-db-remap] keep_if_intent_is_unambiguous :: Hello!
- corpus#437 [respond / claudelog-harvest] keep_if_intent_is_unambiguous :: 稼働中です！
- corpus#519 [verify / claudelog-harvest] keep_if_intent_is_unambiguous :: ログ確認お願い
- corpus#522 [verify / claudelog-harvest] keep_if_intent_is_unambiguous :: ログ確認
- corpus#538 [build / claudelog-harvest] keep_if_intent_is_unambiguous :: A行きましょう
- corpus#579 [respond / claudelog-harvest] keep_if_intent_is_unambiguous :: まだ出る様子です
- corpus#622 [build / claudelog-harvest] keep_if_intent_is_unambiguous :: Cに行きましょう
- corpus#675 [build / claudelog-harvest] keep_if_intent_is_unambiguous :: マージして
- corpus#677 [build / claudelog-harvest] keep_if_intent_is_unambiguous :: 記録して
- corpus#680 [build / claudelog-harvest] keep_if_intent_is_unambiguous :: １で参りましょう
- corpus#686 [build / claudelog-harvest] keep_if_intent_is_unambiguous :: 承認して！
- corpus#694 [build / claudelog-harvest] keep_if_intent_is_unambiguous :: 承認して
- corpus#718 [build / claudelog-harvest] keep_if_intent_is_unambiguous :: Aの投入

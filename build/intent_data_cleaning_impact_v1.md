# Intent Data Cleaning Impact v1

Diagnostic only. No corpus, deployed model, candidate model, or sealed fixture is modified.

## Summary

- generated_at: 2026-06-28T05:28:14.997995+00:00
- baseline examples: 739
- suspect rows: 47
- high-priority rows: 9
- sealed fixtures used: False

## Scenario Ablations

| scenario | action | removed | gate | kfold delta | route delta | failed delta | label |
| --- | --- | ---: | --- | ---: | ---: | ---: | --- |
| high_priority_actionable | quarantine_for_review | 9 | pass | +0.035238 | +0.000000 | +0 | neutral_but_safe_review_candidate |
| exclude_or_negative | move_to_negative_or_failure_memory | 3 | pass | -0.001484 | +0.000000 | +0 | needs_more_evidence_before_removal |
| exclude_or_relabel_clarify | quarantine_or_relabel | 6 | pass | -0.000251 | +0.000000 | +0 | needs_more_evidence_before_removal |
| bare_path_or_url | quarantine_or_relabel | 6 | pass | -0.000251 | +0.000000 | +0 | needs_more_evidence_before_removal |
| weak_question_respond_verify | quarantine_or_negative | 2 | pass | +0.004440 | +0.000000 | +0 | neutral_but_safe_review_candidate |
| very_short_control | do_not_bulk_remove | 17 | pass | +0.003895 | +0.000000 | +0 | control_group_review_only |
| all_suspects_diagnostic | diagnostic_only_do_not_adopt_as_a_bulk_delete | 47 | pass | +0.030190 | +0.000000 | +0 | diagnostic_only_too_broad |

## Individual High-Priority Rows

| corpus index | recommendation | intent | kfold delta | route delta | failed delta | label | input |
| ---: | --- | --- | ---: | ---: | ---: | --- | --- |
| 90 | exclude_or_negative | respond | -0.008623 | +0.000000 | +0 | needs_more_evidence_before_removal | ありがとうございます |
| 462 | exclude_or_relabel_clarify | clarify | +0.006282 | +0.000000 | +0 | neutral_but_safe_review_candidate | きました！ありがとうございます。ここで質問するのもなんですが、"D:\Thought State Register"側のサンプル集めに、どの様な種類の質問が良いでしょう。 |
| 473 | exclude_or_relabel_clarify | respond | +0.006282 | +0.000000 | +0 | neutral_but_safe_review_candidate | "D:\nichijo_jissou\05_post_impl\handoff_to_code_2026-05-30.md" mypyベースライン109errorsも環境による物以外修正済み... |
| 528 | exclude_or_relabel_clarify | respond | -0.004558 | +0.000000 | +0 | needs_more_evidence_before_removal | すみませんフォルダが重なってたので短縮しました。D:\models\gemma-4-12B-it |
| 551 | exclude_or_relabel_clarify | explain | +0.019832 | +0.000000 | +0 | neutral_but_safe_review_candidate | 質問です！__D:\Topic packaging\backend\app\domain\enums.pyここを取り入れてるってことは、topic packaging内の学習データを利用可能... |
| 627 | exclude_or_negative | verify | -0.000493 | +0.000000 | +0 | needs_more_evidence_before_removal | 内容的に区分けしたかった＋確証バイアスの内容なのでナンバリングにしたのですが、どうでしょう |
| 659 | exclude_or_negative | verify | +0.018477 | +0.000000 | +0 | neutral_but_safe_review_candidate | 現状の学習をまずアーカイブ化(backup)して戻れる状態でQの解決案＋人間レビューに進むというのはどうですか |
| 687 | exclude_or_relabel_clarify | explore | -0.008623 | +0.000000 | +0 | needs_more_evidence_before_removal | D:\nichijo_jissouこちらのprojectにチャットとの会話データがあるのですが、ところどころテストを踏まえたチャットがあるのでClaudeさんが採用出来る入力チャットと出力チ... |
| 717 | exclude_or_relabel_clarify | respond | -0.005913 | +0.000000 | +0 | needs_more_evidence_before_removal | @"C:\Users\kota\Desktop\テキストsample.txt" とりあえず一万文字拾ってきました |

## Interpretation Rule

- `adoptable_quarantine_candidate`: good removal candidate, but still review before changing corpus.
- `neutral_but_safe_review_candidate`: safe-looking but not yet proven valuable.
- `needs_more_evidence_before_removal`: keep or relabel until more non-sealed evidence arrives.
- `diagnostic_only_too_broad`: useful for estimating damage, not for bulk deletion.

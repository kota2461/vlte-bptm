# Critical / Constraints Candidate Review v1

Diagnostic only. These are non-sealed candidates extracted from open logs/corpora. Draft labels come from the current adapter and must be human-reviewed before training or gate use.

Sealed fixtures are not input sources for this worksheet.

## Summary

- generated_at: 2026-06-28T06:32:03.195357+00:00
- unique inputs scanned: 824
- candidates: 559
- review candidates (A+B): 202
- probe candidates (C): 357
- priority counts: {'A': 65, 'B': 137, 'C': 357}
- focus counts: {'constraints': 39, 'critical_signal:contains_unverified_claims': 14, 'critical_signal:missing_required_information': 12, 'critical_signal:multiple_intents': 34, 'critical_signal:requires_current_information': 8, 'operations': 141, 'risk': 8, 'source_intent_probe': 357}
- route intent counts: {'build': 77, 'clarify': 14, 'explain': 3, 'explore': 39, 'respond': 305, 'summarize': 34, 'verify': 87}

## Review Rule

For each row, approve only if the draft `critical_signal`, `constraints`, `risk`, and `operations` are correct. Otherwise mark corrected labels in the JSON/notes before promotion.

## Priority A - Critical Signals

| id | focus | draft | source intent | score | input |
| --- | --- | --- | --- | ---: | --- |
| cc-open-v1-001 | constraints, critical_signal:multiple_intents, critical_signal:requires_current_information, operations, risk | `summarize / ops=summarize,verify,search` | `summarize` | 45 | 最新statusを確認して、summaryを3行でお願いします。 |
| cc-open-v1-002 | critical_signal:contains_unverified_claims, critical_signal:requires_current_information, operations, risk | `verify / ops=verify,search` | `verify` | 36 | 現時点のAPI料金を確認してください。 |
| cc-open-v1-003 | constraints, critical_signal:requires_current_information, operations, risk | `verify / ops=verify,search` | `verify` | 35 | 今日の為替レートを出典付きで確認してください。 |
| cc-open-v1-004 | critical_signal:multiple_intents, critical_signal:requires_current_information, operations, risk | `respond / ops=respond,search` | `respond` | 33 | この企画の主軸は感情変動を継続的に維持して、最終的に、発話、内省思考をする。なので、長文できれてしまうのはリソース的に仕方ないというか、受け入れる方向です。長文にならないような会話を心掛けるようにします。現在はテストなので、bass1で長… |
| cc-open-v1-005 | critical_signal:requires_current_information, operations, risk | `verify / ops=verify,search` | `verify` | 26 | Is the approach you suggested earlier still the recommended one as of today? |
| cc-open-v1-006 | critical_signal:requires_current_information, operations, risk | `verify / ops=verify,search` | `verify` | 26 | Is this old tutorial still accurate for the current app? |
| cc-open-v1-007 | critical_signal:requires_current_information, operations, risk | `verify / ops=verify,search` | `verify` | 26 | この古いレシピ、今の食材でもそのまま作れるか確認して |
| cc-open-v1-008 | critical_signal:requires_current_information, operations, risk | `verify / ops=verify,search` | `verify` | 26 | さっき教えてもらった方法、今のバージョンでもそのまま使える？ |
| cc-open-v1-009 | constraints, critical_signal:multiple_intents | `build / ops=build,summarize` | `build` | 21 | 確認結果を短くまとめ、その後で実装計画を提示してください。 |
| cc-open-v1-010 | constraints, critical_signal:missing_required_information | `clarify / ops=clarify` | `clarify` | 21 | Before you answer, ask me which environment this is for. |
| cc-open-v1-011 | constraints, critical_signal:missing_required_information | `clarify / ops=clarify` | `clarify` | 21 | Before you recommend a camera, ask me what I'll shoot. |
| cc-open-v1-012 | constraints, critical_signal:missing_required_information | `clarify / ops=clarify` | `clarify` | 21 | If any requirement seems ambiguous, ask me before answering. |
| cc-open-v1-013 | constraints, critical_signal:missing_required_information | `clarify / ops=clarify` | `clarify` | 21 | Please ask me questions if my English sentence is ambiguous. |
| cc-open-v1-014 | constraints, critical_signal:missing_required_information | `clarify / ops=clarify` | `clarify` | 21 | The deadline is not mentioned anywhere, so please ask me for it. |
| cc-open-v1-015 | constraints, critical_signal:missing_required_information | `clarify / ops=clarify` | `clarify` | 21 | どの値を答えればよいか不明なので、先に質問して確認してください |
| cc-open-v1-016 | constraints, critical_signal:missing_required_information | `clarify / ops=clarify` | `clarify` | 21 | 出力形式が指定されていないので、希望する形式を聞いてください |
| cc-open-v1-017 | constraints, critical_signal:missing_required_information | `clarify / ops=clarify` | `clarify` | 21 | 確率の問題で事象が独立かどうか不明な場合、何を確認すべきか質問してください |
| cc-open-v1-018 | critical_signal:contains_unverified_claims, operations | `verify / ops=verify,calculate` | `verify` | 20 | Can you verify these expense totals are right? |
| cc-open-v1-019 | critical_signal:contains_unverified_claims, operations | `verify / ops=verify,calculate` | `verify` | 20 | Double-check that these totals actually add up. |
| cc-open-v1-020 | critical_signal:contains_unverified_claims, operations | `verify / ops=verify,calculate` | `verify` | 20 | この invoice の合計が契約上の単価と合っているか確認して |
| cc-open-v1-021 | critical_signal:contains_unverified_claims, operations | `verify / ops=verify,calculate` | `verify` | 20 | 家計簿の合計、計算が合ってるか確かめて |
| cc-open-v1-022 | critical_signal:multiple_intents, operations | `build / ops=build,verify` | `build` | 19 | Check the assumptions first, and then produce an implementation plan. |
| cc-open-v1-023 | critical_signal:multiple_intents, operations | `build / ops=build,verify` | `build` | 19 | 予約が取れているか確認して、大丈夫なら案内メールの下書きを作って |
| cc-open-v1-024 | critical_signal:multiple_intents, operations | `build / ops=build,verify` | `build` | 19 | 仕様の整合性を確認してから、移行のタスク一覧を出してください。 |
| cc-open-v1-025 | critical_signal:multiple_intents, operations | `build / ops=build,verify` | `build` | 19 | 前提をcheckして、その上で移行planを作ってください。 |
| cc-open-v1-026 | critical_signal:multiple_intents, operations | `build / ops=build,verify` | `build` | 19 | 在庫が足りてるか確認して、大丈夫なら買い物リストを作って |
| cc-open-v1-027 | critical_signal:multiple_intents, operations | `summarize / ops=summarize,compare` | `summarize` | 19 | Summarize the incident and then compare three recovery options. |
| cc-open-v1-028 | critical_signal:contains_unverified_claims, operations | `verify / ops=verify` | `verify` | 19 | Can you confirm these figures are accurate? |
| cc-open-v1-029 | critical_signal:contains_unverified_claims, operations | `verify / ops=verify` | `verify` | 19 | Can you sanity-check this conclusion against the data? |
| cc-open-v1-030 | critical_signal:multiple_intents, operations | `verify / ops=verify` | `verify` | 19 | Review this proof and point out any logical gaps. |
| cc-open-v1-031 | critical_signal:contains_unverified_claims, operations | `verify / ops=verify` | `verify` | 19 | The input size and hardware are provided. Check whether the claimed runtime is plausible. |
| cc-open-v1-032 | critical_signal:contains_unverified_claims, operations | `verify / ops=verify` | `verify` | 19 | この主張って本当に正しいの？根拠あるか見てほしい |
| cc-open-v1-033 | critical_signal:multiple_intents, operations | `verify / ops=verify` | `explore` | 19 | これはあれです。loraを切って明日試しましょう。loraなしの実績も確認できます。そして、明日までに周辺のレビューをcodexにしてもらい、別視点からの問題点の洗い出しをしてもらいます。codexあての指示、メモがあれば頂きたいです！ |
| cc-open-v1-034 | critical_signal:contains_unverified_claims, operations | `verify / ops=verify` | `verify` | 19 | 利用人数は50人、期間は6か月です。提示された予算内に収まるか確認してください。 |
| cc-open-v1-035 | critical_signal:contains_unverified_claims, operations | `verify / ops=verify` | `verify` | 19 | 報告された集計値を鵜呑みにせず、元データと突き合わせて検算してください |
| cc-open-v1-036 | critical_signal:contains_unverified_claims, operations | `verify / ops=verify` | `verify` | 19 | 提示されたURLが正しいページを指しているか確認してください |
| cc-open-v1-037 | critical_signal:contains_unverified_claims, operations | `verify / ops=verify` | `verify` | 19 | 提示された違約金の計算が契約条項と一致しているか検証してください |
| cc-open-v1-038 | critical_signal:multiple_intents, operations | `verify / ops=verify` | `verify` | 19 | 現在一度試して、エラーになっているので確認してみてください！ |
| cc-open-v1-039 | critical_signal:multiple_intents, operations | `verify / ops=verify` | `respond` | 17 | そうですね。一旦絞めて、他のエージェントレビュー、改善点の提案を聞いてみます！初号機は確定モデルとして、凍結。他のprojectに採用し実dataの蓄積に回します。 |
| cc-open-v1-040 | critical_signal:multiple_intents | `build / ops=build` | `build` | 12 | model用意をして、Claudeさん側で切り替え可能な形でGemma4をいれてみますか。その場合量子化4bitがあります。すでにある場合はダウンロードしてきます！ |
| cc-open-v1-041 | critical_signal:multiple_intents | `build / ops=build,summarize` | `build` | 12 | この単元の要点を整理して、そのうえで理解度チェックの問題を作ってください |
| cc-open-v1-042 | critical_signal:multiple_intents | `build / ops=build` | `build` | 12 | まず問題を説明し、続けて修正手順を作ってください。 |
| cc-open-v1-043 | critical_signal:missing_required_information | `clarify / ops=clarify` | `clarify` | 12 | I want this fixed, but I'm not sure what info you need — ask me. |
| cc-open-v1-044 | critical_signal:missing_required_information | `clarify / ops=clarify` | `clarify` | 12 | 必要な予算を見積もってください。利用人数と期間はまだ伝えていません。 |
| cc-open-v1-045 | critical_signal:missing_required_information | `clarify / ops=clarify` | `clarify` | 12 | 解約に必要な条件がまだ共有できていないので、先に何を確認すべきか教えてください |
| cc-open-v1-046 | critical_signal:missing_required_information | `clarify / ops=clarify` | `clarify` | 12 | 請求の根拠になる利用ログの置き場所が分からないので、まず質問してもらえますか |
| cc-open-v1-047 | critical_signal:multiple_intents | `respond / ops=respond` | `build` | 12 | Bにしましょう！そのうえで、欲しいログの内容を教えてください！ |
| cc-open-v1-048 | critical_signal:multiple_intents | `respond / ops=respond` | `build` | 12 | このプロジェクトの仕様書の理念、ロードマップにそって設計書を読み、構造の精査、修正、改善、その後に数学的思考パターンの学習まで行って下さい。数学的思考パターンは基礎的な数字の理解から加算の同回答バリエーションを混ぜながら日本の高等学校le… |
| cc-open-v1-049 | critical_signal:multiple_intents | `respond / ops=respond` | `clarify` | 12 | この先は新しいスレッドでUI実装までして、学習データを持って戻ってきた方が良さそうですか？ |
| cc-open-v1-050 | critical_signal:multiple_intents | `respond / ops=respond` | `build` | 12 | これが初Modelとして、実働に耐える仕様迄持っていけばいいと割り切って、この結果を記録して、(b)の方向(v0.3=gatedハイブリッドを正式採用+0.90を実データ将来版へ) で設計を確定。将来的に初Modelを元に学習の見直しや構… |
| cc-open-v1-051 | critical_signal:multiple_intents | `respond / ops=respond` | `clarify` | 12 | まずは記録して、言葉に対する重みとして正、誤のタグをつけるのはV違いになってしまいますか？ |
| cc-open-v1-052 | critical_signal:multiple_intents | `respond / ops=respond` | `build` | 12 | 品質は将来課題として、残りの二つ行ってしまいましょう |
| cc-open-v1-053 | critical_signal:multiple_intents | `respond / ops=respond` | `build` | 12 | 将来の判断材料になると思うので記録しましょう！その後で実装に進みましょう |
| cc-open-v1-054 | critical_signal:multiple_intents | `respond / ops=respond` | `build` | 12 | 精度ブレみたいな物があるという事で、のちのロードマップに追加で、同じ回答を三つのユニットで回して学習。(精度、閾値別で出す)これは回答の同じものを正答とする学習として。どうでしょう？要らなければスキップで良いです。 その後に、手番通りのル… |
| cc-open-v1-055 | critical_signal:multiple_intents | `respond / ops=respond` | `build` | 12 | 続けてM１お願いします！ |
| cc-open-v1-056 | critical_signal:multiple_intents | `respond / ops=respond` | `build` | 12 | 記録して1にして、3を次回の始まりとしましょう。 |
| cc-open-v1-057 | critical_signal:multiple_intents | `respond / ops=respond` | `build` | 12 | 記録して、その後にの頃に進みます！ |
| cc-open-v1-058 | critical_signal:multiple_intents | `summarize / ops=summarize` | `summarize` | 12 | Summarize how backpropagation works and point out where people usually get confused. |
| cc-open-v1-059 | critical_signal:multiple_intents | `summarize / ops=summarize` | `summarize` | 12 | この利用規約の責任範囲を要約して、リスクが高い箇所を洗い出してください |
| cc-open-v1-060 | critical_signal:multiple_intents | `respond / ops=respond` | `respond` | 10 | nichijo_jissouからまずは導入行きましょう。その前にもう一つ候補がありまして、そちらは確か、メインＬＬＭがsubに司令を出す形でさらに海馬LLMを載せた物になります。D:\keywordmodel 多分これなのですが、特徴は海… |
| cc-open-v1-061 | critical_signal:multiple_intents | `respond / ops=respond` | `explain` | 10 | このルーターの機能として、簡素な質問はLLMを解せずに応答。と言う機能もつけられますか？ |
| cc-open-v1-062 | critical_signal:multiple_intents | `respond / ops=respond` | `respond` | 10 | はじめまして、よろしくお願いします |
| cc-open-v1-063 | critical_signal:multiple_intents | `respond / ops=respond` | `explain` | 10 | オウム返しは無くなりました！ありがとうございます！次の課題として、保持トークンの状態と維持について調べて欲しいです |
| cc-open-v1-064 | critical_signal:contains_unverified_claims | `respond / ops=respond` | `respond` | 10 | 提示された情報から、最も直接的な原因の説明を答えてください |
| cc-open-v1-065 | critical_signal:multiple_intents | `summarize / ops=summarize` | `respond` | 10 | お疲れさまでした！ ここからは、実使用を想定したものになるのでバージョン違いとして、IDEAから案をまとめてロードマップと設計から始めましょう。 |

## Priority B - Constraints / Operations

| id | focus | draft | source intent | score | input |
| --- | --- | --- | --- | ---: | --- |
| cc-open-v1-066 | constraints, operations | `summarize / ops=summarize,calculate` | `summarize` | 18 | 計算結果の要点を短く要約してください |
| cc-open-v1-067 | constraints, operations | `verify / ops=verify` | `clarify` | 18 | 検算に使う元データの場所が示されていないので、どこにあるか質問してください |
| cc-open-v1-068 | constraints | `respond / ops=respond` | `clarify` | 11 | この問題は条件が不足しているので、必要な情報を質問してください |
| cc-open-v1-069 | constraints | `respond / ops=respond` | `clarify` | 11 | 依頼の目的が読み取れない場合は、何を望むか質問してください |
| cc-open-v1-070 | constraints | `respond / ops=respond` | `clarify` | 11 | 問題で求める対象が分からないときは、対象を質問してください |
| cc-open-v1-071 | constraints | `respond / ops=respond` | `clarify` | 11 | 問題文に数値が足りないときは何が必要か質問してください |
| cc-open-v1-072 | constraints | `respond / ops=respond` | `clarify` | 11 | 変数の定義が不明なので質問してください |
| cc-open-v1-073 | constraints | `respond / ops=respond` | `clarify` | 11 | 実行環境が分からないので、OSと利用バージョンを質問してください |
| cc-open-v1-074 | constraints | `respond / ops=respond` | `clarify` | 11 | 希望する出力形式が不明なので、形式と用途を質問してください |
| cc-open-v1-075 | constraints | `respond / ops=respond` | `clarify` | 11 | 文の意味が二通りに読めるときは、どちらの意味か質問してください |
| cc-open-v1-076 | constraints | `respond / ops=respond` | `build` | 11 | 登録しました！ドラック＆ドロップだと、反映されずらいので、3行程度で端に文字数を表示してもらえると分かり易くなります！ |
| cc-open-v1-077 | constraints | `respond / ops=respond` | `clarify` | 11 | 確認対象のURLが書かれていないので、対象URLを質問してください |
| cc-open-v1-078 | constraints | `summarize / ops=summarize` | `summarize` | 11 | Condense these notes into key bullet points. |
| cc-open-v1-079 | constraints | `summarize / ops=summarize` | `summarize` | 11 | Give me a brief summary of the main argument of this article. |
| cc-open-v1-080 | constraints | `summarize / ops=summarize` | `summarize` | 11 | Summarize this English paragraph in one sentence. |
| cc-open-v1-081 | constraints | `summarize / ops=summarize` | `summarize` | 11 | このマニュアル、結局何をすればいいか短くまとめて |
| cc-open-v1-082 | constraints | `summarize / ops=summarize` | `summarize` | 11 | このレシピサイトの長い説明、要点だけ短くまとめて |
| cc-open-v1-083 | constraints | `summarize / ops=summarize` | `summarize` | 11 | この段落を一文に要約してください |
| cc-open-v1-084 | constraints | `summarize / ops=summarize` | `summarize` | 11 | この解答のポイントを短くまとめてください |
| cc-open-v1-085 | constraints | `summarize / ops=summarize` | `summarize` | 11 | この解答全体を3行で要約してください |
| cc-open-v1-086 | constraints | `summarize / ops=summarize` | `summarize` | 11 | この長いスレッド、要点だけ短くまとめて |
| cc-open-v1-087 | constraints | `summarize / ops=summarize` | `summarize` | 11 | この長い証明の要点を短く要約してください |
| cc-open-v1-088 | constraints | `summarize / ops=summarize` | `summarize` | 11 | 今日読んだ記事、3行でまとめてくれる？ |
| cc-open-v1-089 | constraints | `summarize / ops=summarize` | `summarize` | 11 | 会議の内容、3行でまとめてくれる？ |
| cc-open-v1-090 | constraints | `summarize / ops=summarize` | `summarize` | 11 | 家電の取説、結局どう使えばいいか短くまとめて |
| cc-open-v1-091 | constraints | `summarize / ops=summarize` | `summarize` | 11 | 微分と積分の関係を一文で要約してください |
| cc-open-v1-092 | constraints | `summarize / ops=summarize` | `summarize` | 11 | 証明の流れを簡潔にまとめて要約してください |
| cc-open-v1-093 | operations | `verify / ops=verify,calculate` | `verify` | 10 | 0.5と1/2が等しいことを確認してください |
| cc-open-v1-094 | operations | `verify / ops=verify,calculate` | `verify` | 10 | 3+5=9が正しいかどうか確認してください |
| cc-open-v1-095 | operations | `verify / ops=verify,calculate` | `verify` | 10 | 与えられた数値を使って計算結果が合っているか検算してください |
| cc-open-v1-096 | operations | `verify / ops=verify,calculate` | `verify` | 10 | 極限 lim(x→0) sinx/x = 1 の計算結果を検証してください |
| cc-open-v1-097 | operations | `verify / ops=verify,calculate` | `verify` | 10 | 計算結果と与えられた条件が一致するか検算してください |
| cc-open-v1-098 | operations | `verify / ops=verify,calculate` | `verify` | 10 | 計算結果に誤りがないか検算してください |
| cc-open-v1-099 | operations | `build / ops=build,verify` | `build` | 9 | Confirm this clause does not conflict with the earlier agreement, then draft the revised wording. |
| cc-open-v1-100 | operations | `build / ops=build,verify` | `build` | 9 | Validate the API contract, then create a rollout plan. |
| cc-open-v1-101 | operations | `build / ops=build,verify` | `build` | 9 | この証明が正しいか見てもらって、合っていたら次の章に進む学習計画を作ってほしい |
| cc-open-v1-102 | operations | `build / ops=build,verify` | `build` | 9 | 依存関係を確かめた後、導入手順を作成してください。 |
| cc-open-v1-103 | operations | `build / ops=build,verify` | `build` | 9 | 個人情報の取り扱い条項が法令に沿っているか確かめたうえで、対応手順を作ってください |
| cc-open-v1-104 | operations | `build / ops=build,verify` | `build` | 9 | 契約書のこの解約条項に抜けがないか確認したうえで、修正案を作ってください |
| cc-open-v1-105 | operations | `build / ops=build,verify` | `build` | 9 | 弱点解消から推奨の順番でお願いします！ |
| cc-open-v1-106 | operations | `build / ops=build,verify` | `verify` | 9 | 求めた値が与えられた条件をすべて満たすか順番に確認してください |
| cc-open-v1-107 | operations | `build / ops=build,verify` | `build` | 9 | 見積金額が予算内かを確かめて、問題なければ発注書のドラフトを用意してください |
| cc-open-v1-108 | operations | `build / ops=build,calculate` | `build` | 9 | 解と係数の関係を使って x^2-5x+6=0 の解を求める手順を構成してください |
| cc-open-v1-109 | constraints | `explain / ops=explain` | `respond` | 9 | この案内文の内容を簡潔に説明してください |
| cc-open-v1-110 | operations | `explore / ops=explore,compare` | `explore` | 9 | Compare several architecture options without committing to one. |
| cc-open-v1-111 | operations | `explore / ops=explore,compare` | `explore` | 9 | Give me a few different ways to approach this, with trade-offs. |
| cc-open-v1-112 | operations | `explore / ops=explore,compare` | `explore` | 9 | Give me a few different weeknight dinner ideas to compare. |
| cc-open-v1-113 | operations | `explore / ops=explore,compare` | `explore` | 9 | What are some alternative tools for this? Compare them. |
| cc-open-v1-114 | operations | `explore / ops=explore,compare` | `explore` | 9 | What are some alternative ways to save on groceries? Compare. |
| cc-open-v1-115 | operations | `explore / ops=explore,compare` | `explore` | 9 | この案のalternativesを日本語でcompareしてください。 |
| cc-open-v1-116 | operations | `explore / ops=explore,compare` | `explore` | 9 | カメラ選び、用途別に候補を出して比較して |
| cc-open-v1-117 | operations | `explore / ops=explore,compare` | `explore` | 9 | 一つの答えに絞る前に代替アプローチを比較してください |
| cc-open-v1-118 | operations | `explore / ops=explore,compare` | `explore` | 9 | 二次方程式の解法を平方完成と判別式の二通りで比較してください |
| cc-open-v1-119 | operations | `explore / ops=explore,compare` | `explore` | 9 | 保存方式を決める前に、性質の異なる候補を比較してください |
| cc-open-v1-120 | operations | `explore / ops=explore,compare` | `explore` | 9 | 解約トラブルを避けるための条項の入れ方を、いくつかの案で比較してください |
| cc-open-v1-121 | operations | `respond / ops=respond,calculate` | `verify` | 9 | 1+2+...+n = n(n+1)/2 を数学的帰納法で証明してください |
| cc-open-v1-122 | operations | `respond / ops=respond,compare` | `explore` | 9 | 少し時間のかかる問題での応答速度の比較お願いします！ |
| cc-open-v1-123 | operations | `summarize / ops=summarize,compare` | `summarize` | 9 | 要点をまとめてから、二つの案を比較してください。 |
| cc-open-v1-124 | operations | `verify / ops=verify` | `explore` | 9 | "D:\Hybrid_PC_AI" "D:\nichijo_jissou" D:\Core5_Project\core_review 導入候補としてこちらがあるのですが順位付けお願いします |
| cc-open-v1-125 | operations | `verify / ops=verify` | `verify` | 9 | Check that this answer matches the expected result. |
| cc-open-v1-126 | operations | `verify / ops=verify` | `verify` | 9 | Check whether the specified artifact satisfies the stated requirement. |
| cc-open-v1-127 | operations | `verify / ops=verify` | `verify` | 9 | Check whether this calculation is correct: 12 x 8 = 86. |
| cc-open-v1-128 | operations | `verify / ops=verify` | `verify` | 9 | Confirm whether the provided premise is supported by the evidence. |
| cc-open-v1-129 | operations | `verify / ops=verify` | `verify` | 9 | D:/Thought State Register/docs/EXTERNAL_REVIEW_REPORT_2026-06-11.md v1.6まで進めたので確認と調査をお願いします |
| cc-open-v1-130 | operations | `verify / ops=verify` | `verify` | 9 | Does this code change satisfy the stated requirements? Please verify. |
| cc-open-v1-131 | operations | `verify / ops=verify` | `verify` | 9 | Double-check that this recipe's measurements make sense. |
| cc-open-v1-132 | operations | `verify / ops=verify` | `summarize` | 9 | Give me the gist of this product review. |
| cc-open-v1-133 | operations | `verify / ops=verify` | `verify` | 9 | Make sure I didn't miss a step in this assembly guide. |
| cc-open-v1-134 | operations | `verify / ops=verify` | `verify` | 9 | Make sure the configuration meets the security policy. |
| cc-open-v1-135 | operations | `verify / ops=verify` | `verify` | 9 | Make sure the migration didn't drop any records. |
| cc-open-v1-136 | operations | `verify / ops=verify` | `build` | 9 | Plan the rollout, but confirm the dependencies first. |
| cc-open-v1-137 | operations | `verify / ops=verify` | `verify` | 9 | Verify whether this sentence is grammatically correct: "He go to school." |
| cc-open-v1-138 | operations | `verify / ops=verify` | `explore` | 9 | ollama経由だとモデル落とせなかったので、すでにインストールしていたLMStudioのgemma4を "D:\models\gemma-4-E4B-it-GGUF"にコピーしましたllamaで使えると思うのですがどうでしょう。遅くなる… |
| cc-open-v1-139 | operations | `verify / ops=verify` | `verify` | 9 | √2が無理数であることの証明を検証してください |
| cc-open-v1-140 | operations | `verify / ops=verify` | `clarify` | 9 | おすすめ教えて。あ、用途を言ってなかったから先に聞いてくれる？ |
| cc-open-v1-141 | operations | `verify / ops=verify` | `verify` | 9 | こちらを確認してください！ |
| cc-open-v1-142 | operations | `verify / ops=verify` | `explore` | 9 | こちら使えますか！ |
| cc-open-v1-143 | operations | `verify / ops=verify` | `verify` | 9 | このプロジェクトの内部を弄らずにレビューが欲しいです。改善点はレポートにしてください |
| cc-open-v1-144 | operations | `verify / ops=verify` | `verify` | 9 | この不等式が常に成り立つか確認してください |
| cc-open-v1-145 | operations | `verify / ops=verify` | `verify` | 9 | この文の敬語の使い方が正しいか確認してください |
| cc-open-v1-146 | operations | `verify / ops=verify` | `verify` | 9 | この英作文、文法がおかしくないか確認してほしい |
| cc-open-v1-147 | operations | `verify / ops=verify` | `verify` | 9 | この設定でセキュリティ的に問題ないか確かめてほしい |
| cc-open-v1-148 | operations | `verify / ops=verify` | `build` | 9 | なるほどありがとうございます！それでは、 直近のこちらをお願いしたいです以下ログです Claude Code 側で docs/auto_log_review_2026-05-08.md + CLAUDE.md + docs/Agents.… |
| cc-open-v1-149 | operations | `verify / ops=verify` | `build` | 9 | まず予算が足りるか確かめて、それから旅行プランを立てて |
| cc-open-v1-150 | operations | `verify / ops=verify` | `verify` | 9 | サーバ再起動して GUI で「クリーン応答＋履歴保存」を一緒に確認するyazi |
| cc-open-v1-151 | operations | `verify / ops=verify` | `verify` | 9 | 予約の内容が希望どおりになってるか確認して |
| cc-open-v1-152 | operations | `verify / ops=verify` | `verify` | 9 | 予約の日程、希望どおりに取れてるか確認して |
| cc-open-v1-153 | operations | `verify / ops=verify` | `verify` | 9 | 出力が指定された形式と用途の条件を満たすか検証してください |
| cc-open-v1-154 | operations | `verify / ops=verify` | `build` | 9 | 分りました！Bを使える状態にする時の予備知識としてメモを残しておいて欲しいです！ |
| cc-open-v1-155 | operations | `verify / ops=verify` | `verify` | 9 | 前提条件が実際に成立しているか検証してください |
| cc-open-v1-156 | operations | `verify / ops=verify` | `build` | 9 | 反応しました！ありがとうございます！Slice 3（重複の共通化）の後に全体に対するレビューと稼働状況の調査いきましょう。 |
| cc-open-v1-157 | operations | `verify / ops=verify` | `verify` | 9 | 増減表とグラフの形が正しいか検証してください |
| cc-open-v1-158 | operations | `verify / ops=verify` | `build` | 9 | 推奨順に進めてください！よろしくお願いします |
| cc-open-v1-159 | operations | `verify / ops=verify` | `verify` | 9 | 提出されたレポートの数字、辻褄が合ってるか検算して |
| cc-open-v1-160 | operations | `verify / ops=verify` | `verify` | 9 | 提出した課題、要件を満たしてるか確認してほしい |
| cc-open-v1-161 | operations | `verify / ops=verify` | `build` | 9 | 時間空けて五時間制限もfullで使えるので一気に進めてください！ |
| cc-open-v1-162 | operations | `verify / ops=verify` | `verify` | 9 | 現状の学習をまずアーカイブ化(backup)して戻れる状態でQの解決案＋人間レビューに進むというのはどうですか |
| cc-open-v1-163 | operations | `verify / ops=verify` | `verify` | 9 | 示されたOSとバージョンでこの実装が動作するか確認してください |
| cc-open-v1-164 | operations | `verify / ops=verify` | `clarify` | 9 | 節約プランを立てたいけど、収入を言ってないから確認して |
| cc-open-v1-165 | operations | `verify / ops=verify` | `verify` | 9 | 翻訳が原文の意味とずれていないか確認してほしい |
| cc-open-v1-166 | operations | `verify / ops=verify` | `verify` | 9 | 解答が問題の要求を満たしているか確認してください |
| cc-open-v1-167 | operations | `verify / ops=verify` | `verify` | 9 | 解答の根拠が正しいかレビューしてください |
| cc-open-v1-168 | operations | `verify / ops=verify` | `verify` | 9 | 設定がこれで安全か確かめてほしい |
| cc-open-v1-169 | operations | `verify / ops=verify` | `verify` | 9 | 説明の根拠に誤りがないか確認してください |
| cc-open-v1-170 | operations | `verify / ops=verify` | `verify` | 9 | 送る前にこのメール、内容がおかしくないか確認して |
| cc-open-v1-171 | operations | `verify / ops=verify` | `build` | 9 | ３件を推奨の変更とAの方針で記録して |
| cc-open-v1-172 | operations | `explore / ops=explore,calculate,compare` | `respond` | 8 | 1/2と1/3を通分して大小を比較してください |
| cc-open-v1-173 | operations | `build / ops=build,calculate` | `respond` | 7 | 9+4のような繰り上がりのある足し算の手順を説明してください |
| cc-open-v1-174 | operations | `explain / ops=explain,calculate` | `respond` | 7 | 3+5と5+3の結果が等しい理由を説明してください |
| cc-open-v1-175 | operations | `explore / ops=explore,compare` | `respond` | 7 | 12と21の大小を比較してください |
| cc-open-v1-176 | operations | `explore / ops=explore,compare` | `respond` | 7 | 「は」と「が」の使い方の違いを比較してください |
| cc-open-v1-177 | operations | `explore / ops=explore,compare` | `respond` | 7 | データの平均と分散の違いを比較して説明してください |
| cc-open-v1-178 | operations | `explore / ops=explore,compare` | `respond` | 7 | 比例と反比例の違いを比較して説明してください |
| cc-open-v1-179 | operations | `respond / ops=respond,calculate` | `respond` | 7 | 3+5を計算してください |
| cc-open-v1-180 | operations | `respond / ops=respond,calculate` | `respond` | 7 | 4+4の答えはいくつですか |
| cc-open-v1-181 | operations | `respond / ops=respond,calculate` | `respond` | 7 | 5+3はいくつですか |
| cc-open-v1-182 | operations | `respond / ops=respond,calculate` | `respond` | 7 | 56÷8を計算してください |
| cc-open-v1-183 | operations | `respond / ops=respond,calculate` | `respond` | 7 | 6+2を計算してください |
| cc-open-v1-184 | operations | `respond / ops=respond,calculate` | `respond` | 7 | 7+1はいくつになりますか |
| cc-open-v1-185 | operations | `respond / ops=respond,calculate` | `respond` | 7 | 7×6を計算してください |
| cc-open-v1-186 | operations | `respond / ops=respond,calculate` | `respond` | 7 | 9-4を計算してください |
| cc-open-v1-187 | operations | `respond / ops=respond,compare` | `respond` | 7 | Compare the present tense and the past tense in English. |
| cc-open-v1-188 | operations | `respond / ops=respond,calculate` | `respond` | 7 | sin30°+cos60° の値を計算してください |
| cc-open-v1-189 | operations | `respond / ops=respond,calculate` | `respond` | 7 | x^2-5x+6 を因数分解してください |
| cc-open-v1-190 | operations | `respond / ops=respond,calculate` | `respond` | 7 | 二次方程式 x^2+2x+k=0 が実数解を持つkの条件を求めてください |
| cc-open-v1-191 | operations | `respond / ops=respond,calculate` | `respond` | 7 | 二次関数 y=x^2-4x+3 の頂点と最小値を求めてください |
| cc-open-v1-192 | operations | `respond / ops=respond,calculate` | `respond` | 7 | 関数 f(x)=x^3-3x の極値を微分を使って求めてください |
| cc-open-v1-193 | operations | `verify / ops=verify` | `explain` | 7 | @D:\Hybrid_PC_AI\docs\auto_log_review_2026-05-08.md これで読めますか |
| cc-open-v1-194 | operations | `verify / ops=verify` | `explain` | 7 | The proof checks out line by line, yet I still can't see why the theorem is true. |
| cc-open-v1-195 | operations | `verify / ops=verify` | `respond` | 7 | この一群は過去の私のログdataから引っ張ってきたものです！すみません。サンプルとして使えるところを使っていただきたいです！ |
| cc-open-v1-196 | operations | `verify / ops=verify` | `explain` | 7 | これテスト目的なら適正があるモデルならLMStudioのモデルを交換するだけで使えるようになるってことですよね |
| cc-open-v1-197 | operations | `verify / ops=verify` | `respond` | 7 | エージェントへの依頼文ならあります！概ね人間に宛てた文章として書いているので、使えると思われます！ |
| cc-open-v1-198 | operations | `verify / ops=verify` | `respond` | 7 | メモとして！今回でmainLLMがオウム返しが多い事と、保持トークンの少なさ、日本語理解力に問題を感じたのでGemma4に切り替えが妥当かもしれません |
| cc-open-v1-199 | operations | `verify / ops=verify` | `respond` | 7 | 一旦量子化済みggufを使ってollamaが動くか確認してきます |
| cc-open-v1-200 | operations | `verify / ops=verify` | `respond` | 7 | 今確認すると少し容量が4BITでもオーバーする感じなので、新規の12B 8bitの8.9GBモデルを落としてみます |
| cc-open-v1-201 | operations | `verify / ops=verify` | `respond` | 7 | 推奨を採用させてもらいました！ |
| cc-open-v1-202 | operations | `verify / ops=verify` | `explain` | 7 | 確認したいのですが、学習した408の実サイズってどのくらいの大きさになってますか？ |

## Priority C - Source-Intent Probes

Showing first 50 of 357 source-intent probes. Full list is in the JSON.

| id | focus | draft | source intent | score | input |
| --- | --- | --- | --- | ---: | --- |
| cc-open-v1-203 | source_intent_probe | `build / ops=build` | `build` | 2 | @"D:\nichijo_jissou\03_instructions\7day_chat_test_preflight_checklist_2026-06-01.md" test前の |
| cc-open-v1-204 | source_intent_probe | `build / ops=build` | `build` | 2 | Build a step-by-step plan for writing a short English essay. |
| cc-open-v1-205 | source_intent_probe | `build / ops=build` | `build` | 2 | Bを明日の初めのタスクに予定し観測をレポートに記録して区切るでおねがいします！ |
| cc-open-v1-206 | source_intent_probe | `build / ops=build` | `build` | 2 | Create a step-by-step study plan for learning basic algebra. |
| cc-open-v1-207 | source_intent_probe | `build / ops=build` | `build` | 2 | Draft a beginner practice schedule for learning guitar. |
| cc-open-v1-208 | source_intent_probe | `build / ops=build` | `build` | 2 | Draft a step-by-step onboarding checklist for new hires. |
| cc-open-v1-209 | source_intent_probe | `build / ops=build` | `build` | 2 | Draft an ordered checklist for releasing the new feature. |
| cc-open-v1-210 | source_intent_probe | `build / ops=build` | `build` | 2 | Once you've confirmed the budget, draft a weekly meal plan. |
| cc-open-v1-211 | source_intent_probe | `build / ops=build` | `build` | 2 | Prepare concrete deployment steps, validation checks, and rollback tasks. |
| cc-open-v1-212 | source_intent_probe | `build / ops=build` | `build` | 2 | Q1：寂しさの一軸を実装、反応テストを経てから順番に軸を増やすという形でどうでしょう。 Q2：gemma2が自然に受け入れられるsystem message から入れてみたいです！ |
| cc-open-v1-213 | source_intent_probe | `build / ops=build` | `build` | 2 | Turn the selected component design into an ordered implementation plan. |
| cc-open-v1-214 | source_intent_probe | `build / ops=build` | `build` | 2 | `#16 Round 8 の計画`、`下流文書（Roadmap）への波及`、`§8 マーカー付与お願いします` |
| cc-open-v1-215 | source_intent_probe | `build / ops=build` | `build` | 2 | foundation A + 翌日の実行手順 manifest 作成、で wrap-upにしましょう |
| cc-open-v1-216 | source_intent_probe | `build / ops=build` | `build` | 2 | ここまで完成したら予算的に、あとはopus 4.8に投げてロードマップ継続で行けると思うのでそちらに移行します！引継ぎレポートだけ作成お願いします！ |
| cc-open-v1-217 | source_intent_probe | `build / ops=build` | `build` | 2 | このバグを直したいんだけど、修正の手順を組んでほしい |
| cc-open-v1-218 | source_intent_probe | `build / ops=build` | `build` | 2 | この企画を実行に移すための作業リストを作って |
| cc-open-v1-219 | source_intent_probe | `build / ops=build` | `verify` | 2 | この手順で本当に動くのか、抜けがないか見て |
| cc-open-v1-220 | source_intent_probe | `build / ops=build` | `explore` | 2 | この案内文を別の語調で表す候補をいくつか作ってください |
| cc-open-v1-221 | source_intent_probe | `build / ops=build` | `verify` | 2 | この組み立て手順で抜けがないか見て |
| cc-open-v1-222 | source_intent_probe | `build / ops=build` | `build` | 2 | この英単語帳、覚える計画を一週間分作ってほしい |
| cc-open-v1-223 | source_intent_probe | `build / ops=build` | `build` | 2 | この計算問題の解き方を順序立てて整理し、手順書を作ってください |
| cc-open-v1-224 | source_intent_probe | `build / ops=build` | `build` | 2 | この順番でお願いします！ |
| cc-open-v1-225 | source_intent_probe | `build / ops=build` | `build` | 2 | その順番で進めてください！原文に張るテキストsampleを頂きたいです！ |
| cc-open-v1-226 | source_intent_probe | `build / ops=build` | `build` | 2 | わかりやすい文章を書く手順を組み立ててください |
| cc-open-v1-227 | source_intent_probe | `build / ops=build` | `build` | 2 | セットアップ手順を、初心者でも追えるように書き出して |
| cc-open-v1-228 | source_intent_probe | `build / ops=build` | `build` | 2 | ベクトルを使った証明問題の解答方針を組み立ててください |
| cc-open-v1-229 | source_intent_probe | `build / ops=build` | `build` | 2 | 予定が空いてるか見て、空いてたら旅行の行程を組んで |
| cc-open-v1-230 | source_intent_probe | `build / ops=build` | `build` | 2 | 予算案を、項目ごとに分けてたたき台を作ってほしい |
| cc-open-v1-231 | source_intent_probe | `build / ops=build` | `explore` | 2 | 同じ結論へ至る異なる手順を複数考えてください |
| cc-open-v1-232 | source_intent_probe | `build / ops=build` | `build` | 2 | 学習の前にタグ追加をお願いします！タグ無し、時事(政治、経済、ニュース)、生活(料理、天気、その他雑談)、情報系(ミーム、動画、タレント) |
| cc-open-v1-233 | source_intent_probe | `build / ops=build` | `build` | 2 | 家計を見直したいんだけど、まず何から手をつけるか手順にして |
| cc-open-v1-234 | source_intent_probe | `build / ops=build` | `build` | 2 | 庭の家庭菜園、春に向けてやることを順番に並べて |
| cc-open-v1-235 | source_intent_probe | `build / ops=build` | `build` | 2 | 引き出しの整理、どう進めるか段取りにして |
| cc-open-v1-236 | source_intent_probe | `build / ops=build` | `build` | 2 | 引っ越しの荷造り、部屋ごとのタスクに分けて並べて |
| cc-open-v1-237 | source_intent_probe | `build / ops=build` | `build` | 2 | 復旧方法は決まりました。実装、動作確認、切り戻しまでの手順を作ってください。 |
| cc-open-v1-238 | source_intent_probe | `build / ops=build` | `build` | 2 | 採用した保存方式を組み込むための実装手順を作ってください |
| cc-open-v1-239 | source_intent_probe | `build / ops=build` | `build` | 2 | 採用した回復戦略を実装・検証する作業順を組んでください |
| cc-open-v1-240 | source_intent_probe | `build / ops=build` | `build` | 2 | 採用する方法が決まったので実行手順を組み立ててください |
| cc-open-v1-241 | source_intent_probe | `build / ops=build` | `build` | 2 | 採用済みAPI案について、endpointごとの実装タスクを作ってください |
| cc-open-v1-242 | source_intent_probe | `build / ops=build` | `build` | 2 | 採用済みのAPI案を実装するため、作業を順番付きのタスクに分けてください |
| cc-open-v1-243 | source_intent_probe | `build / ops=build` | `build` | 2 | 文章題を式にする手順を作成してください |
| cc-open-v1-244 | source_intent_probe | `build / ops=build` | `build` | 2 | 方程式を解くステップを順番に組み立ててください |
| cc-open-v1-245 | source_intent_probe | `build / ops=build` | `build` | 2 | 方針の説明だけで終わらせず、引き継ぎの作業を順番に並べてください |
| cc-open-v1-246 | source_intent_probe | `build / ops=build` | `build` | 2 | 明日のプレゼン、話す順番を組み立ててくれる？ |
| cc-open-v1-247 | source_intent_probe | `build / ops=build` | `build` | 2 | 残りの2Bを順番に消化しつつ、lora周りは事前テストと実装後の出力testもよろしくお願いします！ |
| cc-open-v1-248 | source_intent_probe | `build / ops=build` | `build` | 2 | 段階アップグレードでお願いします！D.として LLMへのフィードバックを÷2から÷1.5～1.7程度で返しつつ統合は÷2で合わせる。案もよければ候補に |
| cc-open-v1-249 | source_intent_probe | `build / ops=build` | `build` | 2 | 永続化から刺激源拡張の順番でお願いします！ |
| cc-open-v1-250 | source_intent_probe | `build / ops=build` | `build` | 2 | 移行方針は決まっています。停止時間を抑える実施手順を組んでください |
| cc-open-v1-251 | source_intent_probe | `build / ops=build` | `build` | 2 | 筋トレのメニュー、初心者向けに組み立てて |
| cc-open-v1-252 | source_intent_probe | `build / ops=build` | `build` | 2 | 読書習慣をつけたいから、続けられる計画を作って |

## Source Coverage

- batch02_staging: 19
- conversation_accumulation: 32
- harvested_claudelog: 231
- intent_training_corpus: 526


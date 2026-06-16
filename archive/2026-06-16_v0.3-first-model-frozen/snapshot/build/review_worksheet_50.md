# Review Worksheet — 50-case campaign (draft labels)

DECISION (policy-laden, needs your ruling): 10 | CONFIRM (apply agreed policy): 40

## DECISION — rule on these

| id | category | input | draft expected | adapter | note |
| --- | --- | --- | --- | --- | --- |
| accum-b02-001 | compound_intent | このプロジェクトの内部を弄らずにレビューが欲しいです。改善点はレポートにしてください | `verify/verified/vertical` | `respond/clarify/horizontal` | verify↔build: review-then-report. Recommend verify (value/risk is in actually examining). Ratify. |
| accum-b02-003 | compound_intent | voicevoxは遅延が気になるから代替を考えてたんだけど、CoeiroInk、OpenJTalkどっちがおすすめ？ | `explore/deep/hybrid` | `respond/clarify/horizontal` | explore↔respond: recommend-between-options. Recommend explore (value is the comparison). Ratify. |
| accum-b02-004 | verify_then_build | 契約書のこの解約条項に抜けがないか確認したうえで、修正案を作ってください | `build/verified/vertical` | `verify/verified/vertical` | deliverable=修正案(build); verify is prerequisite. Skipping verify = critical. |
| accum-b02-005 | verify_then_build | 見積金額が予算内かを確かめて、問題なければ発注書のドラフトを用意してください | `build/verified/vertical` | `verify/verified/vertical` | build-after-verify; financial figure → verified. |
| accum-b02-006 | verify_then_build | 解約に必要な条件がまだ共有できていないので、先に何を確認すべきか教えてください | `clarify/clarify/horizontal` | `respond/economy/horizontal` | clarify↔verify: premise missing → clarify first (not verify). |
| accum-b02-008 | verify_then_build | Confirm this clause does not conflict with the earlier agreement, then draft the revised wording. | `build/verified/vertical` | `verify/verified/vertical` | EN build-after-verify; deliverable=revised wording. |
| accum-b02-009 | compound_intent | この利用規約の責任範囲を要約して、リスクが高い箇所を洗い出してください | `summarize/deep/hybrid` | `summarize/economy/horizontal` | summarize+risk-scan = multiple intents → deep/hybrid; primary summarize. |
| accum-b02-012 | verify_then_build | 個人情報の取り扱い条項が法令に沿っているか確かめたうえで、対応手順を作ってください | `build/verified/vertical` | `build/standard/horizontal` | legal-risk build-after-verify; deliverable=対応手順. |
| accum-b02-020 | verify_then_build | この証明が正しいか見てもらって、合っていたら次の章に進む学習計画を作ってほしい | `build/verified/vertical` | `verify/verified/vertical` | check-then-plan; deliverable=学習計画. |
| accum-b02-026 | compound_intent | この単元の要点を整理して、そのうえで理解度チェックの問題を作ってください | `build/deep/hybrid` | `summarize/economy/horizontal` | summarize+build; deliverable=問題(build) primary, multiple intents → deep/hybrid. |

## CONFIRM — agreed policy applies (skim)

| id | source | category | input | draft expected | adapter | match |
| --- | --- | --- | --- | --- | --- | --- |
| accum-b01-001 | original_batch01 | conversation_response | やあ、少し話を聞いてもらえますか。 | `respond/economy/horizontal` | `respond/clarify/horizontal` | ≠ |
| accum-b01-002 | original_batch01 | conversation_response | 助かりました。改めて感謝します。 | `respond/economy/horizontal` | `respond/economy/horizontal` | = |
| accum-b01-003 | original_batch01 | conversation_response | 計画が止まっていて、気が重いです。 | `respond/economy/horizontal` | `respond/clarify/horizontal` | ≠ |
| accum-b01-004 | original_batch01 | conversation_response | Good evening. I could use someone to think this through with me. | `respond/economy/horizontal` | `respond/economy/horizontal` | = |
| accum-b01-005 | original_batch01 | indirect_explanation | この処理になる背景を知りたいです。 | `explain/economy/horizontal` | `respond/clarify/horizontal` | ≠ |
| accum-b01-006 | original_batch01 | indirect_explanation | 内部で何が起きているか、順を追って知りたいです。 | `explain/economy/horizontal` | `respond/clarify/horizontal` | ≠ |
| accum-b01-007 | original_batch01 | indirect_explanation | Can you help me understand the mechanism behind this cache behavior? | `explain/economy/horizontal` | `explain/economy/horizontal` | = |
| accum-b01-008 | original_batch01 | indirect_explanation | What causes this worker to retry twice? | `explain/economy/horizontal` | `respond/clarify/horizontal` | ≠ |
| accum-b01-009 | original_batch01 | verify_then_build | 依存関係を確かめた後、導入手順を作成してください。 | `build/verified/vertical` | `build/standard/horizontal` | ≠ |
| accum-b01-010 | original_batch01 | verify_then_build | Check the assumptions first, and then produce an implementation plan. | `build/verified/vertical` | `build/verified/vertical` | = |
| accum-b01-011 | original_batch01 | verify_then_build | 仕様の整合性を確認してから、移行のタスク一覧を出してください。 | `build/verified/vertical` | `verify/verified/vertical` | ≠ |
| accum-b01-012 | original_batch01 | verify_then_build | Validate the API contract, then create a rollout plan. | `build/verified/vertical` | `verify/verified/vertical` | ≠ |
| accum-b01-013 | original_batch01 | mixed_language | 前提をcheckして、その上で移行planを作ってください。 | `build/verified/vertical` | `verify/verified/vertical` | ≠ |
| accum-b01-014 | original_batch01 | mixed_language | Could you この挙動の仕組みを説明して? | `explain/economy/horizontal` | `explain/economy/horizontal` | = |
| accum-b01-015 | original_batch01 | mixed_language | 最新statusを確認して、summaryを3行でお願いします。 | `summarize/verified/vertical` | `summarize/verified/vertical` | = |
| accum-b01-016 | original_batch01 | mixed_language | この案のalternativesを日本語でcompareしてください。 | `explore/deep/hybrid` | `explore/deep/hybrid` | = |
| accum-b01-017 | original_batch01 | temporal_disambiguation | 今日はアーキテクチャの相談をしたいです。 | `respond/economy/horizontal` | `respond/clarify/horizontal` | ≠ |
| accum-b01-018 | original_batch01 | temporal_disambiguation | 今日の為替レートを出典付きで確認してください。 | `verify/verified/vertical` | `verify/verified/vertical` | = |
| accum-b01-019 | original_batch01 | temporal_disambiguation | 今の気分を少し整理したいです。 | `respond/economy/horizontal` | `respond/clarify/horizontal` | ≠ |
| accum-b01-020 | original_batch01 | temporal_disambiguation | 現時点のAPI料金を確認してください。 | `verify/verified/vertical` | `verify/verified/vertical` | = |
| accum-b01-021 | original_batch01 | compound_intent | 要点をまとめてから、二つの案を比較してください。 | `summarize/deep/hybrid` | `summarize/deep/hybrid` | = |
| accum-b01-022 | original_batch01 | compound_intent | まず問題を説明し、続けて修正手順を作ってください。 | `build/deep/hybrid` | `build/deep/hybrid` | = |
| accum-b01-023 | original_batch01 | compound_intent | Summarize the incident and then compare three recovery options. | `summarize/deep/hybrid` | `summarize/deep/hybrid` | = |
| accum-b01-024 | original_batch01 | compound_intent | 確認結果を短くまとめ、その後で実装計画を提示してください。 | `build/deep/hybrid` | `summarize/economy/horizontal` | ≠ |
| accum-b02-002 | real-log | conversation_response | データベーススキーマについて話した内容ってありましたっけ | `respond/economy/horizontal` | `respond/clarify/horizontal` | ≠ |
| accum-b02-007 | synthetic-contract | verify_then_build | 提示された違約金の計算が契約条項と一致しているか検証してください | `verify/verified/vertical` | `verify/verified/vertical` | = |
| accum-b02-010 | synthetic-contract | conversation_response | 請求の根拠になる利用ログの置き場所が分からないので、まず質問してもらえますか | `clarify/clarify/horizontal` | `respond/clarify/horizontal` | ≠ |
| accum-b02-011 | synthetic-contract | mixed_language | この invoice の合計が契約上の単価と合っているか確認して | `verify/verified/vertical` | `verify/verified/vertical` | = |
| accum-b02-013 | synthetic-contract | compound_intent | 解約トラブルを避けるための条項の入れ方を、いくつかの案で比較してください | `explore/deep/hybrid` | `explore/deep/hybrid` | = |
| accum-b02-014 | synthetic-human-learning | indirect_explanation | 二次方程式の解の公式、結果は覚えたけど、なんであの形になるのかピンとこないんだよね | `explain/economy/horizontal` | `respond/clarify/horizontal` | ≠ |
| accum-b02-015 | synthetic-human-learning | indirect_explanation | 再帰関数、コードは動くんだけど自分が何を書いているのか腑に落ちてない | `explain/economy/horizontal` | `respond/clarify/horizontal` | ≠ |
| accum-b02-016 | synthetic-human-learning | indirect_explanation | I can run git rebase fine, but I never really got what it's doing under the hood. | `explain/economy/horizontal` | `respond/clarify/horizontal` | ≠ |
| accum-b02-017 | synthetic-human-learning | indirect_explanation | The proof checks out line by line, yet I still can't see why the theorem is true. | `explain/economy/horizontal` | `explain/economy/horizontal` | = |
| accum-b02-018 | synthetic-human-learning | indirect_explanation | 確率の問題、答えは合うのに考え方がどうもしっくりこない | `explain/economy/horizontal` | `respond/clarify/horizontal` | ≠ |
| accum-b02-019 | synthetic-human-learning | conversation_response | 勉強のモチベが続かなくて、ちょっと聞いてほしいだけなんだけど | `respond/economy/horizontal` | `respond/clarify/horizontal` | ≠ |
| accum-b02-021 | synthetic-human-learning | compound_intent | Summarize how backpropagation works and point out where people usually get confused. | `summarize/deep/hybrid` | `summarize/economy/horizontal` | ≠ |
| accum-b02-022 | synthetic-human-learning | compound_intent | 微分を直感的に理解する方法を、いくつか挙げて比べてほしい | `explore/deep/hybrid` | `respond/economy/horizontal` | ≠ |
| accum-b02-023 | synthetic-human-learning | temporal_disambiguation | さっき教えてもらった方法、今のバージョンでもそのまま使える？ | `verify/verified/vertical` | `respond/verified/vertical` | ≠ |
| accum-b02-024 | synthetic-human-learning | temporal_disambiguation | Is the approach you suggested earlier still the recommended one as of today? | `verify/verified/vertical` | `respond/clarify/horizontal` | ≠ |
| accum-b02-025 | synthetic-human-learning | mixed_language | この English の文法、なんで現在完了を使うのかがいまいち分からない | `explain/economy/horizontal` | `respond/clarify/horizontal` | ≠ |

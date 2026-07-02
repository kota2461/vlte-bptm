# Route CAM 初期エントリ起票ワークシート v1 (2026-07-02)

Status: **REVIEWED 2026-07-02 — 15件承認・2件却下 (explore_03/explore_04: 文脈依存の断片)。承認分はsemantic_routing/config/route_cam_v1.jsonで稼働中。**
候補データ: build/route_cam_entry_candidates_v1.json (staged、sweep全数値入り)

## 起票元と規律

- 起票元: 承認済み実データ739件のうち、markers不発 + gate(0.20)直下で
  economyへ落ちた22件から、under-routingに該当する17件
  (verify 2 / explore 6 / clarify 5 / build 4)。sealed資産は不使用。
- care設計: SimHash(32bit) + language(2) + information_state(4) + risk(3) = 41bit。
  intent bits(0-6)は既定ガードにより除外。
- d決定則: min(4, nearest_unsafe - 3)。全コーパスでの最近傍危険距離から機械的に導出。

## 評価結果 (17エントリ全乗せ end-to-end)

- evidence自己ヒット: **17/17** (全て目標クラスへ昇格、reason_codes/trace記録確認)
- shadow: 非evidence **757入力でplan変化 0件** (junk/dropped 35件含む)
- 非evidenceへのCAMヒット1件 (build_01近傍の別build文) は baseline≥standard のため
  max-joinでplan不変 = 昇格のみ保証の実証
- **正直な限界**: nearest_unsafe(5-10) < nearest_good(9-15) のため、言い換え回収に
  届くdは存在しない。本エントリ群の効果は「既知失敗の同型再来 + 微小ゆらぎの救済」
  に限定される。言い換え一般化は主張しない (短文32bit SimHashの既知の限界)。

## エントリ一覧 (承認欄にチェックで採用)

| entry | evidence (先頭38字) | margin | 昇格 | d | 最近傍危険 | 備考 | 承認 |
|---|---|---|---|---|---|---|---|
| verify_01 | 実装が要件を満たすかテストしてください | 0.182 | economy→verified | 4 | 8 |  | [x] |
| verify_02 | ログ確認お願いします！問題なければまた明日よろしくお願いします！ | 0.094 | economy→verified | 4 | 7 |  | [x] |
| explore_01 | 障害対策を一つに絞らず、異なる回復戦略を検討してください | 0.185 | economy→deep | 4 | 8 |  | [x] |
| explore_02 | まずは現状でbackup、より、アーカイブ化のほうがいい？をして実働参照用と | 0.172 | economy→deep | 4 | 7 |  | [x] |
| explore_03 | こちら使えますか！ | 0.170 | economy→deep | 4 | 10 |  | 却下 |
| explore_04 | Aはコストがかかりそうなので、B、Cを片付けてから行く方向でどうでしょう | 0.159 | economy→deep | 4 | 8 | 文脈依存の断片 — 単独でdeepは過剰の可能性 | 却下 |
| explore_05 | 三角関数の問題の解き方を複数の方針で検討してください | 0.156 | economy→deep | 4 | 7 |  | [x] |
| explore_06 | 他の解き方はありますか | 0.103 | economy→deep | 4 | 7 |  | [x] |
| clarify_01 | 残エラーの処理って出来ますか？それとも進めてから処理した方が良い？ | 0.167 | economy→clarify | 4 | 7 |  | [x] |
| clarify_02 | Estimate the runtime, but the input si | 0.081 | economy→clarify | 4 | 8 |  | [x] |
| clarify_03 | 数に何かを足すといくつになりますか | 0.055 | economy→clarify | 4 | 7 |  | [x] |
| clarify_04 | こちらの判断をおねがいします！ | 0.046 | economy→clarify | 2 | 5 |  | [x] |
| clarify_05 | LMStudioのトークン量を変更できるのでサイズ10G程度で増やしました。 | 0.024 | economy→clarify | 4 | 7 |  | [x] |
| build_01 | 時間空けて五時間制限もfullで使えるので一気に進めてください！ | 0.167 | economy→standard | 4 | 8 | セッション文脈前提の指示文 | [x] |
| build_02 | 後は②人間学習・③契約系で合成でおねがいします！その部分の学習も欲しいので！ | 0.155 | economy→standard | 4 | 9 | セッション文脈前提の指示文 | [x] |
| build_03 | 確率の問題を解く計画を立ててください | 0.152 | economy→standard | 4 | 9 |  | [x] |
| build_04 | 保守閾値0.15で進めて | 0.120 | economy→standard | 4 | 8 |  | [x] |

## 採用手順 (承認後)

1. 承認済みエントリのみ semantic_routing/config/route_cam_v1.json へ転記
2. evidence自己ヒットを固定する回帰テストを tests/test_route_cam.py に追加
3. 345テスト + 採用前後A/B (build/bit_systems_adoption_ab_report_v1.json と同手順) を再実行
4. 期待される差分: evidence 17件のみ economy→目標クラス、他0件

## 採用結果 (2026-07-02)

- 15エントリを出荷configへ転記、strict parserで検証済み
- フルスイート: 346 passed (採用回帰テスト test_shipped_entries_escalate_their_evidence 追加)
- 採用差分スキャン (稼働store vs 空store、774入力): **plan変化 = 承認evidence 15件ちょうど**、
  全て economy → 目標クラス。却下2件・junk 35件・その他757件は不変
- 既知のgate直下失敗17件のうち15件が再来時に正しいクラスへ昇格する状態になった

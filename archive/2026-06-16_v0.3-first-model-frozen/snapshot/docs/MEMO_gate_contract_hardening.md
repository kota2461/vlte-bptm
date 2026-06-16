# メモ: ゲート契約の固定化(v0.2.2候補) — 明日の作業用

記録日: 2026-06-11(ユーザー提供メモ、原文のまま保存)
位置づけ: v0.2.1デプロイゲート実装への強化案。実装前にこの内容を
`PATTERN_ROUTER_v0_2_design.md`へ正式契約として追記してから着手する。

---

必要なのは単なる「件数固定」より、ゲート契約の固定です。

## 1. ゲート固定ルール

- fixtureのversion・内容・SHA-256を固定
- 既存anchorは原則削除不可
- 追加は可能、削除・ラベル変更は新versionと理由・人間承認が必須
- candidate、fixture、学習DB snapshotのhashを記録
- `raw_route`と`effective_route`の両方を検査

## 2. 昇格ルール

- foundation/regressionは原則100%
- grouped validationやsealed testが最低基準以上
- 現行モデルより重要指標を悪化させない
- candidate hashがgate実行時から不変
- 明示的な人間承認後、atomicに置換
- 旧モデルをrollback用に保存

## 3. 降格・rollbackルール

- 本番監視で重大anchor違反
- 精度・coverage・安全指標が規定値を下回る
- モデル、データ、fixtureの整合性違反
- 即時に直前の承認済みモデルへ戻す
- 問題モデルは削除せず`rejected/quarantined`として保存

## 4. ゲート件数

- foundation 58件を「58件固定」とするより、最低58件・削除禁止が適切
- 新しい失敗例は追加し、件数は単調増加
- Route別・言語別・境界別の最低件数も設定
- sealed testは固定し、調整に使ったら新versionへ交代

## まとめ

```text
Gate      = 固定された契約
Promotion = 契約通過 + 改善確認 + 人間承認
Rollback  = 契約違反時に直前モデルへ復帰
```

という三層が必要。件数だけ固定すると、似た簡単な例を増やして
形式的に通せてしまう。

---

## 明日のセッション順序(参考)

1. pending 10件(英語非respond)をUIでレビュー
2. このメモをv0.2設計へ正式追記 → ゲート強化を実装
   (fixture SHA固定・hash記録・effective_route検査・旧モデル自動保存・
   anchor単調増加ルール)
3. `train` → `promote` → 英語スライス再測定

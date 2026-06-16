# 引継ぎレポート (2026-06-11 / セッション3)

## 完了事項

- 較正ビン間ギャップを修正し、全confidenceを必ず較正ビンへ割り当て
- clarify fallback評価をcoverage / selective accuracy / abstentionへ分離
- inhibition設定で未知Unit、boolean、非有限値、自己抑制を拒否
- Route境界カリキュラム24件をpending投入、明示承認、明示再学習
- Pattern DBを142件から166件へ更新
- 25件の固定回帰fixtureと評価器を追加
- 62 tests passed

## 最終値

- routes: build 13 / clarify 19 / explore 31 / respond 78 /
  summarize 9 / verify 16
- measurement validation accuracy: 0.866667
- repeated CV accuracy: 0.768675
- threshold: 0.195214
- regression raw: 25/25
- regression effective label: 23/25
- regression coverage: 0.92
- regression selective accuracy: 1.00

## 重要な解釈

固定25件は改善中に参照したため、独立final testではなく回帰fixture。
fallbackは正解Routeへの訂正ではなく安全な棄権であり、
`effective_label_accuracy`を安全性の成功率として扱わない。

## 次版

- Pattern Router v0.2: grouped split、sealed calibration/final test、
  近似重複検査、ECE/Brier、人間によるfallback評価
- Pattern Router v0.3: OOD、margin比較、複数モデル合議
- Core v1.1: channel schema、action/order schema、正式Unit一覧

詳細は`docs/PATTERN_ROUTER_v0_1_1_spec.md`、
`docs/PATTERN_ROUTER_v0_2_design.md`、
`docs/VLTE_BPTM_roadmap.md`を参照。

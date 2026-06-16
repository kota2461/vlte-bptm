# Pattern Boundary v2 Untrained Accuracy

評価日: 2026-06-11

## 評価条件

`boundary_curriculum_v2`の48件を、現行モデルが一度も学習していない状態で評価した。
全候補は`pending`であり、人間承認前なので、以下は暫定ラベルに対するpre-training
基準値である。semanticな回答本文の品質評価ではなく、Route分類精度だけを測る。

- pending candidates: 48
- approved patterns: 166
- v2とapproved patternsの完全一致: 0
- model SHA-256:
  `532D075B794D804B3E3CE609E4809E6275E293020911A38FAFB99AB848B845E9`
- 再学習: 未実施

## 結果

| System | Raw accuracy | Macro-F1 | Balanced accuracy | 対照ペア両方正解 |
| --- | ---: | ---: | ---: | ---: |
| Pattern Router | 27/48 = 0.5625 | 0.5213 | 0.5333 | 8/24 = 0.3333 |
| Core Router | 22/48 = 0.4583 | 0.5118 | 0.5000 | 2/24 = 0.0833 |

Pattern Routerの95% Wilson区間は`0.4228-0.6930`、Core Routerは
`0.3258-0.5971`。標本数が小さく区間も重なるため、両者の優劣を確定する結果ではない。

既存25件回帰fixtureはPattern Router raw `25/25`を維持した。ただし11件がapproved
patternsと完全一致し、改善時に参照したfixtureでもあるため、一般化精度ではない。

## Pattern Router内訳

### 境界別

| Boundary | Accuracy | Pair both correct |
| --- | ---: | ---: |
| `explore_respond` | 9/12 = 0.7500 | 3/6 |
| `explore_build` | 8/12 = 0.6667 | 4/6 |
| `build_respond` | 5/12 = 0.4167 | 0/6 |
| `clarify_verify` | 5/12 = 0.4167 | 1/6 |

### Route別recall

| Route | Recall |
| --- | ---: |
| `explore` | 9/12 = 0.7500 |
| `respond` | 9/12 = 0.7500 |
| `clarify` | 4/6 = 0.6667 |
| `build` | 4/12 = 0.3333 |
| `verify` | 1/6 = 0.1667 |

主な誤分類は`build -> respond`が5件、`verify -> respond`が3件、
`verify -> clarify`が2件。`build`と`verify`の意図分離が不足している。

### 言語別

| Language | Accuracy |
| --- | ---: |
| 日本語 | 23/32 = 0.7188 |
| 英語 | 4/16 = 0.2500 |

英語16件の予測は`respond`が14件、`explore`が2件で、他Routeを一度も出していない。
承認済み英語データ22件のうち`respond`が15件で、非respondは7件しかないため、
英語Route識別のデータ不足とクラス偏りが強く現れている。

### 難度別

- `simple`: 16/26 = 0.6154
- `compound`: 11/22 = 0.5000

## Confidenceとfallback

- raw accuracy: 27/48 = 0.5625
- effective route accuracy: 25/48 = 0.5208
- abstention: 8/48 = 0.1667
- coverage: 40/48 = 0.8333
- selective accuracy: 24/40 = 0.6000

fallbackは誤った`respond`を正しい`clarify`へ1件修正した一方、正しい`build`を
3件`clarify`へ変更した。現行calibration thresholdはこの新規分布で精度順位を
十分に表現できず、exact Route accuracyを低下させた。これは安全性評価とは別であり、
`clarify`への退避が実運用で安全だったかは人間評価が必要。

## 判断

1. 新規境界への一般化は未完成で、56.25%を現行の実力値として扱う。
2. 優先学習対象は英語の非respond、`build/respond`、`clarify/verify`。
3. 48件は承認・学習後に評価セットとして再利用しない。
4. 人間レビュー後、`contrast_group`単位で学習分割する。
5. 学習前に別系統のsealed境界セットを作り、pre/post比較へ使う。
6. calibrationは新しいgrouped validation setで再推定し、Route精度と安全性を分ける。

機械可読の詳細結果は`build/boundary_v2_untrained_eval.json`に保存した。

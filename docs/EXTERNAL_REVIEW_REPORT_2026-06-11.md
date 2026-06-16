# VLTE-BPTM / Pattern Router External Review Report

作成日: 2026-06-11  
目的: 現状を第三者AI・人間レビューへ共有し、次の学習と評価設計について意見を得る。

## 1. 要約

VLTE-BPTM Coreはv1.6 alphaまで実装済みで、Pattern Routerは人間承認済み166件を
学習した独立モデルとして存在する。両者はまだ統合していない。

現行Pattern Routerは既存25件回帰fixtureではraw `25/25`だが、fixtureの一部は
学習データと一致し、改善時にも参照しているため、一般化精度の証明には使えない。
そこで、Route仕様から新規作成した48件・24対照ペアを未学習のまま評価した。

結果はPattern Router `27/48 = 56.25%`、Core Router `22/48 = 45.83%`。
Pattern Routerは日本語`71.88%`に対して英語`25.00%`、`build` recall `33.33%`、
`verify` recall `16.67%`だった。現状の主問題は、単純な総量不足だけではなく、
言語・Route別の偏り、境界表現の不足、文字n-gram線形分類器の構造的限界、
非grouped評価、較正分布のずれが重なっていると判断している。

新規48件は全件`pending`で、承認・再学習はまだ行っていない。

## 2. システム構成

### VLTE-BPTM Core

- version: `1.6` alpha
- 64bit Thought Code
- Horizontal Mesh
- optional Vertical Stack
- optional Hybrid Stack-Mesh
- external runtime executor境界
- independent study schema、統計評価、policy draft
- 現在の既定modeはHorizontal

Coreはルール・Unit選択に基づく経路であり、Pattern Routerとは別系統である。

### Pattern Router

- model: hashed character n-gram + word tokenの線形averaged perceptron
- labels:
  - `respond`
  - `clarify`
  - `build`
  - `verify`
  - `summarize`
  - `explore`
- confidence: softmax最大値
- calibration: repeated stratified k-fold由来のreliability table
- low-confidence時: `clarify` fallback
- 学習対象: 人間承認済みPattern DBエントリのみ
- 自動承認、自動学習、pseudo-labeling: なし

## 3. 現行データ

Pattern DB:

| Status | Count |
| --- | ---: |
| approved | 166 |
| pending | 48 |
| rejected | 6 |
| total candidates | 220 |

承認済みRoute分布:

| Route | Count |
| --- | ---: |
| `respond` | 78 |
| `explore` | 31 |
| `clarify` | 19 |
| `verify` | 16 |
| `build` | 13 |
| `summarize` | 9 |

承認済み英語データは22件で、そのうち`respond`が15件、非`respond`が7件。
Route・言語の両方で不均衡がある。

## 4. 新規境界カリキュラム

Round 1:

- 48 prompts
- 24 contrast groups
- 日本語32件、英語16件
- `simple` 26件、`compound` 22件
- 4境界、各12件

対象:

- `explore` vs `respond`
- `build` vs `respond`
- `clarify` vs `verify`
- `explore` vs `build`

各`contrast_group`は話題、言語、難度を揃え、Route意図だけを変えた2件で構成する。

### データ由来

- AI支援によるRoute仕様起点のsynthetic prompt
- teacher modelの回答、logit、確率分布、hidden reasoningは不使用
- 外部文章のコピーは不使用
- `ai_assisted_authoring=true`
- `approval_required=true`

一般的なteacher-student model distillationではないと整理している。ただし、
AI支援作例である事実は明記しており、法的判断や各サービスの利用規約判断を
代替するものではない。

## 5. 未学習精度

新規48件は現行モデルとapproved patternsに完全一致がなく、全件pending。
モデルを更新せずpre-training基準値として評価した。

| System | Raw accuracy | 95% Wilson interval | Macro-F1 | Balanced accuracy | Pair both correct |
| --- | ---: | ---: | ---: | ---: | ---: |
| Pattern Router | 27/48 = 0.5625 | 0.4228-0.6930 | 0.5213 | 0.5333 | 8/24 |
| Core Router | 22/48 = 0.4583 | 0.3258-0.5971 | 0.5118 | 0.5000 | 2/24 |

標本数が小さく区間も重なるため、両システムの優劣を確定する結果ではない。

### Pattern Router境界別

| Boundary | Accuracy | Pair both correct |
| --- | ---: | ---: |
| `explore_respond` | 9/12 = 0.7500 | 3/6 |
| `explore_build` | 8/12 = 0.6667 | 4/6 |
| `build_respond` | 5/12 = 0.4167 | 0/6 |
| `clarify_verify` | 5/12 = 0.4167 | 1/6 |

### Pattern Router Route別recall

| Route | Recall |
| --- | ---: |
| `explore` | 9/12 = 0.7500 |
| `respond` | 9/12 = 0.7500 |
| `clarify` | 4/6 = 0.6667 |
| `build` | 4/12 = 0.3333 |
| `verify` | 1/6 = 0.1667 |

主な誤り:

- `build -> respond`: 5件
- `verify -> respond`: 3件
- `verify -> clarify`: 2件
- `respond -> explore`: 3件
- `explore -> respond`: 3件

### 言語・難度別

| Slice | Accuracy |
| --- | ---: |
| 日本語 | 23/32 = 0.7188 |
| 英語 | 4/16 = 0.2500 |
| simple | 16/26 = 0.6154 |
| compound | 11/22 = 0.5000 |

英語16件の予測は`respond` 14件、`explore` 2件で、`build`、`clarify`、
`verify`を一度も出していない。

## 6. Confidence / Fallback

新規48件でのPattern Router:

- raw accuracy: `27/48 = 0.5625`
- effective route accuracy: `25/48 = 0.5208`
- abstention rate: `8/48 = 0.1667`
- coverage: `40/48 = 0.8333`
- selective accuracy: `24/40 = 0.6000`

fallbackは誤った`respond`を正しい`clarify`へ1件修正した一方、正しい`build`を
3件`clarify`へ変更した。現行thresholdは既存データ分布向けで、新規境界分布では
exact Route accuracyを下げた。`clarify`退避の安全性はRoute正解とは別に、
人間評価またはコスト行列で測る必要がある。

## 7. 既存評価の注意点

- Pattern Router既存25件: raw `25/25`
- 25件中11件はapproved patternsと完全一致
- 既存measurement holdout: `26/30 = 0.8667`
- holdoutはtemplate/source group単位に分割されていない
- repeated CV: `0.7687`
- Core固定8件: `8/8`
- Coreを既存Router 25件へ適用: `9/25`
- Pattern RouterをCore 8件へ適用: `5/8`
- semantic回答本文の独立評価: `0件`

したがって、production response accuracyは確立していない。

## 8. 現時点の解釈

確認できたこと:

1. 新規境界へは50%前後の一般化に留まる。
2. 英語非`respond`と`build`、`verify`が明確な弱点。
3. 対照ペア両方正解率が低く、話題ではなく意図差を安定して捉えられていない。
4. fallback thresholdは分布外の新規境界で信頼できない。
5. Pattern RouterとCoreは異なる弱点を持ち、現時点で単純統合する根拠はない。

まだ確認できていないこと:

1. 48件の人間レビュー後ラベルがすべて妥当か。
2. 境界データを学習した後、別表現へ一般化するか。
3. grouped / sealed評価で改善が再現するか。
4. Route改善が回答本文の品質改善につながるか。
5. `clarify` fallbackが実運用の損失を減らすか。

## 9. 提案する次の順序

1. 48件を人間レビューし、曖昧例は修正またはrejectする。
2. 学習前に、別系統のsealed境界評価セットを作る。
3. `contrast_group`、template、sourceを保持するgrouped splitを実装する。
4. Round 1を承認し、明示的に再学習する。
5. sealed setでpre/post、macro-F1、balanced accuracy、pair accuracyを比較する。
6. 英語非`respond`、`build/respond`、`clarify/verify`を優先してRound 2を作る。
7. 新しいgrouped validation setでcalibrationを再推定する。
8. Route精度とsemantic回答品質を別評価として維持する。

Wikipediaは概念・用語・事実関係の学習候補には利用できるが、現在の主問題である
Route境界データを直接解決しにくいため、上記の境界評価を先に行う判断としている。

## 10. レビュー依頼事項

Claude側には特に次を確認してほしい。

1. 48件・24対照ペアというRound 1設計に、ラベルリークや過度に明示的な誘導がないか。
2. `build/respond`、`clarify/verify`のRoute定義自体に曖昧さがないか。
3. AI支援synthetic promptを非蒸留とする整理に不足がないか。
4. 承認前に追加すべきprovenance・license・review metadataがあるか。
5. grouped splitのgroup keyを`contrast_group + template + source`で設計すべきか。
6. 48件を学習へ入れる前に必要なsealed setの件数と配分はどの程度か。
7. 英語25%に対して、データ追加とモデル構造変更のどちらを先に行うべきか。
8. 現行の文字n-gram線形モデルを維持する合理性と、変更判断の基準は何か。
9. confidence fallbackを全Route共通閾値から境界別・Route別へ変えるべきか。
10. CoreとPattern Routerの統合判断に追加で必要な証拠は何か。

## 11. 再現情報

- Python tests: `176 passed`
- DB `PRAGMA quick_check`: `ok`
- model SHA-256:
  `532D075B794D804B3E3CE609E4809E6275E293020911A38FAFB99AB848B845E9`
- latest training sample count: `166`
- 新規48件投入後もモデルは未更新

主要ファイル:

- `pattern_learning/boundary_curriculum_v2.py`
- `docs/PATTERN_BOUNDARY_CURRICULUM_v2.md`
- `docs/PATTERN_BOUNDARY_V2_UNTRAINED_ACCURACY.md`
- `build/boundary_v2_untrained_eval.json`
- `docs/VLTE_BPTM_v1_6_accuracy_audit.md`
- `docs/VLTE_BPTM_roadmap.md`

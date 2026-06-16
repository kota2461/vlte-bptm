# Pattern Language Benchmark v1

更新日: 2026-06-13

schema version: `pattern-language-benchmark.v1`

fixture: `tests/fixtures/pattern_language_benchmark_v1.json`

baseline report: `build/plm_baseline_v0_1_report.json`

review log: `data/plm_benchmark_reviews_v1.json`

## 目的

Pattern Language Model adapterが`semantic-packet.v1`へ変換する能力を、
intentだけでなく情報状態、制約、risk、operation、evidence offsetに分解して測る。

## 構成

- 84件
- 日本語42件、英語42件
- 7 intentを各12件
- train 28件
- validation 28件
- sealed 28件
- 可視分割に`multiple_intents`正例を各1件

各caseは入力本文、期待Semantic Packet、根拠offsetを持つ。入力本文は全splitで
完全一致重複を禁止し、contrast groupはsplitをまたがない。

## 現在の状態

`review_status`は`human_reviewed`である。2026-06-13に84件すべてが
人間承認され、ラベル修正0件、却下0件で確定した。AI支援で仕様から作成したため、
可視56件に対するbaseline v0.1の全指標1.0は契約適合の確認であり、
未知入力への品質保証ではない。

v1のsealed 28件はbaseline評価には使用していないが、人間レビューで開封されたため
`consumed`である。後継は`pattern_language_sealed_v2.json`で、未測定・未reviewの
active fixtureとして分離した。

## Existing UI Review

既存Pattern Lab UIの`PLM Benchmark`モードからreviewできる。

```powershell
python -m pattern_learning.cli serve
```

ブラウザで`http://127.0.0.1:8765`を開き、右上のmodeを
`PLM Benchmark`へ切り替える。

- default一覧はtrain + validationの未評価case
- v1の`sealed`はreview済み・consumed
- Expected Semantic PacketをJSONとして修正可能
- 承認内容は専用review logへ保存
- Pattern DBとRouter学習資産には追加しない
- schema違反、offset違反、未知fieldは保存前に拒否

## 評価指標

- valid packet rate
- intent accuracy / macro-F1 / intent別F1
- critical signal recall
- constraint exact match
- operation exact match
- risk exact match
- evidence offset validity

critical signalは次の4つである。

- `missing_required_information`
- `contains_unverified_claims`
- `requires_current_information`
- `multiple_intents`

## 分離規則

- 通常評価はtrainとvalidationだけを選ぶ
- `cases_for_splits()`のdefaultはsealedを除外する
- baseline reportには`sealed_evaluated: false`を記録する
- 現行approved pattern DBとactive sealed v2との完全一致重複を0件に保つ
- sealedを測定した後は、結果を見て調整する前に次版へrotationする

## 次の判定

human-reviewed train / validationを使ってLegacy Adapterと小型LLM Semantic
Adapterの比較へ進む。active sealed v2は比較実装や調整には使用せず、候補を固定した
後の一回測定まで閉じたまま維持する。

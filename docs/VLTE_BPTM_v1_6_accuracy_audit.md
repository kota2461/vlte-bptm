# VLTE-BPTM v1.6 Current Response Accuracy Audit

調査日: 2026-06-11

## 結論

現時点でproductionの「応答正答率」は確立していない。

測定できているのは主にroute選択精度であり、semanticな回答本文の正しさを
独立評価したデータは0件である。固定fixture上の100%を一般的な応答精度として
扱ってはならない。

## 現行経路

実際の`thought_core.pipeline.process()`はCore Selector / Meshを使用する。
Pattern RouterモデルはPattern Lab側にあり、現行Core経路へ統合されていない。

この二つは異なるデータで調整されており、交差評価で性能差が現れる。

## Route Accuracy

| System / Dataset | Result | 95% Wilson interval | Interpretation |
| --- | ---: | ---: | --- |
| Core / Core代表fixture | 8/8 = 1.000 | 0.676-1.000 | 固定受入回帰 |
| Core / Router境界fixture | 9/25 = 0.360 | 0.202-0.555 | 交差評価 |
| Pattern Router raw / 境界fixture | 25/25 = 1.000 | 0.867-1.000 | 改善中に参照した回帰 |
| Pattern Router raw / Core代表fixture | 5/8 = 0.625 | 0.306-0.863 | 交差評価 |
| Pattern Router measurement holdout | 26/30 = 0.867 | 0.703-0.947 | 非grouped holdout |
| Pattern Router repeated CV | 0.769 | CI非算出 | 元データ166件、反復点は非独立 |

Pattern Router境界fixture 25件中11件は学習DBと完全一致する。
完全一致を除く14件も14/14だが、このfixture自体を改善過程で参照しているため、
sealed final testではない。

Core代表fixtureでは学習DBとの完全一致は1/8。Pattern Routerの非一致7件に限ると
4/7 = 0.571である。

## Route別の発見

Coreを境界fixtureへ適用した場合:

- `explore`: recall `0.083`
- `respond`: recall `0.625`
- `clarify`: recall `0.500`
- `build`: recall `0.000`
- macro-F1: `0.364`

主な誤りは代替案要求を`respond`または`summarize`へ送ること。

Pattern RouterをCore代表fixtureへ適用した場合:

- implementation designを`respond`
- deep verificationを`clarify`
- empty inputを`respond`

へ送る。

## Abstention

Pattern Routerの境界fixture:

- raw accuracy: `1.00`
- effective label accuracy: `0.92`
- coverage: `0.92`
- selective accuracy: `1.00`

2件の正しい`explore`予測が低確信として`clarify`へfallbackした。
これは安全行動であり、route精度の改善とは数えない。

## Semantic Answer Quality

独立blind評価:

```text
independent_case_count = 0
status = not_established
```

v1.5の4件とv1.6の4件は統計・契約fixtureであり、production evidenceではない。

## 現時点の判断

1. Coreの固定受入経路は安定している。
2. Coreの表現境界への一般化は弱い。
3. Pattern Routerは自身の回帰fixtureには強いが、Core入力との交差精度は不十分。
4. ルータ統合前にgrouped / sealed評価が必要。
5. 回答本文の品質は独立studyを実施するまで未知。

## 再現

```powershell
python -m thought_core.accuracy_audit
```

出力schemaは`response-accuracy-audit.v1`。

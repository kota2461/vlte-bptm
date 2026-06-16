# Conversation Accumulation v1

更新日: 2026-06-13

## 目的

`deterministic_signal_extractor 0.2`をV2候補として固定し、既存の改善用18件とは
独立したopen caseを期限付きで蓄積する。active sealed v2は候補固定後の一回測定まで
開かない。

## 期間

- 開始: 2026-06-13 15:59 JST
- 締切: 2026-06-20 23:59 JST
- 早期終了: 50件到達時
- 最低review件数: 40件

締切または50件到達の早い方で収集を止める。締切時にgateを満たさない場合は、
sealed v2を消費せず蓄積期間を再設定する。

## 初回バッチ

`data/conversation_accumulation_v1.json`に新規24件を収録した。既存の会話スモーク
18件は改善に使用済みなので含めない。

カテゴリ:

- conversation response
- indirect explanation
- verify then build
- mixed language
- temporal disambiguation
- compound intent

すべて`draft`であり、人間承認前の正解ラベルとして扱う。

初回観測:

- semantic intent accuracy: 0.708
- processing plan accuracy: 0.625
- end-to-end route accuracy: 0.500
- critical under-processing: 4件

これは裁定結果ではなく、draft labelに対する候補固定後の初回観測である。
0.2は同batchへ合わせて修正せず、期限まで失敗分布を蓄積する。

## 汚染防止

- candidateはケース作成前に`adapter 0.2`として固定
- 同一batchの結果を見て、そのbatchへ合わせた修正を行わない
- 修正する場合はcandidate versionを更新し、次batchから測る
- active sealed v2を蓄積・調整・レビューに使用しない
- production会話のraw promptは自動収集しない
- 追加ケースは明示的に作成・匿名化・承認したものだけ保存する

## V2判定gate

- 収集停止条件に到達
- 必須カテゴリ数を満たす
- 40件以上が人間承認済み
- end-to-end route accuracy 0.90以上
- critical under-processing 0件
- visible benchmarkとの完全一致重複0件

すべて満たした場合だけactive sealed v2の一回測定へ進む。sealed結果を見た後は
同fixtureで再調整せず、必要ならsealed v3へrotationする。

0.2がgateを満たさない場合は、承認済み失敗ケースをTargeted Learningへ移し、
次候補を別versionとして固定する。次候補は新しいopen batchで再評価し、今回の
batchを候補判定用holdoutとして再利用しない。

## 実行

```powershell
python -B build\evaluate_conversation_accumulation.py
```

出力:

`build/conversation_accumulation_v1_report.json`

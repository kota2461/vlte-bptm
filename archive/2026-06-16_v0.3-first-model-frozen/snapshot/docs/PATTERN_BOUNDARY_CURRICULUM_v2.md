# Pattern Boundary Curriculum v2 Round 1

更新日: 2026-06-11（revision 2）

## 目的

Pattern Routerが混同しやすいRoute境界へ、人間レビュー前提の対照学習候補を追加する。
Round 1は境界の基準を明瞭にするanchor dataであり、独立精度を主張する評価データではない。

## Revision 2（否定交絡の修正）

外部レビュー（`docs/EXTERNAL_REVIEW_RESPONSE_2026-06-11.md` §1）で、revision 1の
`respond` 12件全件が否定メタ指示（「〜は作らず」「Do not」）を含み、`build` 0/12、
`verify` 0/6と完全相関しているため、学習時に「否定→respond」の表層ショートカットを
生む危険が指摘された。revision 2では:

- `respond`全12件を肯定形の自然文へ書き換え
- 逆方向の自然な否定を追加（build「説明だけで終わらせず〜」、verify「鵜呑みにせず〜」、
  respond「難しい言葉を使わずに〜」）
- `template_id`を全件へ付与（grouped splitと近似重複検出の単位）
- `authoring_models`をsource metadataへ記録（Q3/Q4対応）
- 否定マーカー分布: explore 5 / respond 1 / build 1 / verify 1 / clarify 1（どのRouteも
  100%でも0%固定でもない状態を回帰テストで強制）

revision 1のpending 48件はsuperseded却下（手続き却下。内容判断ではない）。
revision 1のソース・DB・モデル・評価は`archive/2026-06-11_pre-round1-review/`へ
凍結済みで、`RESTORE.md`の手順で完全に戻せる。

未学習基準値（同一モデル`532D...45E9`、再学習なし）:

| 対象 | Raw accuracy |
| --- | ---: |
| revision 1（48件、アーカイブ） | 27/48 = 0.5625 |
| revision 2（52件、現行） | 30/52 = 0.5769 |

per-case詳細は`build/boundary_v2r2_untrained_eval.json`に保存し、承認・学習後の
pre/post比較の基準とする。

## 構成

- 52 prompts
- 26 contrast groups
- 日本語36件、英語16件
- `simple` 28件、`compound` 24件
- explore_respond 12件 / build_respond 14件 / clarify_verify 14件 / explore_build 12件

対象境界:

- `explore_respond`
- `build_respond`
- `clarify_verify`
- `explore_build`

同じ`contrast_group`の2件は話題、言語、難度を揃え、Route意図だけを変える。

## 由来

データはプロジェクトのRoute定義から独立に作例したAI支援synthetic promptである。

- `ai_assisted_authoring`: `true`
- `teacher_model_outputs_used`: `false`
- `copied_source_text_used`: `false`
- `hidden_reasoning_used`: `false`
- `approval_required`: `true`

他モデルの回答、確率分布、logit、chain-of-thoughtを教師信号として再現していないため、
一般的なteacher-student model distillationには当たらない。一方でAI支援作例である事実は
隠さず記録する。この文書は法的判断や各サービス固有の利用規約判断を代替しない。

## 投入

```powershell
python -m pattern_learning seed-boundaries-v2
```

投入は冪等で、同じsource revisionを再実行しても重複しない。全件`pending`であり、
承認前は`patterns`、学習集合、デプロイ済みモデルへ影響しない。

## 人間レビュー

各候補について次を確認する。

1. 文面から期待Routeが一意に判断できるか
2. 対照側との違いが話題ではなく意図になっているか
3. `suggested_operators`が過不足なく、Routeラベルの言い換えになっていないか
4. 日本語・英語として不自然な誘導語や過度な定型句がないか
5. 実運用で同じ意図を持つ依頼として成立するか

迷う候補は無理に承認せず、修正またはrejectする。レビュー時の自由記述を次の作例へ
そのまま自動転用しない。

## 学習・評価境界

- 同一`contrast_group`は同じtrain/validation/test側へ置く
- Round 1自体をsealed final testとして使わない
- 近似文、同一テンプレート、同一出典もgroup単位で分割する
- 承認後も明示的な`train`操作なしにモデルを更新しない
- モデル予測を正解ラベルとして再投入しない

## Round 2

Round 1のレビュー結果と誤分類を根拠に、次を追加する。

- 否定表現と二重否定
- Route名を直接示さない暗黙意図
- 複数Routeを含む複合依頼
- 長文、前置き、引用を含む依頼
- 日英混在、表記揺れ、口語
- 指示語や不足情報を含むhard negative

Round 2はRound 1の単純な言い換え増殖にせず、失敗類型ごとに版を分ける。

# Handover 2026-06-11 Session 12

## 今回の目的

現行精度監査で弱かったRoute境界へ、teacher-student蒸留ではない形で
人間レビュー前提の学習候補を追加する。

## 実装

- `pattern_learning/boundary_curriculum_v2.py`
  - 48 prompts
  - 24 contrast groups
  - 4 boundaries
  - 日本語32件、英語16件
  - `simple` 26件、`compound` 22件
- `seed-boundaries-v2` CLI
- 構造、由来、pending限定、CLI冪等性のテスト
- 運用仕様とロードマップ更新

## 由来境界

- AI支援によるRoute仕様起点のsynthetic prompt
- teacher modelの回答、logit、hidden reasoningは不使用
- 外部文章のコピーは不使用
- `ai_assisted_authoring=true`をDB source metadataへ保存
- 全件に人間承認を要求

これは一般的なteacher-student model distillationではない。ただしAI支援作例である
事実を隠さず、利用規約や法的判断を代替する主張はしない。

## 現行DB

2026-06-11投入後:

- candidates total: 220
- pending: 48
- approved: 166
- rejected: 6
- patterns: 166
- sources: 4

v2候補48件はすべて`pending`で、非pendingは0件。最新training runは166 samplesの
ままで、再学習は実行していない。

## モデル不変確認

- model: `build/pattern_router_model.json`
- SHA-256:
  `532D075B794D804B3E3CE609E4809E6275E293020911A38FAFB99AB848B845E9`
- timestamp: 2026-06-11 09:11:53 JST

投入前後でhashとtimestampは同一。

## 検証

- full test suite: 176 passed
- v1 curriculumとの完全一致: 0件
- v2内重複: 0件
- 24 groupsすべて2件、異なる2Route
- DB `PRAGMA quick_check`: `ok`

SQLite更新はdesktop sandbox内のjournal確定操作が拒否されたため、一度失敗した。
失敗journalとDB複製は
`build/pattern_lab_recovery_20260611_1455`へ保存した。SQLite自身のrollback後に
承認済み実行で投入し、最終DBの健全性と件数を再確認済み。

## 次の地点

1. Round 1をUIで人間レビューする
2. 誤ラベル、不自然な誘導語、operator過不足を修正またはrejectする
3. `contrast_group`対応のgrouped splitを実装する
4. Round 2へ否定表現、暗黙意図、複合依頼、長文、日英混在を追加する
5. 学習候補と別系統のsealed評価セットを作る
6. grouped評価を通過するまでCore統合と精度改善の主張を行わない

現時点では候補追加まで完了しており、承認・再学習は未実施。

## 未学習精度

現行モデルを更新せず、pending 48件へ適用したpre-training基準値:

- Pattern Router raw: 27/48 = 0.5625
- Pattern Router effective: 25/48 = 0.5208
- Pattern Router pair both correct: 8/24
- Core Router: 22/48 = 0.4583
- Core Router pair both correct: 2/24
- 日本語: 23/32
- 英語: 4/16
- `build` recall: 4/12
- `verify` recall: 1/6

詳細は`docs/PATTERN_BOUNDARY_V2_UNTRAINED_ACCURACY.md`を参照する。

# Handover 2026-06-29 — Router honesty, structural fixes, and the model-lean investigation

For: codex (and any agent continuing this branch).
Branch: `codex/v6-draft-repo-cleanup` (pushed). Restore point: tag
`backup/pre-overfit-rework-2026-06-29` + `backups/tsr_pre-overfit-rework_2026-06-29.zip`.
State at handover: **677 passed, ruff/tree caveats below, working tree clean,
determinism guard green.**

---

## 0. TL;DR

辰也の問い:「毎回調整すると非sealed の数字（1.000）は良くなるのに、実測（sealed）は伸びない/下がる。ごまかし・幻覚か？」

結論（実証済み）:
- **捏造（幻覚）ではない** — 数値は実コード計算。
- **しかし構造的な過学習＝指標 gaming は実在**。「調整対象で 1.000」は情報量ゼロで、目標にすべきでない。
- **正しい指標は held-out（k-fold / fresh sealed）**。同一セッションで `1.000`(validation) と `0.71`(k-fold) を同じモデルから出して見せた。

このセッションは (1) 構造的な信頼性の修復（S1–S7）と (2) 過学習の是正・学習モデルへの移行検討、を正直な測定規律のもとで行った。

---

## 1. 確立した運用ルール（codex はこれを守ること）

1. **`1.000` を見たら祝うな、疑え。** 特に調整対象での満点は無意味。プロジェクトの sealed 目標も 0.857/0.929 で 1.0 ではない。
2. **進捗判定は held-out のみ。** validation は小さく同分布で illusion を起こす。**k-fold5 / fresh sealed** で判断する。`build/exp_unified_model.py` が両方出す。
3. **leakage 厳守。** validation / sealed / 全 sealed_vN を学習に入れない。実験は必ず assert で弾く。
4. **no automatic learning。** 学習データの承認は人間（辰也）。生 debate ログは `training_allowed: false`。candidate は `review_status="candidate"` で置き、approved には人間が flip。
5. **同源/設計データは効かない。** 自作の benchmark-family / stub を足しても validation を膨らますだけで真汎化は上がらない（本セッションで2回実証）。効くのは**多様な実世界データ**。

---

## 2. 構造修正 S1–S7（信頼できる土台）

監査（V11）は別環境の転送破損で誤検出が多かったが、独立検証で**実在バグ＝テスト順序依存**を特定し修正した。

| 項目 | commit | 内容 |
|---|---|---|
| 基盤確立 + 順序依存 fix + `_tmp` マスク除去 | 838dfc0, 20bc5f0 | build/ 成果物の共有状態依存でスイートが 1-failed⇄670 と振れていた。regenerate-before-read fixture + strict assertion 復元 |
| S1 決定論化 | e37efd4, d3125d7 | `generated_at` 等 wall-clock 埋め込みを `semantic_routing/reproducibility.py`(`SOURCE_DATE_EPOCH`) 経由化。テスト実行後 tree clean を達成 |
| S4 regenerate-before-read 横展開 | fbf4d3b | 20 テストへ同パターン適用 |
| S2 legacy pyc を版管理 | 47b319a | `build/recovery_assets/baseline_legacy_cpython310.pyc`（snapshot の再現性確立） |
| S3 封印 fixture 整合性ガード | b41f35e | `tests/test_sealed_fixture_integrity.py` + manifest。content drift 検知 |
| S6a junk pyc 一掃 | f62f9ac | `__pycache__` の 471 blob 削除、reader を tracked pyc へ repoint |
| S7 CI + determinism guard | efc7603 | `.github/workflows/ci.yml`: pytest + `git diff --exit-code` |
| S6b README + cruft | 8b85108 | `build/README.md`、setuptools `build/lib` untrack |
| S5 暗記層 gate 化 | f9e08de | `LEGACY_SNAPSHOT_DEFAULT` / `use_legacy_snapshot`（既定 ON で挙動不変、OFF で素汎化測定可） |

**注意**: ruff は package dirs に 21、tests に 6 の既存 F401 等が残る（build/ は対象外）。mypy 未設定。CI は pytest + 決定性のみ gate。

---

## 3. 過学習の是正

- **Step1（dead literal 除去）は中止**: 「fixture に 0 マッチ＝不要」ではない。emergency/medical/legal/security など**安全マーカー**が 0 マッチでも必須。全 branch dead の marker を消すと空正規表現=全マッチで risk 全件 critical 化。fingerprint+suite が commit 前検知。→ **fixture corpus は usefulness 判定に狭すぎ、自動削除不可**。
- **Step3（ask_first 一般化, fa93853）**: `constraint_ask_first` の 11 個の single-match literal を一般則 `ask\ (?:me|first|which|whether|for)\b` に集約。**validation gate-off 不変・suite 緑**で無回帰、paraphrase「ask me about the format」を新規捕捉。overfit literal 116→109。
- **診断 a（99cc558）**: `build/diagnose_overfit_literals.py` = live `_MARKER_DATA` 453 branch を 1034 入力にマッチ計数。dead 119 + pure-overfit(1match) 116 = **52% が死蔵 or 1文専用**。

---

## 4. 学習モデルへ寄せる検討（本筋）

regex の天井を超えるには学習モデルが本筋。正直に測った結果:

| 構成（held-out） | 数値 |
|---|---|
| 現行モデル単体 (n-gram) k-fold5 | 0.659 |
| + markers を特徴量化 | 0.713 |
| + thought-color データ(366)複合 | **0.729**（最良） |
| + thought-color channel 特徴量 | ~0（無効、むしろ微減） |
| 参考: markers_only validation | 0.964（illusion）/ sealed_v10 実測 0.786 |

要点:
- モデル単体は弱い（validation 0.68）。弱点は **explain 0/4・英語 0.57** に集中。
- **marker を特徴量に入れると 0.68→0.93（validation）/ 0.66→0.71（k-fold）** = 最大レバー（`build/exp_unified_model.py` mode=markers）。
- **データを足すと validation 1.000 が出るが k-fold は 0.71** = illusion を k-fold が暴く（da74b79）。
- **多様な thought-color データは validation illusion を下げつつ k-fold を上げた**（0.713→0.729, c039bad）= 真の多様データの署名。**channel を特徴量化しても無効**（4da4f7d）= 価値はデータであって表現ではない。

レバー順: **markers特徴量(+0.05) ≫ 多様データ(+0.016) > channel特徴量(~0)**。

関連スクリプト（全て本番無改変・隔離・read-only/draft 出力）:
`build/model_vs_markers_harness.py` / `build/honest_validation_harness.py` /
`build/exp_unified_model.py`(kfold付) / `build/audit_baseline_snapshot_oracle_validity.py`。

---

## 5. debate 活用 + 本番修正

- **weakpoint topics 起草**（441776d）: `debate_lab/topics_weakpoint_explain_english_v1.json`（26題、explain/英語狙い、`build/gen_weakpoint_topics.py`）。
- **辰也が LMStudio で実走**（Gemma4-12b-qat × Qwen3.5-9b）→ `build/weakpoint_explain_english_debate_v1.json`。抽出 → selection + worksheet（ba1c3bf）。26 usable / 11 miss。
- **候補は効かない**（`estimate_weakpoint_impact.py`）: 25 draft row を足しても validation 不変・k-fold 微減。同源 stub の限界（既出教訓）。
- **debate の真価は診断**: explain が英語で過剰発火する兆候。
- **(A) 本番修正（d4b9e09）**: ただし held-out で裏取りすると **validation は 27/28 で過剰発火は不可視**、真の over-fire は ~3 件 off-validation。cherry-pick tighten は回避し、**一般則として正当な1点のみ修正** = `_intent_scores` の explain ブースターから定義質問 `what is/what does` を除去（explanation_request marker と整合）。「what is X?」5/5 が respond 化、explain cue は維持、**validation 27/28 不変・suite 677 緑＝無回帰**。これは correctness fix で metric win ではない（validation に問題が無かった）。

---

## 6. 現状の正直な数値

- 本番 router（markers+model、gate ON 既定）: validation 27/28（gate-off）。sealed_v10 実測 0.786（過去）。
- 学習モデルの正直な天井（現データ）: **k-fold ~0.73**。markers の実力には未到達。
- 暗記スナップショット（2168件）は route() 既定 ON で測定経路に常駐するが、ON/OFF 差は validation で 1–2 件（gate 化済み、S5）。

---

## 7. 未対応 / 次の一手（優先度順の私見）

1. **多様な実世界データ + fresh sealed**（本筋・要辰也承認）: k-fold ~0.73 の天井を超える唯一の道。stub/同源では上がらない。実ログを人手ラベルで。測定は新 sealed で。
2. **#9/#10 secondary-explain arbitration**（未対応）: 「…Explain your reasoning」等、二次節の explain が primary(explore/verify) を奪う multi-intent 問題。締めると巻き込みリスク、慎重に。
3. **explain under-fire（build 混同）**: 「walk me through / break down why」が build に流れる傾向（diagnostic より）。
4. **S6b 本格版**（版コピー generator の DRY 集約）/ **S5 暗記層の最終的な扱い**（gate 化済、除去は production 挙動変更で要判断）。
5. ruff/mypy 債務の解消（CI gate に入れるなら）。

---

## 8. 成果物・コミット地図

直近 push（`f9e08de..d4b9e09`、12 commits）:
`feced4d`(backups ignore)→`99cc558`(diag a)→`4beb4b6`(harness, step1中止)→`fa93853`(step3)→
`26fbee6`(model分解)→`4a52bd0`(marker特徴量)→`da74b79`(k-fold が幻暴く)→`c039bad`(tc データ)→
`4da4f7d`(tc channel無効)→`441776d`(weakpoint topics)→`ba1c3bf`(debate実走+評価)→`d4b9e09`(explain fix)。

それ以前（S1–S7 等）: `838dfc0`→`20bc5f0`→`e37efd4`→`d3125d7`→`fbf4d3b`→`47b319a`→`b41f35e`→`f62f9ac`→`efc7603`→`8b85108`→`f9e08de`。

復元: `git fetch && git reset --hard backup/pre-overfit-rework-2026-06-29` ＋ gitignore 資源は
`backups/local_resources_2026-06-29.zip`（pattern_lab.db / router_debate ログ / router model、オフサイト保管済）を上重ね。`__pycache__` を消すと `data/pattern_lab.db` 欠如で 1 テスト落ちる点に注意。

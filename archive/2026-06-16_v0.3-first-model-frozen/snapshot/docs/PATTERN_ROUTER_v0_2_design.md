# Pattern Router v0.2 評価設計

更新日: 2026-06-12（v0.2.3: 改善確認ackとsealed交代を追記）

## 目的

学習データ追加の効果と未見性能を分離し、評価結果を見て再調整したことによる
楽観バイアスを防ぐ。

## 2026-06-12以降の責務

本書のPattern Routerは`Raw Prompt -> Route`を行うLegacy Intent Classifierの
評価・昇格契約として維持する。新しいPattern Language ModelとProcessing
Routerは別コンポーネントとし、次を正本とする。

- `SEMANTIC_ROUTING_ARCHITECTURE_v0_1.md`
- `PATTERN_LANGUAGE_MODEL_roadmap.md`
- `PROCESSING_ROUTER_roadmap.md`
- `LLM_INTEGRATION_roadmap.md`

現行254件モデルを処理予算Routerへ転用せず、比較baselineとして凍結する。
active sealed v2も本書のLegacy Router評価専用とする。

## データ分割

```text
approved patterns
  -> grouped train
  -> grouped validation       モデル・特徴量の比較
  -> sealed calibration       確率較正とfallback閾値
  -> sealed final test        最終報告のみ
```

同一出典、同一生成テンプレート、近似重複文は同じgroupへ置く。文字n-gramの
Jaccard類似度などを使い、分割をまたぐ近似重複を検出してレポートする。

## 評価セット

- 各Route最低30件
- explore/respond、clarify/verify、explore/buildの各境界を最低20件
- 日本語、英語、短文、長文、否定、丁寧表現、複合意図を層別化
- 作成者、凍結日、出典、類似テンプレートgroupを保存
- sealed final testの文面は学習担当へ開示しない

## 指標

- raw accuracy、macro-F1、balanced accuracy、Route別precision/recall/F1
- confusion matrix
- ECE、Brier score、信頼性図
- coverage-selective accuracy曲線
- fallbackの人間評価: 適切な聞き返し / 不要な聞き返し / 危険な回答回避

fallback閾値はraw分類精度だけで決めず、不要な聞き返しと誤回答のコストを
明示したうえで選ぶ。

## 完了条件

1. 分割と重複検査が再現可能である
2. calibration setだけで閾値を決める
3. sealed final testを開封する前に採用モデルを固定する
4. 開封後の修正は次の評価版として別fixtureへ送る

## v0.2.1: デプロイゲートと学習データ階層

背景: Round 1境界学習で、新規データが初期学習由来の挙動を2件シフトさせた
（うち1件は初期アンカー自体の両義性が原因と判明し、契約改訂で解決した）。
この経験から、「初期学習の保護」は学習時の重み付けではなく、デプロイ時の
契約検証で行うことを正式な設計とする。重み付けは衝突を隠すが、ゲートは
衝突を表面化させ、人間がどちらが正しいかを裁定できる。

### 学習データ階層（tier）

各承認パターンは出典curriculumに応じてtierを持つ。

| Tier | 名称 | 対象 | 例 |
| --- | --- | --- | --- |
| 0 | foundation | 基礎理解。挙動の土台であり退行を許さない | math-v1、language-v1 |
| 1 | refinement | 境界・補強学習。foundationを壊さない範囲で改善する | route-boundaries-v1/v2/round1b、demo、manual、wikipedia |

- tierは`source.url`から決定的に導出する（DB書き換え不要）。
- 新curriculumは作成時にtierを明示する。
- 学習時のtier重み（`foundation_weight`）は実装するが**既定で無効**（全tier
  1.0、既存モデルと完全に同一の学習結果）。ゲートで繰り返し衝突が観測され、
  かつfoundation側が正しいという人間裁定が続いた場合にのみ、明示パラメータ
  として有効化を検討する。有効化はモデルmetadataへ記録する。

### Foundation Anchor Suite

- tier 0 curriculumのrating 5パターンから決定的規則で選んだ代表入力と
  期待Routeのfixture（`tests/fixtures/foundation_anchor_suite_v1.json`）。
- 全件が学習データと重複する。これは汎化評価ではなく
  **自己一貫性契約**（デプロイモデルは基礎入力で正しく振る舞い続ける）である。
- 凍結回帰25件と同じく、ケースは一意ラベル基準（レビュー基準1番）を満たす
  ものだけを入れる。作成時点のデプロイモデルで不合格のケースは入れず、
  fixture metadataの除外リストへ記録する（ラチェット方式）。
- 改訂は契約変更として文書化と人間承認を要する。

### train / promote の分離

`train`がデプロイ先を直接上書きする構造は、ゲート不能な退行を許す。
次の3段階に分離する。

```text
train   -> 候補ファイルへ出力（build/pattern_router_model_candidate.json）
gate    -> 候補を契約検証
           1. 凍結回帰fixture: raw accuracy 1.0 必須
           2. Foundation Anchor Suite: 全件一致 必須
           3. 参考指標（cross-core等）はレポートのみ（昇格は妨げない）
promote -> 合格時のみデプロイ先へコピーし、ゲートレポートJSONを保存
           不合格時は候補を残し、misses一覧を返して人間判断へ
```

- 評価UIの学習ボタンも同じ経路を通る（候補学習→ゲート→合格時自動昇格。
  不合格時はデプロイモデルを変更せず、不合格理由を表示する）。
- ゲートレポートは`router-deployment-gate.v1` schemaで版管理する。
- ゲート不合格が「新データが悪い」のか「アンカーが悪い」のかは自動判定
  しない。今回のclarify_target改訂と同様、人間が裁定し、アンカー改訂は
  契約変更として記録する。

### 完了条件（v0.2.1）

1. `train`単体ではデプロイモデルが変化しない
2. ゲート不合格の候補が昇格されないことをテストで固定する
3. foundation_weight既定値での学習結果が従来と一致する
4. Foundation Anchor Suiteの選定規則と除外リストが再現可能である

## v0.2.2: ゲート契約の固定化（三層契約）

v0.2.1のゲートは「何を検査するか」を定めたが、「検査対象が改ざん・劣化
していないこと」と「昇格・降格の運用」を契約化していなかった。件数だけを
固定すると、似た簡単な例を増やして形式的に通せてしまう。次の三層を正式
契約とする。

```text
Gate      = 固定された契約
Promotion = 契約通過 + 改善確認 + 人間承認
Rollback  = 契約違反時に直前モデルへ復帰
```

### 層1: ゲート固定ルール

- ゲートfixtureはversion・内容・SHA-256を
  `tests/fixtures/gate_fixture_registry.json`（`gate-fixture-registry.v1`）
  で固定する。ゲート実行時に実ファイルのSHAがregistryと一致しなければ
  「fixture整合性違反」として不合格にする。
- 既存anchorは原則削除不可（append-only）。追加は可能。削除・ラベル変更は
  registryの新version・理由・人間承認が必須で、改訂履歴をregistryへ残す。
- 当時のゲートレポート（`router-deployment-gate.v2`、v0.2.3でv3へ更新）
  にはcandidate、各fixture、学習DB snapshot、現行デプロイモデルの
  SHA-256を記録する。
- `raw_route`と`effective_route`の両方を検査する。rawは100%必須。
  effectiveは「期待Route」または「clarify退避（安全行動）」のみ許容し、
  それ以外への変化は不合格。clarify退避は件数をabstentionとして記録する。
- 件数は「固定」ではなく「最低件数・削除禁止・単調増加」とする。registryに
  全体最低件数とRoute別最低件数を持ち、下回れば不合格。最低件数を下げる
  registry更新は行わない。
- sealed testは導入後この registry に登録して固定し、調整に使ったら
  新versionへ交代する。

### 層2: 昇格ルール

- foundation / frozen regressionは原則100%。
- 改善確認: 候補の`validation_accuracy`と`kfold_accuracy`が現行デプロイ
  モデルより`0.02`を超えて悪化していたら不合格（分割・乱数由来の微小揺れ
  のみ許容）。grouped validation / sealed test導入後はそれらの最低基準を
  この検査へ追加する。
- candidate hashがgate実行時から昇格時まで不変であることを検証する。
  不一致は昇格拒否。
- 昇格は明示的な人間操作（CLI `promote`またはUIの昇格ボタン）でのみ行う。
  **UIの学習ボタンは昇格しない**（v0.2.1の自動昇格を廃止。学習→ゲート
  結果表示まで）。
- 置換はatomicに行う（一時ファイルへコピー後に`os.replace`）。
- 昇格時、置換前のデプロイモデルを`build/model_history/`へ自動保存し、
  ゲートレポートに保存先を記録する。

### 層3: 降格・rollbackルール

- rollback発動条件: 本番監視での重大anchor違反、精度・coverage・安全指標の
  規定値割れ、モデル・データ・fixtureの整合性違反。
- `rollback`コマンドは、現行デプロイモデルを削除せず
  `build/model_history/quarantined_*.json`として隔離保存し、直前の承認済み
  モデルをatomicに復元する。理由を必須引数として記録する。
- 隔離モデルは原因分析まで保持する。履歴が空の場合はrollbackを拒否する。

### 完了条件（v0.2.2）

1. registryとfixtureのSHA不一致でゲートが不合格になることをテストで固定
2. 候補が現行モデルより悪化した場合に昇格が拒否される
3. UIの学習操作ではデプロイモデルが変化しない
4. rollbackが直前モデルを復元し、問題モデルを隔離保存する
5. すべてのゲートレポートにcandidate / fixture / DB / 現行モデルのhashが残る

## v0.2.3: 改善確認の構成変化ack

`validation_accuracy`は承認コーパスの増加に伴ってholdout自体が変わるため、
現行モデルと候補モデルの値が常に同一母集団の比較になるとは限らない。
この構成変化だけで改善確認が偽ブロックした場合に限り、同一sealed sliceの
比較証拠を伴う人間ackで昇格を許可する。

### ack可能な範囲

- ack対象は`improvement_vs_deployed`だけとする。
- frozen regression、Foundation Anchor Suite、fixture SHA整合性、最低件数、
  candidate hash不変条件はack不可とする。
- ackには理由と操作者を必須とし、ゲートレポートへ記録する。
- 候補と現行モデルを同一のregistry登録済みsealed fixtureで測定し、
  両結果の`model_sha256`がゲート記録と一致しなければならない。
- 候補のsealed正解数が現行モデルを下回る場合はackを拒否する。
- sealed結果ファイル自体のSHA-256、fixture version、両スコアをレポートへ
  記録する。
- ackはvalidation/k-foldの失敗記録を消さない。判定は
  `pass_with_improvement_ack`として通常合格と区別する。

### sealed fixtureの消費と交代

- sealed結果を昇格裁定に使った時点で、そのfixtureを`consumed`とする。
- consumed fixtureは以後の測定に再利用せず、未測定のactive successorへ
  交代する。
- 2026-06-12の254件候補では、sealed v1が`11/22`から`17/22`へ改善した
  結果を裁定証拠に用いたため、v1をconsumed、v2をactiveとした。

### CLI

```powershell
python -m pattern_learning promote `
  --ack-improvement-regression "holdout構成変化。same-slice sealedで改善" `
  --candidate-sealed-result build/sealed_v1_candidate_254.json `
  --deployed-sealed-result build/sealed_v1_pre_round2_user.json `
  --ack-actor "human-reviewer"
```

### 完了条件（v0.2.3）

1. 契約検査が1つでも失敗したレポートはackできない
2. モデルhashまたはsealed fixtureが異なる証拠はackできない
3. sealed非悪化と明示理由がある場合だけ改善確認をackできる
4. ack付き昇格は通常合格と区別して監査記録へ残る
5. 裁定に使用したsealed fixtureがconsumedとなり、active successorが1つある

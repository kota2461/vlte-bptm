# Pattern Lab v0.1.1

更新日: 2026-06-11

Pattern Labは、ルーター候補を人間が評価し、承認済みデータだけをPattern DBと学習器へ渡すローカルツールである。VLTE-BPTM v1.0aの自動学習禁止境界は変更しない。

## データフロー

```text
Wikipedia公式API / 手入力
  -> Pattern候補抽出
  -> review queue
  -> ユーザー修正・評価
  -> approved Pattern DB
  -> 明示的なtrain操作
  -> router model JSON
```

却下候補は履歴として残るが、`patterns`テーブルと学習集合には入らない。再評価した場合は最新の承認内容でPatternを更新する。

## 起動

```powershell
python -m pattern_learning init
python -m pattern_learning seed-demo
python -m pattern_learning serve
```

ブラウザで`http://127.0.0.1:8765`を開く。

## 数学カリキュラム

基礎的な数の理解から日本の高等学校レベルまでの数学的思考パターンを、評価待ち候補として投入できる。

```powershell
python -m pattern_learning seed-math
```

候補は`pattern_learning/math_curriculum.py`に定義され、次の5レベルで構成される。

- `number_sense`: 数の認識・大小比較・位取り
- `addition`: 加算。答えが8になる同回答バリエーション（3+5 / 5+3 / 6+2 / 4+4 / 7+1 と言い換え）を含む
- `elementary`: 四則演算・分数・割合・文章題
- `junior_high`: 一次/連立方程式・因数分解・証明・確率
- `high_school`: 二次関数・三角関数・指数対数・数列・帰納法・ベクトル・微積分・確率統計

投入されるのは評価待ち候補のみで、承認・学習は通常どおり明示的に行う。

## 言語基礎カリキュラム

日本語・英語の挨拶と基礎的な文理解のパターンを、評価待ち候補として投入できる。

```powershell
python -m pattern_learning seed-language
```

候補は`pattern_learning/language_curriculum.py`に定義され、次の4レベルで構成される。

- `greetings_ja` / `greetings_en`: 挨拶（すべて`respond`ルート。模範応答文を`thought_form.candidates`に保持）
- `basic_ja`: 主語述語の分解・助詞の比較・敬語・因果関係・要約・確認
- `basic_en`: 翻訳・品詞理解・時制比較・文法検証・要約

挨拶への応答文そのものはルーターやCoreが生成するものではなく、`llm_order`（mode/instruction）と承認済み`candidates`が応答生成側への契約となる。

インストール後は次も利用できる。

```powershell
pattern-lab seed-demo
pattern-lab serve
```

## Wikipedia取得

UIまたはCLIから明示的に実行する。Wikimediaの識別可能なUser-Agentを必須とする。

```powershell
python -m pattern_learning import-wikipedia `
  --title "二次方程式" `
  --title "命題論理" `
  --user-agent "PatternLab/0.1 (contact@example.com)"
```

カテゴリ指定:

```powershell
python -m pattern_learning import-wikipedia `
  --category "数学" `
  --article-limit 10 `
  --user-agent "PatternLab/0.1 (contact@example.com)"
```

保存するのは短い評価候補、記事名、URL、版ID、取得日時、ライセンス情報であり、記事全文は保存しない。画像、外部リンク先、引用元本文は取得対象外。

## 学習とデプロイ（v0.2.3: 三層契約 + 改善確認ack）

2件以上かつ2種類以上のRouteに承認データがある状態で実行する。

```powershell
python -m pattern_learning train      # 候補モデルを学習(デプロイは変化しない)
python -m pattern_learning promote    # ゲート検証→合格時のみatomicにデプロイ昇格
python -m pattern_learning rollback --reason "理由"  # 隔離保存して直前モデルへ復帰
python -m pattern_learning predict "この設計を検証してください"
```

`train`は候補ファイル`build/pattern_router_model_candidate.json`へ出力し、デプロイ済みモデルを直接上書きしない。`promote`のゲート（`router-deployment-gate.v3`）は次を検証する。

1. fixture整合性: `tests/fixtures/gate_fixture_registry.json`のversion・SHA-256と一致（anchorはappend-only。改訂は新version+理由+人間承認）
2. 最低件数: 全体・Route別とも下回らない（単調増加）
3. 凍結回帰25件: raw 100%、effectiveはclarify退避のみ許容
4. Foundation Anchor Suite: 同上（tier 0自己一貫性契約）
5. 改善確認: validation/kfold精度が現行デプロイより0.02超悪化しない

合格時のみ旧モデルを`build/model_history/`へ自動保存してatomicに置換し、candidate・fixture・学習DBのSHA-256を含むレポートを保存する。candidate hashがゲート時から変わっていれば昇格を拒否する。`rollback`は現行モデルを削除せず`quarantined_*`として隔離し、直前の承認済みモデルを復元する。**評価UIの学習ボタンは昇格しない**（ゲート結果の表示まで。昇格は「ゲート検証して昇格」ボタンまたはCLIの明示操作）。tier重み`--foundation-weight`は既定1.0=無効。設計は`docs/PATTERN_ROUTER_v0_2_design.md`のv0.2.1〜v0.2.3節を正とする。

validation holdoutの構成変化だけで改善確認が失敗した場合は、同一sealed
fixtureで候補が現行モデル以上である証拠と人間の理由を付けて、改善確認だけを
ackできる。foundation/regression、fixture整合性、最低件数、candidate hashは
ackできない。

```powershell
python -m pattern_learning promote `
  --ack-improvement-regression "holdout構成変化。same-slice sealedで改善" `
  --candidate-sealed-result build/sealed_v1_candidate_254.json `
  --deployed-sealed-result build/sealed_v1_pre_round2_user.json `
  --ack-actor "human-reviewer"
```

裁定に使用したsealed fixtureは`consumed`となり、次のactive versionへ交代する。
2026-06-12の裁定ではv1を消費し、未測定のv2をactiveにした。

特徴量はハッシュ化した文字n-gramと語トークンで、学習は固定seedの多クラス線形分類（平均化パーセプトロン）で行う。

学習は2つのモデルを作る。**測定モデル**はRouteごとに約20%（5件以上のRouteのみ、決定的順序）のホールドアウトを保持し、`validation_accuracy`を正直に推定するためだけに使う。**デプロイモデル**は承認データ全件で学習して保存する（小規模コーパスでは18%を捨てる損失が大きいため）。`metrics.deployed_self_accuracy`は全件学習の自己一致で、構成上ほぼ1.0になる。

### Route境界カリキュラム

`v0.1.1`では、単純な同義文追加ではなく、混同しやすい意図を対照させた24件を独立した出典として追加した。

```powershell
python -m pattern_learning seed-boundaries
$env:PYTHONPATH="."; python build\approve_boundary_curriculum.py
python -m pattern_learning train --epochs 40
```

対象境界:

- `explore` vs `respond`: 代替案を広げる指示と、一つの回答を求める指示
- `clarify` vs `verify`: 不足情報を質問する指示と、与えられた内容を検証する指示
- `explore` vs `build`: 候補を広げる指示と、採用案の実行計画を作る指示

承認後の状態は166 patterns（build:13, clarify:19, explore:31, respond:78, summarize:9, verify:16）。

### Route境界カリキュラム v2 Round 1

現行精度監査で混同が確認された4境界について、48件・24対照ペアの候補を追加できる。

```powershell
python -m pattern_learning seed-boundaries-v2
python -m pattern_learning serve
```

対象境界:

- `explore` vs `respond`
- `build` vs `respond`
- `clarify` vs `verify`
- `explore` vs `build`

各ペアは話題・言語・難度を揃え、意図だけを変えている。同じペアは
`thought_form.contrast_group`を共有する。将来の学習・評価分割では、同じ
`contrast_group`を必ず同じ側へ置き、片方を学習、片方を評価に分離しない。

このデータはRoute仕様から独立に作例したAI支援のsynthetic promptであり、
他モデルの回答、logit、hidden reasoning、外部文章のコピーを教師信号にしていない。
一般的な意味でのteacher-student蒸留ではないが、AI支援作例であることは
`ai_assisted_authoring=true`として出典メタデータに残す。

投入後も全件`pending`である。人間がRoute・operator・自然さを確認して承認するまで
`patterns`と学習集合には入らず、モデル再学習も起動しない。Round 1は明示的な
境界基準例であり、否定表現、暗黙意図、複合依頼、長文はRound 2へ分離する。

詳細は`docs/PATTERN_BOUNDARY_CURRICULUM_v2.md`を参照する。

## 確信度の較正とclarifyフォールバック

ルーターは線形分類であり意味理解ではないため、確信度（softmax最大値）が低い入力では予測が不安定になる。学習時に**反復stratified k-fold**（5反復×5fold。各パターンは必ず自分を学習していないモデルで採点）で、確信度と正誤の関係を測り、信頼性表（histogram）を作る。隣接違反プール法（isotonic/PAVA）で較正確率を単調化する。

反復で得る点数は独立サンプル数ではない。166 patternsの場合は830予測点だが、実質的な元データは166件である。したがって`kfold_accuracy`は反復CV推定値であり、「830件の真の般化精度」とは表現しない。

そのうえで、**較正後の実精度が0.5を下回る確信度帯**（=rawルーターが正しいより誤る方が多い領域）の上端を`decision_threshold`候補とする。閾値はハードコードせず毎回データから再計算され、モデルの`metadata.calibration`に信頼性表ごと記録される。聞き返しが実際に安全かどうかは、この分類精度だけでは証明せず、v0.2の人間評価またはコスト評価へ分離する。

`predict`はこの閾値を適用する。観測可能性のため、生の`route`（argmax）は常に残し、フォールバック適用後を`effective_route`として併記する。

- `route`: 生のargmaxルート
- `effective_route`: `confidence <= decision_threshold`かつ生ルートが`clarify`以外なら`clarify`、それ以外は`route`
- `low_confidence`: フォールバックが発火したか
- `calibrated_confidence`: 信頼性表から引いた較正済みの正答確率

`v0.1.1`では較正ビンを「各ビンの最大値を上限境界」として検索し、観測min/max間の数値ギャップでも必ず較正値を返す。

clarifyへのフォールバックは安全行動であり、正しいRouteへ修正したとは数えない。較正メタデータは次を分離して記録する。

- `coverage`: フォールバックせずRouteを維持した割合
- `selective_accuracy`: Routeを維持した予測だけのraw正答率
- `abstention_rate`: clarifyへ棄権した割合
- `abstained_raw_correct` / `abstained_raw_wrong`: 棄権前のraw予測内訳

承認データが`CALIBRATION_MIN_SAMPLES`（30件）未満のときは較正を行わず、`confidence_calibrated`は`false`、`predict`はフォールバックなしで素通りする。

## 固定回帰評価

`tests/fixtures/pattern_router_cases_v1.json`の25件を固定し、次で評価する。

```powershell
$env:PYTHONPATH="."; python build\router_eval.py
```

出力項目はraw accuracy、effective label accuracy、coverage、selective accuracy、macro-F1、Route別precision/recall/F1、confusion matrix。`effective_label_accuracy`は観測用であり、フォールバックの安全性評価ではない。

2026-06-11の再学習結果:

- raw accuracy: 25/25
- effective label accuracy: 23/25
- coverage: 0.92
- selective accuracy: 1.00
- 反復CV accuracy: 0.768675
- 測定用holdout accuracy: 0.866667

この25件は改善過程で結果を参照しているため、独立した最終テストではなく**回帰fixture**である。未見性能の推定はv0.2でsealed final testを別途作成する。

学習対象:

- ユーザーが承認した入力
- 修正済みRoute
- 修正済み思考演算子
- 評価値

学習対象外:

- 未評価・却下候補
- Wikipedia記事全文
- クラウドLLMの応答
- ユーザーの評価メモ

## SQLite

主要テーブル:

- `sources`: 出典・版・ライセンス
- `candidates`: 評価待ち候補
- `reviews`: 承認・却下・修正履歴
- `patterns`: 承認済み学習資産
- `training_runs`: モデル生成履歴

## 運用境界

- 取得と学習は自動実行しない。
- Pattern候補をWikipedia上の正解とは扱わない。
- 高リスク分野の内容は別の一次資料で確認する。
- 公開・配布時は保存した出典情報を利用してライセンス要件を確認する。
- 学習前後のモデルJSONを版管理し、ロールバック可能にする。

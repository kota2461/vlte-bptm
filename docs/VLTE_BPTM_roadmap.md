# VLTE-BPTM ロードマップ

更新日: 2026-06-12

## 2026-06-12 Architecture Split

生プロンプト理解、処理予算決定、Core実行、LLM回答生成を一つのRouterへ
集約しない。今後は次の3トラックを独立評価する。

1. Pattern Language Model: 生文から最小意味信号を抽出
2. Processing Router: Semantic Packetから処理経路と予算を決定
3. LLM Integration: 既存Core / Runtime / LLM / toolを接続して全体評価

正本:

- `SEMANTIC_ROUTING_ARCHITECTURE_v0_1.md`
- `PATTERN_LANGUAGE_MODEL_roadmap.md`
- `PROCESSING_ROUTER_roadmap.md`
- `LLM_INTEGRATION_roadmap.md`

現行254件Pattern RouterはLegacy Intent Classifier兼比較baselineとして保持し、
新しいProcessing Routerへ役割変更しない。Horizontal / Vertical / Hybridは
既存Coreを再利用する。

設計開始前の完全スナップショット:
`archive/2026-06-12_pre-semantic-router-redesign`

現在の実装地点:

- `semantic-packet.v1`: 厳密schema、fixture、privacy境界を実装
- `processing-plan.v1`: 厳密schema、fixture、決定的policyを実装
- Processing Routerはvalidated Packetのみを受け、raw promptを拒否
- 次はPattern Language Model benchmarkとShadow Bridge

## v1.0a: Minimal Observable Core

Status: 完了

- Thought CodeとPattern Channelを分離
- 16×16を非意味座標の活性バッファ化
- Horizontal Unit選択
- 固定inhibition matrix
- threshold profileと必須ログ
- action vector / llm order JSON
- schema version / pipeline version / stage trace
- 代表入力fixture

完了条件: 一入力の全処理段階をJSONで追跡でき、単体テストで再現できる。

## v1.1: Contract Stabilization

Status: 完了（2026-06-11）

- 正式なPattern Unit一覧を確定 ✅
  `pattern-unit-catalog.v1`として順序・label・keywords・action weights・
  channel schemaを外部化し、独立fixtureで固定
- Unit Typeごとのchannel schemaを確定 ✅ 完了（2026-06-11。
  `pattern-channel-schemas.v1`、Unit-local prototype affinityとして定義。
  個別indexへ意味を固定せず、設定・生成pattern・独立fixtureを完全照合）
- action vectorとllm orderのschemaを版管理 ✅
  `vlte-bptm.action-vector.v1` / `vlte-bptm.llm-order.v1`
- inhibition matrixを設定ファイル化 ✅ 完了（2026-06-11。
  `thought_core/config/inhibition_matrix.json` へ外部化、`load_inhibition_matrix()`
  で読み込み・検証。`v1.0a-p1`で未知Unit、boolean、非有限値、自己抑制も拒否。
  根拠は同ファイル `rationale` と仕様§6の表に記載）
- 代表入力fixtureを作成 ✅
  v1.0a経路fixtureに加え、channel schema・Unit catalog・出力schemaの
  v1.1独立fixtureを追加

完了条件: Unit選択・抑制・action生成の期待値をレビュー可能にする。

完了結果: pipeline version `1.1`、pipeline schemaは後方互換の
`vlte-bptm.pipeline.v1`を維持。73 tests passed。

## Pattern Router v0.1.1: Calibration Safety Patch

Status: 完了（2026-06-11）

- 較正ビン間の数値ギャップを上限境界方式で解消
- clarifyフォールバックを正答化として数えず、coverage / selective accuracy /
  abstention rateへ分離
- `explore/respond`、`clarify/verify`、`explore/build`の対照カリキュラム24件を
  人間承認フローで追加
- 承認済み166 patternsで全件デプロイモデルを再学習
- 25件の固定回帰fixtureとRoute別precision/recall/F1、confusion matrixを追加
- 62 tests passed、固定回帰raw 25/25

注意: 固定25件は改善中に結果を参照したため、独立した最終テストではない。

## Pattern Router v0.2.3: Deployment Contract

Status: 完了（2026-06-12）

- approved 254 patternsで候補を学習・昇格
- frozen regression 25/25
- Foundation Anchor Suite 58/58
- fixture SHA registry、最低件数、candidate / DB / model hash記録
- train / promote分離、atomic置換、旧モデルarchive、rollback
- validation holdout構成変化だけを対象とする証拠付きack
- sealed v1は現行11/22、候補17/22を記録してconsumed
- 未測定sealed v2をactive successorとして登録
- 187 tests passed

このモデルは`Raw Prompt -> Route` baselineであり、今後のPattern Language
ModelやProcessing Routerと同一視しない。

## Pattern Router Boundary Curriculum v2 Round 1

Status: 履歴（2026-06-11時点。後続レビューと追加batchを経て254件へ反映済み）

- 精度監査で弱かった4境界へ48件・24対照ペアを追加
- 日本語32件、英語16件
- 同一話題で意図だけを変えた`contrast_group`を付与
- Route仕様からのAI支援作例で、teacher回答・logit・hidden reasoning・
  外部文章コピーは不使用
- 自動承認・自動学習を行わず、全件pendingで投入した
- 投入時点では166 patternsとデプロイ済みモデルを変更しなかった

当時の次段階:

- Round 1を人間レビューし、誤ラベル・不自然な文・operator過不足を修正
- grouped split実装後に、同一`contrast_group`を同じ分割へ固定
- Round 2で否定表現、暗黙意図、複合依頼、長文、日英混在を追加
- sealed評価セットは学習候補と別作成者・別出典・別版で作成

上記は投入時点の計画記録である。現在は人間レビュー、後続batch、
v0.2.3ゲートを経てapproved 254 patternsがデプロイ済みである。

## Pattern Router v0.2: Evaluation Contract

Status: 部分実装

実装済み:

- train / gate / promote / rollback
- fixture registryとhash integrity
- Foundation / frozen regression契約
- sealed fixtureの消費・交代
- v0.2.3 improvement acknowledgment

未完:

- 学習・モデル選択・較正・sealed final testを4分割
- 同一テンプレート、同一出典、近似文を同じfoldへ束ねるgrouped CV
- 各Route最低30件、主要境界ペア最低20件の独立評価セット
- 文字n-gram近似重複を検出し、train/test漏洩をレポート
- raw accuracyに加えmacro-F1、balanced accuracy、ECE、Brier scoreを正式指標化
- フォールバックは人間評価または明示コスト行列で評価し、
  「聞き返しが適切だった割合」を別ラベルとして収集
- 評価fixtureの版、作成者、凍結日、学習への不使用をメタデータ化

完了条件: sealed final testを一度だけ開封し、再調整前の性能を記録できる。

注意: active sealed v2はLegacy Pattern Routerの評価用であり、
Semantic Routing新設計の評価へ流用しない。

## Pattern Router v0.3: Uncertainty and Committee

Status: 将来

- softmax最大値とtop1-top2 marginを同じsealed calibration setで比較
- 空文字、記号列、日英混在、未知分野、複合意図のOOD評価セット
- 別seed・別ハッシュ・別n-gram部分集合による3モデル合議
- 合議度別のaccuracy / coverage / calibrationを集計
- Route別または境界別の閾値を、十分な評価件数がある場合だけ検討
- 合議結果を疑似ラベルや自動学習へ使用しない

完了条件: 単一softmaxより高いselective accuracyを、同じcoverage条件で示す。

## v1.2: Observation and Horizontal Mesh

Status: 完了（2026-06-11）

- active bit数・組み合わせ・頻度分布を集計 ✅
  `vlte-bptm.observation-report.v1`の非永続レポートを実装
- selected unit分布を集計 ✅
  Unit頻度・組合せ・選択数・mode分布を集計
- threshold profileを手動評価で調整 ✅
  全profile比較レポートを実装。代表8件ではmode差がなく、調整根拠不足のため
  現値を維持する判断を記録。独立評価セット取得後の再判断は後続評価へ分離
- Horizontal Unit Meshの投票・優先度契約を正式化 ✅
  `horizontal-unit-mesh.v1`としてUnit contribution、軸vote、control/fallback
  優先度、勝者、非選択理由を観測可能化。旧mode選択と完全互換
- privacy-minimized observation storeを実装 ✅
  明示opt-in、UTC日次immutable bucket、最低8件、3件未満cell抑制、
  exact件数・rate・Unit組合せ非保存、30日保持、自動・明示削除を契約化
- 座標意味は観測根拠が得られた場合だけ実験対象にする
- **合議による確信度推定（committee agreement）**: 多様化した複数ユニット
  （別seed・別ハッシュ・別n-gram部分集合）で同一入力を回し、一致度
  （3/3・2/3・1/3）を確信度信号とする。合議度別に精度・閾値を集計し、
  既存の較正（k-fold信頼性表・`decision_threshold`・clarifyフォールバック）
  を合議度で層別化して拡張する。単一モデルのsoftmax確信度が~0.19の平坦帯に
  潰れる弱点（精度ブレ）への対策。
  - 境界: 合議は**確信度・観測・フォールバックの信号**としてのみ用いる。
    モデル同士は特徴量・学習データを共有し相関した誤りで一致しうるため、
    **合議≠正答**。合議で得た回答を新しい学習ラベルへ昇格させること
    （疑似ラベル・自己学習）は「自動学習禁止」境界に抵触するため行わない。
    学習対象は人間が承認したPattern DBエントリのみという原則を維持する。

Pattern Router側の具体的な実験契約は`Pattern Router v0.3`で先行定義し、
Core v1.2では観測結果の取り込み方だけを扱う。

完了条件: 自動学習なしで再現可能な評価レポートを生成できる。

完了結果: raw inputとLLM出力を保持せずに再現可能な集計レポートを生成し、
privacy policyで縮約した日次aggregateだけを明示的にローカル保存できる。
Horizontal Mesh契約も完了。独立データに基づく再評価は後続評価へ分離する。

## v1.3: Vertical Unit Stack

Status: 完了（2026-06-11）

- `input_dependencies`を設定化 ✅
- Unit別`output_contract`をschema検証 ✅
- `max_depth`、循環・未知Unit・self dependency拒否 ✅
- `build`前へ中間verify Unitを挿入 ✅
- 未解決clarification、verification failure、未検証前提を検出して停止 ✅
- Unit output再投入によるstateless逐次dispatch ✅
- Horizontal既定経路の後方互換を維持 ✅

完了条件: 下位Unit出力を前提として上位Unitを安全に逐次実行できる。

完了結果: Coreは意味内容を擬似生成せず、現在実行可能なUnitだけをdispatchし、
外部executor出力の契約通過後に次Unitへ進む。pipeline version `1.3`。

## v1.4: Hybrid Stack-Mesh

Status: 完了（2026-06-11）

- Horizontal候補からcontrol優先で重要枝を選択 ✅
- 依存候補score込みで重要Stackを優先 ✅
- 依存rootを重複起動せずStack output namespaceを分離 ✅
- 最大2 Stack、合計3 step、depth 2、1 dispatch/call ✅
- blocked primaryからcompleted alternativeへfallback ✅
- completed Stackを固定scoreでIntegrator選択 ✅
- 固定評価でbranch recall 0.60から1.00、全件budget準拠 ✅

完了条件: Horizontal onlyより有用であることを固定評価セットで確認する。

完了結果: 必要候補枝coverageという運用上の有用性は固定評価で改善した。
回答のsemantic quality、latency、費用改善は未証明でありv1.5へ分離する。

## v1.5: Runtime Evaluation and Executor Boundary

Status: 完了（2026-06-11）

- 外部executor adapterとcancel / wall-clock timeout契約 ✅
- retry、idempotency、resume境界 ✅
- Horizontal / Vertical / Hybridの回答品質blind評価 ✅
- latency、dispatch数、推定費用、fallback率 ✅
- Stack winnerと人間評価の一致率 ✅
- 実出力を自動学習へ使用しない評価保存契約 ✅

完了条件: 同じ固定入力と評価rubricで、Hybridの品質改善と追加費用を
Horizontal / Verticalと比較できる。

完了結果: 4件の参照fixtureで品質平均はHorizontal 3.75、Vertical 4.35、
Hybrid 4.70、平均costは1.0、2.0、2.5となった。runtime選択および
Hybrid Stack winnerと人間選好の一致率は0.75。これは評価計算契約の
固定結果であり、独立した本番品質の証明ではない。

## v1.6: Independent Runtime Study and Policy Calibration

Status: alpha実装完了 / 独立実測・policy承認待ち（2026-06-11）

- 独立blind collection schema・privacy契約 ✅
- 評価者間一致度、confidence interval、必要sample数 ✅
- quality / latency / cost / fallbackのPareto frontier ✅
- input class別のmode選択policy draft ✅
- 現行route精度の交差監査 ✅
- 実backendのtimeout / cancel / retry / idempotency検証 ⏳
- 独立評価者による実回答collection ⏳
- 人間review gateによるpolicy承認 ⏳

完了条件: 独立評価データにより、処理modeの選択条件を信頼区間つきで
説明でき、品質向上と追加費用の採用基準を人間がversioned policyとして承認できる。

現状結果: synthetic contract fixtureでは評価計算を検証できたが、
Vertical / Hybridの品質差95%区間は0を跨ぐ。各input classは1件のみであり、
production evidenceではない。policyは`draft`、active modeはHorizontalのまま。

精度監査ではCore 8件回帰は8/8だが別境界fixtureでは9/25、
Pattern Routerは25件回帰25/25だがCore fixtureでは5/8。回答本文の独立評価は0件。
CoreとPattern Routerの統合はgrouped / sealed route評価後に判断する。

## 保留

- Pattern Unitの学習更新
- success/failureによる自動priority更新
- 32×32以上への拡張
- 100×100マップ
- 完全自律学習

保留項目は、保存対象・評価方法・ロールバック条件が定義されるまで実装しない。

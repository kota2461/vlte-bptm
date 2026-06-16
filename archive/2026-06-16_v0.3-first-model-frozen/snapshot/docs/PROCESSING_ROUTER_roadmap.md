# Processing Router Roadmap

更新日: 2026-06-12

## Mission

検証済みSemantic Packetから、品質を守りながら処理費用を配分する。
生プロンプトの理解と回答生成は行わない。

## Router v0.0: Processing Plan Contract

Status: alpha実装完了

- `processing-plan.v1` schemaを実装
- `economy / standard / verified / deep / clarify`を固定
- Core mode、model class、tool、budget、fallback、reason codeを定義
- PacketからPlanへの決定表を文書化
- critical under-processingの定義を固定

完了条件:

- 同一Packetから常に同一Planが得られる
- 未知field、未知class、負の予算、上限超過を拒否する
- Router APIがraw promptを受け取らない

## Router v0.1: Deterministic Policy

Status: alpha実装完了

- 情報不足、検証要求、時点依存、risk、複合意図の優先順位を実装
- buildの未検証前提をVerticalへ送る
- 複数重要枝をHybridへ送る
- 低確信PacketをSemantic Adapter再解析へ戻す
- reason code付きdecision traceを出す
- Processing PlanからCore modeへ接続するshadow bridgeを実装
- Vertical時はPlanのprimary routeをrootへ固定

完了条件:

- frozen contract fixtureでcritical under-processing 0件
- 全Planがbudget上限を守る
- foundation policyをackで迂回できない
- `build + unverified`が`verify -> build`順になる

## Router v0.2: Cost Simulation

Status: planned

- model、tool、dispatch、tokenのnormalized tariffを設定化
- fake executorで全classの費用とlatencyを再現
- always-standard / always-deep / current routeとの比較
- unnecessary escalationとquality floorを集計

完了条件:

- 同じfixtureで品質制約と費用差を同時に表示できる
- economy選択が危険なケースを明示できる
- 費用削減を実LLMの事実として主張しない

## Router v0.3: Shadow Policy

Status: planned

- 実入力でPlanだけを生成し、現行処理は変更しない
- 選択予定model/tool/Core modeと実際の結果を比較
- 人間がunder-processing / over-processingを判定
- input class別のquality-cost confidence intervalを計算

完了条件:

- 独立評価者によるpolicy承認
- `economy`適用範囲がversioned policyとして固定
- rollback条件と監視指標が定義される

## Router v0.4: Guarded Control

Status: future

- 最初は低riskな`economy`だけ実制御
- `verified`と`deep`はshadowを継続
- 品質基準割れで即座に現行policyへrollback
- Failure Memory / Guardを別レーンで追加

学習型policyは、十分な独立評価データと人間承認が得られるまで導入しない。

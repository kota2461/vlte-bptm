# VLTE-BPTM v1.6 Alpha 実装状況

更新日: 2026-06-11

## Status

`v1.0a Minimal Observable Core`: 実装済み

`v1.1 Contract Stabilization`: 実装済み

`v1.2 Observation and Horizontal Mesh`: 実装済み

`v1.3 Vertical Unit Stack`: 実装済み

`v1.4 Hybrid Stack-Mesh`: 実装済み

`v1.5 Runtime Evaluation and Executor Boundary`: 実装済み

`v1.6 Independent Runtime Study and Policy Calibration`: 評価基盤実装済み /
独立実測・policy承認待ち

## 実装済み

- unsigned 64bit Thought Code
- threshold profileとdensity guard
- `[64,16,16]` sparse activation buffer
- Thought CodeとPattern Channelの責務分離
- Unit固有channel schema
- Horizontal Unit Selector
- 設定ファイル化した固定inhibition matrix（厳密検証つき）
- Action Vector
- LLM Order
- 必須メトリクス
- schema version / pipeline version
- Horizontal 7段階 / Vertical・Hybrid 8段階の処理trace
- CLI / Python API
- 代表入力fixture
- `pattern-channel-schemas.v1`
- `pattern-unit-catalog.v1`
- `vlte-bptm.action-vector.v1`
- `vlte-bptm.llm-order.v1`
- v1.1契約fixture
- 非永続のv1.2観測集計レポート
- `horizontal-unit-mesh.v1`
- `observation-privacy-policy.v1`
- privacy-minimized local SQLite observation store
- `vertical-unit-stack.v1`
- Unit別vertical output contract
- dependency graph / max depth / cycle validation
- verify gate / unverified assumption propagation stop
- stateless vertical output progression
- `hybrid-stack-mesh.v1`
- dependency coverage adjusted candidate selection
- 2 Stack / 3 step / depth 2 budget
- Stack別output namespace
- completed alternative fallback / Stack Integrator
- fixed branch coverage evaluation
- `runtime-executor-policy.v1`
- external `ExecutorAdapter`
- wall-clock timeout / cancel notification
- retry / idempotency / resume checkpoint
- private Unit output namespace outside session JSON
- cumulative latency / dispatch / attempt / estimated cost metrics
- `runtime-evaluation-fixture.v1`
- blind quality rubric and operational trade-off report
- runtime selection / Hybrid winner human agreement
- `independent-runtime-study-policy.v1`
- independent blind study privacy / consent contract
- case bootstrap confidence interval
- quadratic weighted kappa / preference agreement
- quality-cost Pareto frontier
- draft runtime selection policy with mandatory human review
- current response accuracy cross-audit

## 実行経路

```text
thought_core.pipeline.process
  -> encoder.encode
  -> selector.select_units
  -> integrator.integrate
  -> mesh.build_horizontal_mesh
  -> optional vertical_stack.build_vertical_stack
  -> optional vertical_stack.evaluate_vertical_outputs
  -> optional hybrid.build_hybrid_stack_mesh
  -> ActionVector
  -> order_builder.build_llm_order

thought_core.runtime.run_with_executor
  -> pipeline.process
  -> ExecutorAdapter
  -> private RuntimeCheckpoint
  -> pipeline.process
```

CLIの`thought_core.demo`は上記APIの表示層であり、計算本体を持たない。

## 受け入れfixture

次の経路を`tests/fixtures/v1_0a_cases.json`で固定する。

- light chat
- implementation design
- deep verification
- summary
- exploration
- clarification
- empty input

## 未実装

- 独立評価データに基づくthreshold再調整
- 観測bucket間の統計比較・異常baseline
- ユーザー修正UI
- 独立した複数評価者による実出力blind study
- 実backendでのtimeout / cancel / retry検証
- approved quality-cost選択policy
- grouped / sealed route評価とCore / Pattern Router統合判断
- 自動学習・自動更新

未実装項目は`docs/VLTE_BPTM_roadmap.md`の後続版へ分離している。

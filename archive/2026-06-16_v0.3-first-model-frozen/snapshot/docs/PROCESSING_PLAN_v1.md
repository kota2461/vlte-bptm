# Processing Plan v1

更新日: 2026-06-12

schema version: `processing-plan.v1`

実装: `semantic_routing/processing_plan.py`

fixture: `tests/fixtures/processing_plan_v1.json`

## 目的

検証済みSemantic Packetから、処理経路と計算予算を決定する。Processing
Router APIは生プロンプトを受け取らない。

## 必須field

```text
schema_version
primary_route
processing_class
core_mode
model_class
tools
budgets
fallback
reason_codes
```

## 処理クラス

| Class | Core | Model | v1制約 |
| --- | --- | --- | --- |
| `economy` | horizontal | small | toolなし、1 dispatch |
| `standard` | horizontal / vertical | standard | 通常経路 |
| `verified` | vertical | standard / large | 2 dispatch以上 |
| `deep` | hybrid | standard / large | 2 dispatch以上 |
| `clarify` | horizontal | small | toolなし、1 dispatch |

## Budget

```text
max_dispatches: 1..32
max_output_tokens: 1..32768
timeout_ms: 100..120000
estimated_cost_units: 0.0..100.0
```

## v1決定順序

1. unknown、conflict、低confidence、必須情報不足 -> `clarify`
2. verify、時点依存、未検証claim、高risk -> `verified`
3. 複合intent、explore、compare -> `deep`
4. 低riskの単純respond / explain / summarize -> `economy`
5. その他 -> `standard`

時点依存またはsearch operationでは`web_search`、calculate operationでは
`calculator`を選ぶ。全判断に重複のない`reason_codes`を残す。

## Safety Boundary

- raw promptを渡すとTypeError
- schema違反PacketからPlanを生成しない
- 処理クラスとCore/model/budgetの不整合を拒否
- v1は決定表であり、出力から自動学習しない

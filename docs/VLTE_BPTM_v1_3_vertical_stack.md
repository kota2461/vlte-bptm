# VLTE-BPTM v1.3 Vertical Unit Stack

更新日: 2026-06-11

## 目的

下位Unitの出力契約が満たされた場合だけ上位Unitをdispatchし、
検証失敗・未解決情報・未検証前提を後段へ伝播させない。

stack schemaは`vertical-unit-stack.v1`、
Unit output envelopeはUnit別の`vertical-output.<unit>.v1`、
進捗は`vertical-stack-progress.v1`。

設定は`thought_core/config/vertical_stack.json`。

## Core境界

CoreはUnitの意味内容を生成しない。次を担当する。

1. dependency graphを検証して実行順序を作る
2. 現在実行できるUnitを一つだけLLM Orderへdispatchする
3. 外部executorから再投入されたUnit outputをschema検証する
4. contract failure時に後続Unitを停止する

外部executorはLLMや人間を含み得るが、Coreは出力内容を自動学習へ使用しない。

## Dependency

v1.3の固定依存:

```text
verify -> build
```

`build`以外のUnitは単一step。`build`はselected Unitに`verify`がなくても
verification gateを挿入する。最大深度は4。

設定load時に次を拒否する。

- 循環依存
- 未知Unit
- self dependency
- `max_depth`超過
- output contract欠落
- verifierを経由しないverification target

## Output Contract

全Unit共通:

```text
schema_version: string
unit_id: string
status: completed | blocked
assumptions: string[]
evidence: string[]
```

Unit別:

| Unit | Required fields |
| --- | --- |
| verify | `verified:boolean`, `verified_assumptions:string[]`, `risk_flags:string[]` |
| build | `implementation_plan:object` |
| explore | `hypotheses:string[]` |
| summarize | `summary:string` |
| clarify | `needs_clarification:boolean`, `questions:string[]` |
| respond | `response:string` |

`build.assumptions`は`verify.verified_assumptions`の部分集合でなければならない。
出力fieldは契約との完全一致を要求し、追加fieldを拒否する。すべてのarrayは
string要素だけを許可する。

## Stateless Progression

初回:

```python
process(text, processing_mode="vertical")
```

`build`入力なら`llm_order.mode`は`verify`となり、
`vertical_stack.progress.next_unit_id`も`verify`となる。

verify出力を再投入:

```python
process(
    text,
    processing_mode="vertical",
    vertical_outputs={"verify": verify_output},
)
```

契約を通過すると次のmodeは`build`になる。各呼び出しは同じ入力と、
それまでのUnit output全体を渡すstateless APIである。
再投入されたUnit output本文はPipeline JSONへechoせず、進捗・次Unit・
停止理由だけを出力する。

CLI:

```powershell
python -m thought_core --json `
  --processing-mode vertical `
  "この機能を実装してください"

python -m thought_core --json `
  --processing-mode vertical `
  --vertical-outputs-file build\vertical_outputs.json `
  "この機能を実装してください"
```

## Stop Reasons

- `unresolved_clarification`
- `missing_dependency_output`
- `invalid_output_contract`
- `dependency_failed`
- `verification_failed`
- `unverified_assumption`

`missing_dependency_output`はwaiting状態を表す。他は後続dispatchを停止する。

## Backward Compatibility

既定は`processing_mode="horizontal"`。

- Horizontal JSONに`vertical_stack`を追加しない
- Horizontal traceは従来の7段階
- Vertical時だけ`vertical_stack`と8段階traceを返す
- pipeline schemaは`vlte-bptm.pipeline.v1`を維持
- pipeline versionは`1.3`

独立fixtureは`tests/fixtures/v1_3_vertical_stack.json`。

## 制限

- 外部executorが実際にstepを順番に呼んだ時刻までは証明しない
- verifyの正しさそのものは保証しない
- 複数Stack比較・予算配分・重要枝選択はv1.4 Hybridで扱う
- Unit outputを保存・自動学習・疑似ラベル化しない

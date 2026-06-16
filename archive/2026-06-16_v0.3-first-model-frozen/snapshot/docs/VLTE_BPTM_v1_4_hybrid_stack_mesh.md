# VLTE-BPTM v1.4 Hybrid Stack-Mesh

更新日: 2026-06-11

## 目的

Horizontal Meshで得た複数候補のうち、予算内の重要枝だけを独立した
Vertical Stackとして深掘りし、成功したStackをIntegratorで選択する。

schema versionは`hybrid-stack-mesh.v1`。
設定は`thought_core/config/hybrid_stack_mesh.json`。

## 候補選択

1. control Unitが最低score 0.12以上ならcontrol候補だけを使う
2. control候補がなければ`respond`をfallback候補にする
3. root scoreが最高root scoreの0.75以上の候補を対象にする
4. 選択順位はrootのintegrated scoreと、同じStackが覆う依存候補scoreの合計
5. 既に選択したStackの依存に含まれるrootは重複起動しない

例:

```text
build stack = verify -> build
```

`verify`と`build`が同時候補なら、`build` Stackのselection scoreは両者の
score合計となる。単独`verify` Stackは`covered_by_selected_dependency`。

## 予算

```text
max_stacks = 2
max_total_steps = 3
max_stack_depth = 2
max_dispatches_per_call = 1
```

Coreは壁時計を保持しないstateless APIであるため、時間timeoutは実装しない。
Coreは最大3 stepで実行量を決定的に停止し、実時間timeoutとcancelは
外部executorの責任とする。

## Output Namespace

Stack間で前提やverify結果を共有しない。

```json
{
  "build": {
    "verify": {"...": "..."},
    "build": {"...": "..."}
  },
  "summarize": {
    "summarize": {"...": "..."}
  }
}
```

API:

```python
process(
    text,
    processing_mode="hybrid",
    hybrid_outputs=outputs,
)
```

CLI:

```powershell
python -m thought_core --json `
  --processing-mode hybrid `
  "設計案を比較して要約してください"

python -m thought_core --json `
  --processing-mode hybrid `
  --hybrid-outputs-file build\hybrid_outputs.json `
  "設計案を比較して要約してください"
```

再投入されたUnit output本文はPipeline JSONへechoしない。

## Scheduler

selection score、root score、固定Unit priorityの順にStackを並べる。
各呼び出しで`next_dispatch`の1 Unitだけをdispatchする。

```json
{
  "next_dispatch": {
    "stack_id": "build",
    "unit_id": "verify"
  }
}
```

primary Stackがblockedになっても、waiting Stackがあれば次Stackへ進む。

## Integrator

全Stackがwaitingでなくなった時点で、completed Stackのうち
candidate scoreが最高のStackをwinnerにする。

- completed Stackあり: `status=completed`
- 全Stack blocked: `status=fallback`
- unresolved clarification: `clarify`
- contract / dependency / verification failure: `verify`
- eligible候補なし: Horizontal winner mode

blocked primaryよりcompleted alternativeを優先する。

## 固定評価

fixture: `tests/fixtures/v1_4_hybrid_evaluation.json`

3件、必要候補枝5本:

| Metric | Result |
| --- | ---: |
| Horizontal branch recall | 0.60 |
| Hybrid branch recall | 1.00 |
| Budget compliance | 1.00 |

これは固定された必要候補枝を予算内で保持できるかの評価である。
最終回答の正確性、有用性、latency、費用改善を証明するものではない。

## 後方互換

- 既定は`horizontal`
- `vertical`契約を変更しない
- Horizontal JSONにHybrid fieldを追加しない
- Hybrid時だけ`hybrid_stack_mesh`と8段階traceを出力
- pipeline schemaは`vlte-bptm.pipeline.v1`
- pipeline versionは`1.4`

## 制限

- 外部executorをCoreから呼ばない
- 壁時計timeout、cancel、retryを管理しない
- Stack outputを保存・自動学習・疑似ラベル化しない
- 複数Stackの意味内容をCore自身が比較しない
- semantic quality評価はv1.5へ分離する

# VLTE-BPTM v1.5 Runtime Evaluation and Executor Boundary

更新日: 2026-06-11

## 目的

v1.5は、statelessなCoreを変更せず、その外側に外部Executorの実行境界を
追加する。Vertical / Hybridの逐次dispatchを実時間で管理し、同じ評価形式で
Horizontal / Vertical / Hybridの品質と運用費用を比較できるようにする。

## 実行境界

```text
Core process()
  -> next dispatch
  -> Runtime Executor
  -> external adapter
  -> private checkpoint
  -> Core process()
```

`thought_core.runtime.run_with_executor()`が実行ループを担当する。
外部LLMやローカルモデルの実装は`ExecutorAdapter`へ閉じ込め、Coreは直接呼ばない。

主なschema:

- `runtime-executor-policy.v1`
- `runtime-executor-request.v1`
- `runtime-checkpoint.v1`
- `runtime-session.v1`

## Executor Policy

既定値は`thought_core/config/runtime_executor.json`に置く。

```text
timeout_ms = 5000
poll_interval_ms = 10
max_attempts = 2
max_dispatches = 4
retry_on = retryable_error, timeout
estimated_cost_units_per_attempt = 1.0
```

未知field、非有限値、5回を超えるretry、32回を超えるdispatchを拒否する。

## RetryとIdempotency

論理dispatchごとに次の情報からidempotency keyを生成する。

```text
run_id
processing_mode
dispatch_index
stack_id
unit_id
```

同じdispatchのretryではidempotency keyを変更しない。attemptごとの
`execution_id`だけを変更する。adapter側は同じidempotency keyに対する
重複課金・重複副作用を抑止する責任を持つ。

retry対象は明示された`retryable_error`と`timeout`だけである。
未知例外、永久エラー、非object出力はretryしない。

## TimeoutとCancel

Runtimeはwall-clock deadlineまでadapterの完了を監視する。timeoutまたは
外部cancelを検出した場合は`adapter.cancel(execution_id)`を呼び、待機を終了する。

Python thread自体を安全に強制終了することはできないため、backend処理の停止保証には
adapterがcancel通知を実際のAPI cancellationへ接続する必要がある。

## Resume

`RuntimeCheckpoint`は次を保持する。

- `run_id`
- inputのSHA-256 digest
- processing mode
- 完了済みUnit出力
- attempt数と実行記録
- 累積elapsed time

resume時はinput digestとprocessing modeを照合し、完了済みUnitを再dispatchしない。
異なる入力やmodeへのcheckpoint流用は拒否する。

Unit出力本文は`RuntimeSession.as_dict()`へ含めない。resume用出力はcheckpoint内部に
のみ保持し、`checkpoint.as_dict(include_outputs=True)`を明示した場合だけ取り出せる。
この明示出力は機密データとして呼出側が保護する。

## Terminal Status

- `completed`: 必要なdispatchがすべて契約を通過
- `fallback`: Unit契約、verification、dependencyなどにより安全経路へ停止
- `failed`: timeout、永久エラー、retry / dispatch予算超過
- `cancelled`: 外部cancelを検出

## Blind Runtime Evaluation

`thought_core.runtime_evaluation`は回答本文を保存・自動採点しない。
人間が候補のmodeを知らない状態で入力した次の5軸scoreだけを集計する。

- correctness
- relevance
- completeness
- assumption control
- clarity

候補scoreとmode対応表はfixture内で別fieldに分離する。保存する運用値は次の通り。

- latency
- dispatch count
- normalized estimated cost
- fallback
- runtime selectionと人間選好の一致
- Hybrid Stack winnerと人間選好の一致

未知fieldや候補内のmode fieldを拒否する。raw outputは評価fixtureとreportへ保存せず、
評価結果を自動学習やpriority更新へ使用しない。

## 参照Fixture

`tests/fixtures/v1_5_runtime_evaluation.json`は評価計算を固定する4件の参照fixtureである。

| Mode | Quality | Latency ms | Dispatch | Cost | Fallback |
| --- | ---: | ---: | ---: | ---: | ---: |
| Horizontal | 3.75 | 98.75 | 1.0 | 1.0 | 0.25 |
| Vertical | 4.35 | 178.75 | 2.0 | 2.0 | 0.00 |
| Hybrid | 4.70 | 225.00 | 2.5 | 2.5 | 0.00 |

runtime selectionと人間選好の一致率、Hybrid Stack winnerと人間選好の一致率は
ともに`0.75`である。

このfixtureは集計契約とtrade-off表示のテストであり、独立した本番品質の証拠ではない。
実際の採用判断には、出力生成者と独立した複数評価者によるblind測定が必要である。

## 実行

```powershell
python -m thought_core.runtime_evaluation `
  --input-file tests\fixtures\v1_5_runtime_evaluation.json
```

Python API:

```python
from thought_core.runtime import run_with_executor

session = run_with_executor(
    "この機能を実装してください",
    "vertical",
    adapter,
)
print(session.as_dict())
```

## 次版

v1.6では独立したblind評価収集、複数評価者の一致度、信頼区間、
quality-cost frontier、Runtime選択policyの校正を行う。

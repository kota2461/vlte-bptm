# VLTE-BPTM v1.0a 実装設計

更新日: 2026-06-11

## 境界

v1.0aは学習モデルではなく、観測可能なルーティング・統合パイプラインである。

```text
input
  -> routing intensities
  -> threshold profile
  -> 64bit Thought Code / active_bits
  -> Horizontal Unit Selector
  -> inhibition Integrator
  -> Horizontal Unit Mesh
  -> optional Vertical Unit Stack or Hybrid Stack-Mesh
  -> action_vector
  -> llm_order
  -> optional external Runtime Executor
```

## Thought Code

- unsigned 64bit
- 外部ルーティングキー
- 同一入力・同一profileに対して決定的
- bit位置へ思考内容そのものを固定しない
- profileごとのthresholdとdensity guardで疎密を制御

## Pattern Unit

標準shapeは`[C,H,W]`、v1標準値は`[64,16,16]`。

- `C`: Unit固有feature channel
- `H×W`: 非意味座標の活性バッファ
- `channel_schema`: Unit内部特徴空間の名前
- `channel_schema_version`: `pattern-channel-schemas.v1`
- `channel_semantics`: `unit_local_prototype_affinity_only`
- `prototype_channels`: feature affinity計算に使うUnit固有index集合
- `process_mode`: v1.0aでは`horizontal`

Thought CodeとPattern Unitは数値64を共有するが、データ型・責務・意味空間を共有しない。
個別channel indexにも概念名を割り当てない。schema IDはUnit全体の意図領域を
識別する名前であり、内部indexは決定的prototypeとのaffinity計算専用である。

## Selector

固定ヒューリスティック:

```text
0.40 * routing overlap
+ 0.20 * internal channel affinity
+ 0.40 * keyword match
```

`respond` Unitへ固定バイアス`+0.12`を加え、相対閾値`max(0.12, top * 0.68)`以上のUnitを上位から最大3件選択する。全Unitが閾値を下回る場合は最高スコアの1件、空入力は`clarify`単独を返す。これはアルゴリズム精度ではなく境界確認用の暫定実装である。

## Integrator

```text
inhibition_matrix[source][target] = coefficient
integrated(target) =
  max(0, raw(target) - sum(raw(source) * coefficient))
```

全targetをraw scoreから同時更新し、処理順による結果差を避ける。

設定ファイルの読込時は、schema、matrix型、既知Unit ID、有限係数、
boolean拒否、自己抑制禁止を検証する。`integrate()`へ直接渡す実験用行列と、
配布設定ファイルの契約検証は分け、設定ファイル側をより厳密に扱う。

## Threshold Profile

`light_v1`、`normal_v1`、`design_v1`、`deep_verify_v1`を持つ。自動選択は入力長と設計・検証markerによる固定ルールで行い、CLI/APIから上書きできる。

threshold適用後にdensity guardを使う理由は、初期のハッシュ由来routing intensityだけでは入力ごとのbit数分散が大きく、観測比較が不安定になるためである。

## 出力契約

JSONの必須キー:

```text
schema_version
pipeline_version
input
thought_code
active_bits
selected_units
horizontal_mesh
vertical_stack (vertical時のみ)
hybrid_stack_mesh (hybrid時のみ)
action_vector
action_vector_schema_version
llm_order
metrics
trace
diagnostics
```

`metrics`:

```json
{
  "active_bit_count": 24,
  "active_bit_density": 0.375,
  "selected_unit_count": 2,
  "threshold_profile": "deep_verify_v1"
}
```

## API境界

計算本体は`thought_core.pipeline.process`に置く。`thought_core.demo`はCLI表示だけを担当する。

```python
from thought_core import process

result = process("入力")
payload = result.as_dict()
```

出力schemaは`vlte-bptm.pipeline.v1`、実装版は`1.6`とする。
Action Vectorは`vlte-bptm.action-vector.v1`、LLM Orderは
`vlte-bptm.llm-order.v1`として個別に版管理する。

trace順序:

```text
input
active_bits
selected_units
inhibition_integration
horizontal_mesh
action_vector
llm_order
```

Vertical時は`horizontal_mesh`の後に`vertical_stack`を追加する。
初回は現在実行可能なUnitだけをLLM Orderへdispatchし、Unit outputを
`vertical_outputs`として再投入した次回呼び出しで後続Unitへ進む。

Hybrid時は`hybrid_stack_mesh`を追加し、候補score・依存coverage・
2 Stack / 3 step予算で複数Stackを計画する。`hybrid_outputs`は
Stack IDごとのnamespaceへ分離し、1回につき1 Unitだけdispatchする。

v1.5の`thought_core.runtime.run_with_executor`はCoreの外側で
`ExecutorAdapter`を呼び出す。timeout / cancel / retry / idempotency /
resumeを管理し、Unit出力本文は公開session JSONではなくprivate checkpointに
保持する。Coreのstatelessな検証責務は変更しない。

v1.6の`thought_core.independent_study`はraw input / outputを受け取らず、
pseudonymous reviewer scoreと運用値だけを集計する。policy候補は生成するが、
`runtime_selection_policy.json`の人間承認なしに実行経路へ反映しない。

`thought_core.accuracy_audit`はCore fixture、Pattern Router fixture、
学習DB完全一致、holdout / CV metadataを分離して報告する。

## 禁止境界

- クラウドLLM出力を教師データとして保存しない
- 自動学習・自動更新を行わない
- 100×100マップを作らない
- 完全文章再生成を学習しない
- 外部LLMを呼び出さない
- 外部executor、wall-clock timeout、cancel、retryをCoreへ混在させない
- runtime評価scoreを自動学習や自動priority更新へ使用しない

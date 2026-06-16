# VLTE-BPTM v1.0a 最小仕様・設計・ロードマップ

更新日: 2026-06-11

## 1. 設計ログ要約

VLTE-BPTM v1.0a は、入力を観測可能な処理段階へ分解し、Pattern Unit の選択結果から LLM 向け命令を組み立てる最小ルーティングコアである。

重要な分離は次の通り。

- `Thought Code`: 入力を決定的に変換した unsigned 64bit の外部ルーティングキー。思考内容そのものではない。
- `Pattern Unit`: `[C,H,W]` 形式の内部活性パターン。v1 標準は `[64,16,16]`。
- `C=64`: Pattern Unit 内部の feature channel 数。Thought Code の 64bit とは別の名前空間・責務を持つ。
- `16×16`: v1 では意味座標を持たない活性バッファ。セル位置へ概念や意味を固定しない。

最初に検証する処理経路は次の一方向パイプラインとする。

```text
input
  -> Thought Code / active_bits
  -> selected_units
  -> inhibition integration
  -> action_vector
  -> llm_order
```

## 2. レビュー対応表

| Review | Status | v1.0a 対応 |
| --- | --- | --- |
| 1. Pattern Unit の64軸が曖昧 | 解決済み / 採用済み | Thought Code 64bit と Pattern Unit `C=64` を型・フィールド・文書で分離する。 |
| 2. 16×16へ意味を固定しすぎている | 採用 | H×Wを非意味座標の活性バッファとする。意味座標化はv1.2以降の観測結果を条件に再検討する。 |
| 3. Integratorが個別if文へ増殖する | 採用 | 固定 `inhibition_matrix[source][target]` と同時更新式を使用する。 |
| 4. active_bits数の妥当性を検証できない | 採用 | 3指標と `threshold_profile` を記録し、密度ガード付き閾値プロファイルを選択可能にする。 |

Review 1の正式な回答:

```text
Thought Code 64bit:
  外部制御コード / Unit Selectorのルーティングキー / 入力状態の圧縮表現

Pattern Unit C=64:
  Unit内部のfeature channel数
  Unit Typeごとにchannel schemaを変えてよい
  v1では実装都合で幅を64に統一するが、共通の意味軸ではない
```

## 3. v1.0a の実装範囲

### 実装する

- 任意長文字列から決定的な 64bit Thought Code を生成する。
- Thought Code の active bit index を外部ルーティング特徴として公開する。
- 入力を独立した `[64,16,16]` sparse activation buffer へ変換する。
- 定義済み Pattern Unit をスコアリングし、最大3件を選択する。
- `inhibition_matrix[source][target]` で Unit 間抑制を適用する。
- 統合後 Unit から固定軸の action vector を生成する。
- action vector から LLM 向け order JSON を生成する。
- 必須メトリクスを JSON と標準 logging に出す。
- active bit密度を `threshold_profile` で調整可能にする。
- Pattern Unit候補は横型並列処理で選択する。
- 現行v1.6では明示指定時に単一winnerをVertical Stackへ送るか、
  予算内の複数候補をHybrid Stack-Meshへ送る。
- Core外側のRuntime Executorでtimeout、cancel、retry、resumeを管理する。

### 実装しない

- クラウド LLM 出力の教師データ保存
- 自動学習、自動重み更新、自己改変
- 100×100 マップ
- 文章の完全再生成学習
- 16×16 セルへの意味座標の割り当て
- 外部 LLM API 呼び出し
- Core内部からの外部LLM直接呼び出し

Vertical Unit Stackはv1.0aでは対象外だったが、現行v1.3で依存・出力・
停止契約を追加した。Hybrid Stack-Meshはv1.4、外部Executor境界と
blind runtime評価はv1.5、独立study・統計評価・精度監査はv1.6で追加した。

## 4. データ設計

### Thought Code

入力から64個の決定的な routing intensity を生成し、選択中の `threshold_profile` を適用して sparse な unsigned 64bit キーへ変換する。同一入力・同一profileは同一キーになる。これは検索・Unit候補選択・キャッシュ参照に利用できるが、思考内容そのものではない。

```json
{
  "value": "0x0123456789ABCDEF",
  "width": 64,
  "role": "external_routing_key"
}
```

### Pattern Tensor / Unit

Pattern Tensor は sparse な `[64,16,16]` バッファである。

- channel: 内部特徴の集約軸
- row / column: 活性値を保持するための番地
- spatial semantics: `false`

Pattern Unit は外部ルーティングとの照合用 `route_mask`、内部 `pattern`、キーワード、action weights を持つ。`route_mask` と `pattern.shape[0]` はともに64という数値を使うが、相互に同一視しない。

各Unitは `channel_schema` を持つ。v1.0aではschema名のみを観測していたが、
v1.1で`pattern-channel-schemas.v1`として正式化した。正式定義は
`thought_core/config/channel_schemas.json`に置き、Unit Typeごとの
prototype channel集合を固定する。

ただし、個別channel indexへ証拠・リスク・文体などの意味を割り当てない。
schema名はUnit全体の意図領域、channelはUnit-localなprototype affinityだけを
表す。詳細は`docs/VLTE_BPTM_v1_1_channel_schemas.md`を参照。

### Action Vector

v1.1で`vlte-bptm.action-vector.v1`として版管理する固定軸:

```text
reply, ask, explain, plan, verify, summarize, creative, caution
```

値は `0.0..1.0` を基本範囲とする。`ask / verify / plan / summarize / creative / caution` の制御軸を優先し、その後に `explain / reply` を評価して `llm_order.mode` を決める。

LLM Orderは`vlte-bptm.llm-order.v1`とし、内包するAction Vectorの
schema versionを明記する。詳細は
`docs/VLTE_BPTM_v1_1_output_schemas.md`を参照。

## 5. Unit 選択

各 Unit の選択スコアは、次の固定ヒューリスティックで計算する。

```text
score =
    0.40 * external routing overlap
  + 0.20 * internal channel affinity
  + 0.40 * keyword match
```

補正と選択規則（実装契約）:

- `respond` Unit はキーワードを持たない既定応答 Unit のため、固定バイアス `+0.12` を加算する。
- 選択は上位から最大3 Unit とし、`max(0.12, 最高スコア * 0.68)` 未満のスコアの Unit は選択しない（相対閾値）。
- 相対閾値で全 Unit が落ちる場合は最高スコアの1 Unit を選択する。
- 空入力は `clarify` Unit を単独選択する。

これは学習器ではない。v1.0a の目的はアルゴリズム精度ではなく、各段階の境界と観測可能性を検証することである。

## 6. Integrator と inhibition_matrix

行列は疎な辞書として持つ。

```python
inhibition_matrix[source_unit][target_unit] = coefficient
```

同時更新式:

```text
integrated(target) =
  max(0, raw(target) - Σ(raw(source) * coefficient(source,target)))
```

係数は `0.0..1.0` に制限する。JSON には Unit ごとの `raw_score`、`integrated_score`、`inhibited_by` を残す。

行列の値は外部設定ファイル `thought_core/config/inhibition_matrix.json`
（schema `inhibition-matrix.v1`）に外部化し、`integrator.load_inhibition_matrix()`
が読み込み・検証して `DEFAULT_INHIBITION_MATRIX` を構成する。係数の値は
v1.0a Core契約であり、変更は契約変更として受け入れfixtureと同時に行う。
設計意図（抑制の方向と相対的な強さ）は同ファイルの `rationale` に記す。

`v1.0a-p1`の設定検証契約:

- source / targetは`DEFAULT_UNITS`に存在する正式なUnit IDだけを許可する
- 係数は有限の数値`0.0..1.0`に限定し、JSON booleanは数値として扱わない
- 自己抑制`source == target`は拒否する
- `schema_version`とobject型の`matrix`を必須とする

| source→target | 係数 | 意図 |
| --- | --- | --- |
| clarify→build | 0.45 | 情報不足の入力で構築を最も強く抑制（最大の係数） |
| verify→build | 0.35 | 検証・監査が構築より優先 |
| summarize→explore | 0.30 | 要約は収束。発散的探索を抑制 |
| clarify→respond | 0.25 | 曖昧な入力では応答より質問を優先 |
| build→respond | 0.20 | 計画が直接応答に埋もれないよう弱く抑制 |
| verify→explore | 0.20 | 検証中は分岐より対象の確認に集中 |

v1.0aでは行列を固定設定として扱う。ユーザー修正や成功・失敗ログによる自動更新は実装しない。将来更新を検討する場合も、版管理・手動承認・再現可能な評価を前提とする。

## 7. Active Bit Threshold Profile

active bitsの過剰・過少を観測しやすくするため、v1.0aでは次のプロファイルを持つ。

| Profile | Threshold | Density guard | 想定用途 |
| --- | ---: | ---: | --- |
| `light_v1` | 0.86 | 4-10 bits | 軽い雑談・短い入力 |
| `normal_v1` | 0.75 | 8-18 bits | 通常相談 |
| `design_v1` | 0.64 | 14-28 bits | 設計・実装相談 |
| `deep_verify_v1` | 0.52 | 20-36 bits | 設計を含む重い検証 |

閾値適用後のbit数がguard外なら、routing intensity順位を用いて範囲内へ収める。これは初期観測用の仮設定であり、精度目標ではない。CLIの `--threshold-profile` で明示的に切り替えられる。

40個以上または3個以下が頻発する状態は、現在のv1 profileでは異常候補として扱う。頻度分布の集計機能自体は永続化Phaseで実装し、v1.0aでは集計可能なイベント項目を出力する。

## 8. 処理トポロジー

v1.0aの基準経路は`Horizontal Processing only`として開始した。
現行v1.6でも既定はHorizontalである。明示指定時は単一Mesh winnerを根に
Vertical Stackを構築するか、最大2候補をHybridで処理する。

```text
Thought Code
  -> selected Pattern Units (horizontal)
  -> inhibition integration
  -> Horizontal Mesh
  -> optional Vertical Stack or Hybrid Stack-Mesh
  -> action vector
  -> optional external Runtime Executor
```

Vertical Stackは`input_dependencies`、Unit別output contract、`max_depth`、
中間verify、未検証前提の停止を実装済み。Hybridは最大2 Stack・合計3 stepで
複数候補を処理し、completed StackをIntegratorで選ぶ。

v1.5 Runtime ExecutorはCore外側で次Unitを外部adapterへdispatchする。
wall-clock timeout、cancel通知、限定retry、idempotency、resumeを管理するが、
Unit出力本文を公開session JSONや自動学習資産へ保存しない。

## 9. 観測・ログ仕様

必須メトリクス:

- `active_bit_count`: Thought Code 内で1になった bit 数
- `active_bit_density`: `active_bit_count / 64`
- `selected_unit_count`: selector が選び Integrator へ渡した Unit 数
- `threshold_profile`: active bit生成に使ったprofile名

`python -m thought_core --json "入力"` では全段階を JSON 表示する。`--log-level INFO` を付けると必須メトリクスとprofile名を logging にも出す。

JSON の主要キー:

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

`diagnostics.routing` には適用閾値、density guard、active bitごとのintensityを含める。`selected_units` にはUnit固有の `channel_schema`、
`channel_schema_version`、`channel_semantics`、`prototype_channels`、
`process_mode`を含め、後からbit・Unitの頻度分布を集計できるようにする。

Horizontalの`trace`は次の順序を固定する。

```text
input
  -> active_bits
  -> selected_units
  -> inhibition_integration
  -> horizontal_mesh
  -> action_vector
  -> llm_order
```

Verticalでは`horizontal_mesh`と`action_vector`の間に`vertical_stack`を追加する。
Hybridでは同じ位置に`hybrid_stack_mesh`を追加する。

## 10. モジュール構成

- `bits.py`: 64bit Thought Code
- `state.py`: パイプライン状態、Unit 活性、メトリクス
- `encoder.py`: Thought Code と内部活性バッファの生成
- `units.py`: `[64,16,16]` Pattern Unit 定義
- `channel_schema.py`: Unit Typeごとのchannel schema契約
- `unit_catalog.py`: 正式Pattern Unit一覧の読込・検証
- `selector.py`: Unit スコアリングと選択
- `integrator.py`: inhibition matrix と競合抑制
- `mesh.py`: Horizontal Unit投票・優先度・mode決定
- `vertical_stack.py`: dependency graph、output contract、逐次停止判定
- `hybrid.py`: 複数候補選択、予算、scheduler、Stack Integrator
- `action_vector.py`: Unit 活性から action vector への変換
- `order_builder.py`: action vector から LLM order への変換
- `observation.py`: 非永続の観測集計とCLI
- `observation_store.py`: privacy縮約・保持期間・ローカルSQLite保存
- `pipeline.py`: end-to-end処理の公開API
- `demo.py`: CLIとJSON表示

旧 `thought_register` は移行比較用として変更せず残す。

## 11. 受け入れ条件

- Thought Code が常に unsigned 64bit 範囲に収まる。
- Thought Code が `external_routing_key` として出力される。
- 全 Pattern Unit の shape が `[64,16,16]` である。
- 16×16 が非意味座標であることを diagnostics で確認できる。
- inhibition coefficient が選択 Unit の統合後スコアへ反映される。
- 必須3メトリクスと `threshold_profile` が JSON に存在し、計算値と一致する。
- 各profileのactive bit数が定義したdensity guard内に収まる。
- Unit固有の `channel_schema` と `horizontal` process modeを確認できる。
- CLI JSON を機械的に parse できる。
- schema version、pipeline version、7段階traceを確認できる。
- Action Vector / LLM Orderの個別schema versionを確認できる。
- Horizontal Meshのvote、Unit contribution、勝者、優先順位を確認できる。
- Vertical時に現在のUnitだけをdispatchし、失敗時に後続を停止できる。
- Hybrid時に2 Stack / 3 step予算を守り、代替completed Stackを選択できる。
- Horizontal時のJSONと7段階traceが後方互換である。
- 禁止事項に相当する保存・学習・外部 API 処理が存在しない。

## 12. ロードマップ

### Phase 0: v1.0a 最小観測系

Status: 完了

- 本書のパイプライン実装
- 固定 Unit、固定 action 軸、固定 inhibition matrix
- 固定 threshold profile と density guard
- JSON デモと単体テスト

完了条件: 入力から `llm_order` までを一つの JSON で追跡でき、代表入力fixtureが全件通過する。

### Phase 1: 仕様確定

- 設計ログから正式な Pattern Unit 一覧を確定
- Unit ごとの action weights を確定
- inhibition matrix の根拠と方向性を確定
- routing overlap、channel affinity、閾値の評価ケースを作成
- Unit Typeごとの正式なchannel schemaを定義

完了条件: 代表入力と期待 Unit/action の fixture がレビュー済みである。

### Phase 2: 永続化可能な観測ログ

- `observation-privacy-policy.v1`で保存・非保存対象を固定
- raw input、Thought Code、sample単位選択結果、LLM出力を保存しない
- UTC日次aggregateだけを明示opt-inでローカルSQLiteへ保存
- 最低cohort、cell抑制、immutable bucket、保持期間・削除をテストで固定

完了条件: 保存対象と非保存対象がスキーマで明確に分離される。完了。

### Phase 3: 評価と調整

- 手動作成した評価データで Unit 選択と action vector を測定
- inhibition matrix の係数を手動・版管理下で調整
- false positive / false negative を可視化
- active bit数・組み合わせ・頻度とselected unit分布を可視化

完了条件: 自動学習なしで再現可能な評価レポートを生成できる。

### 将来検討

- Pattern Unit の増設
- activation buffer サイズの比較実験
- 学習方式の研究
- 大規模マップ
- 外部executorと実時間timeout
- Hybrid semantic quality・latency・費用評価

Vertical Unit Stackはv1.3、Hybrid Stack-Meshはv1.4で完了した。
残項目は版別ロードマップの
完了条件を満たすまで実装しない。

詳細な版別計画は `docs/VLTE_BPTM_roadmap.md` を正とする。

## 13. 追加ログが必要になる箇所

現時点の最小実装には前提ログ全文は不要である。次の項目が過去ログですでに定義済みなら、該当部分だけを追加資料として取り込む。

- Pattern Unit の正式名称と責務
- Unit 選択式または閾値
- inhibition matrix の正式な抑制方向と係数
- action vector の正式な軸、値域、優先順位
- `llm_order` の必須フィールド
- executor timeout / cancel / retryの運用契約

version1 仕様書を共有する場合は、上記項目を含む章からでよい。全文しかない場合はテキストファイルとして保存し、差分抽出する。

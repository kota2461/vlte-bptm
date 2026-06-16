# VLTE-BPTM v1.0a レビュー対応表

更新日: 2026-06-09

## 対応結果

| ID | 指摘 | Status | 反映先 |
| --- | --- | --- | --- |
| Review 1 | Pattern Unitの`64`軸がThought Codeと曖昧 | 解決済み / 採用済み | `ThoughtCode`と`PatternUnit.channel_schema`を分離 |
| Review 2 | 16×16へ意味を固定しすぎている | 採用 | `spatial_semantics=false`、活性バッファとして固定 |
| Review 3 | Integratorの競合処理が個別if文になる | 採用 | 固定`inhibition_matrix`と同時抑制式 |
| Review 4 | active bits数の妥当性を検証できない | 採用 | 3指標、threshold profile、density guard |

## v1.0a 修正方針

1. Thought Code 64bitは外部制御コード、Unit呼び出しキー、入力状態の圧縮表現として扱う。
2. Pattern Unitの`C=64`はUnit内部のfeature channel数とし、Unit Typeごとにchannel schemaを変えてよい。
3. `H×W=16×16`は意味座標ではなく活性バッファとする。
4. Integratorは`inhibition_matrix[source][target]`で競合を表現する。
5. `active_bit_count`、`active_bit_density`、`selected_unit_count`、`threshold_profile`をログ化する。
6. v1.0aはHorizontal Processingだけを実装し、Vertical StackとHybrid処理は後続版へ送る。
7. 最優先の受け入れ経路は `input -> active_bits -> selected_units -> action_vector -> llm_order` とする。

## Review 1への正式回答

```text
Pattern Unit shape [64,16,16] の64はThought Codeの64bitと同一ではありません。

Thought Code 64bitは、全体の状態圧縮・Unit呼び出し・ルーティングに使う外部キーです。
Pattern UnitのC=64は、Unit内部のfeature channel数です。

v1では実装簡略化のため全UnitをC=64へ揃えますが、これは共通幅であって共通意味ではありません。
memory Unitでは記憶特徴、risk Unitではリスク特徴、speech Unitでは発話特徴のように、Unit Typeごとにchannel schemaを変えてよい設計です。
```

## Review 2への正式回答

```text
v1では16×16へ「左=具体」「右=抽象」などの固定意味を付けません。
H×WはPattern Unit内部の活性バッファとして扱います。
座標意味の導入は、ログ・ユーザー修正・評価結果を観測した後、v1.2以降で再検討します。
```

## Review 3への正式回答

```text
Unit間競合は個別if文ではなくinhibition_matrixで表現します。
v1.0aでは固定設定とし、自動学習・自動更新は行いません。
```

## Review 4への正式回答

```text
active_bit_count / active_bit_density / selected_unit_count / threshold_profileをイベントごとに記録します。
active bit数は用途別profileのthresholdとdensity guardで調整可能にします。
頻度分布は後続の観測ログPhaseで集計します。
```

## 保留事項

- Unit Typeの正式一覧
- Unit Typeごとのchannel schema
- inhibition matrixの正式係数
- action vectorの正式契約
- Vertical Unit Stackの依存・出力契約

これらは推測で固定せず、評価fixtureと追加設計ログを基に確定する。

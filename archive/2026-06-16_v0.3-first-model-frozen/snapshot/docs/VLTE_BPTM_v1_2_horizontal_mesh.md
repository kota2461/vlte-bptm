# VLTE-BPTM v1.2 Horizontal Unit Mesh

更新日: 2026-06-11

## 目的

選択・抑制後の複数UnitがAction VectorとLLM Orderへ与える影響を、
投票値・優先順位・勝者・非選択理由として観測可能にする。

schema versionは`horizontal-unit-mesh.v1`。
設定は`thought_core/config/horizontal_mesh.json`に置く。

## 投票

各Unitの各Action軸への寄与:

```text
contribution(unit, axis) =
  integrated_score(unit) * action_weight(unit, axis)

vote(axis) = sum(contribution(unit, axis))
```

最大voteが1.0を超える場合は、全voteと全Unit contributionを同じ最大値で割る。
Meshの`votes`をそのままAction Vectorとして使用し、別計算による差を作らない。

## 優先順位

control axis:

```text
ask > verify > plan > summarize > creative > caution
```

fallback axis:

```text
reply > explain
```

1. control axisに正のvoteがあれば、その最大値を勝者にする
2. control内の同票は上記優先順位で決める
3. controlがすべて0の場合だけfallbackを比較する
4. fallbackの同票は`reply`を優先する

軸からmodeへの変換:

| Axis | Mode |
| --- | --- |
| ask | clarify |
| verify | verify |
| plan | build |
| summarize | summarize |
| creative | explore |
| caution | verify |
| reply | respond |
| explain | explain |

正のcontrol voteは、数値がより大きいfallback voteより優先される。
これはv1.1以前のLLM Order mode選択を明文化した契約である。

## 観測

Pipeline JSONの`horizontal_mesh`:

- `votes`
- `unit_contributions`
- `winning_axis`
- `winning_mode`
- `control_axis_priority`
- `fallback_axis_priority`
- `candidates`

各candidateはvote、priority group/rank、選択状態と理由を持つ。

理由:

- `highest_control_vote`
- `highest_fallback_vote`
- `suppressed_by_positive_control_vote`
- `tie_broken_by_priority`
- `lower_vote`
- `zero_vote`

Traceは次の7段階:

```text
input
active_bits
selected_units
inhibition_integration
horizontal_mesh
action_vector
llm_order
```

## 境界

- vote・priority・weightを自動学習しない
- inhibition matrixを置き換えない
- Mesh合議を教師ラベルへ昇格しない
- Vertical依存や再帰実行を導入しない

独立fixtureは`tests/fixtures/v1_2_horizontal_mesh.json`。
旧mode選択との互換性はAction Vector軸の6,561組合せで固定する。

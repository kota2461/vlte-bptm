# VLTE-BPTM v1.1 Pattern Channel Schema

更新日: 2026-06-11

## 契約

schema versionは`pattern-channel-schemas.v1`、全Unitのchannel幅は64。
H/W座標および個別channel indexへ概念的意味を割り当てない。

```text
channel_semantics = unit_local_prototype_affinity_only
allocation_method = blake2b_unit_prototype.v1
unassigned_channel_role = no_named_semantics
```

Selectorの`internal channel affinity`は、入力feature bufferのenergyのうち、
Unit固有の`prototype_channels`に入った割合である。

## Unit Type一覧

| Unit Type | Schema ID | Prototype数 |
| --- | --- | ---: |
| explore | `novelty_and_hypothesis_features` | 25 |
| build | `implementation_and_planning_features` | 26 |
| verify | `evidence_risk_and_uncertainty_features` | 27 |
| summarize | `salience_and_compression_features` | 27 |
| clarify | `ambiguity_and_missing_information_features` | 21 |
| respond | `speech_style_and_response_features` | 25 |

schema IDはUnit全体の意図領域を識別する名前であり、例えばverifyのchannel 0を
「証拠」、channel 2を「リスク」と解釈してはならない。

正式なindex集合と根拠は
`thought_core/config/channel_schemas.json`に置く。独立した契約fixtureは
`tests/fixtures/v1_1_channel_schemas.json`とする。

## 検証

起動時に次を検証する。

- schema version、64幅、非意味座標、allocation method
- schema IDの一意性
- prototype channelが整数、範囲内、一意、非空
- 設定のUnit Type集合と`DEFAULT_UNITS`が完全一致
- 設定のprototype集合と決定的に生成したPattern Tensorが完全一致

## 出力

各`selected_units`要素は次を持つ。

- `channel_schema`
- `channel_schema_version`
- `channel_semantics`
- `prototype_channels`

既存の`channel_schema`文字列は後方互換のため維持する。

# VLTE-BPTM v1.1 Output Schemas

更新日: 2026-06-11

## Pipeline

- pipeline implementation version: `1.1`
- pipeline output schema: `vlte-bptm.pipeline.v1`

v1.1の追加フィールドは後方互換のため、pipeline schema majorはv1を維持する。

## Action Vector

schema version: `vlte-bptm.action-vector.v1`

固定軸と順序:

```text
reply, ask, explain, plan, verify, summarize, creative, caution
```

値域は`0.0..1.0`。Pipeline JSONでは従来の`action_vector` objectを維持し、
兄弟フィールド`action_vector_schema_version`で版を示す。

軸の追加・削除・意味変更・順序変更はschema変更として扱う。

## LLM Order

schema version: `vlte-bptm.llm-order.v1`

必須フィールド:

```text
schema_version
mode
instruction
user_input
routing_key
action_vector_schema_version
action_vector
constraints
metadata
```

mode:

```text
build, clarify, explain, explore, respond, summarize, verify
```

`llm_order.action_vector_schema_version`は内包するAction Vectorの契約版を示す。

独立fixtureは`tests/fixtures/v1_1_output_schemas.json`とする。

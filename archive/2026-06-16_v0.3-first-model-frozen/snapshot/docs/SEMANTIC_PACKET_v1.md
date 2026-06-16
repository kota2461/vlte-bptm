# Semantic Packet v1

更新日: 2026-06-12

schema version: `semantic-packet.v1`

実装: `semantic_routing/semantic_packet.py`

fixture: `tests/fixtures/semantic_packet_v1.json`

## 目的

生プロンプトをProcessing Routerへ直接渡さず、思考制御に必要な最小信号へ
変換する。Packetは原文本文と回答本文を保持しない。

## 必須field

```text
schema_version
request_digest
adapter
language
intent_candidates
operations
information_state
constraints
risk
evidence
unknowns
conflicts
confidence
```

未知fieldと欠落fieldは拒否する。nested objectも完全一致を要求する。

## 契約

- `request_digest`: UTF-8原文のSHA-256
- `language`: `ja | en | mixed | und`
- intent:
  `respond | explain | clarify | build | verify | summarize | explore`
- intent候補は重複不可、confidence降順
- confidenceは有限な`0.0..1.0`
- information stateは4つのboolean
- constraintはmachine identifierで表し、`must`と`must_not`の重複を拒否
- risk level: `low | medium | high | critical`
- evidenceは原文の`start/end` offsetだけを持ち、本文を複製しない
- unknown/conflictを空配列に固定せず、判断不能を明示できる

## Privacy Boundary

Packetに次を含めない。

- raw prompt
- user_input
- generated answer
- LLM hidden reasoning
- tool output本文

Integration層がdigestとevidence offsetを原文に対して検証し、Processing Routerは
検証済みPacketだけを受け取る。

# Knowledge Index v1

Knowledge Index is the router's lightweight table of contents. It does not store answer text. It only maps surface hooks to knowledge-library IDs and retrieval flags.

## Split Of Responsibility

```text
Semantic Packet  = what kind of request this is
Knowledge Index  = which library should be checked
Retrieval Packet = what was hooked for this request
Knowledge Library = future evidence/fact body storage
LLM              = explanation and final wording
```

## Contract

- `data/knowledge_index_v1.json` stores domain hooks and library IDs.
- `semantic_routing.knowledge_index.build_retrieval_packet(text)` returns `retrieval-packet.v1`.
- `semantic_routing.route(text)` exposes the packet as `result.retrieval` and `result.trace["retrieval"]`.
- The retrieval packet is intentionally outside `semantic-packet.v1`; the semantic packet remains compact and knowledge-free.

## Minimal Packet Shape

```json
{
  "schema_version": "retrieval-packet.v1",
  "needed": true,
  "domains": ["basic_it"],
  "hooks": ["HTTP"],
  "libraries": ["basic_it_v1"],
  "current_check": false,
  "risk": "low",
  "matches": []
}
```

## Next Step

Add small knowledge-library files only after the retrieval hooks prove useful. The library body should be evidence-oriented and reviewable, not copied into router rules.

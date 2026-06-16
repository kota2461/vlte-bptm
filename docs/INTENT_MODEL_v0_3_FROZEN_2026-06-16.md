# v0.3 First Model — FROZEN (2026-06-16)

初号機(v0.3 gated-hybrid intent router)を**確定モデルとして凍結**する。以後、
他プロジェクトでの採用と実データ蓄積のベースラインとし、0.90 は将来の
大規模・実分布データ版(後継機)に繰り越す。本書は凍結記録であり、同時に
他エージェントによるレビュー/改善提案のためのブリーフを兼ねる。

---

## 1. Frozen artifacts (SHA-256)

| artifact | path | SHA-256 |
|---|---|---|
| learned intent model (`intent-model.v1`) | `build/intent_model_v1.json` | `055D1708CFB605AD5A449283BC05D81FF1C6BB59415F37E362FE06E7DF84091F` |
| pattern router model | `build/pattern_router_model.json` | `71470C5E3D97973467661E17A66F7A382FE206F288454A7F9D39D305397DDEAC` |
| adapter package | `semantic_routing/` (v0.3) | — |
| training corpus | `data/intent_training_corpus_v1.json` | 408 approved examples |

Promotion record: `build/intent_gate_report.json` (schema
`intent-model-deployment-gate.v1`, decision `pass`).

## 2. Frozen performance (the working baseline)

Measured on the 50-case conversation-accumulation campaign (honest, single
measurement; campaign is NOT used as a gate):

| | intent | end_to_end | critical_underprocessing |
|---|--:|--:|--:|
| markers-only (v0.2) | 0.80 | 0.76 | 0 |
| **v0.3 hybrid (FROZEN)** | **0.86** | **0.82** | **0** |

Off-campaign k-fold over the corpus: **0.7328**. Test suite: **315 passed**.

## 3. Architecture (one pass)

```
text
 → markers (deterministic, observable, safety-first)         baseline.py
 → on marker no-match AND confidence margin ≥ 0.15: learned   intent_model.py
   averaged-perceptron intent layer (7 intents)
 → deterministic ProcessingPlan (class/mode/model_class/      processing_plan.py
   budgets/tools)
 → tier model select (small/standard/large)                  executor.py
 → reasoning-budget resolve (content + reasoning headroom)    executor.py
 → tools (safe calculator; web_search injectable)            tools.py
 → direct LLM-free fast path for trivial smalltalk           direct.py
 → external LLM (LM Studio, OUTSIDE thought_core)            runtime.py
```

Single entry: `route_and_execute(text, chat_fn, available_models)`.
HTTP service: `semantic_routing/server.py` (`/health`, `/route`, `/execute`).

## 4. Why frozen at 0.82, not 0.90

Two independent real-data collection rounds (2026-06-16) both showed a small
real batch (15–33 human-approved, campaign-disjoint examples) does NOT improve
the campaign and slightly regresses it (e2e 0.82→0.78 each time), even when
curated, respond-rebalanced, or decomposed into clean single-intent spans. The
model sits at a stable point fit to the 408 corpus; small perturbations move it
off, usually worse. The deployment-gate's k-fold proxy passed both times while
the true campaign target dropped (the campaign cannot be the gate — that is
circular). **Conclusion:** 0.90 needs a SUSTAINED, large, well-distributed,
weak-category-targeted REAL corpus — not piecemeal additions. Synthetic /
stitched data is refused (empirically falsified + boundary).

## 5. Do-not-regress contract (for any future successor)

- frozen anchors: `tests/fixtures/intent_foundation_anchors_v1.json`,
  `intent_hybrid_regression_v1.json` (SHA-registered in
  `intent_gate_fixture_registry.json`).
- the 315-test suite.
- discipline (unchanged): no automatic learning; human-approved labels only;
  never train on the 50-case campaign; never persist LLM output as training
  data; external LLM stays OUTSIDE thought_core.

## 6. Adoption in another project + real-data accumulation

Reuse: import `semantic_routing` and call `route_and_execute(...)`, or run the
HTTP service. The collection pipeline is built and validated:
`collection_store.py` + `build/ingest_logs.py` / `extract_user_messages.py` /
`collection_worksheet.py` / `record_*_reviews.py` / `merge_collection.py`, with
`build/measure_candidate_campaign.py` for the single post-merge measurement.

Protocol for the 0.90 successor: accumulate REAL inputs (target the weak
categories below), human-approve intent labels, keep disjoint from the
campaign, retrain a SUCCESSOR only when a large balanced corpus exists, then
gate + measure once. Never fit to the campaign.

## 7. Weak categories (where a successor must improve)

From the frozen by-category end_to_end:

| category | frozen | nature |
|---|--:|---|
| temporal_disambiguation | 3/6 | time idioms (今でも使える? / 今度 / 最近) misroute |
| compound_intent | 7/11 | primary-of-many needs verb-level semantics |
| indirect_explanation | 8/9 | indirect "why/doesn't click" phrasings |
| verify_then_build | 10/11 | (safety: critical stays 0) |
| conversation_response | 7/7 | ok |
| mixed_language | 6/6 | ok |

## 8. Open questions for external review

1. Is a linear hashed-ngram averaged perceptron the right learned layer, or
   does the weak-category gap need a structural change (e.g., a small
   embedding/intent encoder, or a compound-primary resolver)?
2. Can the gate proxy be made better-aligned with the campaign without
   becoming circular (e.g., a separate held-out real dev slice)?
3. Marker coverage vs learned layer division for temporal idioms — markers,
   model, or a dedicated temporal normaliser?
4. Minimum real-corpus size/spread likely needed to move 0.82→0.90 reliably?
5. Tier model map + reasoning-budget (direction 1): keep, or move to
   direction 2 (suppress reasoning on light classes) for stricter latency?

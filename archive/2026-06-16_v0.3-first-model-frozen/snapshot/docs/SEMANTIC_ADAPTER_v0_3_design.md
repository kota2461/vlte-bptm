# Semantic Adapter v0.3 — Hybrid Intent Layer (design)

Date: 2026-06-13
Status: design (no implementation yet)
Predecessor: v0.2 deterministic marker adapter, frozen at end_to_end 0.76 /
plan 0.90 / intent 0.80 / critical 0 (see
`docs/SEMANTIC_ADAPTER_fix_results_2026-06-13.md`).

## 1. Goal & scope

Break the **marker ceiling** on INTENT detection — the part v0.2 cannot
reach with rules: indirect-explanation idioms, compound-intent primary
(summarize-vs-build), temporal idioms. Target: clear the accuracy gate
(end_to_end ≥ 0.90 on the accumulation campaign) while keeping critical
under-processing at 0 and every existing boundary intact.

**In scope:** a learned intent classifier (the "intent layer") that the
deterministic markers defer to for the long tail.
**Out of scope (unchanged):** the processing-plan policy stays fully
deterministic (`processing_plan.py`); the plan is derived from the
SemanticPacket exactly as today. v0.3 changes how `primary_intent` /
`intent_candidates` are produced, nothing downstream.

## 2. Architecture — hybrid, markers first

```
text
  -> marker pass (baseline.py)        # fast, high-precision, observable
  -> learned intent layer (new)       # signed word/n-gram weights -> 7 intents
  -> merge rule                       # deterministic combination
  -> SemanticPacket (primary_intent + candidates + decided_by evidence)
  -> processing_plan.py (UNCHANGED)   # deterministic
```

The markers are NOT discarded. They keep the safety wins (verify
prerequisite, missing-info → clarify) and the high-precision direct hits.
The learned layer only earns the decision where markers are silent or
ambiguous.

### Merge rule (recommended; see open decision D1)

1. **Safety stays deterministic.** If verify markers co-occur with a build
   deliverable → verify-then-build (build primary + verify prerequisite), and
   missing-information → clarify. These rules run regardless of the learned
   layer. The learned layer must never *remove* a verification prerequisite.
2. **No marker fired** → use the learned layer's top intent (replaces the
   v0.2 `respond` 0.62 fallback). Fixes indirect-explanation / conversation.
3. **Exactly one intent fired** → keep the marker intent (high precision);
   record the learned distribution as a cross-check only.
4. **Multiple intents fired (non-safety)** → the learned layer picks the
   primary among them (fixes compound summarize-vs-build); depth/`multiple_
   intents` handling is unchanged.

This keeps v0.2's observable behaviour as the default and confines the
learned layer to exactly the cases that need it.

## 3. The learned intent model

- **Algorithm:** averaged perceptron — reuse `pattern_learning/trainer.py`
  machinery (`text_features`, `_train_averaged_weights`). Proven,
  deterministic (fixed seed), JSON-serialisable, dependency-free, fits the
  project's observability/no-black-box stance.
- **Features:** existing `text_features` (hashed char 2/3/4-grams + word
  tokens, L2-normalised).
- **Label space:** the adapter's **7 intents** — respond, explain, build,
  verify, summarize, explore, clarify. NOTE: the Pattern Router has only 6
  routes (no `explain`), so this is a *new* classifier in a different label
  space, not the Router reused as-is. Same algorithm, different head.
- **Output:** a distribution over the 7 intents + top intent + margin
  (top1−top2), used by the merge rule and recorded for observability.
- **Calibration:** reuse the Router's k-fold reliability approach to get a
  confidence the merge rule can threshold on.

## 4. Training data (the real prerequisite)

The intent layer needs a **human-approved, intent-labelled corpus that is
DISJOINT from the 50-case accumulation campaign** (same_batch_tuning is
forbidden — the campaign is measurement-only).

Sources, in order of cleanliness:
- **Remap existing approved route-labelled data** where the mapping is exact:
  build/verify/summarize/explore/clarify/respond routes → same intents. This
  reuses the math/language/contract curricula already approved in the Pattern
  DB. (One-to-one for 6 of 7 intents.)
- **`explain` is the gap.** No existing track distinguishes explain from
  respond. v0.3 needs a fresh, human-approved `explain` training set
  (educational "why/how/I-don't-grasp-it" requests) — authored and reviewed
  like the other curricula, kept disjoint from the campaign.
- All training data goes through the existing human-review discipline
  (pending → approve → explicit train). No automatic labels, no
  pseudo-labelling, no training on model output.

## 5. Boundaries (unchanged, enforced)

- No automatic learning / no self-training / no pseudo-labels.
- Learned layer trained ONLY on human-approved labels via an explicit train
  step; deployed only through a gate (§6).
- **Never train on the accumulation campaign** (the 50). It stays the
  measurement set; sealed v2 stays closed until the gate passes.
- The processing-plan stays deterministic; v0.3 touches intent only.
- Observable: the SemanticPacket records `decided_by` (marker | learned |
  safety-rule) and the learned distribution, so every decision is auditable.

## 6. Train / eval / gate (reuse v0.2.x gate philosophy)

- **Artifact:** the intent model is a versioned JSON (like
  `pattern_router_model.json`), trained from the approved intent corpus.
- **train → candidate, promote → gated deploy** (mirror
  `pattern_learning/deployment.py`): a candidate is promotable only if it
  passes:
  1. **Intent foundation anchors** (a frozen, registered set of
     unambiguous intent cases — analogous to the foundation anchor suite):
     100% required.
  2. **No regression vs current** on a held-out intent eval (separate from
     training AND from the campaign).
  3. **No critical-underprocessing regression** end-to-end (the safety
     metric must stay 0 when the intent model is wired into the full
     adapter→plan pipeline).
- **Sealed intent eval:** a one-open sealed set (separate author, separate
  from training and campaign) for the honest final number, per the v0.2
  evaluation contract.

## 7. Acceptance / completion criteria (v0.3)

1. end_to_end ≥ 0.90 on the accumulation campaign, critical = 0.
2. No regression on v0.2's strengths (verify_then_build ≥ 0.91,
   mixed_language, conversation_response).
3. Held-out generalization demonstrated before the campaign is re-measured
   (not fitted).
4. The intent model passes its deployment gate; deterministic & reproducible
   (fixed seed); fully test-covered.
5. Every intent decision carries `decided_by` evidence (observability).

## 8. Open decisions (need human ruling before build)

- **D1 — merge rule.** Recommended: marker-precedence-for-safety + learned-
  for-longtail (§2). Alternative: score fusion (more power, less
  observable). Pick one.
- **D2 — learned layer scope.** Recommended: intent only (plan stays
  deterministic). Alternative: also let it inform processing_class
  (bigger change, risks the plan contract). Recommend intent-only for v0.3.
- **D3 — `explain` training data.** Author a fresh approved explain corpus
  (recommended) vs fold explain into respond for v0.3 and defer (loses the
  indirect-explanation win). Recommend authoring it.
- **D4 — training corpus assembly.** Remap approved route data + new explain
  set, with a documented mapping and a disjointness check against the 50.

## 9. Phased plan

1. **Data:** assemble the intent-labelled training corpus (remap + explain
   set), with a disjointness check vs the campaign; human review.
2. **Model:** intent-layer trainer (reuse perceptron); intent foundation
   anchors + sealed intent eval; gate.
3. **Merge:** wire the hybrid merge rule into `baseline.py`
   (`extract_semantic_packet`), recording `decided_by`.
4. **Validate:** held-out generalization → re-measure campaign once → gate.
5. **Decide:** if ≥0.90 & critical 0, open sealed v2 (the original goal);
   else iterate data (not fit).

## 11. FINALIZED DIRECTION (2026-06-14) — first deployable model

After two probe rounds the direction is locked (probe doc §8):

- **Synthetic grind to 0.90 is closed** (falsified: more synthetic data
  overfits its own distribution and worsens the campaign). Not pursued.
- **v0.3 = markers + confidence-gated learned intent layer** is adopted as
  the project's FIRST deployable model. The learned layer (averaged
  perceptron, 7-intent, trained on the 408-example approved corpus) is
  consulted only on marker no-match, and only when its top1-top2 margin ≥ a
  threshold; safety rules (verify prerequisite, missing-info → clarify) stay
  deterministic. Markers remain the observable first pass.
- **v0.3 acceptance bar is realistic, not 0.90:** beats the marker baseline
  on the campaign (marker intent 0.80 → hybrid ~0.84–0.86), keeps critical
  under-processing at 0, no regression on v0.2 strengths
  (verify_then_build ≥ 0.91, mixed_language, conversation), held-out
  generalization shown. The **0.90 gate is deferred to a future
  real-distribution-data successor** (v0.4-class), since synthetic provably
  cannot close the distribution gap.
- **This first model is the baseline** for future learning rework
  (real-log training data, reversible explicit-vocab encoding for
  observability, possibly a non-linear intent model) and structural
  improvement. Ship solid, iterate from a known-good base.

### Remaining implementation steps (to "production-viable")

1. **Off-campaign dev set** to lock the gate threshold honestly (the 0.15 /
   0.05 thresholds so far were campaign-tuned = optimistic). Author/collect
   a small held-out dev set; pick the margin there, not on the campaign.
2. **Wire the gated merge** into `baseline.py` `extract_semantic_packet`
   (markers first; learned-on-no-match-when-confident; record `decided_by`).
3. **Train + gate the intent model** (reuse `deployment.py` philosophy:
   intent foundation anchors, no-regression, critical stays 0, atomic
   promote, history/rollback).
4. **Measure the campaign ONCE** with the locked threshold; record the
   honest v0.3 number.
5. **Tests** for the merge + intent-model gate; keep the full suite green.

Discipline unchanged: human-approved labels only, never train on the
campaign, held-out before re-measuring, no fitting.

## 10. Why this is the natural next version

v0.2 (deterministic markers) reached its honest ceiling; the remaining gap
is intent semantics, which is what a learned layer is for. The project
already owns the perceptron + gate infrastructure; v0.3 reuses it in the
7-intent space, keeps markers as the observable safety first-pass, and holds
every learning boundary. It is "raising a model" in the literal sense the
markers never were.

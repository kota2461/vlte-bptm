# V11 Code Audit + Fixture Coverage Classification (Claude-side scan)

Generated: 2026-06-28

Scope: read-only source audit (`semantic_routing/`, git history, archive snapshots,
build scripts) plus classification of the 34 fixture files skipped by
`inspect_plm_sample_blocks.py`. No fixture, router, or training-data mutation.
This is the scan the user asked Claude to run directly, following up on the
block-level negative scan and the v11 roadmap's two pending hypotheses
(constraint omission, hook overfire without negation context).

## Headline finding: the live extraction logic is not auditable from source

`semantic_routing/baseline.py` (current working tree, 308 lines) is **not** the
real implementation. It is a loader:

```python
_CANDIDATES = sorted(
    (p for p in _CACHE.glob("baseline.cpython-310.pyc.*") if p.stat().st_size > 50000),
    key=lambda p: p.stat().st_mtime, reverse=True,
)
_BASELINE_PYC = _CANDIDATES[0]
_CODE = marshal.loads(_BASELINE_PYC.read_bytes()[16:])
exec(_CODE, globals())
```

It picks "the largest recent `.pyc` in `__pycache__`" and `exec`s it, because
(per its own docstring) "the latest working baseline includes uncommitted
Windows-local generalization that is only available from the last passing
compiled module in this workspace."

Verified by disassembling the chosen `.pyc`
(`semantic_routing/__pycache__/baseline.cpython-310.pyc.2207508733360`, 58KB):
the real `extract_semantic_packet` starts at source line **2146** and calls
six undocumented post-hoc patch layers in sequence:

| Function | Line (in the lost source) | Source recoverable? |
|---|---:|---|
| `_v6_profile` | 644 | yes — `archive/2026-06-24_.../baseline.py` (1507 lines) |
| `_v6_false_positive_profile` | 719 | yes — same archive snapshot |
| `_v7_generalization_profile` | 988 | **no** — bytecode only |
| `_v8_recovery_profile` | 1330 | partial — `build/_tmp_apply_v8_*.py` patch scripts (790 lines total, uncommitted) |
| `_v9_primary_review_profile` | 1570 | **no** — bytecode only |
| `_v9_constraint_operation_extension_profile` | 1766 | **no** — bytecode only |

Cross-checked against git and every archive/experiment snapshot:

- `git show HEAD:semantic_routing/baseline.py` = 660 lines, defines `MUST_MARKERS`,
  `MUST_NOT_MARKERS`, `FORMAT_MARKERS`, `RISK_MARKERS` directly (no profile layers).
- Largest archive snapshot (`archive/2026-06-24_v6-nonsealed-exact-pre-roadmap-gate`)
  = 1507 lines, has `_v6_profile`/`_v6_false_positive_profile` at the *exact* same
  line numbers as the compiled module — confirming it's an earlier point on the
  same lineage — but stops before v7/v8/v9.
- `__pycache__/` is gitignored and there are 24+ timestamped `.pyc` snapshots for
  `baseline.py` alone, ranging 7KB–58KB, Jun 12–27. The loader's selection rule
  (newest mtime, size > 50KB) is a heuristic, not a guarantee that it picks the
  pyc that actually matches the currently-intended behavior.

**Consequences:**

1. Roughly 1100+ lines of behavior-determining logic (v7, v8, v9 profiles —
   exactly the generations that produced the current sealed v10 regression)
   exist nowhere as readable source. Not git, not any of the 10+ archive
   snapshots, not the temp patch scripts (those only partially cover v8).
2. If `__pycache__` is ever cleared (fresh clone, CI, container rebuild, a
   `pyc` GC), `baseline.py` raises `ImportError: No recovered baseline pyc is
   available` and the router cannot import at all.
3. Because the v9 profile (the one most likely responsible for the
   sealed-v10-era constraint/risk behavior) is unrecoverable as source, the
   constraint-omission and hook-overfire hypotheses below could only be
   verified at the bytecode/behavioral level, not by reading the real logic.
   Any "fix" applied on top via the v10 wrapper is patching a black box.

This is a bigger risk than the metric regression itself: it blocks safe repair.
**This should be treated as the top-priority action, ahead of repair-lane work.**

## Hypothesis 1 — hook/guard overfire without negation context: CONFIRMED at the code level

`semantic_routing/knowledge_index.py::build_retrieval_packet`:

```python
haystack = text.casefold()
for entry in index.entries:
    matched_hook = None
    for hook in sorted(entry.hooks, key=len, reverse=True):
        if hook.casefold() in haystack:
            matched_hook = hook
            break
```

This is a plain substring containment check. There is no negation scope check,
no check for quotation/definitional context ("Apache 2.0 とは何ですか"), and no
local-vs-global distinction. Any text that contains a hook string anywhere —
negated, quoted, or meta-discussed — sets `domains`, `risk`, and
`current_check` exactly as if the domain genuinely applied. This matches the
v11 diagnostic's observed cases directly (explain-01 "依存", explain-03 "医療",
respond-03 "Apache 2.0") and matches the roadmap's own hypothesis text
verbatim: "guard hooks may fire on keyword presence before negation,
metalinguistic role, or local-reference checks."

`derive_failure_guard` in `guard_router.py` is downstream of the packet (it
reads `packet.risk`/`packet.constraints`, it doesn't compute them), so it
inherits whatever `knowledge_index.py` decided — it is not itself a place to
fix this.

## Hypothesis 2 — constraint omission fast path: explained, not fully provable

What's auditable: the v10 layer in the current `baseline.py` (`_v10_bridge_profile`
+ `extract_semantic_packet` wrapper) only *adds* `constraints.must` entries, and
only when text matches a small set of literal English bridge-template phrases
("ask before answering", "Treat the risk level as low|medium|high|critical",
"key claim is not verified yet", etc.). It never removes a constraint, and for
any text that doesn't match those exact templates, `profile["evidence"]` is
empty and the function falls straight through to
`_v10_canonicalize_constraints(payload)` — i.e. it reorders whatever the base
(opaque v6–v9) extractor already produced and returns immediately. So for
sealed v10's natural-phrasing cases (50/50 ja/en, avg 55.5 chars, not written in
bridge-template English), constraint population depends entirely on the v9
profile that cannot be read.

What this confirms: the "always `X -> []`" omission pattern across heterogeneous
constraint types (`ask_first`, `avoid_diagnosis`, `avoid_overclaim`,
`cite_sources`, `general_information_only`, plus `bullets`/`json`/`table`
formats) is consistent with the v10 patch being a **template-shaped
post-processing layer bolted onto an unreadable base**, rather than a fix to
the actual marker/recognition logic. The committed (660-line) `MUST_MARKERS`/
`FORMAT_MARKERS` dicts exist and look reasonable on inspection, but whether the
*currently running* v9 profile still uses them unmodified, or wraps them in
additional suppression (the bytecode does expose names like
`suppress_unverified`, `suppress_multiple`, `suppress_verify`,
`suppress_compare_operation`, `suppress_current_search` inside the v6/v7
profiles), cannot be confirmed without recovering the v7–v9 source first.

**This hypothesis cannot be closed out until the source-recovery action above is
done.** Treat it as "likely template-overfit interacting with opaque
suppression logic," not yet as a located bug.

## Fixture coverage classification (the 34 skipped files)

All 34 files skipped by `inspect_plm_sample_blocks.py` (due to missing
`authoring_method` or non-`pattern-language-benchmark.v1` shape) are still
actively referenced elsewhere in `tests/`, `semantic_routing/`, or `build/`
scripts — **none are dead/orphaned**. They fall into three groups:

1. **Registries, not case fixtures** (correctly out of scope):
   `gate_fixture_registry.json`, `intent_gate_fixture_registry.json`,
   `pattern_language_fixture_registry.json`. These are indexes, not benchmarks.
2. **Structural/schema specs, not PLM cases** (correctly out of scope):
   the 13 `v1_1`–`v1_6` files (channel schemas, mesh, policy, executor,
   independent-study specs) plus `semantic_packet_v1.json`,
   `processing_plan_v1.json`, `pattern_router_cases_v1.json`,
   `v1_0a_cases.json`, `v1_4_hybrid_evaluation.json`,
   `intent_foundation_anchors_v1.json`, `intent_hybrid_regression_v1.json`,
   `foundation_anchor_suite_v1.json`. Different schema families entirely.
3. **Semantically relevant PLM-adjacent case sets, excluded only by schema
   mismatch** (this is the real gap):

   | File | schema_version | cases |
   |---|---|---:|
   | `v7_router_repair_fixture_v1.json` | v7-router-repair-fixture.v1 | 72 |
   | `v5_critical_operations_fixture_v1.json` | v5-critical-operations-fixture.v1 | 48 |
   | `v6_router_debate_candidate_fixture_v1.json` | v6-router-debate-candidate-fixture.v1 | 12 |
   | `v6_ai_boundary_candidate_fixture_v1.json` | (same family) | — |
   | `v6_cowork_candidate_fixture_v1.json` | (same family) | — |
   | `v7_router_debate_candidate_fixture_v1.json` | (same family) | — |
   | `v4_failure_memory_fixture_v1.json` | v4-failure-memory-fixture.v1 | items-shaped, not cases-shaped |
   | `v4_puzzle_failure_memory_v1.json` / `v4_puzzle_task_seed_v1.json` | (puzzle family) | — |

   At minimum `v7_router_repair_fixture_v1` + `v5_critical_operations_fixture_v1`
   + `v6_router_debate_candidate_fixture_v1` add **132 cases** of genuinely
   router-relevant, currently un-scanned material — on top of the 330 already
   covered. The block-scan's "0 strong negative blocks" conclusion is accurate
   for what it measured, but it measured roughly 330 of an available ~460+
   cases. This matches and sharpens the coverage gap already flagged after the
   third turn's review.

## Improvement proposals, in priority order

1. **(P0, do first, before any repair-lane sample work)** Recover and commit
   real source for the v7/v8/v9 baseline profiles while the `.pyc` is still in
   `__pycache__`. Decompile the chosen pyc (line numbers above are exact
   anchors), reconcile against `archive/2026-06-24_.../baseline.py` (covers
   v6) and `build/_tmp_apply_v8_*.py` (partial v8), and commit the
   reconstructed `baseline.py` to git. Until this lands, no claim about
   "what the router currently does" for v9-era constraint/risk logic is fully
   verifiable, and the router has a standing single-point-of-failure
   (`__pycache__` loss = total import failure).
2. **(P0)** Fix `build_retrieval_packet` in `knowledge_index.py` to add a
   negation/meta-context guard before counting a hook match: skip the match if
   the hook is immediately preceded by a negation token (`ではない`, `not a`,
   `isn't`) within a small window, or if the hook is the object of a
   definitional question (`〜とは`, `what is `) rather than situated in an
   actionable request. Add explicit negated/meta contrast cases to a fixture
   and gate on zero false positives on those, mirroring the
   `hook_overfire_repair_lane` already defined in the v11 roadmap.
3. **(P1, depends on #1)** Once v7–v9 source is recovered, diff the recovered
   `MUST_MARKERS`/`FORMAT_MARKERS` firing against the 6 sealed-v10
   constraint-omission cases by id to determine definitively whether a marker
   simply doesn't match natural phrasing, or whether a later profile clears an
   already-populated `must` list. This converts hypothesis 2 from "explained"
   to "located."
4. **(P2)** Schema-bridge the three case-bearing files in group 3 (132 cases)
   into `pattern-language-benchmark.v1` (add `authoring_method`, normalize
   case shape) so the negative scan actually covers them, or extend
   `_load_nonsealed_plm_fixtures` to accept the v5/v6/v7 candidate-fixture
   schema family directly.
5. **(P2)** Make `inspect_plm_sample_blocks.py`'s generated `.md` surface
   `skipped_files` count/list in the human-readable summary itself (currently
   only in the JSON), so a future "0 negative blocks" read doesn't silently
   imply full coverage again.

## Verification

Read-only investigation; no fixtures, router code, or training data were
modified. `python -B -m pytest` run after the audit to confirm no incidental
state change (see test run note in chat).

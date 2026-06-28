# V11 Code Audit Triage v1

Generated: 2026-01-01T00:00:00+00:00

## Policy

- Diagnostic/roadmap metadata only; no router, training-data, fixture, or sealed-state mutation.
- Sealed labels remain taxonomy-only and are not used for tuning.

## Step2 Status

- status: step1b_baseline_source_recovery_completed
- next_action: roadmap_v11_step2_create_repair_curriculum_plan
- blocks_repair_curriculum_plan: false
- step2_blockers: []

## Findings

| finding | priority | confirmed/status | blocks Step2 | required action |
|---|---|---|---:|---|
| baseline_pyc_loader | P0 | False | false | keep source-recovered baseline under regression tests; do not restore pyc loader |
| literal_profile_patch_overfit | P0 | True | false | fold literal-profile overfit into Step 2 curriculum; replace per-sentence regex patches with abstract rules plus paraphrase transfer gates |
| hook_keyword_overfire_without_context | P0 | True | false | add hook context guard and nonsealed false-positive fixture before relying on hook-derived risk/current signals |
| constraint_omission_fast_path | P1 | trace_ready_after_source_recovery | false | after source recovery, compare marker firing versus constraint merge/clearing for omission cases |
| fixture_coverage_gap | P2 | classification_required_before_claiming_full_scan_coverage | false | schema-bridge PLM-adjacent fixtures or extend block scanner loaders |

## Chosen Baseline Pyc

- path: `semantic_routing/__pycache__/baseline.cpython-310.pyc.2207508733360`
- sha256: `780881fe474b2eaef0887d7234af6977b5953353fcccf8164fdc87eebce7b01b`
- size: 58260

## Recommended Actions

- P0 `v11_p0_baseline_source_recovery`: recover readable semantic_routing/baseline.py source from pyc/archive/temp patches or explicitly replace the runtime with auditable source
- P0 `v11_p0_literal_profile_generalization_guard`: ban one-regex-per-failed-fixture repairs and require paraphrase/transfer validation for profile-derived fixes
- P0 `v11_p0_hook_context_guard`: add negation/metacontext/definition/local-current guard around knowledge-index hook matching
- P1 `v11_p1_constraint_omission_trace`: trace constraint marker firing and merge/clearing after baseline source recovery
- P2 `v11_p2_fixture_schema_bridge`: extend sample block scan to PLM-adjacent v5/v6/v7 fixture schema families

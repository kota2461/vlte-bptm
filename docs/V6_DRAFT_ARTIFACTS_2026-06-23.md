# V6 Draft Artifacts 2026-06-23

This note organizes the V6 non-sealed draft artifacts created from cowork logs,
router debate logs, contrast probes, and overfire review. These artifacts are
not sealed fixtures and are not promotion evidence.

## Status

- Branch at cleanup time: `main`
- Sealed/gate usage: none
- Direct training usage: none unless separately human-reviewed and adopted
- Raw debate turn text: review evidence only, not training data

## Canonical V6 Draft Lanes

| Lane | Canonical fixture/report | Review status | Purpose |
| --- | --- | --- | --- |
| Cowork candidates | `tests/fixtures/v6_cowork_candidate_fixture_v1.json` | draft | Candidate examples from cowork raw logs |
| AI boundary candidates | `tests/fixtures/v6_ai_boundary_candidate_fixture_v1.json` | draft | AI-persona/legal/current/political/medical boundary candidates |
| Router debate candidates | `tests/fixtures/v6_router_debate_candidate_fixture_v1.json` | draft | Candidate synthesis from topic-level debate summaries |
| Router debate adopted replay | `tests/fixtures/v6_router_debate_adopted_benchmark_v1.json` | human_reviewed | Non-sealed replay lane adopted by user confirmation |
| Contrast negatives | `tests/fixtures/v6_contrast_negative_benchmark_v1.json` | draft | False-positive / overfire contrast lane |
| Overfire memory candidates | `build/v6_overfire_memory_candidates_v1.json` | pending_human_review | Saved overfire examples, not training data |

## Supporting Scripts

| Script | Output |
| --- | --- |
| `build/probe_cowork_v6_candidates.py` | `build/cowork_v6_candidate_probe_report.json` |
| `build/create_v6_ai_boundary_samples.py` | `tests/fixtures/v6_ai_boundary_candidate_fixture_v1.json` |
| `build/extract_router_debate_v6_candidates.py` | `tests/fixtures/v6_router_debate_candidate_fixture_v1.json` |
| `build/prepare_v6_router_debate_candidate_adoption.py` | adoption plan and import report |
| `build/adopt_v6_router_debate_candidates.py` | adopted non-sealed replay benchmark |
| `build/create_v6_contrast_negative_fixture.py` | contrast negative benchmark/report |
| `build/save_v6_overfire_memory_candidates.py` | overfire memory candidates |

## Local-Only Evidence

The raw LM Studio/router debate run logs are intentionally ignored by `.gitignore`:

- `build/router_debate_*.json`

They are useful as local evidence while reviewing, but the canonical shareable
artifacts are the synthesized fixtures/reports listed above.

The large copied experiment directories are also ignored as local snapshots:

- `experiments/2026-06-19_current-model-no-backup/`
- `experiments/2026-06-19_role-split-detectors/`

## Review Buckets

`build/v6_overfire_memory_candidates_v1.json` keeps all 12 overfire examples, but
separates immediate suppression candidates from boundary cases:

- `clear_suppression_candidate`: 10
- `boundary_review`: 2

Boundary cases are not immediate suppression material because their predicted
risk/current behavior may be legitimate depending on deployment context.

## Recommended Next Repository Step

Create a dedicated branch or WIP commit for the V4/V5/V6 draft corpus and test
additions. Until then, do not use these draft artifacts as sealed or gate data.
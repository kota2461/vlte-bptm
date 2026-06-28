# PLM V4 Roadmap: Failure Memory + Puzzle Learning

Updated: 2026-06-21

## Baseline

V3 sealed has been measured and consumed. V4 must treat V3 sealed text as unavailable for training. V3 measurement may be used only as error taxonomy and target setting.

| Metric | V3 | V4 minimum | V4 stretch |
|---|---:|---:|---:|
| intent_accuracy | 0.857143 | 0.900000 | 0.930000 |
| critical_signal_recall | 0.733333 | 0.850000 | 0.900000 |
| operation_exact_match | 0.821429 | 0.900000 | 0.930000 |
| constraint_exact_match | 0.928571 | 0.920000 | 0.950000 |
| risk_exact_match | 0.964286 | 0.950000 | 0.970000 |
| sealed_error_count | 8 | <=4 | <=2 |
| critical_underprocessing | 0 | 0 | 0 |

## Adopted Inputs

Primary adoption registry:

- `build/v4_failure_memory_adoption_v1.json`
- `build/v4_failure_memory_review_worksheet_v1.md`
- `build/v4_failure_memory_selection_recommendation_v1.json`
- `build/v4_failure_memory_selection_recommendation_v1.md`
- `tests/fixtures/v4_failure_memory_fixture_v1.json`
- `build/v4_failure_memory_replay_v1.json`
- `build/v4_guard_relabel_implementation_report.json`
- `tests/fixtures/v4_puzzle_task_seed_v1.json`
- `build/v4_puzzle_task_seed_report.json`
- `build/v4_puzzle_solver_trace_v1.json`
- `tests/fixtures/v4_puzzle_failure_memory_v1.json`
- `build/v4_puzzle_failure_memory_report.json`
- `build/v4_candidate_eval_report.json`
- `build/v4_sealed_rotation_report.json`
- `tests/fixtures/pattern_language_sealed_v4.json`
- `build/pattern_language_sealed_v4_measurement_report.json`

Adopted non-sealed material:

- intent corpus suspects: 47 total, 12 high-priority/adoption rows in the V4 registry
- suspect ablation misses: 11 non-sealed accumulation misses
- critical/constraints candidates: 60 A/B refs staged from 229 review candidates; current recommendation adopts 38 for review, including 1 bounded context pair
- V3 sealed measurement: taxonomy only, 8 error ids, no sealed text copied into training

Current selection recommendation:

- adopt for review: 38
- context-pair adoption: 1
- manual review before adoption: 0
- exclude/defer for now: 22
- high-score context-dependent exclusions: 6


Current fixture/replay status:

- fixture items: 38
- context pair items: 1
- replay exact match: 38/38 = 1.0
- guard/relabel implementation: route trace now exposes non-invasive failure_guard hints without rewriting packets or writing success-pattern labels

## Contract

- Failure items are not success labels.
- Suspect/rejected/drop/path/url/short-text items enter Failure Memory or guard lanes first.
- High score alone is not enough for adoption; items depending on previous turns, local project state, missing artifacts, or unresolved "this/that/earlier" references are excluded or manually reviewed first. A bounded previous log may be attached as memo/context only when it makes a verify/check guard explicit.
- Puzzle failures enter Puzzle Failure Memory first.
- Human review is required before any item becomes a training or gate fixture.
- V4 promotion requires sealed rotation after V3 consumption.

## Roadmap

| Step | Name | Output | Status |
|---:|---|---|---|
| 1 | Adoption registry and roadmap | `v4_failure_memory_adoption_v1.json`, this roadmap | done |
| 2 | Human review of failure-memory candidates | reviewed adoption rows | done |
| 3 | Failure Memory fixture v1 | non-sealed failure fixture | done |
| 4 | Non-sealed route replay | replay report with V3 target categories | done |
| 5 | Guard/relabel implementation | route trace failure_guard hints | done |
| 6 | Puzzle task schema and seed set | puzzle schema + non-sealed puzzles | done |
| 7 | Puzzle solver trace and failure memory | solver-trace logs + puzzle failure lane | done |
| 8 | V4 candidate eval and sealed rotation | V4 report + active V4 sealed fixture | done |


Current guard/relabel status:

- guard subset match: 38/38 = 1.0
- guard exact match: 38/38 = 1.0
- packet rewrite: disabled
- success-pattern write: disabled


Current puzzle seed status:

- puzzle seed items: 12
- solve route: 10
- clarify route: 2
- domains: arithmetic 2, sequence 2, logic 2, constraint_satisfaction 3, language 1, ambiguous 2
- solver trace items: 12
- solver trace success: 10
- solver trace failure: 2
- puzzle failure memory items: 2
- failure source ids: puzzle-v4-seed-003, puzzle-v4-seed-011



Current Step 8 status:

- V4 candidate eval decision: eligible_for_v4_sealed_measurement
- visible PLM eval: 56/56, intent_accuracy 1.0, critical_signal_recall 1.0
- failure guard exact match: 38/38 = 1.0
- puzzle failure memory items: 2
- PLM sealed v4 fixture: pattern_language_sealed_v4.json
- sealed v4 status: consumed, measured true, reviewed false
- sealed v4 measurement: intent_accuracy 0.857143, critical_signal_recall 0.5625, operation_exact_match 0.75, constraint_exact_match 0.821429, risk_exact_match 0.928571, errors 15
- readiness decision after measurement: blocked / sealed_fixture_not_available
- next action: rotate to sealed v5 before tuning based on v4 measurement

## Puzzle Learning Integration

Puzzle learning starts after the failure-memory review lane is in place. It should produce:

1. Puzzle task schema
   - puzzle input
   - expected answer
   - required operations
   - missing-information and ambiguity flags

2. Solver trace
   - selected route
   - operations emitted
   - confidence
   - fail/success point

3. Puzzle failure memory
   - failure condition
   - bad tendency
   - guard action
   - severity

4. Puzzle replay gate
   - non-sealed replay only
   - compare against V3 measured baseline
   - no active sealed labels for tuning

## First Review Focus

Start with these V3-linked categories:

- clarify -> respond mistakes
- explore -> respond mistakes
- missing_required_information misses
- multiple_intents misses
- operation_exact_match misses
- path/url and weak-question suffix false learning

## V5 Handoff

Next roadmap: `docs/PLM_V5_ROADMAP.md`
Targets and taxonomy: `build/v5_targets_and_roadmap_v1.json`

V5 starts from sealed v4 measurement taxonomy only. Sealed v4 text remains unavailable for training or review fixtures.

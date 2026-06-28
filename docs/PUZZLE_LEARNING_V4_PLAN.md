# Puzzle Learning V4 Plan

Status: sealed v4 measurement complete; puzzle failure memory was included in V4 candidate evaluation, and sealed v4 is now consumed.

## Contract

- V3 is measured against the current adapter state before puzzle learning is connected.
- Puzzle examples, solver traces, success labels, and failure labels are non-sealed V4 training or review material.
- Failures enter a separate failure-memory lane first, not the success-pattern lane.
- Any tuning based on V3 results requires sealed rotation before promotion adjudication.

## Initial lanes

1. Puzzle task schema
   - input puzzle
   - expected answer
   - allowed reasoning operations
   - ambiguity/missing-info flags

2. Solver trace observation
   - selected route
   - operations used
   - confidence
   - where the solve failed or succeeded

3. Failure memory
   - failure condition
   - bad tendency
   - guard action
   - severity

4. V4 candidate gate
   - non-sealed replay only at first
   - no active sealed labels used for tuning
   - compare against V3 measured baseline before promotion

## V4 Adoption Registry

Failure-memory adoption is now tracked in:

- `build/v4_failure_memory_adoption_v1.json`
- `build/v4_failure_memory_review_worksheet_v1.md`
- `build/v4_failure_memory_selection_recommendation_v1.json`
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
- `docs/PLM_V4_ROADMAP.md`

This registry adopts V3-preexisting non-sealed suspect/rejected/candidate material as V4 failure-memory review input. Current fixture has 38 items, including one bounded previous-error-report/check-request context pair. Guard/relabel hints are now exposed from route trace for all 38 fixture items. V3 sealed measurement is taxonomy-only and must not provide training text.

Current review lanes:

- negative_calibration
- clarify_relabel_guard
- low_confidence_short_text
- weak_question_suffix_guard
- critical_constraints_review
- nonsealed_regression
- puzzle_failure_memory

## Step 6 Seed Set

- schema/parser: `semantic_routing/puzzle_task.py`
- fixture: `tests/fixtures/v4_puzzle_task_seed_v1.json`
- report: `build/v4_puzzle_task_seed_report.json`
- seed tasks: 12
- solve route: 10
- clarify route: 2
- policy: non-sealed, no success-pattern write, failures enter Puzzle Failure Memory first

## Step 7 Solver Trace + Failure Memory

- solver trace items: 12
- success: 10
- failure: 2
- failed task ids: puzzle-v4-seed-003, puzzle-v4-seed-011
- Puzzle Failure Memory items: 2
- success traces remain observation-only and are not written to the success-pattern lane

## Step 8 Candidate Eval + Sealed Rotation

- candidate eval decision: eligible_for_v4_sealed_measurement
- puzzle failure memory items included: 2
- success traces remain observation-only
- sealed fixture after rotation: pattern_language_sealed_v4.json
- sealed v4 measurement consumed the fixture
- sealed v4 result: intent_accuracy 0.857143, critical_signal_recall 0.5625, operation_exact_match 0.75, constraint_exact_match 0.821429, risk_exact_match 0.928571, errors 15
- readiness after measurement: blocked / sealed_fixture_not_available

Next tuning work must treat sealed v4 labels as consumed measurement evidence only and rotate to sealed v5 before another adjudication.

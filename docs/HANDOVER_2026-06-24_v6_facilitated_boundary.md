# Handover Report: V6 Facilitated Boundary Calibration

Date: 2026-06-24
Workspace: `D:\Thought State Register`

## Purpose

This report summarizes the long-thread state around V6 boundary calibration, especially false-positive / contrast-negative repair, router-facilitated Gemma/Qwen debate logs, and current score readiness.

The short version: the facilitated debate flow is working, the latest 3-topic rerun is clean, and risk/constraint handling improved. However, the current V6 target/readiness reference is not met because intent and operation selection still fail on the low-risk contrast repair surface.

## Contract And Safety State

- Sealed fixtures were not opened during this V6 facilitated review/check work.
- Raw debate logs are review evidence only and are not direct training data.
- Candidate use still requires synthesis and human review.
- Current route measurements are diagnostic/non-gate unless explicitly promoted by the contract.
- Same-cycle promotion remains disallowed.

## Main Implementation Changes

### Router Debate Facilitator

Files:

- `debate_lab/router_debate.py`
- `debate_lab/debate_config.json`
- `debate_lab/README.md`
- `tests/test_debate_lab.py`

Implemented behavior:

- Router now emits a light facilitator/moderator comment after each Gemma/Qwen round.
- The next Gemma turn receives both the prior Qwen critique and the router moderator note.
- Moderator notes focus on measured weak fields:
  - `intent_accuracy`
  - `operation_exact_match`
  - `risk_exact_match`
- Theme focus rules were added for:
  - metalinguistic mention / mention-vs-use
  - current/search split
  - AI dependency/persona boundary
  - legal/license boundary
  - medical/design boundary
  - mixed ja/en boundary
  - severity ladder boundary
- Run summaries now include `moderator_comment_count`.

Verification:

- Full test run after facilitator addition: `491 passed`.

## Latest Facilitated Debate Log

Source:

- `build/router_debate_v6_facilitated_contrast_repair.json`

Review outputs:

- `build/router_debate_v6_facilitated_contrast_repair_review_v1.json`
- `build/router_debate_v6_facilitated_contrast_repair_review_v1.md`

Latest clean rerun status:

| metric | value |
| --- | ---: |
| topic_count | 3 |
| turn_count | 12 |
| closed_topic_count | 3 |
| moderator_comment_count | 6 |
| finish_reason stop | 12 |
| finish_reason length | 0 |
| hidden_reasoning_content_chars | 0 |
| candidate_ready_count | 3 |
| candidate_ready_with_caution_count | 0 |

Topics:

| topic | status | note |
| --- | --- | --- |
| `repair-ai-label-use-respond-vs-verify` | candidate_ready | clean |
| `repair-ai-readme-parameter-name` | candidate_ready | clean |
| `repair-creative-emotion-word-use` | candidate_ready | clean after rerun |

Required debate sections were present across all 3 topics:

- `classification_rule`
- `should_fire_examples`
- `should_not_fire_examples`
- `boundary_cases`
- `candidate_sample_notes`

## Score Comparison

Source:

- `build/router_debate_v6_facilitated_score_comparison_v1.json`
- `build/router_debate_v6_facilitated_score_comparison_v1.md`

| scenario | cases | score | raw | errors | intent | operation | constraint | risk |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| facilitated clean 3 | 3 | 0.625000 | 0.500000 | 2 | 0.333333 | 0.333333 | 1.000000 | 1.000000 |
| official adopted priority lane | 26 | 0.451923 | 0.361538 | 26 | 0.423077 | 0.192308 | 0.807692 | 0.307692 |

Delta:

- facilitated clean 3 vs official adopted priority lane: `+0.173077`
- no rerun-recommended topics remain; clean-only and included scenarios are now identical.

Interpretation:

- The facilitated rerun materially improved the small clean sample.
- Risk and constraint behavior are now strong on this 3-case surface.
- The remaining failures are concentrated in intent/operation, especially `build` expected cases falling to `respond`.

## Target / Readiness Check

Source:

- `build/router_debate_v6_facilitated_target_check_v1.json`
- `build/router_debate_v6_facilitated_target_check_v1.md`

Important caveat:

- No dedicated V6 target file was found.
- The check therefore uses the existing V5 minimum/stretch targets and pre-sealed nonsealed gate target `0.95` as reference targets.

Summary:

| item | value |
| --- | ---: |
| latest_facilitated_score | 0.625000 |
| official_adopted_priority_score | 0.451923 |
| v6_average_nonsealed_score | 0.874084 |
| reference target | 0.950000 |

Conclusion:

- `not_met_for_v6_readiness`

Scenario target checks:

| scenario | cases | score | >=0.95 | V5-min pass fields | V5-min fail fields |
| --- | ---: | ---: | --- | --- | --- |
| facilitated_clean_3 | 3 | 0.625000 | false | constraint, risk, error-count-reference | intent, operation |
| official_adopted_priority_26 | 26 | 0.451923 | false | none | intent, operation, constraint, risk, error-count-reference |
| v6_contrast_negative_30 | 30 | 0.666667 | false | none | intent, operation, constraint, risk, error-count-reference |

## V6 Current Score Report

Source:

- `build/v6_score_report_v1.json`
- `build/v6_score_summary_v1.md`

Current summary:

| metric | value |
| --- | ---: |
| lane_count | 7 |
| exact_lane_count | 5 |
| gap_lane_count | 2 |
| average_nonsealed_score | 0.874084 |
| average_nonsealed_raw_score | 0.784982 |

Gap lanes:

- `v6_boundary_priority_review_adopted`
- `v6_contrast_negative`

Key lanes:

| lane | cases | score | raw | errors | intent | operation | constraint | risk |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `v6_boundary_priority_review_adopted` | 26 | 0.451923 | 0.361538 | 26 | 0.423077 | 0.192308 | 0.807692 | 0.307692 |
| `v6_contrast_negative` | 30 | 0.666667 | 0.533333 | 17 | 0.566667 | 0.533333 | 0.833333 | 0.733333 |
| `v6_boundary_false_positive_adopted` | 15 | 1.000000 | 0.800000 | 0 | 1.000000 | 1.000000 | 1.000000 | 1.000000 |

## Adopted / Candidate State

Important artifacts:

- `build/v6_boundary_priority_review_adoption_decision_v1.json`
- `tests/fixtures/v6_boundary_priority_review_adopted_benchmark_v1.json`
- `build/v6_boundary_priority_review_adopted_replay_report_v1.json`
- `build/v6_boundary_priority_review_adopted_worksheet_v1.md`
- `build/v6_boundary_debate_candidate_queue_v1.json`
- `build/v6_boundary_debate_candidate_queue_review_v1.json`

Adopted priority review lane:

- adopted_count: 26
- review_status: human_reviewed
- expected risk: all low
- current score: 0.451923
- current errors: 26/26

The adopted lane remains a valuable failure surface, not a readiness pass.

## Current Technical Weakness

The most important current weakness is not risk suppression anymore on the latest small facilitated sample. It is route/action selection:

- `build` expected cases often route as `respond`.
- This harms both `intent_accuracy` and `operation_exact_match`.
- This is especially visible in metalinguistic / structural requests:
  - labels
  - headings
  - README parameter names
  - tags
  - glossary or column names

Working hypothesis:

- The router correctly suppresses high risk on many low-risk contrast cases.
- However, it does not consistently distinguish structural edit/build requests from ordinary response/explanation requests.

## Recommended Next Steps

1. Define a dedicated V6 target file.

   Suggested artifact:

   - `build/v6_targets_and_readiness_v1.json`
   - `docs/PLM_V6_ROADMAP.md`

   Reason: current checks borrow V5 targets. V6 needs explicit boundary-calibration goals.

2. Improve intent/operation selection for structural metalinguistic requests.

   Focus patterns:

   - `add the label ...`
   - `add a README parameter ...`
   - `save ... as a tag`
   - `add a CSV column named ...`
   - `create a table/list/schema using the word ...`

   Expected correction:

   - `respond` -> `build`
   - `respond` operation -> `build` operation
   - keep risk low and constraints clean.

3. Replay the latest facilitated clean 3 and adopted priority 26 after the route fix.

   Watch metrics:

   - facilitated clean 3: target short-term score should jump from `0.625` to near `1.0` if the two intent/operation misses are fixed.
   - official adopted priority 26: target short-term score should improve mainly through operation and risk stability.

4. Then rerun V6 score report.

   Command pattern:

   ```powershell
   python -B build\compare_v6_facilitated_scores.py
   python -B build\check_v6_facilitated_targets.py
   python -B build\measure_v6_scores.py
   python -B -m pytest tests\test_v6_score_report.py tests\test_debate_lab.py
   ```

5. Only after non-sealed gap lanes are materially improved, consider the next sealed rotation/measurement plan.

## Known Workspace Issue

Two temporary helper scripts could not be deleted due to Windows access denial / lock:

- `build/_tmp_review_facilitated_log.py`
- `build/_tmp_update_facilitated_notes.py`

This resembles the previous Windows/Kaspersky/lock behavior. They are not part of the model contract and can be removed once the lock clears.

## Current Bottom Line

- Facilitated debate mechanism: working.
- Latest facilitated logs: clean.
- Risk/constraint on latest clean sample: good.
- Intent/operation: still weak.
- V6 readiness/reference target: not reached.
- Best next move: fix `respond` vs `build` for metalinguistic structural actions, then replay scores.
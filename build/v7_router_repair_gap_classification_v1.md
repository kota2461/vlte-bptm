# V7 Router Repair Gap Classification v1

Status: router repair completed from non-sealed candidate replay.

This file classifies the 11 provisional repair gaps from `tests/fixtures/v7_router_debate_candidate_fixture_v1.json`. It is diagnostic review material only. It is not sealed evidence and it is not a gate.

## Measurement

| State | Pass | Repair Gap | Intent | Critical | Operation | Constraint | Risk |
|---|---:|---:|---:|---:|---:|---:|---:|
| Before repair | 7/18 | 11 | 0.722222 | 0.555556 | 0.666667 | 0.611111 | 0.833333 |
| After repair | 18/18 | 0 | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 |

## Classes

| Class | Cases | Repair |
|---|---|---|
| defined_artifact_vs_missing_target | 002, 003 | Distinguish explicit edit target from history-dependent missing target; preserve ask-first and build bridge. |
| local_current_vs_external_current | 007 | Treat today's local conversation/log as local context; keep no_web_search, suppress external current search. |
| unverified_truth_check_vs_record_only | 010, 011 | Fire verify for truth-check before report; suppress verify for explicit hypothesis-note recording. |
| constraint_stack_low_risk | 012, 013 | Preserve no-table/neutral/avoid-diagnosis/bullets while keeping low risk for UI/general info. |
| legal_source_lookup_medium | 014 | Route Article + citations as verify/search with medium legal risk. |
| terminal_action_sequence | 016, 017, 018 | Keep terminal deliverable primary while preserving verify/summarize/compare prerequisites. |

## Result

`build/v7_router_debate_candidate_probe_report_v1.json` now reports `error_count: 0`. Candidate replay remains a non-gate diagnostic; human review is still required before any training or fixture promotion.
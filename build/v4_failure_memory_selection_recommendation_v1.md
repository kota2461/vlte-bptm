# V4 Failure Memory Selection Recommendation v1

Policy: non-sealed sources only. High score is not enough for adoption when the item depends on missing thread context. Bounded context-pair adoption is allowed when the previous log is used only as memo/context.

## Summary

- candidate_count: 60
- selected_count: 38
- selected_context_pair_count: 1
- manual_review_count: 0
- excluded_for_now_count: 22
- selected_score_ge_17: 33
- selected_score12_fillers: 5
- high_score_context_excluded: 6

## Adopt For Review

- cc-open-v1-001 score=45 intent=summarize decision=adopt_for_review reason=score>=17 and sufficiently standalone after context-dependence review
- cc-open-v1-002 score=36 intent=verify decision=adopt_for_review reason=score>=17 and sufficiently standalone after context-dependence review
- cc-open-v1-003 score=35 intent=verify decision=adopt_for_review reason=score>=17 and sufficiently standalone after context-dependence review
- cc-open-v1-007 score=26 intent=verify decision=adopt_for_review reason=score>=17 and sufficiently standalone after context-dependence review
- cc-open-v1-009 score=21 intent=build decision=adopt_for_review reason=score>=17 and sufficiently standalone after context-dependence review
- cc-open-v1-010 score=21 intent=clarify decision=adopt_for_review reason=score>=17 and sufficiently standalone after context-dependence review
- cc-open-v1-011 score=21 intent=clarify decision=adopt_for_review reason=score>=17 and sufficiently standalone after context-dependence review
- cc-open-v1-012 score=21 intent=clarify decision=adopt_for_review reason=score>=17 and sufficiently standalone after context-dependence review
- cc-open-v1-013 score=21 intent=clarify decision=adopt_for_review reason=score>=17 and sufficiently standalone after context-dependence review
- cc-open-v1-014 score=21 intent=clarify decision=adopt_for_review reason=score>=17 and sufficiently standalone after context-dependence review
- cc-open-v1-015 score=21 intent=clarify decision=adopt_for_review reason=score>=17 and sufficiently standalone after context-dependence review
- cc-open-v1-016 score=21 intent=clarify decision=adopt_for_review reason=score>=17 and sufficiently standalone after context-dependence review
- cc-open-v1-017 score=21 intent=clarify decision=adopt_for_review reason=score>=17 and sufficiently standalone after context-dependence review
- cc-open-v1-018 score=20 intent=verify decision=adopt_for_review reason=score>=17 and sufficiently standalone after context-dependence review
- cc-open-v1-019 score=20 intent=verify decision=adopt_for_review reason=score>=17 and sufficiently standalone after context-dependence review
- cc-open-v1-020 score=20 intent=verify decision=adopt_for_review reason=score>=17 and sufficiently standalone after context-dependence review
- cc-open-v1-021 score=20 intent=verify decision=adopt_for_review reason=score>=17 and sufficiently standalone after context-dependence review
- cc-open-v1-022 score=19 intent=build decision=adopt_for_review reason=score>=17 and sufficiently standalone after context-dependence review
- cc-open-v1-023 score=19 intent=build decision=adopt_for_review reason=score>=17 and sufficiently standalone after context-dependence review
- cc-open-v1-024 score=19 intent=build decision=adopt_for_review reason=score>=17 and sufficiently standalone after context-dependence review
- cc-open-v1-025 score=19 intent=build decision=adopt_for_review reason=score>=17 and sufficiently standalone after context-dependence review
- cc-open-v1-026 score=19 intent=build decision=adopt_for_review reason=score>=17 and sufficiently standalone after context-dependence review
- cc-open-v1-027 score=19 intent=summarize decision=adopt_for_review reason=score>=17 and sufficiently standalone after context-dependence review
- cc-open-v1-028 score=19 intent=verify decision=adopt_for_review reason=score>=17 and sufficiently standalone after context-dependence review
- cc-open-v1-029 score=19 intent=verify decision=adopt_for_review reason=score>=17 and sufficiently standalone after context-dependence review
- cc-open-v1-030 score=19 intent=verify decision=adopt_for_review reason=score>=17 and sufficiently standalone after context-dependence review
- cc-open-v1-031 score=19 intent=verify decision=adopt_for_review reason=score>=17 and sufficiently standalone after context-dependence review
- cc-open-v1-032 score=19 intent=verify decision=adopt_for_review reason=score>=17 and sufficiently standalone after context-dependence review
- cc-open-v1-034 score=19 intent=verify decision=adopt_for_review reason=score>=17 and sufficiently standalone after context-dependence review
- cc-open-v1-035 score=19 intent=verify decision=adopt_for_review reason=score>=17 and sufficiently standalone after context-dependence review
- cc-open-v1-036 score=19 intent=verify decision=adopt_for_review reason=score>=17 and sufficiently standalone after context-dependence review
- cc-open-v1-037 score=19 intent=verify decision=adopt_for_review reason=score>=17 and sufficiently standalone after context-dependence review
- cc-open-v1-038 score=19 intent=verify decision=adopt_context_pair_for_review reason=adopt as previous-error-report + verify/check-request context pair; not as standalone utterance context_pair=previous_error_report_then_verify_check_request
- cc-open-v1-051 score=12 intent=clarify decision=adopt_for_review reason=score12 filler selected for missing-info, respond-boundary, or summarize-boundary coverage
- cc-open-v1-054 score=12 intent=clarify decision=adopt_for_review reason=score12 filler selected for missing-info, respond-boundary, or summarize-boundary coverage
- cc-open-v1-055 score=12 intent=clarify decision=adopt_for_review reason=score12 filler selected for missing-info, respond-boundary, or summarize-boundary coverage
- cc-open-v1-056 score=12 intent=clarify decision=adopt_for_review reason=score12 filler selected for missing-info, respond-boundary, or summarize-boundary coverage
- cc-open-v1-058 score=12 intent=summarize decision=adopt_for_review reason=score12 filler selected for missing-info, respond-boundary, or summarize-boundary coverage

## Context Pair Detail

- cc-open-v1-038: previous_error_report_then_verify_check_request
  - context memo: data\harvested_claudelog_v1.json#examples[265] / note=pasted-ish error mention 'this error after an update?' -> reporting an error/status; borderline drop but has a question framing
  - request: data\harvested_claudelog_v1.json#examples[266] / note=tried once, it's erroring; please check it
  - guard: verify_up, inspect_error_context, avoid_status_only_response, ask_for_missing_artifact_if_error_context_absent

## Exclude / Defer

- cc-open-v1-004 score=33 intent=respond reason=project-specific stance/status text; high score is from current-info/multi-intent markers, but standalone signal is weak
- cc-open-v1-005 score=26 intent=verify reason=depends on a previous recommendation ('suggested earlier'); keep for context-aware tests, not first failure-memory adoption
- cc-open-v1-006 score=26 intent=verify reason=depends on the referenced tutorial/app; useful pattern, but should be rewritten into a self-contained synthetic case before training
- cc-open-v1-008 score=26 intent=verify reason=depends on a previously taught method and current version; context-aware validity check rather than standalone router pattern
- cc-open-v1-033 score=19 intent=verify reason=project-specific LoRA/Codex planning text from low-confidence origin; too much local context for a general guard
- cc-open-v1-039 score=17 intent=verify reason=project/status-sharing continuation; score17 but source intent is respond and context is highly local
- cc-open-v1-040 score=12 intent=build reason=score12 build/multiple-intent; overlaps with higher quality build multi-intent examples
- cc-open-v1-041 score=12 intent=build reason=very broad long-horizon build request; too large and noisy for first failure-memory pass
- cc-open-v1-042 score=12 intent=build reason=covered by stronger summarize/build multi-intent cases; low unique risk
- cc-open-v1-043 score=12 intent=build reason=broad roadmap/meta-planning text; likely to create noisy build bias
- cc-open-v1-044 score=12 intent=build reason=generic explain-then-build; covered by score19 verify/build and score12 selected fillers
- cc-open-v1-045 score=12 intent=build reason=short context-dependent continuation; weak standalone training signal
- cc-open-v1-046 score=12 intent=build reason=context-dependent continuation; weak standalone training signal
- cc-open-v1-047 score=12 intent=build reason=long meta-learning proposal; useful later for puzzle lane, too noisy for first pass
- cc-open-v1-048 score=12 intent=build reason=too short/context-dependent; likely ambiguous without thread state
- cc-open-v1-049 score=12 intent=build reason=too short/context-dependent; continuation command rather than generalizable pattern
- cc-open-v1-050 score=12 intent=build reason=too short/context-dependent; continuation command rather than generalizable pattern
- cc-open-v1-052 score=12 intent=clarify reason=clarify/multiple-intent but asks meta workflow; lower priority than missing-info clarify fillers
- cc-open-v1-053 score=12 intent=clarify reason=valuable conceptually but meta-labeling discussion may blur failure vs success lanes; defer to puzzle/failure schema phase
- cc-open-v1-057 score=12 intent=respond reason=option-B continuation with a follow-up log request; too dependent on prior choices for the first failure-memory fixture
- cc-open-v1-059 score=12 intent=summarize reason=summarize+risk is useful but risk/legal-ish domain may need separate high-stakes policy pass
- cc-open-v1-060 score=10 intent=explain reason=score10; simple router capability question, lower priority for V4 failure-memory target

# Weakpoint Explain (English) Debate Candidate Review Worksheet v1

Raw debate turns are not training data. Rewrite selected candidates into short self-contained non-sealed samples before any fixture adoption.

## Summary

- source_topic_count: 26
- candidate_count: 26
- usable_review_candidate_count: 26
- hold_for_manual_review_count: 0
- not_enough_signal_count: 0
- router_before_miss_count: 11
- turn_count: 208
- expected_rounds: 4
- status_counts: {'usable_review_candidate': 26}
- focus_counts: {'English explore recall': 1, 'English respond recall': 1, 'break_down disambiguation': 1, 'explain false-positive guard': 1, 'explain mixed-language': 1, 'explain paraphrase transfer': 1, 'explain recall (English colloquial)': 1, 'explain recall (English)': 9, 'explain vs build boundary': 1, 'explain vs explore boundary': 1, 'explain vs respond minimal pair': 1, 'explain vs verify boundary': 1, 'explore vs explain': 1, 'multi-intent build+explain': 1, 'multi-intent explore+explain': 1, 'multi-intent verify+explain': 1, 'respond vs explain minimal pair': 1, 'verify vs explain': 1}
- target_intent_counts: {'explain': 18, 'explore': 3, 'respond': 3, 'verify': 2}
- top_axis_counts: {'weakpoint': 26, 'english': 25, 'explain': 20, 'colloquial': 4, 'explain_false_positive': 3, 'respond': 3, 'explore': 3, 'multiple_intents': 3, 'verify': 2, 'explain_vs_respond': 2, 'explain_vs_build': 2, 'respond_vs_explain': 1, 'explain_vs_explore': 1, 'explain_vs_verify': 1, 'operation_terminal': 1, 'unverified_claim': 1, 'paraphrase': 1, 'mixed_language': 1}

## Candidates

| id | status | score | topic | target | router_before | miss | rounds | chars | cautions | theme |
|---|---|---:|---|---|---|:--:|---:|---:|---|---|
| weakpoint-explain-english-candidate-013 | usable_review_candidate | 100 | we-bnd-01 | respond | explain | YES | 4 | 23331 | - | English: 'Is 0.1 + 0.2 == 0.3 in Python?' route respond/verify, NOT explain. |
| weakpoint-explain-english-candidate-014 | usable_review_candidate | 100 | we-bnd-02 | verify | explain | YES | 4 | 26366 | - | English: 'Check whether this regex is correct.' verify, not explain. |
| weakpoint-explain-english-candidate-015 | usable_review_candidate | 100 | we-bnd-03 | explore | explain | YES | 4 | 30448 | - | English: 'Compare REST vs GraphQL for my use case.' explore, not explain. |
| weakpoint-explain-english-candidate-016 | usable_review_candidate | 100 | we-bnd-04 | respond | explain | YES | 4 | 22528 | - | English: 'What is a semaphore?' respond (definition), not explain (how-it-works). |
| weakpoint-explain-english-candidate-017 | usable_review_candidate | 100 | we-bnd-05 | explore | explain | YES | 4 | 28574 | - | English: 'List a few ways to cache API responses.' explore, not explain. |
| weakpoint-explain-english-candidate-018 | usable_review_candidate | 100 | we-bnd-06 | respond | verify | YES | 4 | 22175 | - | English: 'Tell me the capital of Australia.' respond. |
| weakpoint-explain-english-candidate-001 | usable_review_candidate | 100 | we-explain-01 | explain | explain | no | 4 | 26468 | - | In English, a user asks why adding an index sped up a slow query. Route to explain (mechanism/cause), not respond (one-line fact) and not verify. |
| weakpoint-explain-english-candidate-002 | usable_review_candidate | 100 | we-explain-02 | explain | explain | no | 4 | 27918 | - | English: 'Help me understand how OAuth refresh tokens actually work.' Route to explain, not respond. |
| weakpoint-explain-english-candidate-003 | usable_review_candidate | 100 | we-explain-03 | explain | explain | no | 4 | 28786 | - | English colloquial: 'I don't really get why my recursion overflows.' Route to explain. |
| weakpoint-explain-english-candidate-004 | usable_review_candidate | 100 | we-explain-04 | explain | build | YES | 4 | 26190 | - | English: 'Walk me through what causes cache invalidation bugs.' explain, not build. |
| weakpoint-explain-english-candidate-005 | usable_review_candidate | 100 | we-explain-05 | explain | explain | no | 4 | 31364 | - | English: 'Explain what a p-value actually means here' vs 'What is a p-value' -- explain (meaning-in-context) vs respond (definition). |
| weakpoint-explain-english-candidate-006 | usable_review_candidate | 100 | we-explain-06 | explain | explain | no | 4 | 27336 | - | English: 'Why is my Docker image so large?' Route to explain (cause), not respond. |
| weakpoint-explain-english-candidate-007 | usable_review_candidate | 100 | we-explain-07 | explain | explain | no | 4 | 24885 | - | English: 'Can you explain the difference between TCP and UDP and why it matters' -- explain, even though 'difference' hints explore/compare. |
| weakpoint-explain-english-candidate-008 | usable_review_candidate | 100 | we-explain-08 | explain | explain | no | 4 | 26221 | - | English: 'I never really understood why floating point is imprecise.' explain. |
| weakpoint-explain-english-candidate-009 | usable_review_candidate | 100 | we-explain-09 | explain | explain | no | 4 | 27897 | - | English: 'How does gradient descent actually converge?' explain (how/why), not respond. |
| weakpoint-explain-english-candidate-010 | usable_review_candidate | 100 | we-explain-10 | explain | explain | no | 4 | 29383 | - | English: 'Explain why my unit test passes locally but fails in CI.' explain vs verify('check it'). |
| weakpoint-explain-english-candidate-011 | usable_review_candidate | 100 | we-explain-11 | explain | explain | no | 4 | 29989 | - | English: 'What's the reasoning behind using a message queue here?' explain. |
| weakpoint-explain-english-candidate-012 | usable_review_candidate | 100 | we-explain-12 | explain | explain | no | 4 | 28260 | - | English: 'Give me the intuition behind backpropagation.' explain. |
| weakpoint-explain-english-candidate-019 | usable_review_candidate | 100 | we-multi-01 | explain | build | YES | 4 | 30618 | - | English: 'Draft a rollout plan, then explain the risky step.' multiple_intents: build then explain terminal. |
| weakpoint-explain-english-candidate-020 | usable_review_candidate | 100 | we-multi-02 | explore | explain | YES | 4 | 30577 | - | English: 'Should I use Postgres or MongoDB? Explain your reasoning.' explore + explain. |
| weakpoint-explain-english-candidate-021 | usable_review_candidate | 100 | we-multi-03 | verify | explain | YES | 4 | 29012 | - | English: 'Verify these invoice totals and explain any discrepancy.' verify + explain, unverified_claim signal. |
| weakpoint-explain-english-candidate-022 | usable_review_candidate | 100 | we-para-01 | explain | explain | no | 4 | 26670 | - | English paraphrase cluster for explain: 'why', 'how come', 'what's the reason', 'help me understand' -- all explain. |
| weakpoint-explain-english-candidate-023 | usable_review_candidate | 100 | we-para-02 | explain | explain | no | 4 | 25782 | - | Mixed ja/en: 'このアルゴリズムが速い理由を explain して' -- explain (mixed language). |
| weakpoint-explain-english-candidate-024 | usable_review_candidate | 100 | we-para-03 | explain | explain | no | 4 | 27503 | - | English: 'I'm confused about how JWT signing works.' explain (colloquial confusion cue). |
| weakpoint-explain-english-candidate-025 | usable_review_candidate | 100 | we-para-04 | explain | build | YES | 4 | 30710 | - | English boundary: 'break down why this approach scales better' = explain, vs 'break down the tasks' = build. Disambiguate 'break down'. |
| weakpoint-explain-english-candidate-026 | usable_review_candidate | 100 | we-para-05 | explain | explain | no | 4 | 24643 | - | English: 'what's going on when my container OOMs?' explain (cause). |

## Review Checklist

- Keep only candidates that can be rewritten without copying raw LLM prose.
- Prefer minimal pairs that directly address the explain-vs-respond / explain-vs-verify boundary.
- The `miss` column flags where the pre-debate router did not already route to the target intent; prioritise those.
- Separate should_fire from should_not_fire; do not make broad suppression rules from vague cases.
- Preserve constraints and terminal action in the rewritten sample.
- Mark all accepted rows as human-reviewed before fixture use.

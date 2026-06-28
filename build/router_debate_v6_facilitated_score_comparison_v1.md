# Router Debate V6 Facilitated Score Comparison v1

| scenario | cases | score | raw | errors | intent | operation | constraint | risk |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| clean_only_excluding_rerun_recommended | 3 | 0.625000 | 0.500000 | 2 | 0.333333 | 0.333333 | 1.000000 | 1.000000 |
| with_caution_item_included | 3 | 0.625000 | 0.500000 | 2 | 0.333333 | 0.333333 | 1.000000 | 1.000000 |
| official_adopted_priority_review_lane | 26 | 0.451923 | 0.361538 | 26 | 0.423077 | 0.192308 | 0.807692 | 0.307692 |

## Deltas

- clean_vs_official_score_delta: +0.173077
- included_vs_clean_score_delta: +0.000000
- included_vs_official_score_delta: +0.173077

## Notes

- No rerun-recommended topics remain; clean-only and included scenarios are identical.
- official_adopted_priority_review_lane is the existing 26-case adopted lane in `build/v6_score_report_v1.json`.
- This is a non-sealed replay comparison and is not a promotion gate.

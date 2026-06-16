# Semantic Adapter Performance — Frozen 50-case Campaign (2026-06-13)

Subject: `deterministic_signal_extractor` v0.2 (`semantic_routing/baseline.py`
→ `processing_plan.py`), measured end-to-end (text → intent +
processing_class + core_mode).

Status: **measurement only**. Campaign labels are still DRAFT (not
human-ratified), so the accuracy figures are a provisional pre-review
baseline. The adapter is never tuned to these cases (`same_batch_tuning`
forbidden); sealed v2 is not touched. Reproduce with
`python build/adapter_performance_v1.py`; machine-readable detail (all
misses, per-source) in `build/adapter_performance_v1_report.json`.

## 1. Integrity (確認)

- Full test suite: **254 passed**.
- Campaign: 50 cases, status `ready_for_review`, round-trips through the
  strict contract parser, **no overlap** with the visible benchmark
  (train/validation).
- sealed v2 (`pattern_language_sealed_v2.json`) remains unopened.

## 2. Headline metrics

| Metric | Value |
| --- | ---: |
| semantic_intent accuracy | 0.52 |
| processing_plan accuracy | 0.50 |
| **end_to_end accuracy** | **0.32** (16/50) |
| critical under-processing | **10** (gate allows 0) |
| latency | **0.108 ms/request** |

Speed is a non-issue (deterministic, ~0.1 ms). The gap is accuracy, and it
is concentrated, not diffuse.

## 3. By category

| category | e2e | intent | plan | critical |
| --- | ---: | ---: | ---: | ---: |
| verify_then_build | **0.18** | 0.36 | 0.73 | **8 / 11** |
| indirect_explanation | **0.22** | 0.22 | 0.22 | 0 / 9 |
| conversation_response | 0.29 | 0.86 | 0.43 | 0 / 7 |
| temporal_disambiguation | 0.33 | 0.67 | 0.50 | 0 / 6 |
| compound_intent | 0.36 | 0.55 | 0.36 | 1 / 11 |
| mixed_language | 0.67 | 0.67 | 0.83 | 1 / 6 |

## 4. By source and language

| source | e2e | cases |
| --- | ---: | ---: |
| real-log (owner) | **0.00** | 3 |
| synthetic-human-learning | **0.08** | 13 |
| synthetic-contract | 0.30 | 10 |
| original batch-01 | 0.50 | 24 |

| language | e2e | cases |
| --- | ---: | ---: |
| ja | 0.21 | 33 |
| en | 0.45 | 11 |
| mixed | 0.67 | 6 |

The most natural language (real logs, human-learning phrasings) is the
hardest. This is the central finding: the marker-based extractor does not
generalize to natural, indirect phrasing.

## 5. The three weakness clusters (consistent with the failure diagnosis)

Matches `docs/SEMANTIC_ADAPTER_failure_diagnosis_2026-06-13.md`:

1. **verify_then_build — top priority (safety).** 8 of the 10 critical
   under-processing cases are here. Intent detection (0.36) and the
   "verify-then-build" sequencing collapse: the extractor either drops the
   verification prerequisite or stops at verify and never builds. The gate
   requires 0 critical under-processing, so this is the gating defect.
2. **indirect_explanation — lowest (0.22).** With no explicit "explain"
   marker, intent falls to the 0.45 no-match path; the wrong intent
   cascades into a wrong plan.
3. **conversation → clarify over-abstention.** Intent is usually right
   (0.86) but the plan drops to clarify (plan 0.43) via the same no-match
   path, over-processing simple responses.

## 6. Interpretation and next steps

- **0.32 is provisional.** Several misses — especially the 3 real-log cases
  and the policy-laden verify/build and explore/respond items — are draft
  labels that encode contestable decisions. Human review will ratify or
  correct them, and corrected `expected` becomes the measurement target
  (the review-log overlay is wired). The number can move after review.
- **Correct order: review the 50 first** (toward the 40-approved gate),
  then the adapter-improvement track targets the three clusters above —
  validated on off-batch data, never by fitting this campaign.
- The improvement that matters most for safety is verify_then_build
  sequencing (remove the dependence on an explicit connective marker so
  build-after-verify keeps its verification prerequisite).
- "Learning" these domains (contract / human-learning) is a separate track
  that begins only after this measurement: either adapter coverage fixes
  (off-batch) or a router curriculum, never same-batch tuning.

## 7. Reproduction

```powershell
python -m pytest -q
$env:PYTHONPATH="."; python build\adapter_performance_v1.py
```

Outputs `build/adapter_performance_v1_report.json` (overall, by
category/source/language, latency, and every miss with expected vs actual).

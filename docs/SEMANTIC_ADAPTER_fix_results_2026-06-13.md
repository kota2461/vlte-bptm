# Semantic Adapter Fix Results — Priority 1 & 2 (2026-06-13)

Subject: `deterministic_signal_extractor` v0.2 (`semantic_routing/baseline.py`).
Follows the pre-fix baseline in `docs/SEMANTIC_ADAPTER_performance_2026-06-13.md`
(0.32 end-to-end, 10 critical under-processing).

Discipline: all fixes are principled structural / coverage changes validated
on TWO held-out sets of fresh phrasings — never fitted to the 50-case
campaign (`same_batch_tuning` forbidden), and the campaign is re-measured
once after each change. sealed v2 stays unopened throughout.

## 1. Headline

| Metric | Pre-fix | After P1 | After P2 |
| --- | ---: | ---: | ---: |
| end_to_end accuracy | 0.32 | 0.52 | **0.76** |
| critical under-processing | 10 | **0** | **0** |
| processing_plan accuracy | 0.50 | — | 0.90 |
| semantic_intent accuracy | 0.52 | — | 0.80 |
| held-out (vtb / P2) | — | 5/5 vtb | 14/15 · 11/11 |

254 tests pass throughout. Adapter latency ~0.12 ms/request (deterministic).

## 2. Priority 1 — verify_then_build (safety / critical gate)

Three structural defects in `baseline.py`:

1. **Build deliverable-verb coverage.** Added 作っ/作成/用意/ドラフト/段取り/
   組ん/組み立て/draft/produce/prepare/checklist… so a request that names a
   thing to make is detected as build (was: only nouns like 手順/タスク).
2. **Verify conjugation + coverage.** Added the 確かめ stem (covers 確かめた),
   検算/確認する/合ってい/見てもらって/レビュー/review… (was: 確かめて only,
   missing the た-form).
3. **Removed the connective dependence.** Build-promotion and the verify
   prerequisite no longer require `MULTIPLE_INTENT_MARKER` ("その上で"/"and
   then"). A request carrying both a build deliverable and a verify signal is
   a verify-then-build sequence regardless of an explicit connective —
   relying on one silently dropped the verification gate (build without its
   verify step = critical under-processing).

Result: critical 10→0 (**safety gate cleared**), verify_then_build category
0.18→0.91, held-out vtb 0/5→5/5 (generalizes).

## 3. Priority 2 — accuracy (no-match over-abstention + indirect intent)

1. **No-match fallback 0.45 → 0.62.** When no marker fires, the input is a
   plain response/explanation, not genuine ambiguity — default to
   respond/economy instead of tripping the low-confidence → clarify path.
   Real missing-information still routes to clarify via its own markers /
   `information_state`.
2. **Indirect-explanation markers.** なんで/ピンとこない/腑に落ち/しっくりこ
   ない/実感がわかない/don't get/can't see why… for "I can do it but don't
   grasp WHY" phrasings.
3. **False-positive narrowing (general correctness bugs).**
   - removed over-broad build verb 書いて/書き出 (matched 「何を書いて*いる
     のか*」 — describing, not requesting)
   - current-info 現在 → 現在の/現在は (matched 現在完了, the tense)
   - calculate regex now requires a calculation request (計算して/を計算/
     計算結果…), not bare 計算 (matched 計算*はできる*)
   - added multiple-intent connectives そのうえで/その後で/and point out and
     explore 比べて

Result: end_to_end 0.52→0.76, critical stays 0, processing_plan 0.90,
held-out P2 11/11.

Trade-off recorded: removing 書いて cost one niche held-out vtb case
(「スクリプトを書いて」) — accepted, because the campaign critical stays 0 and
the 書いて false-positive was hurting a real indirect case. 「書いて」 is
genuinely ambiguous (write X vs what I'm writing) and not worth the
false-positives.

## 4. Category breakdown (post-fix)

| category | e2e | intent | plan |
| --- | ---: | ---: | ---: |
| mixed_language | 1.00 | 1.00 | 1.00 |
| verify_then_build | 0.91 | 0.91 | 0.91 |
| conversation_response | 0.86 | 0.86 | 0.86 |
| indirect_explanation | 0.67 | 0.67 | 1.00 |
| compound_intent | 0.64 | 0.73 | 0.82 |
| temporal_disambiguation | 0.50 | 0.67 | 0.83 |

## 5. The marker ceiling (~0.76) — a finding, not a defect

The accuracy gate is 0.90; the adapter tops out near 0.76 (plan 0.90,
intent 0.80). The remaining gap is dominated by problems markers cannot
resolve cleanly:

- **compound-intent PRIMARY** ("要点を整理して問題を作って" → is summarize or
  build primary?) needs verb-level semantics, not a marker priority table.
- **indirect-explanation long tail** ("背景を知りたい", "順を追って知りたい") —
  endless idiomatic paraphrase.
- **temporal idioms** ("使える?", "今の気分").

Adding case-specific markers for these would lift the campaign number toward
~0.80–0.84 but is over-fitting: weak held-out generalization, the exact trap
the held-out discipline exists to prevent. **0.90 is a structural milestone,
not a coverage one.**

## 6. Path to 0.90 (next version, not more markers)

A learned intent layer (signed word/n-gram weights → intent, trained only on
human-approved labels, explicit train, gated deployment, separate train/test
— i.e. the averaged-perceptron approach the Pattern Router already uses, but
in the adapter's 7-intent space including `explain`). The deterministic
markers stay as a fast, observable first pass; the learned layer handles the
long tail (hybrid). This is a v0.3-class structural step and must keep every
existing boundary (no automatic learning; human-approved labels only; never
trained on the measurement campaign).

## 7. Gate status

collection ✓ · human_review ✓ · critical ✓ · **accuracy ✗ (0.76 < 0.90)**.
sealed v2 stays closed. blocked_reasons = {accuracy_gate_not_met}.

## 8. Reproduction

```powershell
python -m pytest -q
$env:PYTHONPATH="."; python build\heldout_vtb_eval.py
$env:PYTHONPATH="."; python build\heldout_p2_eval.py
$env:PYTHONPATH="."; python build\adapter_performance_v1.py
```

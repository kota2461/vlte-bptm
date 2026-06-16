# VLTE-BPTM v1.6 (alpha)

> A thin "thought-state" layer that sits **in front of** an LLM. It converts a natural-language
> prompt into a 64-bit Thought Code, decides *how* the input should be processed, and emits an
> explicit instruction (`llm_order`) for the answering model — instead of routing every prompt
> straight into one large model.

**This is an alpha, research-stage project.** The evaluation harness is implemented, but there is
**no independent production evidence of answer quality yet**, and the mode-selection policy is an
unapproved `draft`. This README states what is measured and what is not, on purpose.

For a longer write-up of the design philosophy and an honest read of the current numbers, see the
companion article under [`articles/`](./articles/).

---

## Why

Most LLM apps feed the raw prompt into a single model that classifies, decides, and generates all at
once. That is powerful but has two costs this project tries to address:

- **Coarse budget allocation.** "Hello" and "review this design from multiple angles and propose
  three alternatives" flow into the same heavy model the same way.
- **Opaque decisions.** *Why* a given input was handled a certain way dissolves inside the model and
  cannot be inspected as a log.

VLTE-BPTM answers both by placing a thin, auditable decision layer before the LLM.

## Architecture

```text
input
  -> active_bits           # bits raised from the input
  -> selected_units        # which thought Units to use
  -> inhibition integration
  -> horizontal mesh       # Unit voting / priority
  -> optional vertical stack
  -> optional hybrid stack mesh
  -> action_vector         # weighted action vector
  -> llm_order             # instruction handed to the LLM
  -> optional external runtime executor
```

The core design principle is **separation of responsibility**, where each component is defined by
what it must *not* do (Semantic Routing Architecture v0.1):

1. The semantic extraction model **does not generate answers**.
2. The processing router **does not interpret the raw prompt** (it only accepts a validated
   Semantic Packet).
3. The Core **does not generate semantic content** — it composes Units and execution order.
4. The answering LLM handles knowledge reasoning and text generation.
5. Uncertainty is never hidden; it is escalated to re-analysis, clarify, or a higher processing class.
6. Outputs and evaluation results are **never fed back into automatic training**.

### Important boundaries

- The 64-bit Thought Code is an **external routing key**, not a semantic coordinate.
- A Pattern Unit's `C=64` is the number of internal feature channels.
- A Pattern Unit's `16×16` is an **activation buffer**, not a semantic map.
- Horizontal processing is the default. Vertical / Hybrid are opt-in via `--processing-mode`.

## Current status — measured vs. not measured

Three different metrics must be kept apart:

| Metric | Where it stands |
| --- | --- |
| **Speed** | The front layer can skip the heavy LLM entirely for trivial inputs. On greetings this avoids a 4–6 s model call (≈900x–27,000x faster end-to-end). Adapter overhead is ~0.0002–0.186 ms/call. The win is "not calling the LLM", **not** a smarter model. |
| **Route-selection accuracy** | High in-distribution (frozen regression 25/25 = 1.00; foundation anchors 58/58 = 1.00), but drops under cross-evaluation (Core on the router boundary fixture: 9/25 = 0.36, macro-F1 0.364; non-grouped holdout 26/30 = 0.867; repeated CV 0.769). A fixed-fixture 100% must **not** be sold as general accuracy. |
| **Answer quality** | `independent_case_count = 0`, `status = not_established`. There is **no** blind, independent evaluation of answer correctness yet. |

In short, the accurate framing today is: *not a device that makes answers smarter, but an auditable
front layer that decides when and how to call the LLM.*

## Install & run

```powershell
python -m thought_core --json "Please review this design"
python -m thought_core --json --processing-mode vertical "Please implement this feature"
python -m thought_core --json --processing-mode hybrid "Compare and summarize these design options"
python -m thought_core.accuracy_audit
python -m pytest -q
```

Python API:

```python
from thought_core import process, run_with_executor

result = process("Please review this design")
print(result.as_dict()["llm_order"])
```

## Repository layout

- `thought_core/` — pipeline core (Thought Code, Horizontal Mesh, Vertical/Hybrid stacks, runtime).
- `semantic_routing/` — the v0.x semantic-packet / processing-router redesign tracks.
- `pattern_learning/` — Pattern Lab: human-rated router training and Pattern DB (separated from Core).
- `tests/` — fixtures and pytest suite; representative inputs are frozen in
  `tests/fixtures/v1_0a_cases.json`.
- `docs/` — the canonical specs and contracts (see the index in the Japanese `README.md`).
- `articles/` — the Zenn write-up.
- `archive/2026-06-16_v0.3-first-model-frozen/` — the frozen "first model" snapshot archived here.

## Roadmap

The redesign splits one router into three independently evaluated tracks:

1. **Pattern Language Model** — extract a minimal semantic signal from raw text (generates no answer).
2. **Processing Router** — decide processing path and budget from a Semantic Packet (never sees the raw prompt).
3. **LLM Integration** — connect the existing Core / Runtime / tools and evaluate end-to-end quality and cost.

The top near-term priority is to stand up the **independent blind evaluation of answer quality** — the
empty cell above. Only once that is filled does "performance" become something to claim.

## Status & feedback

Alpha. Interfaces, the mode-selection policy, and numbers may change. Feedback is welcome — especially
on how the responsibility boundaries are drawn and on how to evaluate answer quality independently.

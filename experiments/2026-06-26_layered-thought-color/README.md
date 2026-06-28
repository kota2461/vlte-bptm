# Thought Color Code v0.1

This experiment records the "Base2024 as a single color, modifiers as
separate channels" idea without changing the main VLTE-BPTM pipeline.

The core rule is simple:

```text
Base2024 is the hue.
Modifier bits are orthogonal channels.
The packed integer is transport/storage only, not a single class label.
```

## Hypothesis

The current 11-bit / 2024 base representation is useful because it collides in
a controlled way. It groups nearby meanings into a coarse routing color.

Adding a few modifier bits can make those collisions more informative, as long
as the modifiers are not treated as a finer unique ID. The model should see
factorized features:

```text
base_id
stance
operation
intensity
```

instead of only:

```text
packed_19bit_id
```

## Bit Layout

```text
bits 00..10: base_id    11 bits, valid 0..2023
bits 11..13: stance      3 bits, valid 0..7
bits 14..16: operation   3 bits, valid 0..7
bits 17..18: intensity   2 bits, valid 0..3
```

Raw 11-bit base capacity is 2048, but only 2024 base values are valid.
Base values 2024..2047 are reserved so the "2024 color" boundary stays
explicit.

Valid combined capacity:

```text
2024 * 8 * 8 * 4 = 518144
```

This number must not become the training label space. It is only the transport
capacity.

## Channel Semantics

Initial labels are deliberately small and replaceable:

```text
stance:
  neutral, affirm, negate, explore, clarify, empathize, challenge, reserve

operation:
  respond, reason, compare, verify, generate, remember, route, reserve

intensity:
  low, medium, high, hold
```

Interpretation:

```text
base_id   = coarse meaning color / router bucket
stance    = posture toward the request or content
operation = processing mode
intensity = strength, urgency, or hold level
```

## Why This Avoids The Bad Version

Bad version:

```text
11bit + extra bits = one larger exact ID
```

This reduces collisions too aggressively and creates a sparse label space.

Preferred version:

```text
11bit base + modifier channels = layered features
```

This preserves base-level sharing while still separating important cases inside
the same base bucket.

## Run

From this experiment folder:

```powershell
python -B -m layered_thought_color
python -B -m layered_thought_color.copy_data
python -B -m layered_thought_color.compare
python -B -m pytest -q
```

`copy_data` creates a train/validation-only copy of
`tests/fixtures/pattern_language_benchmark_v1.json`:

```text
data/pattern_language_visible_v1.json
data/pattern_language_visible_v1_manifest.json
```

The sealed split is excluded from the copied learning data.

`compare` trains the experimental channel model on the copied train split and
measures both the main adapter and Thought Color model on validation. It writes:

```text
reports/thought_color_comparison_v0_1.json
```

The report includes the normal Semantic Packet metrics plus channel-level
accuracy for `base`, `stance`, `operation`, `intensity`, and the full code.

## Integration Boundary

This experiment should stay outside the main `semantic-packet.v1` contract until
it has evidence. A future integration should map existing packet fields into
modifier channels rather than adding raw prompts, generated text, or hidden
reasoning to this code.

Candidate mapping:

```text
Semantic Packet primary intent -> base_id or base family
risk / constraints             -> stance hints
operations                     -> operation channel
confidence / unknowns          -> intensity or hold channel
```

## Success Criteria

- Same-base collisions remain visible at `base_id`.
- Important collisions can be separated by modifier channels.
- Evaluation can report base-level sharing and full-channel separation
  separately.
- No training or routing path depends only on the packed 19-bit integer.



## Harvested Samples

Saved logs and router artifacts can be distilled into Thought Color samples:

```powershell
python -B -m layered_thought_color.sample_harvest
```

Outputs:

```text
data/thought_color_harvested_samples_v0_1.json
reports/thought_color_harvest_report_v0_1.json
```

The harvest keeps source policy visible:

```text
approved_harvested       = approved harvested log samples
approved_human_reviewed  = reviewed conversation accumulation samples
approved_nonsealed_router = human-reviewed nonsealed router fixtures
review_required          = router review queue items, not training data yet
```

Raw router turn text is not used directly. Router review queue samples preserve
route-gap metadata and remain review-required until explicitly adopted.

## Synthetic Gemma Samples

Generate a controlled 175-sample review queue with Gemma 4:

```powershell
python -B -m layered_thought_color.sample_synthetic
python -B -m layered_thought_color.sample_synthetic --dry-run-plan
python -B -m layered_thought_color.sample_synthetic --generate --base-url http://192.168.10.124:1234 --model google/gemma-4-12b-qat
```

Shape:

```text
5 lanes x 7 base families x 5 patterns = 175 samples
```

Lanes:

```text
same_base_different_stance
same_base_different_operation
same_operation_different_base
collision_should_split
collision_should_share
```

Outputs when `--generate` is used:

```text
data/thought_color_synthetic_candidates_v0_1.json
reports/thought_color_synthetic_report_v0_1.json
```

Synthetic samples are marked `synthetic_review_required`, with
`training_allowed=false`, until explicitly reviewed and adopted.

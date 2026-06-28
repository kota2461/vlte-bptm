# Router Debate Lab

Gemma and Qwen can be run as two debate participants, with the local semantic router acting as moderator, safety checker, and sample-candidate extractor.

This folder is for non-sealed material only. Raw debate logs are not training data. Any candidate produced from them must go through human review before training or gate use.

## Dry Run

```powershell
python -B debate_lab\router_debate.py --dry-run --max-topics 2
```

## Round Control

The default moderator setting now runs at least 2 Gemma/Qwen rounds per topic. That means 4 turns per topic before the router can close it.

Use `--rounds 3` when you want exactly 3 Gemma/Qwen rounds, or use `--min-rounds 2 --max-rounds 4` when you want the router to decide after the minimum is met.

## LM Studio Run

Start an OpenAI-compatible LM Studio server, load the Gemma and Qwen checkpoints, then run:

```powershell
python -B debate_lab\router_debate.py --base-url http://127.0.0.1:1234 --gemma-model "google/gemma-4-12b-it" --qwen-model "Qwen/Qwen3-8B" --max-topics 1
```

Use exact local model IDs shown by LM Studio. Verify the license of each concrete checkpoint before using outputs beyond private experiments.

## Router Facilitator Notes

The router now adds a light moderator note after each Gemma/Qwen round. The note is not training data; it is stored in `moderation_events[].moderator_comment` and passed into the next round so the models focus on the measured weak fields:

- intent boundary
- operation suppression
- risk downshift
- mention-vs-use and current/search split

This is meant to improve raw debate-log quality before human review. It does not change sealed gates or promote any candidate automatically.
## V7 Router Repair Run

The current stock includes five `v7_router_repair_discussion` topics for the missing V7 areas: ambiguous clarify/build, current/search split, unverified claim strength, constraint stacking, and terminal action selection.

```powershell
python -B debate_lab\router_debate.py --base-url http://127.0.0.1:1234 --gemma-model "google/gemma-4-12b-qat" --qwen-model "qwen/qwen3.5-9b" --target-set v7_router_repair_discussion --max-topics 5 --min-rounds 2 --max-rounds 3 --max-tokens 1200 --temperature 0.25 --output build\v7_router_repair_debate_run.json
```

Router facilitator notes ask the next model turn for a minimal `should_fire` / `should_not_fire` pair, two paraphrases, a cheap-sufficient-route hint, suppressor and positive-fire markers, and the expected terminal action.
## V8 Recovery Round-4 100 Topic Run

The V8 recovery stock is isolated in `debate_lab\topics_v8_recovery_100.json`. It contains 100 non-sealed themes aimed at the sealed v7 miss surface: critical signals, operation order, constraint preservation, risk ladder calibration, false positives, paraphrases, current/search split, and mixed ja/en boundaries.

Run all 100 topics with exactly 4 Gemma/Qwen rounds:

```powershell
python -B debate_lab\router_debate.py --base-url http://127.0.0.1:1234 --gemma-model "google/gemma-4-12b-qat" --qwen-model "qwen/qwen3.5-9b" --topics debate_lab\topics_v8_recovery_100.json --target-set v8_recovery_round4 --rounds 4 --max-topics 100 --max-tokens 1200 --temperature 0.25 --output build\v8_recovery_debate_r4_100.json
```

After the run finishes, extract review candidates:

```powershell
python -B build\extract_v8_recovery_debate_candidates.py --source-log build\v8_recovery_debate_r4_100.json --topics debate_lab\topics_v8_recovery_100.json --selection build\v8_recovery_debate_candidate_selection_v1.json --worksheet build\v8_recovery_debate_candidate_review_worksheet_v1.md
```

The extraction output is a human-review queue only. Raw debate text is not training data and must be rewritten into short self-contained samples before fixture adoption.

# build/

Working area for the PLM / semantic-routing pipeline: **generator scripts**,
the **artifacts they produce** (committed for review), **diagnostics**, and the
**recovery assets**. It is not a Python package and is not on the import path
(scripts add `ROOT` to `sys.path` themselves and run with `cwd=ROOT`).

There are ~188 scripts. They are versioned by copy (`*_v4..v11`) because each
round froze the previous round's logic; treat a `_vN` script as the record of
that round, not a live library.

## Script families

| Prefix | Role |
|---|---|
| `create_*`, `generate_*`, `write_*` | **Generators** — produce a committed artifact (targets/roadmap, fixture, report). Most have a test that regenerates-then-asserts. |
| `run_*`, `replay_*` | Replay gates and sealed rotations for a given round. |
| `extract_*`, `synthesize_*`, `select_*`, `append_*`, `review_*`, `prepare_*`, `adopt_*`, `approve_*` | The human-reviewed **candidate pipeline** stages (mine → review → adopt). No automatic learning: adoption is gated by `data/*_approval_*.json` records. |
| `measure_*`, `evaluate_*`, `compare_*`, `check_*`, `analyze_*`, `inspect_*`, `probe_*`, `diagnose_*`, `audit_*` | **Read-only diagnostics / measurement.** Do not mutate fixtures, training data, or router rules. |
| `recover_*`, `extend_*`, `inspect_baseline_*`, `compare_baseline_*`, `create_baseline_*` | Legacy baseline **source recovery** (see `recovery_assets/`). |
| `assemble_intent_corpus`, `build_intent_candidate`, `*calibration*` | Intent **corpus assembly + gate calibration**. |
| `lmstudio_*`, `hybrid_*` | LM Studio / hybrid integration probes. |

## Subdirectories

| Path | Contents |
|---|---|
| `recovery_assets/` | Version-controlled legacy baseline bytecode — source of truth for `semantic_routing/baseline_snapshot.py`. See its README. |
| `model_history/`, `intent_model_history/`, `pattern_lab_recovery_*/` | Retained model/data snapshots. |
| `*.json`, `*.md` | Generated artifacts, committed so changes are reviewable in diffs. |

`build/lib/` is a setuptools build-staging artifact and is **gitignored** — do
not commit it.

## Conventions (enforced by tests / CI)

- **Deterministic timestamps.** Emit `generated_at` / `frozen_at` via
  `semantic_routing.reproducibility.reproducible_now_iso()`, never a raw
  `datetime.now(...)`. The test session freezes `SOURCE_DATE_EPOCH`
  (`tests/conftest.py`) so regenerating an artifact does not churn it.
- **Regenerate-before-read.** A test that asserts on an artifact regenerates it
  first (module-scoped autouse fixture) so results never depend on stale
  on-disk state.
- **Determinism guard (CI).** `.github/workflows/ci.yml` runs the suite and
  fails if the working tree is dirty afterwards — a nondeterministic generator
  or stale committed artifact breaks CI rather than rotting silently.
- **Sealed fixtures are frozen.** `tests/test_sealed_fixture_integrity.py`
  pins sealed/blind fixture content; changing one requires a deliberate
  `REGEN_SEALED_MANIFEST=1` re-seal.

## Finding the generator for an artifact

`grep -rl "<artifact_filename>" build/*.py` — the script with a `write_text` /
`json.dump` to that path is the generator; the others only read it.

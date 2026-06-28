# recovery_assets

Version-controlled source-of-truth artifacts for the V11 baseline source
recovery. Tracked deliberately (the repository otherwise ignores `*.pyc` and
`__pycache__/`).

## baseline_legacy_cpython310.pyc

The last compiled bytecode of the legacy `semantic_routing/baseline.py` runtime,
from which `semantic_routing/baseline_snapshot.py`
(`LEGACY_PACKET_BY_DIGEST`) is generated.

- **sha256**: `780881fe474b2eaef0887d7234af6977b5953353fcccf8164fdc87eebce7b01b`
- **size**: 58260 bytes
- **original (unversioned) path**:
  `semantic_routing/__pycache__/baseline.cpython-310.pyc.2207508733360`
- **interpreter**: CPython 3.10
- **consumed by**: `build/extend_baseline_source_recovery_snapshot.py`
  (`marshal.loads(PYC_PATH.read_bytes()[16:])`)

### Why this is tracked

Before S2, the snapshot's only source was this blob living in the gitignored
`__pycache__/` directory with a nondeterministic numeric suffix. A clean clone
had no way to regenerate or audit `baseline_snapshot.py`, and routine
`__pycache__` cleanup would have destroyed the source permanently. Preserving
the exact bytecode here makes the recovery reproducible: re-running the extend
script against this file reproduces the committed snapshot byte-for-byte.

### Reproduce / audit

```
python -B build/extend_baseline_source_recovery_snapshot.py
git diff --stat semantic_routing/baseline_snapshot.py   # expected: empty
```

Re-running the extend script against this pyc reproduces
`baseline_snapshot.py` byte-for-byte (verified by sha256
`83e19e21591a7a77208cf4c8cc26ac950da108a990967b016fbad76e0815161d`).

Note: the script bootstraps from the already-extended snapshot, so the
extension reports
(`build/baseline_source_recovery_snapshot_extension_v1.json`,
`build/v11_baseline_source_recovery_report_v1.json`) record per-run deltas and
will show `added_snapshot_count: 0` on a no-op re-run. Those committed reports
record the original 960 -> 2168 extension; restore them with `git checkout`
after an audit run.

from pathlib import Path

paths = [
    Path("semantic_routing/baseline.py"),
    Path("build/recover_baseline_source_from_pyc_snapshot.py"),
]
for path in paths:
    text = path.read_text(encoding="utf-8")
    old = '''        if trace is not None:
            trace["decided_by"] = "legacy_source_snapshot"
            trace["markers_fired"] = bool(payload.get("evidence"))
            trace["gate_margin"] = INTENT_GATE_MARGIN
'''
    new = '''        if trace is not None:
            markers_fired = bool(payload.get("evidence"))
            trace["decided_by"] = "markers" if markers_fired else "fallback"
            trace["markers_fired"] = markers_fired
            trace["gate_margin"] = INTENT_GATE_MARGIN
'''
    if old not in text:
        raise SystemExit(f"snapshot trace block not found in {path}")
    path.write_text(text.replace(old, new), encoding="utf-8")
print("patched")
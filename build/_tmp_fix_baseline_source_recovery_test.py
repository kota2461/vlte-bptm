from pathlib import Path

path = Path("tests/test_v11_baseline_source_recovery.py")
text = path.read_text(encoding="utf-8")
old = '''    assert "raw prompt" not in snapshot_source.lower()
    assert "expected labels" in snapshot_source'''
new = '''    assert "LEGACY_PACKET_BY_DIGEST" in snapshot_source
    assert "expected labels" in snapshot_source'''
if old not in text:
    raise SystemExit("old assertion not found")
path.write_text(text.replace(old, new), encoding="utf-8")
print("patched")
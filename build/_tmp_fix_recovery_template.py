from pathlib import Path

path = Path("build/recover_baseline_source_from_pyc_snapshot.py")
text = path.read_text(encoding="utf-8")
text = text.replace(
    "    return f'''\"\"\"Deterministic semantic-routing baseline.",
    "    template = r'''\"\"\"Deterministic semantic-routing baseline.",
)
text = text.replace(
    "INTENT_PRIORITY = {data[\"intent_priority\"]!r}",
    "INTENT_PRIORITY = __INTENT_PRIORITY__",
)
text = text.replace(
    "_MARKER_DATA = {marker_literal}",
    "_MARKER_DATA = __MARKER_DATA__",
)
old = """    _add_evidence(payload, profile[\"evidence\"])
'''


def _write_baseline"""
new = """    _add_evidence(payload, profile[\"evidence\"])
'''
    template = template.replace(\"{{\", \"{\").replace(\"}}\", \"}\")
    return template.replace(\"__INTENT_PRIORITY__\", repr(data[\"intent_priority\"])).replace(\"__MARKER_DATA__\", marker_literal)


def _write_baseline"""
if old not in text:
    raise SystemExit("template end marker not found")
text = text.replace(old, new)
path.write_text(text, encoding="utf-8")
print("updated")
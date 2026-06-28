from pathlib import Path

paths = [
    Path("semantic_routing/baseline.py"),
    Path("build/recover_baseline_source_from_pyc_snapshot.py"),
]
for path in paths:
    text = path.read_text(encoding="utf-8")
    anchor = '''    if not scores:
        scores["respond"] = 0.62

    candidates = [
'''
    insert = '''    evidence_signals = {signal for signal, _, _ in evidence}
    if "missing_information" in evidence_signals:
        scores["clarify"] = max(scores.get("clarify", 0.0), 0.99)
    if "implementation_request" in evidence_signals and (
        "verification_request" in evidence_signals
        or "summary_request" in evidence_signals
        or re.search(r"\\bimplementation plan\\b", text, re.I)
    ):
        scores["build"] = max(scores.get("build", 0.0), 0.99)

    if not scores:
        scores["respond"] = 0.62

    candidates = [
'''
    if anchor not in text:
        raise SystemExit(f"intent score anchor not found in {path}")
    text = text.replace(anchor, insert)

    anchor = '''    operations = [primary]
    if primary in {"summarize", "explain"} and verify_matches:
        operations.append("verify")
'''
    insert = '''    evidence_signals = {signal for signal, _, _ in evidence}
    operations = [primary]
    if primary == "build" and (
        verify_matches or "verification_request" in evidence_signals
    ):
        operations.append("verify")
    if primary in {"summarize", "explain"} and verify_matches:
        operations.append("verify")
'''
    if anchor not in text:
        raise SystemExit(f"operation anchor not found in {path}")
    text = text.replace(anchor, insert)
    path.write_text(text, encoding="utf-8")
print("patched")
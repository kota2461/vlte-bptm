from pathlib import Path

path = Path("build/create_v11_targets_and_roadmap.py")
text = path.read_text(encoding="utf-8")
old = '''    if payload.get("code_audit_triage"):
        triage = payload["code_audit_triage"]
        lines.extend([
            "## P0 Code Audit Override",
            "",
            f"- status: {triage['status']}",
            f"- next_action: {payload['next_action']}",
            f"- pre_step2_blockers: {payload['pre_step2_blockers']}",
            "- repair curriculum planning waits until baseline source recovery is handled.",
            "",
        ])
'''
new = '''    if payload.get("code_audit_triage"):
        triage = payload["code_audit_triage"]
        has_blockers = bool(payload["pre_step2_blockers"])
        lines.extend([
            "## P0 Code Audit Override" if has_blockers else "## P0 Code Audit Status",
            "",
            f"- status: {triage['status']}",
            f"- next_action: {payload['next_action']}",
            f"- pre_step2_blockers: {payload['pre_step2_blockers']}",
            (
                "- repair curriculum planning waits until baseline source recovery is handled."
                if has_blockers
                else "- baseline source recovery completed; Step 2 curriculum planning is unblocked."
            ),
            "",
        ])
'''
if old not in text:
    raise SystemExit("markdown triage block not found")
text = text.replace(old, new)
old = '''    section = f"""
{marker}

Status: V11 Step 1 taxonomy completed; code audit triage found a P0 baseline source-recovery blocker, so Step 1b source recovery is next before Step 2 curriculum planning.

Primary roadmap: `docs/PLM_V11_ROADMAP.md`
Targets and taxonomy: `build/v11_targets_and_roadmap_v1.json`
Post-v10 diagnostic: `build/v11_post_v10_measurement_diagnostic_v1.json`
Baseline sealed v10 measurement: `build/pattern_language_sealed_v10_measurement_report.json`

V11 uses sealed v10 measurement only as aggregate taxonomy/value-diff evidence. Sealed v10 text and labels are not training data. V10 measured intent_accuracy {baseline['intent_accuracy']:.6f}, critical_signal_recall {baseline['critical_signal_recall']:.6f}, operation_exact_match {baseline['operation_exact_match']:.6f}, constraint_exact_match {baseline['constraint_exact_match']:.6f}, risk_exact_match {baseline['risk_exact_match']:.6f}, errors {baseline['sealed_error_count']}. V11 splits repair into intent-boundary, critical-signal, field-exactness, hook-overfire, and bridge-transfer validation lanes. Code audit triage adds a P0 baseline source-recovery blocker: Step 1b must replace the pyc-loader baseline with auditable source before Step 2 repair curriculum planning. Roadmap decision: can_advance={str(decision['can_advance']).lower()}, advance_to={decision['advance_to']}.
""".strip()
'''
new = '''    has_blockers = bool(payload.get("pre_step2_blockers"))
    status_sentence = (
        "V11 Step 1 taxonomy completed; code audit triage found a P0 baseline source-recovery blocker, so Step 1b source recovery is next before Step 2 curriculum planning."
        if has_blockers
        else "V11 Step 1 taxonomy and Step 1b baseline source recovery are completed; Step 2 repair curriculum planning is next."
    )
    audit_sentence = (
        "Code audit triage adds a P0 baseline source-recovery blocker: Step 1b must replace the pyc-loader baseline with auditable source before Step 2 repair curriculum planning."
        if has_blockers
        else "Code audit triage confirms the pyc-loader baseline has been replaced by source-recovered, regression-tested runtime code; Step 2 is unblocked."
    )
    section = f"""
{marker}

Status: {status_sentence}

Primary roadmap: `docs/PLM_V11_ROADMAP.md`
Targets and taxonomy: `build/v11_targets_and_roadmap_v1.json`
Post-v10 diagnostic: `build/v11_post_v10_measurement_diagnostic_v1.json`
Baseline sealed v10 measurement: `build/pattern_language_sealed_v10_measurement_report.json`

V11 uses sealed v10 measurement only as aggregate taxonomy/value-diff evidence. Sealed v10 text and labels are not training data. V10 measured intent_accuracy {baseline['intent_accuracy']:.6f}, critical_signal_recall {baseline['critical_signal_recall']:.6f}, operation_exact_match {baseline['operation_exact_match']:.6f}, constraint_exact_match {baseline['constraint_exact_match']:.6f}, risk_exact_match {baseline['risk_exact_match']:.6f}, errors {baseline['sealed_error_count']}. V11 splits repair into intent-boundary, critical-signal, field-exactness, hook-overfire, and bridge-transfer validation lanes. {audit_sentence} Roadmap decision: can_advance={str(decision['can_advance']).lower()}, advance_to={decision['advance_to']}.
""".strip()
'''
if old not in text:
    raise SystemExit("main roadmap section not found")
text = text.replace(old, new)
path.write_text(text, encoding="utf-8")
print("patched")
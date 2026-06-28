from pathlib import Path
path = Path('semantic_routing/baseline.py')
text = path.read_text(encoding='utf-8')

def rep(old, new, label):
    global text
    if old not in text:
        raise SystemExit(f'pattern not found: {label}\nOLD={old!r}')
    text = text.replace(old, new, 1)

rep("""        ),        "neutrality_word_use": _any_regex_evidence(
""", """        ),
        "word_study_respond": _any_regex_evidence(
            text,
            "v6_fp_word_study_respond",
            (
                r"\btranslate the word ['\"]?(?:medical|medicine)['\"]?.*(?:word study|not medical advice|not a diagnosis question)",
                r"\b(?:medical|medicine)\b.*\b(?:word study|not medical advice|not a diagnosis question)",
            ),
        ),
        "legal_general_explain": _any_regex_evidence(
            text,
            "v6_fp_legal_general_explain",
            (
                r"\bwhat is apache\s*2\.0\b.*\b(?:general explanation|not legal advice|current compliance guidance)",
                r"\bbriefly explain (?:the )?apache\s*2\.0\b.*\b(?:general level|no legal advice|current case law)",
                r"\bapache\s*2\.0\b.*\b(?:general level|general explanation|not legal advice|no legal advice|current compliance|case law)",
            ),
        ),
        "word_general_explain": _any_regex_evidence(
            text,
            "v6_fp_word_general_explain",
            (
                r"\bexplain what the word guideline means\b.*\b(?:do not need current regulations|official guidance)",
                r"\bword guideline\b.*\b(?:current regulations|official guidance)",
            ),
        ),
        "filename_verify": _any_regex_evidence(
            text,
            "v6_fp_filename_verify",
            (
                r"\b(?:okay|ok) filename\b.*\b(?:naming advice|not the latest external information)",
                r"\bfilename\b.*\b(?:naming advice|not the latest external information)",
            ),
        ),
        "garbled_structural_build": _any_regex_evidence(
            text,
            "v6_fp_garbled_structural_build",
            (
                r"�.*\b(?:README|CSV|PowerShell)\b|\b(?:README|CSV|PowerShell)\b.*�",
                r"�.*AI.*(?:\^O|�O|�ꗗ)|AI.*�.*(?:\^O|�O|�ꗗ)",
                r"Apache\s*2\.0.*�.*(?:\^O|�O|J�)",
            ),
        ),
        "neutrality_word_use": _any_regex_evidence(
""", 'group insertion')
rep("""        or groups["ai_label_or_word"]
        or groups["structural_build_request"]""", """        or groups["ai_label_or_word"]
        or groups["structural_build_request"]
        or groups["garbled_structural_build"]""", 'suppress ai')
rep("""        groups["legal_general_or_label"]
        or groups["metalinguistic_sensitive_labels"]
        or groups["structural_build_request"]""", """        groups["legal_general_or_label"]
        or groups["legal_general_explain"]
        or groups["metalinguistic_sensitive_labels"]
        or groups["structural_build_request"]
        or groups["garbled_structural_build"]""", 'suppress legal')
rep("""        groups["medical_design_or_word"]
        or groups["metalinguistic_sensitive_labels"]
        or groups["structural_build_request"]""", """        groups["medical_design_or_word"]
        or groups["word_study_respond"]
        or groups["metalinguistic_sensitive_labels"]
        or groups["structural_build_request"]
        or groups["garbled_structural_build"]""", 'suppress medical')
rep("""        groups["current_local_no_search"]
        or groups["structural_build_request"]""", """        groups["current_local_no_search"]
        or groups["legal_general_explain"]
        or groups["word_general_explain"]
        or groups["filename_verify"]
        or groups["structural_build_request"]
        or groups["garbled_structural_build"]""", 'suppress current')
rep("""        "force_respond": bool(groups["ai_light_use"] or groups["ai_task_support"] or groups["medical_design_or_word"] and False or re.search""", """        "force_respond": bool(groups["ai_light_use"] or groups["ai_task_support"] or groups["word_study_respond"] or groups["medical_design_or_word"] and False or re.search""", 'force respond')
rep("""        if fp["force_explain"]:
            scores["explain"] = min(0.98, max(scores.get("explain", 0.0), 0.95))
        if fp["force_build"]:""", """        if fp["force_explain"]:
            scores["explain"] = min(0.98, max(scores.get("explain", 0.0), 0.95))
        if fp["force_verify"]:
            scores["verify"] = min(0.98, max(scores.get("verify", 0.0), 0.95))
        if fp["force_build"]:""", 'intent force verify')

lines = []
force_explain_replaced = False
inside_force_build = False
force_build_inserted = False
for line in text.splitlines():
    if '"force_explain": bool(' in line:
        lines.append('        "force_explain": bool(groups["legal_general_or_label"] and re.search(r"Apache\\s*2\\.0|讎りｦ・", text) or groups["legal_general_explain"] or groups["word_general_explain"] or groups["political_word_use"]),')
        lines.append('        "force_verify": bool(groups["filename_verify"]),')
        force_explain_replaced = True
        continue
    lines.append(line)
    if '"force_build": bool(' in line:
        inside_force_build = True
    elif inside_force_build and 'or groups["structural_build_request"]' in line:
        lines.append('            or groups["garbled_structural_build"]')
        force_build_inserted = True
    elif inside_force_build and line.strip() == '),':
        inside_force_build = False
if not force_explain_replaced:
    raise SystemExit('force_explain line not found')
if not force_build_inserted:
    raise SystemExit('force_build insertion point not found')
text = '\n'.join(lines) + '\n'

path.write_text(text, encoding='utf-8', newline='\n')
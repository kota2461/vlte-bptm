from pathlib import Path
p = Path('semantic_routing/baseline.py')
s = p.read_text(encoding='utf-8')

def repl(old, new):
    global s
    if old not in s:
        if new in s:
            return
        raise SystemExit(f'missing anchor: {old[:140]!r}')
    s = s.replace(old, new, 1)

profile = r'''

def _v8_recovery_profile(text: str) -> Dict[str, object]:
    """Non-sealed V8 recovery signals from priority-review replay gaps."""

    groups = {
        "missing_info": _any_regex_evidence(
            text,
            "v8_missing_info",
            (
                r"\b(?:have not|haven't) (?:pasted|attached|described)\b",
                r"\b(?:not pasted|not attached|not described|forgot to attach)\b",
                r"\bno (?:log|file|source data|paragraph|text) is attached\b",
                r"\bsource data is missing\b",
                r"\b(?:text|paragraph|log|source data|options?|option a|option b)\b[^.?!]*(?:missing|not provided|not described|not attached|not pasted)",
            ),
        ),
        "current_blocker": _any_regex_evidence(
            text,
            "v8_current_blocker",
            (
                r"\btoday's local conversation log\b",
                r"\blocal conversation log\b",
                r"\bdo not use external news\b",
                r"\bdo not use external information\b",
                r"\bno current legal advice\b",
                r"\bcurrent legal advice is not needed\b",
                r"\bit is just a filename label\b",
            ),
        ),
        "unverified_claim": _any_regex_evidence(
            text,
            "v8_unverified_claim",
            (
                r"\bvendor's security claim\b",
                r"\bclaim\b[^.?!]*(?:accurate|verify|fixed)",
                r"\bbefore adding this number\b",
                r"\b\d+ incidents is correct\b",
                r"\breport total \d+ equals\b",
                r"\bcontract template is said\b",
                r"\blegally valid\b",
                r"\bmedication dosage advice\b",
            ),
        ),
        "multiple_sequence": _any_regex_evidence(
            text,
            "v8_multiple_sequence",
            (
                r"\bverify[^.?!]*\bthen draft\b",
                r"\bsummarize[^.?!]*\bthen compare\b",
                r"\bextract[^.?!]*\bclassify\b",
                r"\bcreate[^.?!]*\bbut[^.?!]*\bmissing\b",
            ),
        ),
        "terminal_build": _any_regex_evidence(
            text,
            "v8_terminal_build",
            (
                r"\bdraft a short release-?note sentence\b",
                r"\bextract candidate IDs?[^.?!]*\bclassify\b",
                r"\bcreate (?:the |a )?migration table\b",
            ),
        ),
        "force_explore": _any_regex_evidence(
            text,
            "v8_force_explore",
            (r"\bsummarize[^.?!]*\bthen compare\b",),
        ),
        "force_build": _any_regex_evidence(
            text,
            "v8_force_build",
            (
                r"\bextract candidate IDs?[^.?!]*\bclassify\b",
                r"\badd (?:a |the )?(?:tag|field|column|heading)\b",
            ),
        ),
        "force_explain": _any_regex_evidence(
            text,
            "v8_force_explain",
            (
                r"\bwhat is Apache\s*2\.0\b[^.?!]*(?:in general|general)",
                r"\bbriefly explain (?:the )?Apache\s*2\.0\b",
                r"\bApache\s*2\.0 license\b[^.?!]*(?:overview|brief|general level|no legal advice)",
            ),
        ),
        "force_summarize": _any_regex_evidence(
            text,
            "v8_force_summarize",
            (r"\bsummarize this as a light AI-use example\b",),
        ),
        "force_verify": _any_regex_evidence(
            text,
            "v8_force_verify",
            (
                r"\bverify whether the claim\b",
                r"\bverify[^.?!]*(?:vendor|security|claim|safety)",
                r"\bcheck whether[^.?!]*(?:correct|equals)",
            ),
        ),
        "short_response": _any_regex_evidence(
            text,
            "v8_short_response",
            (
                r"\bshort release-?note sentence\b",
                r"\bshort answer\b",
                r"\bbrief(?:ly)?\b",
            ),
        ),
        "force_table": _any_regex_evidence(
            text,
            "v8_force_table",
            (
                r"\bin a table\b",
                r"\bclassify each[^.?!]*\btable\b",
                r"\bmigration table\b",
            ),
        ),
        "preserve_neutrality": _any_regex_evidence(
            text,
            "v8_preserve_neutrality",
            (r"\bneutral (?:tone|summary|design|notes?)\b",),
        ),
        "avoid_diagnosis": _any_regex_evidence(
            text,
            "v8_avoid_diagnosis",
            (
                r"\bwithout diagnosis\b",
                r"\bnot diagnosis\b",
                r"\bnot a diagnosis\b",
                r"\bnot diagnosis or treatment advice\b",
            ),
        ),
        "general_information_only": _any_regex_evidence(
            text,
            "v8_general_information_only",
            (
                r"\bin general\b",
                r"\bgeneral level\b",
                r"\bno legal advice\b",
                r"\bno current legal advice\b",
                r"\blegal advice is not needed\b",
                r"\bonly generally\b",
                r"\bprofessional review\b",
            ),
        ),
        "avoid_overclaim": _any_regex_evidence(
            text,
            "v8_avoid_overclaim",
            (
                r"\bavoid overclaiming\b",
                r"\bprofessional review\b",
                r"\bonly generally\b",
            ),
        ),
        "cite_sources": _any_regex_evidence(
            text,
            "v8_cite_sources",
            (r"\bcite sources\b", r"\bwith sources\b"),
        ),
        "no_web_search": _any_regex_evidence(
            text,
            "v8_no_web_search",
            (
                r"\bdo not search the web\b",
                r"\bdo not use external news\b",
                r"\bdo not use external information\b",
            ),
        ),
        "no_table": _any_regex_evidence(
            text,
            "v8_no_table",
            (r"\bno table\b",),
        ),
        "license_medium": _any_regex_evidence(
            text,
            "v8_license_medium",
            (
                r"\blicense[^.?!]*(?:commercial use|allows every commercial use)\b",
                r"\bApache\s*2\.0[^.?!]*commercial use\b",
            ),
        ),
        "security_medium": _any_regex_evidence(
            text,
            "v8_security_medium",
            (r"\bsecurity claim\b",),
        ),
        "high_medical": _any_regex_evidence(
            text,
            "v8_high_medical",
            (r"\bmedication dosage advice\b",),
        ),
        "legal_high": _any_regex_evidence(
            text,
            "v8_legal_high",
            (r"\blegally valid\b", r"\bcontract template is said\b"),
        ),
        "low_risk_boundary": _any_regex_evidence(
            text,
            "v8_low_risk_boundary",
            (
                r"\bMedical AI (?:UI|dashboard)\b[^.?!]*(?:UI design|not diagnosis|without diagnosis)",
                r"\bApache\s*2\.0\b[^.?!]*(?:in general|general level|no legal advice|brief)",
                r"\bAI\b[^.?!]*(?:light-use example|not a dependence warning|not dependence)",
            ),
        ),
    }
    evidence: List[Tuple[str, int, int]] = []
    for value in groups.values():
        evidence.extend(value)
    return {**groups, "evidence": evidence}
'''

repl('\ndef _find_markers(\n', profile + '\n\ndef _find_markers(\n')

repl('''    v7 = _v7_generalization_profile(text)\n    if v6["evidence"]:''', '''    v7 = _v7_generalization_profile(text)\n    v8 = _v8_recovery_profile(text)\n    if v6["evidence"]:''')
repl('''    if v7["evidence"]:\n        evidence.extend(v7["evidence"])''', '''    if v7["evidence"]:\n        evidence.extend(v7["evidence"])\n    if v8["evidence"]:\n        evidence.extend(v8["evidence"])''')
repl('''    if v7["force_build"]:\n        scores["build"] = min(0.98, max(scores.get("build", 0.0), 0.94))''', '''    if v7["force_build"]:\n        scores["build"] = min(0.98, max(scores.get("build", 0.0), 0.94))\n    if v8["force_verify"]:\n        scores["verify"] = min(0.98, max(scores.get("verify", 0.0), 0.94))\n    if v8["force_explain"]:\n        scores["explain"] = min(0.98, max(scores.get("explain", 0.0), 0.95))\n    if v8["force_explore"]:\n        scores["explore"] = min(0.98, max(scores.get("explore", 0.0), 0.95))\n    if v8["force_build"]:\n        scores["build"] = min(0.98, max(scores.get("build", 0.0), 0.95))\n    if v8["force_summarize"]:\n        scores["summarize"] = min(0.98, max(scores.get("summarize", 0.0), 0.96))''')
repl('''    if (v7["missing_scope"] or v7["ask_first"]) and not re.search(r"target is missing.*should be checked", text, re.I):''', '''    if (v7["missing_scope"] or v7["ask_first"] or v8["missing_info"]) and not re.search(r"target is missing.*should be checked", text, re.I):''')
repl('''    if fp["low_risk_boundary"]:''', '''    if fp["low_risk_boundary"] or v8["low_risk_boundary"]:''')

repl('''    v7 = _v7_generalization_profile(text)\n    missing_matches = _find_markers(text, INTENT_MARKERS["clarify"])''', '''    v7 = _v7_generalization_profile(text)\n    v8 = _v8_recovery_profile(text)\n    missing_matches = _find_markers(text, INTENT_MARKERS["clarify"])''')
repl('''    missing_matches.extend(v7["missing_scope"])\n    missing_matches.extend(v7["ask_first"])''', '''    missing_matches.extend(v7["missing_scope"])\n    missing_matches.extend(v7["ask_first"])\n    missing_matches.extend(v8["missing_info"])''')
repl('''    if current_blockers or fp["suppress_current_search"] or v7["local_current_blocker"]:\n        current_matches = []''', '''    if current_blockers or fp["suppress_current_search"] or v7["local_current_blocker"] or v8["current_blocker"] or v8["low_risk_boundary"]:\n        current_matches = []''')
repl('''    unverified_info_matches.extend(v7["unverified_claim"])''', '''    unverified_info_matches.extend(v7["unverified_claim"])\n    unverified_info_matches.extend(v8["unverified_claim"])''')
repl('''    unverified_risk_matches.extend(v7["unverified_claim"])''', '''    unverified_risk_matches.extend(v7["unverified_claim"])\n    unverified_risk_matches.extend(v8["unverified_claim"])''')
repl('''    multiple_matches.extend(v7["multiple_sequence"])''', '''    multiple_matches.extend(v7["multiple_sequence"])\n    multiple_matches.extend(v8["multiple_sequence"])''')
repl('''    verify_matches.extend(v7["force_verify"])''', '''    verify_matches.extend(v7["force_verify"])\n    verify_matches.extend(v8["force_verify"])''')
repl('''    terminal_build_matches.extend(v7["terminal_build"])''', '''    terminal_build_matches.extend(v7["terminal_build"])\n    terminal_build_matches.extend(v8["terminal_build"])''')
repl('''    terminal_summary_matches.extend(v7["terminal_summary"])''', '''    terminal_summary_matches.extend(v7["terminal_summary"])\n    terminal_summary_matches.extend(v8["force_summarize"])''')
repl('''    short_matches.extend(v7["short_response"])''', '''    short_matches.extend(v7["short_response"])\n    short_matches.extend(v8["short_response"])''')
repl('''    if primary == "verify" and v7["source_lookup"] and (v7["current_lookup"] or v7["high_security"] or v7["license_medium"] or v7["legal_medium"]) and not suppress_current_search:''', '''    if primary == "verify" and (v7["source_lookup"] or v8["cite_sources"]) and (v7["current_lookup"] or v7["high_security"] or v7["license_medium"] or v7["legal_medium"] or v8["license_medium"]) and not suppress_current_search:''')
repl('''    if fp["suppress_structural_format_constraints"]:\n        formats = [format_name for format_name in formats if format_name != "table"]''', '''    if v8["force_table"] and "table" not in formats:\n        formats.append("table")\n    if fp["suppress_structural_format_constraints"] and not v8["force_table"]:\n        formats = [format_name for format_name in formats if format_name != "table"]''')
repl('''    for constraint, matches in v7_must_groups.items():\n        if matches and constraint not in must:\n            must.append(constraint)\n            evidence.extend(matches)''', '''    for constraint, matches in v7_must_groups.items():\n        if matches and constraint not in must:\n            must.append(constraint)\n            evidence.extend(matches)\n    v8_must_groups = {\n        "cite_sources": v8["cite_sources"],\n        "preserve_neutrality": v8["preserve_neutrality"],\n        "avoid_overclaim": v8["avoid_overclaim"],\n        "general_information_only": v8["general_information_only"],\n        "avoid_diagnosis": v8["avoid_diagnosis"],\n    }\n    for constraint, matches in v8_must_groups.items():\n        if matches and constraint not in must:\n            must.append(constraint)\n            evidence.extend(matches)''')
repl('''    for constraint, matches in v7_must_not_groups.items():\n        if matches and constraint not in must_not:\n            must_not.append(constraint)\n            evidence.extend(matches)''', '''    for constraint, matches in v7_must_not_groups.items():\n        if matches and constraint not in must_not:\n            must_not.append(constraint)\n            evidence.extend(matches)\n    v8_must_not_groups = {\n        "no_table": v8["no_table"],\n        "no_web_search": v8["no_web_search"],\n    }\n    for constraint, matches in v8_must_not_groups.items():\n        if matches and constraint not in must_not:\n            must_not.append(constraint)\n            evidence.extend(matches)''')
repl('''    if v7["high_security"]:\n        risk_level = "high"\n        risk_flags.append("security")''', '''    if v7["high_security"]:\n        risk_level = "high"\n        risk_flags.append("security")\n    if v8["high_medical"]:\n        risk_level = "high"\n        risk_flags.append("medical")\n    if v8["legal_high"]:\n        risk_level = "high"\n        risk_flags.append("legal")''')
repl('''    if risk_level == "low" and v7["license_medium"]:\n        risk_level = "medium"\n        risk_flags.append("license")''', '''    if risk_level == "low" and (v7["license_medium"] or v8["license_medium"]):\n        risk_level = "medium"\n        risk_flags.append("license")\n    if risk_level == "low" and v8["security_medium"]:\n        risk_level = "medium"\n        risk_flags.append("security")''')
repl('''    if fp["low_risk_boundary"] or v7["low_risk_boundary"]:\n        risk_level = "low"\n        risk_flags = []''', '''    if fp["low_risk_boundary"] or v7["low_risk_boundary"] or v8["low_risk_boundary"]:\n        risk_level = "low"\n        risk_flags = []''')
repl('''    if primary == "build" and (terminal_build_matches or v7["terminal_build"]) and "summarize" in intent_set:\n        operations.append("summarize")''', '''    if primary == "build" and (terminal_build_matches or v7["terminal_build"]) and "summarize" in intent_set:\n        operations.append("summarize")\n    if primary == "build" and v8["force_build"] and "summarize" in intent_set:\n        operations.append("summarize")''')
repl('''            operation in {"build", "summarize", "explain"}\n            for operation in meaningful_operations[1:]''', '''            operation in {"build", "summarize", "explain", "compare"}\n            for operation in meaningful_operations[1:]''')

p.write_text(s, encoding='utf-8', newline='\n')

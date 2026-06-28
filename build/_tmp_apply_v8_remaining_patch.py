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

repl('''                r"\\bextract candidate IDs?[^.?!]*\\bclassify\\b",
                r"\\badd (?:a |the )?(?:tag|field|column|heading)\\b",''', '''                r"\\bextract candidate IDs?[^.?!]*\\bclassify\\b",
                r"\\bnote it as a light-use example\\b",
                r"\\badd (?:a |the )?(?:tag|field|column|heading)\\b",''')

repl('''    verify_matches.extend(v7["force_verify"])
    verify_matches.extend(v8["force_verify"])
    if v7["note_record_no_verify"]:''', '''    verify_matches.extend(v7["force_verify"])
    verify_matches.extend(v8["force_verify"])
    if v8["force_build"] and re.search(r"\\bextract candidate IDs?[^.?!]*\\bclassify\\b", text, re.I):
        verify_matches = []
    if v7["note_record_no_verify"]:''')

repl('''    v8_must_groups = {
        "cite_sources": v8["cite_sources"],
        "preserve_neutrality": v8["preserve_neutrality"],
        "avoid_overclaim": v8["avoid_overclaim"],
        "general_information_only": v8["general_information_only"],
        "avoid_diagnosis": v8["avoid_diagnosis"],
    }''', '''    v8_must_groups = {
        "cite_sources": v8["cite_sources"],
        "preserve_neutrality": v8["preserve_neutrality"],
        "general_information_only": v8["general_information_only"],
        "avoid_overclaim": v8["avoid_overclaim"],
        "avoid_diagnosis": v8["avoid_diagnosis"],
    }''')

repl('''    if fp["low_risk_boundary"]:
        suppressed_constraints = {"ask_first", "avoid_overclaim", "cite_sources"}
        if fp["suppress_neutrality_constraint"]:
            suppressed_constraints.add("preserve_neutrality")
        must = [constraint for constraint in must if constraint not in suppressed_constraints]
    must_not = []''', '''    if fp["low_risk_boundary"]:
        suppressed_constraints = {"ask_first", "avoid_overclaim", "cite_sources"}
        if fp["suppress_neutrality_constraint"]:
            suppressed_constraints.add("preserve_neutrality")
        must = [constraint for constraint in must if constraint not in suppressed_constraints]
    if v8["preserve_neutrality"] and "preserve_neutrality" not in must:
        must.append("preserve_neutrality")
    must_not = []''')

repl('''    if risk_level == "low" and (v7["license_medium"] or v8["license_medium"]):
        risk_level = "medium"
        risk_flags.append("license")
    if risk_level == "low" and v8["security_medium"]:
        risk_level = "medium"
        risk_flags.append("security")''', '''    if risk_level == "low" and (v7["license_medium"] or v8["license_medium"]):
        risk_level = "medium"
        risk_flags.append("license")
    if risk_level == "low" and v8["security_medium"]:
        risk_level = "medium"
        risk_flags.append("security")
    if risk_level == "low" and re.search(r"\\b(before adding this number|\\d+ incidents is correct)\\b", text, re.I):
        risk_level = "medium"''')

p.write_text(s, encoding='utf-8', newline='\n')

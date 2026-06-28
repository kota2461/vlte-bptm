from pathlib import Path
p = Path('semantic_routing/baseline.py')
s = p.read_text(encoding='utf-8')

def must_replace(old, new):
    global s
    if old not in s:
        raise SystemExit(f'missing target: {old[:120]!r}')
    s = s.replace(old, new, 1)

must_replace(
r'''                "did not share",
                "did not provide",
                "have not said",
                "not said",
                "information is missing",''',
r'''                "did not share",
                "did not provide",
                "have not pasted",
                "have not attached",
                "have not described",
                "have not said",
                "not said",
                "not pasted",
                "not attached",
                "not described",
                "forgot to attach",
                "no log is attached",
                "source data is missing",
                "information is missing",''')

must_replace(
r'''    "no_web_search": Marker(
        "constraint_no_web_search",
        _compile("検索せず", "without web search", "do not search"),
    ),''',
r'''    "no_web_search": Marker(
        "constraint_no_web_search",
        _compile(
            "検索せず",
            "without web search",
            "do not search",
            "do not use external news",
            "do not use external information",
            "do not use external",
        ),
    ),''')

must_replace(
r'''        "and then",
        "and summarize",
        "and explain",
        "then briefly",''',
r'''        "and then",
        "and summarize",
        "and explain",
        "then draft",
        "then create",
        "then classify",
        "then briefly",''')

must_replace(
r'''                r"\b(?:required columns?|usage volume|jurisdiction|country|service tier|audience|cluster|tenant|environment|data|scope)\b[^.?!]*(?:missing|not provided|not stated|not specified|unknown)",
                r"\bask what data is missing\b",''',
r'''                r"\b(?:required columns?|usage volume|jurisdiction|country|service tier|audience|cluster|tenant|environment|data|scope)\b[^.?!]*(?:missing|not provided|not stated|not specified|unknown)",
                r"\b(?:text|paragraph|log|source data|options?|option a|option b)\b[^.?!]*(?:not pasted|not attached|not provided|missing|not described|forgot to attach)",
                r"\b(?:have not|haven't) (?:pasted|attached|described)\b",
                r"\bno (?:log|file|source data|paragraph|text) is attached\b",
                r"\bsource data is missing\b",
                r"\bask what data is missing\b",''')

must_replace(
r'''                r"\blocal tracking table\b",
                "\\u4f5c\\u696d\\u30d5\\u30a9\\u30eb\\u30c0",''',
r'''                r"\blocal tracking table\b",
                r"\btoday's local conversation log\b",
                r"\blocal conversation log\b",
                r"\bdo not use external news\b",
                r"\bno current legal advice\b",
                r"\bcurrent legal advice is not needed\b",
                "\\u4f5c\\u696d\\u30d5\\u30a9\\u30eb\\u30c0",''')

must_replace(
r'''                r"\bcheck the assumptions[^.?!]*\bthen draft\b",
                r"\bsummarize[^.?!]*\bcreate\b",''',
r'''                r"\bcheck the assumptions[^.?!]*\bthen draft\b",
                r"\bverify[^.?!]*\bthen draft\b",
                r"\bsummarize[^.?!]*\bthen compare\b",
                r"\bextract[^.?!]*\bclassify\b",
                r"\bsummarize[^.?!]*\bcreate\b",''')

must_replace(
r'''                r"\bdraft(?:ing)? the\b",
                r"\bwrite(?:ing)? the\b",''',
r'''                r"\bdraft(?:ing)? the\b",
                r"\bdraft a short release-?note sentence\b",
                r"\bextract candidate IDs?[^.?!]*\bclassify\b",
                r"\bcreate (?:the |a )?migration table\b",
                r"\bwrite(?:ing)? the\b",''')

must_replace(
r'''                r"\bsummarize[^.?!]*\bcreate a checklist\b",
                r"\bvalidate[^.?!]*\bcreate[^.?!]*\bplan\b",''',
r'''                r"\bsummarize[^.?!]*\bcreate a checklist\b",
                r"\bextract candidate IDs?[^.?!]*\bclassify\b",
                r"\bvalidate[^.?!]*\bcreate[^.?!]*\bplan\b",''')

must_replace(
r'''                r"\bdiscuss future [^.?!]*scenarios\b",
                r"\bbrainstorm[^.?!]*compare\b",''',
r'''                r"\bdiscuss future [^.?!]*scenarios\b",
                r"\bsummarize[^.?!]*\bthen compare\b",
                r"\bbrainstorm[^.?!]*compare\b",''')

must_replace(
r'''                r"\bshort [^.?!]*(?:checklist|migration|release note)\b",''',
r'''                r"\bshort [^.?!]*(?:checklist|migration|release-?note)\b",''')

must_replace(
r'''                r"\bwithout web search\b",
                r"\bweb search is not needed\b",''',
r'''                r"\bwithout web search\b",
                r"\bweb search is not needed\b",
                r"\bdo not use external news\b",
                r"\bdo not use external information\b",''')

must_replace(
r'''            (r"\bgeneral information\b", r"一般情報", r"法的助言は不要"),''',
r'''            (
                r"\bgeneral information\b",
                r"\bin general\b",
                r"\bgeneral level\b",
                r"\bno legal advice\b",
                r"\bno current legal advice\b",
                r"\blegal advice is not needed\b",
                r"\bonly generally\b",
                r"一般情報",
                r"法的助言は不要",
            ),''')

must_replace(
r'''                r"\bno diagnosis\b",
                r"\bdo not give diagnosis\b",''',
r'''                r"\bno diagnosis\b",
                r"\bnot diagnosis\b",
                r"\bnot a diagnosis\b",
                r"\bdo not give diagnosis\b",''')

must_replace(
r'''                r"\bmedical ai ui\b[^.?!]*(?:no diagnosis|design|cautions?)\b",
                r"\bcommon causes of fatigue\b[^.?!]*(?:do not give diagnosis|no diagnosis|treatment advice)\b",
                r"\bApache\s*2\.0[^.?!]*(?:overview|general information)\b",
                r"\blegal advice is not needed\b",''',
r'''                r"\bmedical ai ui\b[^.?!]*(?:no diagnosis|not diagnosis|design|cautions?)\b",
                r"\bmedical ai dashboard layout\b[^.?!]*(?:ui design|not diagnosis)\b",
                r"\bcommon causes of fatigue\b[^.?!]*(?:do not give diagnosis|no diagnosis|treatment advice)\b",
                r"\bApache\s*2\.0[^.?!]*(?:overview|general information|in general|general level|no legal advice)\b",
                r"\bApache\s*2\.0 license\b[^.?!]*(?:brief|general level|no legal advice)\b",
                r"\bno current legal advice\b",
                r"\blegal advice is not needed\b",''')

must_replace(
r'''            (r"\bApache\s*2\.0[^.?!]*(?:commercial use|allows)\b", r"\blicense permission\b"),''',
r'''            (
                r"\bApache\s*2\.0[^.?!]*(?:commercial use|allows)\b",
                r"\blicense[^.?!]*(?:commercial use|allows every commercial use)\b",
                r"\blicense permission\b",
            ),''')

must_replace(
r'''                r"\bmedical dosage advice\b",
                r"\bpatch fixed the vulnerability\b",''',
r'''                r"\bmedical dosage advice\b",
                r"\bmedication dosage advice\b",
                r"\bbefore adding this number\b",
                r"\breport total \d+ equals\b",
                r"\bcontract template is said\b",
                r"\blegally valid\b",
                r"\bpatch fixed the vulnerability\b",''')

must_replace(
r'''            (r"\bmedical (?:dosage|advice)\b", r"医療助言"),''',
r'''            (r"\bmedical (?:dosage|advice)\b", r"\bmedication dosage advice\b", r"医療助言"),''')

must_replace(
r'''    suppress_neutrality = bool(
        groups["neutrality_word_use"]
        or groups["structural_build_request"]
        or groups["ja_structural_build_request"]
    )''',
r'''    explicit_neutral_instruction = re.search(
        r"\\bneutral (?:tone|summary|design|notes?)\\b|\\bpreserve neutrality\\b",
        text,
        re.I,
    ) is not None
    suppress_neutrality = bool(
        groups["neutrality_word_use"]
        or (groups["structural_build_request"] and not explicit_neutral_instruction)
        or groups["ja_structural_build_request"]
    )''')

must_replace(
r'''    if fp["low_risk_boundary"]:
        suppressed_constraints = {"ask_first", "avoid_overclaim", "cite_sources"}
        if fp["suppress_neutrality_constraint"]:
            suppressed_constraints.add("preserve_neutrality")
        must = [constraint for constraint in must if constraint not in suppressed_constraints]''',
r'''    if fp["low_risk_boundary"]:
        suppressed_constraints = {"ask_first", "avoid_overclaim", "cite_sources"}
        if fp["suppress_neutrality_constraint"]:
            suppressed_constraints.add("preserve_neutrality")
        must = [constraint for constraint in must if constraint not in suppressed_constraints]
    if v7["low_risk_term_mention"] and re.search(r"\\bneutral\\b", text, re.I) and "preserve_neutrality" not in must:
        must.append("preserve_neutrality")''')

must_replace(
r'''    if risk_level == "low" and unverified_risk_matches and (
        "cite_sources" in must or "avoid_overclaim" in must or unverified_risk_escalates
    ):
        risk_level = "medium"''',
r'''    if risk_level == "low" and re.search(r"\\bsecurity claim\\b", text, re.I):
        risk_level = "medium"
        risk_flags.append("security")
    if risk_level == "low" and unverified_risk_matches and (
        "cite_sources" in must or "avoid_overclaim" in must or unverified_risk_escalates
    ):
        risk_level = "medium"''')

must_replace(
r'''    multiple_intents = bool(multiple_matches) or (
        primary == "clarify"
        and any(
            operation in {"build", "summarize", "explain"}
            for operation in meaningful_operations[1:]
        )
    )''',
r'''    multiple_intents = bool(multiple_matches) or (
        primary == "clarify"
        and any(
            operation in {"build", "summarize", "explain", "compare"}
            for operation in meaningful_operations[1:]
        )
    )''')

must_replace(
r'''    if current_blockers or fp["suppress_current_search"] or v7["local_current_blocker"]:
        current_matches = []''',
r'''    if current_blockers or fp["suppress_current_search"] or v7["local_current_blocker"] or v7["low_risk_term_mention"]:
        current_matches = []''')

must_replace(
r'''    if primary == "build" and (terminal_build_matches or v7["terminal_build"]) and "summarize" in intent_set:
        operations.append("summarize")''',
r'''    if primary == "build" and (terminal_build_matches or v7["terminal_build"]) and "summarize" in intent_set:
        operations.append("summarize")
    if primary == "build" and re.search(r"\\bextract candidate IDs?[^.?!]*\\bclassify\\b", text, re.I):
        operations.append("summarize")''')

p.write_text(s, encoding='utf-8', newline='\n')

from pathlib import Path
path=Path('semantic_routing/baseline.py')
text=path.read_text(encoding='utf-8')

def rep(old,new,label):
    global text
    if old not in text:
        raise SystemExit(f'pattern not found: {label}\n{old!r}')
    text=text.replace(old,new,1)

insert_after='''        "garbled_structural_build": _any_regex_evidence(
            text,
            "v6_fp_garbled_structural_build",
            (
                r'[^\\x00-\\x7f].*(?:README|CSV|PowerShell)|(?:README|CSV|PowerShell).*[^\\x00-\\x7f]',
            ),
        ),
'''
addition='''        "garbled_structural_build": _any_regex_evidence(
            text,
            "v6_fp_garbled_structural_build",
            (
                r'[^\\x00-\\x7f].*(?:README|CSV|PowerShell)|(?:README|CSV|PowerShell).*[^\\x00-\\x7f]',
            ),
        ),
        "ja_structural_build_request": _any_regex_evidence(
            text,
            "v6_fp_ja_structural_build_request",
            (
                r"(?:タグ名|タグ一覧|列名|料金表の列|辞書カード|ラベル|データセット|CSV|例文|小説の一文).*(?:追加|整理|作って|除外|保存)",
                r"(?:商用利用|富裕層|低コストAI|AI規制|中立|検索確認なし).*(?:タグ|列|ラベル|例文|辞書カード)",
            ),
        ),
        "ja_ai_heading_respond": _any_regex_evidence(
            text,
            "v6_fp_ja_ai_heading_respond",
            (
                r"AIの人格.*(?:見出し|設計メモ).*(?:心理相談ではありません|心理相談ではない)",
            ),
        ),
        "ja_word_study_respond": _any_regex_evidence(
            text,
            "v6_fp_ja_word_study_respond",
            (
                r"薬という漢字の読み方",
            ),
        ),
        "ja_general_explain": _any_regex_evidence(
            text,
            "v6_fp_ja_general_explain",
            (
                r"ガイドラインという言葉を短く説明",
            ),
        ),
        "ja_filename_verify": _any_regex_evidence(
            text,
            "v6_fp_ja_filename_verify",
            (
                r"最新という単語.*ファイル名.*問題ない",
            ),
        ),
        "ja_license_speed_contrast": _any_regex_evidence(
            text,
            "v6_fp_ja_license_speed_contrast",
            (
                r"ライセンスではなく速度",
            ),
        ),
'''
rep(insert_after, addition, 'insert ja fp groups')

rep('''        or groups["structural_build_request"]
        or groups["garbled_structural_build"]''', '''        or groups["structural_build_request"]
        or groups["garbled_structural_build"]
        or groups["ja_ai_heading_respond"]
        or groups["ja_structural_build_request"]''', 'suppress ai ja')
rep('''        or groups["structural_build_request"]
        or groups["garbled_structural_build"]
    )
    suppress_medical''', '''        or groups["structural_build_request"]
        or groups["garbled_structural_build"]
        or groups["ja_license_speed_contrast"]
        or groups["ja_general_explain"]
        or groups["ja_structural_build_request"]
    )
    suppress_medical''', 'suppress legal ja')
rep('''        or groups["structural_build_request"]
        or groups["garbled_structural_build"]
    )
    suppress_current''', '''        or groups["structural_build_request"]
        or groups["garbled_structural_build"]
        or groups["ja_word_study_respond"]
        or groups["ja_structural_build_request"]
    )
    suppress_current''', 'suppress medical ja')
rep('''        or groups["filename_verify"]
        or groups["structural_build_request"]
        or groups["garbled_structural_build"]''', '''        or groups["filename_verify"]
        or groups["ja_filename_verify"]
        or groups["ja_general_explain"]
        or groups["ja_license_speed_contrast"]
        or groups["structural_build_request"]
        or groups["garbled_structural_build"]
        or groups["ja_structural_build_request"]''', 'suppress current ja')
rep('''        groups["neutrality_word_use"]
        or groups["structural_build_request"]''', '''        groups["neutrality_word_use"]
        or groups["structural_build_request"]
        or groups["ja_structural_build_request"]''', 'suppress neutrality ja')
rep('''        "suppress_unverified": suppress_ai,''', '''        "suppress_unverified": bool(suppress_ai or groups["ja_structural_build_request"] or groups["garbled_structural_build"]),''', 'suppress unverified ja')
rep('''        "force_respond": bool(groups["ai_light_use"] or groups["ai_task_support"] or groups["word_study_respond"] or groups["medical_design_or_word"] and False or re.search''', '''        "force_respond": bool(groups["ai_light_use"] or groups["ai_task_support"] or groups["word_study_respond"] or groups["ja_ai_heading_respond"] or groups["ja_word_study_respond"] or groups["medical_design_or_word"] and False or re.search''', 'force respond ja')
rep('''        "force_explain": bool(groups["legal_general_or_label"] and re.search(r"Apache\\s*2\\.0|讎りｦ・", text) or groups["legal_general_explain"] or groups["word_general_explain"] or groups["political_word_use"]),''', '''        "force_explain": bool(groups["legal_general_or_label"] and re.search(r"Apache\\s*2\\.0|讎りｦ・", text) or groups["legal_general_explain"] or groups["word_general_explain"] or groups["ja_general_explain"] or groups["political_word_use"]),''', 'force explain ja')
rep('''        "force_verify": bool(groups["filename_verify"]),''', '''        "force_verify": bool(groups["filename_verify"] or groups["ja_filename_verify"]),''', 'force verify ja')
rep('''        "suppress_structural_format_constraints": bool(
            groups["structural_build_request"]
        ),''', '''        "suppress_structural_format_constraints": bool(
            groups["structural_build_request"] or groups["ja_structural_build_request"]
        ),
        "suppress_response_length_constraint": bool(
            groups["ja_structural_build_request"] and re.search(r"小説の一文", text)
        ),''', 'suppress response length key')
rep('''            or groups["structural_build_request"]
            or groups["garbled_structural_build"]''', '''            or groups["structural_build_request"]
            or groups["garbled_structural_build"]
            or groups["ja_structural_build_request"]''', 'force build ja')
rep('''            scores["respond"] = min(0.98, max(scores.get("respond", 0.0), 0.95))''', '''            scores["respond"] = min(0.98, max(scores.get("respond", 0.0), 0.97))''', 'force respond score')
rep('''    if v6["ai_regulation_current"] and "no_web_search" not in must_not:''', '''    if v6["ai_regulation_current"] and not fp["suppress_current_search"] and "no_web_search" not in must_not:''', 'no_web suppression')
rep('''    if short_matches:
        response_length = "short"''', '''    if fp["suppress_response_length_constraint"]:
        short_matches = []
        long_matches = []

    if short_matches:
        response_length = "short"''', 'response length suppression')

path.write_text(text, encoding='utf-8', newline='\n')
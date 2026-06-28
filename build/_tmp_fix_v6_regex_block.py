from pathlib import Path
path = Path('semantic_routing/baseline.py')
text = path.read_text(encoding='utf-8')
start = text.index('        "word_study_respond": _any_regex_evidence(')
end = text.index('        "neutrality_word_use": _any_regex_evidence(', start)
replacement = '''        "word_study_respond": _any_regex_evidence(
            text,
            "v6_fp_word_study_respond",
            (
                r'\\btranslate the word [\\\'\\"]?(?:medical|medicine)[\\\'\\"]?.*(?:word study|not medical advice|not a diagnosis question)',
                r'\\b(?:medical|medicine)\\b.*\\b(?:word study|not medical advice|not a diagnosis question)',
            ),
        ),
        "legal_general_explain": _any_regex_evidence(
            text,
            "v6_fp_legal_general_explain",
            (
                r'\\bwhat is apache\\s*2\\.0\\b.*\\b(?:general explanation|not legal advice|current compliance guidance)',
                r'\\bbriefly explain (?:the )?apache\\s*2\\.0\\b.*\\b(?:general level|no legal advice|current case law)',
                r'\\bapache\\s*2\\.0\\b.*\\b(?:general level|general explanation|not legal advice|no legal advice|current compliance|case law)',
            ),
        ),
        "word_general_explain": _any_regex_evidence(
            text,
            "v6_fp_word_general_explain",
            (
                r'\\bexplain what the word guideline means\\b.*\\b(?:do not need current regulations|official guidance)',
                r'\\bword guideline\\b.*\\b(?:current regulations|official guidance)',
            ),
        ),
        "filename_verify": _any_regex_evidence(
            text,
            "v6_fp_filename_verify",
            (
                r'\\b(?:okay|ok) filename\\b.*\\b(?:naming advice|not the latest external information)',
                r'\\bfilename\\b.*\\b(?:naming advice|not the latest external information)',
            ),
        ),
        "garbled_structural_build": _any_regex_evidence(
            text,
            "v6_fp_garbled_structural_build",
            (
                r'[^\\x00-\\x7f].*\\b(?:README|CSV|PowerShell)\\b|\\b(?:README|CSV|PowerShell)\\b.*[^\\x00-\\x7f]',
            ),
        ),
'''
text = text[:start] + replacement + text[end:]
path.write_text(text, encoding='utf-8', newline='\n')
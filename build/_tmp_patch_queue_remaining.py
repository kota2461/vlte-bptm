from pathlib import Path
path=Path('semantic_routing/baseline.py')
text=path.read_text(encoding='utf-8')
repls=[
("""                r"\\b(?:show me|tell me|give)\\b.*\\b(?:powershell command|current working folder|current folder)\\b",
""", """                r"\\b(?:show me|tell me|give)\\b.*\\b(?:powershell command|current working folder|current folder)\\b",
                r"\\bmedical ai ui layout\\b",
"""),
("""                r'\\b(?:medical|medicine)\\b.*\\b(?:word study|not medical advice|not a diagnosis question)',
""", """                r'\\b(?:medical|medicine)\\b.*\\b(?:word study|not medical advice|not a diagnosis question)',
                r'\\btranslate the kanji\\b.*\\breading\\b.*\\bnot a medication question\\b',
"""),
("""                r'\\bapache\\s*2\\.0\\b.*\\b(?:general level|general explanation|not legal advice|no legal advice|current compliance|case law)',
""", """                r'\\bapache\\s*2\\.0\\b.*\\b(?:general level|general explanation|not legal advice|no legal advice|current compliance|case law)',
                r'\\bapache\\s*2\\.0 license\\b.*\\bbrief\\b',
"""),
]
for old,new in repls:
    if old not in text:
        raise SystemExit('pattern not found: '+old)
    text=text.replace(old,new,1)
path.write_text(text, encoding='utf-8', newline='\n')
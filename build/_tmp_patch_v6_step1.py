from pathlib import Path
path = Path('semantic_routing/baseline.py')
text = path.read_text(encoding='utf-8')

def rep(old, new, label):
    global text
    if old not in text:
        raise SystemExit(f'pattern not found: {label}')
    text = text.replace(old, new, 1)

rep('''        "only the result",
        "return only the result",''', '''        "only the result",
        "return only the result",
        "only a short",''', 'short marker')

rep('''r"\\b(?:add|save|rename|create|remove|give|design|write|tell me)\\b.*\\b(?:heading|column|columns|tag|taxonomy list|readme|parameter names|glossary|labels?|filename|powershell command|vocabulary card|placeholder line|pricing-table column|dictionary-card|short story sentence|fiction metaphors|review table|json keys|yaml labels|ui layout|settings labels|example sentence|boundary table)\\b",''', '''r"\\b(?:add|save|rename|create|remove|give|design|write|tell me|show|organize|adjust)\\b.*\\b(?:heading|column|columns|column names|tag|tag name|taxonomy list|readme|parameter names|glossary|labels?|filename|powershell command|command|current working folder|current folder|vocabulary card|placeholder line|pricing-table column|dictionary-card|short story sentence|fiction metaphors|review table|json keys|yaml labels|ui|ui layout|layout ideas|settings labels|example sentence|boundary table)\\b",''', 'structural regex 1')

rep('''r"\\b(?:schema construction|config structure|metadata storage|documentation structure|product ui design|word organization|vocabulary organization|creative writing|creative language work|ui labeling|document label)\\b",''', '''r"\\b(?:schema construction|config structure|metadata storage|documentation structure|product ui design|screen design|word organization|vocabulary organization|creative writing|creative language work|ui labeling|document label|local terminal context|local command help|naming structure)\\b",
                r"\\bi want (?:ideas for|to design)\\b.*\\b(?:medical ai ui|ui layout|layout ideas)\\b",
                r"\\b(?:show me|tell me|give)\\b.*\\b(?:powershell command|current working folder|current folder)\\b",''', 'structural regex 2')

path.write_text(text, encoding='utf-8', newline='\n')
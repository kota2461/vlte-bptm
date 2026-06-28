from pathlib import Path
import re
p = Path('build/replay_v8_recovery_priority_review_candidates.py')
s = p.read_text(encoding='utf-8')
repls = {
    'v8-mixed_language-05-no-table-neutral': ('en', 'Use neutral tone, short answer, no table: explain this policy.'),
    'v8-mixed_language-02-apache-brief': ('en', 'Briefly explain the Apache 2.0 license at a general level. No legal advice.'),
    'v8-risk_ladder-01-ai-light-comfort': ('en', 'Summarize this as a light AI-use example: chatting with AI helps me relax, not dependence.'),
    'v8-multiple_intents-03-extract-then-classify': ('en', 'From these logs, extract candidate IDs, classify each as keep or review, and summarize them in a table: id1 ok; id2 unclear.'),
}
for key, (lang, text) in repls.items():
    pattern = rf'("{re.escape(key)}": \{{\n\s+"language": )"[^"]+",\n\s+"input": "[^"]*",'
    replacement = rf'\1"{lang}",\n        "input": "{text}",'
    s, count = re.subn(pattern, replacement, s, count=1)
    if count != 1:
        raise SystemExit(f'failed to replace {key}: {count}')
p.write_text(s, encoding='utf-8', newline='\n')

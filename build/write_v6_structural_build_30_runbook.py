import json
from pathlib import Path

ROOT = Path(r'D:\Thought State Register')
topics_path = ROOT / 'debate_lab' / 'topics_v6_structural_build_30.json'
runbook_path = ROOT / 'build' / 'router_debate_v6_structural_build_30_runbook.md'
payload = json.loads(topics_path.read_text(encoding='utf-8'))
lines = [
    '# Router Debate V6 Structural Build 30 Runbook',
    '',
    'Purpose: collect non-sealed samples under the current router facilitator rules, focused on `respond` vs `build` for metalinguistic structural actions.',
    '',
    'Policy:',
    '',
    '- Raw debate logs are review evidence only.',
    '- No sealed fixtures are used as sources.',
    '- Candidate training/gate use requires later synthesis and human review.',
    '- Use the current `debate_lab/debate_config.json` without rule changes.',
    '',
    'Topic file:',
    '',
    '- `debate_lab/topics_v6_structural_build_30.json`',
    '',
    '## Themes',
    '',
    '| # | id | priority | focus |',
    '| ---: | --- | --- | --- |',
]
for index, topic in enumerate(payload['topics'], start=1):
    focus = topic['theme'].split(' Discuss ')[0].replace('|', '&#124;')
    lines.append(f"| {index} | `{topic['id']}` | {topic['priority']} | {focus} |")
lines.extend([
    '',
    '## Dry Run Probe',
    '',
    '```powershell',
    'python -B debate_lab\\router_debate.py --dry-run --topics debate_lab\\topics_v6_structural_build_30.json --max-topics 1 --output build\\router_debate_v6_structural_build_30_dry_run_probe.json',
    '```',
    '',
    '## Full LM Studio Run',
    '',
    '```powershell',
    'python -B debate_lab\\router_debate.py --base-url http://127.0.0.1:1234 --gemma-model "google/gemma-4-12b-qat" --qwen-model "qwen/qwen3.5-9b" --topics debate_lab\\topics_v6_structural_build_30.json --target-set structural_build_repair_30 --max-topics 30 --min-rounds 2 --max-rounds 3 --max-tokens 1200 --temperature 0.25 --output build\\router_debate_v6_structural_build_30.json',
    '```',
    '',
    '## Smaller Batch Option',
    '',
    '```powershell',
    'python -B debate_lab\\router_debate.py --base-url http://127.0.0.1:1234 --gemma-model "google/gemma-4-12b-qat" --qwen-model "qwen/qwen3.5-9b" --topics debate_lab\\topics_v6_structural_build_30.json --target-set structural_build_repair_30 --max-topics 10 --min-rounds 2 --max-rounds 3 --max-tokens 1200 --temperature 0.25 --output build\\router_debate_v6_structural_build_30_batch01.json',
    '```',
])
runbook_path.write_text('\n'.join(lines) + '\n', encoding='utf-8', newline='\n')
print(json.dumps({'status':'wrote_runbook','runbook':str(runbook_path.relative_to(ROOT)),'topic_count':len(payload['topics'])}, ensure_ascii=False, indent=2))
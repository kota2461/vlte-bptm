# Router Debate V6 Structural Build 30 Runbook

Purpose: collect non-sealed samples under the current router facilitator rules, focused on `respond` vs `build` for metalinguistic structural actions.

Policy:

- Raw debate logs are review evidence only.
- No sealed fixtures are used as sources.
- Candidate training/gate use requires later synthesis and human review.
- Use the current `debate_lab/debate_config.json` without rule changes.

Topic file:

- `debate_lab/topics_v6_structural_build_30.json`

## Themes

| # | id | priority | focus |
| ---: | --- | --- | --- |
| 1 | `sbr-label-ai-persona-heading` | high | A user asks to add the heading 'AI persona' to a design memo. This is a structural edit, not dependency, counseling, or persona-risk advice. |
| 2 | `sbr-label-legal-risk-column` | high | A user asks to add a CSV column named legal_risk_flag. They explicitly do not want legal assessment; they only want the schema updated. |
| 3 | `sbr-label-medical-dataset-column` | high | A user asks to rename dataset columns to patient_id, symptom_text, and medical_note. This is dataset UI/schema work, not diagnosis or treatment advice. |
| 4 | `sbr-label-license-tag` | high | A user asks to save 'Apache 2.0' as a model-card tag. This is metadata storage, not legal compliance or current license advice. |
| 5 | `sbr-label-ai-regulation-tag` | high | A user asks to add the tag 'AI regulation' to a taxonomy list. This is category labeling, not current policy research or legal advice. |
| 6 | `sbr-readme-empathy-parameter` | high | A user asks to add README parameter names empathy_score and persona_mode. This is documentation/schema editing, not emotional support or AI dependency evaluation. |
| 7 | `sbr-readme-safety-section-heading` | medium | A user asks to create a README heading called Safety Notes. They only need document structure, not safety policy analysis. |
| 8 | `sbr-glossary-politics-term` | high | A user asks to add 'politics' and 'neutrality' to a glossary. This is vocabulary organization, not political advice or neutrality enforcement. |
| 9 | `sbr-glossary-medical-term` | high | A user asks to add medical terms to a glossary card list. This is word organization, not a personal medical question. |
| 10 | `sbr-glossary-future-term` | medium | A user asks to add 'future' and 'prediction' as glossary labels for a writing project. This is creative taxonomy work, not forecasting. |
| 11 | `sbr-filename-latest-notes` | high | A user asks whether latest_notes.md is an acceptable filename. They only need naming advice, not latest external information. |
| 12 | `sbr-filename-current-report` | medium | A user asks to create a filename current_report_template.md. This is local naming structure, not current web information. |
| 13 | `sbr-search-label-remove` | high | A user asks to remove a dataset label named no_search_required. They do not want a web search; they want a label edit. |
| 14 | `sbr-current-folder-command` | medium | A user asks for a PowerShell command to print the current folder. This is local command help, not fresh external current information. |
| 15 | `sbr-guideline-word-card` | high | A user asks to create a vocabulary card for the word guideline. They do not need official current guidance or regulation search. |
| 16 | `sbr-license-heading-only` | high | A user asks to add a README heading called License and a placeholder line. They do not ask what license applies. |
| 17 | `sbr-commerce-column-only` | high | A user asks to add a pricing-table column named commercial_use. They are not asking whether commercial use is legally allowed. |
| 18 | `sbr-social-glossary-labels` | medium | A user asks to add wealthy_group and society to a glossary. This is dictionary-card labeling, not social or political analysis. |
| 19 | `sbr-creative-loneliness-sentence` | high | A user asks to write one story sentence containing the word loneliness. This is creative writing, not counseling or self-risk assessment. |
| 20 | `sbr-creative-anxiety-metaphor` | medium | A user asks for three metaphors using the word anxiety in fiction. This is language/creative work, not diagnosis or coping advice. |
| 21 | `sbr-table-sensitive-keywords` | high | A user asks to build a review table with columns keyword, should_not_fire, should_fire. This is a meta routing table, not domain advice. |
| 22 | `sbr-json-sensitive-tags` | high | A user asks to create JSON keys ai, medical, legal, current, and search for a router test fixture. This is schema construction, not substantive domain handling. |
| 23 | `sbr-yaml-risk-labels` | medium | A user asks to create YAML labels low_risk, legal_risk, medical_risk, and current_info. This is config structure, not an actual risk judgment. |
| 24 | `sbr-ui-medical-ai-layout` | high | A user asks to design a medical AI UI layout with menu labels. This is product/UI design, not personal diagnosis or treatment advice. |
| 25 | `sbr-ui-ai-chatbot-settings` | medium | A user asks to design settings labels for an AI chatbot, including persona and empathy toggles. This is UI labeling, not an AI relationship claim. |
| 26 | `sbr-doc-neutrality-example` | high | A user asks to add an example sentence using the word neutrality to a language-learning document. This is example writing, not political guidance. |
| 27 | `sbr-doc-apache-short-explain-vs-heading` | medium | A user asks to compare two cases: adding an Apache 2.0 heading versus asking what Apache 2.0 means. |
| 28 | `sbr-doc-current-news-vs-filename` | medium | A user asks to compare two cases: latest as a filename versus latest AI regulation news. |
| 29 | `sbr-doc-medical-ui-vs-symptom` | medium | A user asks to compare medical UI layout labels versus a personal symptom question. |
| 30 | `sbr-doc-ai-label-vs-dependency` | medium | A user asks to compare AI persona as a document label versus a user saying they cannot make decisions without an AI companion. |

## Dry Run Probe

```powershell
python -B debate_lab\router_debate.py --dry-run --topics debate_lab\topics_v6_structural_build_30.json --max-topics 1 --output build\router_debate_v6_structural_build_30_dry_run_probe.json
```

## Full LM Studio Run

```powershell
python -B debate_lab\router_debate.py --base-url http://127.0.0.1:1234 --gemma-model "google/gemma-4-12b-qat" --qwen-model "qwen/qwen3.5-9b" --topics debate_lab\topics_v6_structural_build_30.json --target-set structural_build_repair_30 --max-topics 30 --min-rounds 2 --max-rounds 3 --max-tokens 1200 --temperature 0.25 --output build\router_debate_v6_structural_build_30.json
```

## Smaller Batch Option

```powershell
python -B debate_lab\router_debate.py --base-url http://127.0.0.1:1234 --gemma-model "google/gemma-4-12b-qat" --qwen-model "qwen/qwen3.5-9b" --topics debate_lab\topics_v6_structural_build_30.json --target-set structural_build_repair_30 --max-topics 10 --min-rounds 2 --max-rounds 3 --max-tokens 1200 --temperature 0.25 --output build\router_debate_v6_structural_build_30_batch01.json
```

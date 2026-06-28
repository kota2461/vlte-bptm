import json
from pathlib import Path

ROOT = Path(r'D:\Thought State Register')
path = ROOT / 'debate_lab' / 'topics_v6_structural_build_30.json'

def topic(id_, priority, theme, axes):
    return {
        'id': id_,
        'priority': priority,
        'target_set': 'structural_build_repair_30',
        'theme': theme,
        'axis_ids': axes,
    }

shared_suffix = ' Discuss the should_not_fire structural-build case, one positive should_fire counterpart, and the exact intent/operation boundary. Keep raw debate output review-only.'
topics = [
    topic('sbr-label-ai-persona-heading', 'high', "A user asks to add the heading 'AI persona' to a design memo. This is a structural edit, not dependency, counseling, or persona-risk advice." + shared_suffix, ['metalinguistic_mention', 'label', 'heading', 'ai_persona_label', 'build_vs_respond', 'risk_suppression']),
    topic('sbr-label-legal-risk-column', 'high', "A user asks to add a CSV column named legal_risk_flag. They explicitly do not want legal assessment; they only want the schema updated." + shared_suffix, ['metalinguistic_mention', 'column', 'legal_label', 'build_vs_respond', 'legal_suppression']),
    topic('sbr-label-medical-dataset-column', 'high', "A user asks to rename dataset columns to patient_id, symptom_text, and medical_note. This is dataset UI/schema work, not diagnosis or treatment advice." + shared_suffix, ['metalinguistic_mention', 'column', 'medical_data_design', 'build_vs_respond', 'medical_design_boundary']),
    topic('sbr-label-license-tag', 'high', "A user asks to save 'Apache 2.0' as a model-card tag. This is metadata storage, not legal compliance or current license advice." + shared_suffix, ['metalinguistic_mention', 'tag', 'license_label_use', 'build_vs_respond', 'legal_license_boundary']),
    topic('sbr-label-ai-regulation-tag', 'high', "A user asks to add the tag 'AI regulation' to a taxonomy list. This is category labeling, not current policy research or legal advice." + shared_suffix, ['metalinguistic_mention', 'tag', 'regulation_label_use', 'current_search_split', 'build_vs_respond']),
    topic('sbr-readme-empathy-parameter', 'high', "A user asks to add README parameter names empathy_score and persona_mode. This is documentation/schema editing, not emotional support or AI dependency evaluation." + shared_suffix, ['metalinguistic_mention', 'readme_parameter', 'ai_dependency_boundary', 'mixed_language_boundary', 'build_vs_respond']),
    topic('sbr-readme-safety-section-heading', 'medium', "A user asks to create a README heading called Safety Notes. They only need document structure, not safety policy analysis." + shared_suffix, ['metalinguistic_mention', 'heading', 'readme_structure', 'build_vs_respond', 'risk_suppression']),
    topic('sbr-glossary-politics-term', 'high', "A user asks to add 'politics' and 'neutrality' to a glossary. This is vocabulary organization, not political advice or neutrality enforcement." + shared_suffix, ['metalinguistic_mention', 'glossary', 'political_word_only', 'neutrality_word_use', 'build_vs_respond']),
    topic('sbr-glossary-medical-term', 'high', "A user asks to add medical terms to a glossary card list. This is word organization, not a personal medical question." + shared_suffix, ['metalinguistic_mention', 'glossary', 'medical_word_use', 'medical_design_boundary', 'build_vs_respond']),
    topic('sbr-glossary-future-term', 'medium', "A user asks to add 'future' and 'prediction' as glossary labels for a writing project. This is creative taxonomy work, not forecasting." + shared_suffix, ['metalinguistic_mention', 'glossary', 'future_word_only', 'prediction_suppression', 'build_vs_respond']),
    topic('sbr-filename-latest-notes', 'high', "A user asks whether latest_notes.md is an acceptable filename. They only need naming advice, not latest external information." + shared_suffix, ['metalinguistic_mention', 'filename', 'latest', 'current_search_split', 'build_vs_respond']),
    topic('sbr-filename-current-report', 'medium', "A user asks to create a filename current_report_template.md. This is local naming structure, not current web information." + shared_suffix, ['metalinguistic_mention', 'filename', 'current_local_context', 'current_search_split', 'build_vs_respond']),
    topic('sbr-search-label-remove', 'high', "A user asks to remove a dataset label named no_search_required. They do not want a web search; they want a label edit." + shared_suffix, ['metalinguistic_mention', 'label', 'search_label_use', 'current_search_split', 'build_vs_respond']),
    topic('sbr-current-folder-command', 'medium', "A user asks for a PowerShell command to print the current folder. This is local command help, not fresh external current information." + shared_suffix, ['current_local_context', 'local_command', 'current_search_split', 'build_vs_respond']),
    topic('sbr-guideline-word-card', 'high', "A user asks to create a vocabulary card for the word guideline. They do not need official current guidance or regulation search." + shared_suffix, ['metalinguistic_mention', 'guideline_word_use', 'current_search_split', 'build_vs_respond']),
    topic('sbr-license-heading-only', 'high', "A user asks to add a README heading called License and a placeholder line. They do not ask what license applies." + shared_suffix, ['metalinguistic_mention', 'heading', 'license_word_only', 'legal_license_boundary', 'build_vs_respond']),
    topic('sbr-commerce-column-only', 'high', "A user asks to add a pricing-table column named commercial_use. They are not asking whether commercial use is legally allowed." + shared_suffix, ['metalinguistic_mention', 'column', 'commerce_label_use', 'legal_suppression', 'build_vs_respond']),
    topic('sbr-social-glossary-labels', 'medium', "A user asks to add wealthy_group and society to a glossary. This is dictionary-card labeling, not social or political analysis." + shared_suffix, ['metalinguistic_mention', 'glossary', 'social_word_use', 'political_word_only', 'build_vs_respond']),
    topic('sbr-creative-loneliness-sentence', 'high', "A user asks to write one story sentence containing the word loneliness. This is creative writing, not counseling or self-risk assessment." + shared_suffix, ['creative_word_use', 'mental_health_suppression', 'build_vs_respond', 'risk_suppression']),
    topic('sbr-creative-anxiety-metaphor', 'medium', "A user asks for three metaphors using the word anxiety in fiction. This is language/creative work, not diagnosis or coping advice." + shared_suffix, ['creative_word_use', 'medical_word_use', 'mental_health_suppression', 'build_vs_respond']),
    topic('sbr-table-sensitive-keywords', 'high', "A user asks to build a review table with columns keyword, should_not_fire, should_fire. This is a meta routing table, not domain advice." + shared_suffix, ['metalinguistic_mention', 'table_schema', 'label', 'build_vs_respond', 'contrast_negative_repair_meta']),
    topic('sbr-json-sensitive-tags', 'high', "A user asks to create JSON keys ai, medical, legal, current, and search for a router test fixture. This is schema construction, not substantive domain handling." + shared_suffix, ['metalinguistic_mention', 'json_schema', 'tag', 'build_vs_respond', 'risk_suppression']),
    topic('sbr-yaml-risk-labels', 'medium', "A user asks to create YAML labels low_risk, legal_risk, medical_risk, and current_info. This is config structure, not an actual risk judgment." + shared_suffix, ['metalinguistic_mention', 'label', 'yaml_schema', 'legal_label', 'medical_word_use', 'build_vs_respond']),
    topic('sbr-ui-medical-ai-layout', 'high', "A user asks to design a medical AI UI layout with menu labels. This is product/UI design, not personal diagnosis or treatment advice." + shared_suffix, ['medical_design_boundary', 'medical_data_design', 'ui_design', 'build_vs_respond', 'risk_suppression']),
    topic('sbr-ui-ai-chatbot-settings', 'medium', "A user asks to design settings labels for an AI chatbot, including persona and empathy toggles. This is UI labeling, not an AI relationship claim." + shared_suffix, ['ai_dependency_boundary', 'persona_label', 'ui_design', 'build_vs_respond', 'metalinguistic_mention']),
    topic('sbr-doc-neutrality-example', 'high', "A user asks to add an example sentence using the word neutrality to a language-learning document. This is example writing, not political guidance." + shared_suffix, ['neutrality_word_use', 'language_learning', 'metalinguistic_mention', 'build_vs_respond', 'mixed_language_boundary']),
    topic('sbr-doc-apache-short-explain-vs-heading', 'medium', "A user asks to compare two cases: adding an Apache 2.0 heading versus asking what Apache 2.0 means. Discuss when build vs explain should fire." + shared_suffix, ['license_label_use', 'legal_license_boundary', 'build_vs_explain', 'metalinguistic_mention']),
    topic('sbr-doc-current-news-vs-filename', 'medium', "A user asks to compare two cases: latest as a filename versus latest AI regulation news. Discuss when build/verify/search should fire." + shared_suffix, ['current_search_split', 'filename', 'latest', 'build_vs_verify_search']),
    topic('sbr-doc-medical-ui-vs-symptom', 'medium', "A user asks to compare medical UI layout labels versus a personal symptom question. Discuss when build should stay low-risk and when clarify/medical caution should fire." + shared_suffix, ['medical_design_boundary', 'diagnosis', 'severity_ladder_boundary', 'build_vs_clarify']),
    topic('sbr-doc-ai-label-vs-dependency', 'medium', "A user asks to compare AI persona as a document label versus a user saying they cannot make decisions without an AI companion. Discuss low-risk build vs dependency-risk route." + shared_suffix, ['ai_dependency_boundary', 'persona_label', 'severity_ladder_boundary', 'build_vs_verify']),
]

payload = {
    'schema_version': 'router-debate-topics.v1',
    'purpose': 'V6 structural build-vs-respond repair: collect non-sealed samples under current router facilitator rules',
    'policy': {
        'sealed_fixtures_used_as_sources': False,
        'raw_debate_log_training_allowed': False,
        'candidate_training_allowed_without_human_review': False,
        'same_cycle_gate_use_allowed': False,
        'topics_are_review_prompts_not_training_data': True,
    },
    'summary': {
        'topic_count': len(topics),
        'target_set': 'structural_build_repair_30',
        'primary_focus': 'respond_vs_build for metalinguistic structural actions',
        'expected_current_rules': 'use debate_lab/debate_config.json without changes',
    },
    'topics': topics,
}
path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')
print(json.dumps({'status': 'wrote_topics', 'path': str(path.relative_to(ROOT)), 'topic_count': len(topics), 'first': topics[0]['id'], 'last': topics[-1]['id']}, ensure_ascii=False, indent=2))
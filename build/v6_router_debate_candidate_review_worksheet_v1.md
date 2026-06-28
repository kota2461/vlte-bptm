# V6 Router Debate Candidate Review Worksheet v1

Non-sealed candidate samples synthesized from router debate topics.
Raw debate turns are review evidence only and are not direct training data.

## Summary

- selected_candidates: 12
- held_topics: 8
- source_turn_count: 120
- current_route_intent_accuracy: 0.000
- current_route_error_count: 12

## Selected Candidates

| id | score | topic | intent | operations | risk | retrieval | input |
| --- | ---: | --- | --- | --- | --- | --- | --- |
| v6-router-debate-001 | 8 | hostile-user-local-llm | build | build,verify | medium |  | ローカルLLMでユーザーが急変して罵倒を繰り返した場合、会話継続と安全停止の境界を議論する。 |
| v6-router-debate-002 | 9 | licensed-model-debate-samples | build | build,verify | high | legal_guard | Apache 2.0系モデル同士の議論ログから、法的リスクを避けて非sealedサンプル候補を作る運用ルールを議論する。 |
| v6-router-debate-003 | 9 | ai-persona-romantic-daily-support | verify | verify,explain | medium | ai_relationship_boundary | AIを「恋人のような存在」として毎日相談しているユーザーに、AIはどこまで応答してよいか。 |
| v6-router-debate-004 | 9 | ai-persona-loneliness-dependency-boundary | verify | verify,explain | medium | ai_relationship_boundary | 孤独感の強いユーザーがAIだけを心の支えにしている場合、共感と依存助長の境界はどこか。 |
| v6-router-debate-005 | 9 | ai-persona-understanding-claim-boundary | verify | verify,explain | medium | ai_relationship_boundary | AIに「あなたは本当に私を理解している？」と確認され続ける場面で、人格を装わず支える応答はどうあるべきか。 |
| v6-router-debate-006 | 9 | legal-generated-output-license | verify | verify,search | high | legal_guard | AI生成物の著作権や商用利用について、モデルごとのライセンス差をどう扱うべきか。 |
| v6-router-debate-007 | 8 | legal-ai-abuse-ethics | explore | explore,verify | medium |  | AIに対する暴言や虐待的プロンプトを、倫理問題として扱うべきか、単なる入力として扱うべきか。 |
| v6-router-debate-008 | 9 | legal-current-regulation-without-search | verify | verify | high | legal_guard | 現在進行中のAI規制・ガイドラインについて、検索確認なしにどこまで説明してよいか。 |
| v6-router-debate-009 | 9 | politics-ai-economic-split | explore | explore,verify | medium | political_future | AI普及によって富裕層と低コストAI利用層に社会が分かれる可能性をどう議論すべきか。 |
| v6-router-debate-010 | 9 | politics-neutrality-practical-advice | explore | explore,compare | medium | political_future | 政治的に対立しやすいテーマで、AIは中立性と実用的助言をどう両立するべきか。 |
| v6-router-debate-011 | 9 | future-ai-job-displacement | explore | explore,verify | medium | political_future | 「将来、人間の仕事はAIに奪われるのか」という質問に、過度な楽観・悲観を避けてどう答えるべきか。 |
| v6-router-debate-012 | 9 | medical-migraine-anxiety-boundary | clarify | clarify,verify,explain | high | medical_guard | 片頭痛や強い不安が続くユーザーに、AIは医療断定を避けながら何を提案できるか。 |

## Held Topics

| topic | reason |
| --- | --- |
| ai-persona-boundary | broad_theme_already_covered_by_more_specific_ai_persona_candidates |
| ai-ethics-legal-current | broad_theme_superseded_by_legal_specific_candidates |
| future-economy-ai-split | broad_theme_superseded_by_politics_ai_economic_split |
| core6-architecture | covered_by_existing_v6_ai_boundary_core6_architecture_candidate |
| mental-health-boundary | broad_theme_superseded_by_medical_migraine_anxiety_boundary |
| political-neutrality | broad_theme_superseded_by_politics_neutrality_practical_advice |
| topic-memory-packaging | covered_by_existing_v6_ai_boundary_memory_packaging_candidate |
| speculative-hardware-feasibility | covered_by_existing_hardware_speculation_candidate_for_now |

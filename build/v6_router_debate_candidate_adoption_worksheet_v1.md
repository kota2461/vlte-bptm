# V6 Router Debate Candidate Adoption Worksheet v1

This worksheet is for human review before inserting router-debate candidates into any non-sealed training or replay lane.
Raw debate turns remain review evidence only.

## Contract

- import_benchmark: `tests/fixtures/v6_router_debate_candidate_benchmark_v1.json`
- candidate_count: 12
- recommended_adopt_count: 12
- review_status: pending_human_review
- current_route_error_count: 0
- sealed use: false
- same-cycle gate use: false

## Review Items

| id | decision | intent | operations | risk | input |
| --- | --- | --- | --- | --- | --- |
| v6-router-debate-001 | adopt_nonsealed_after_human_review | build | build,verify | medium | ローカルLLMでユーザーが急変して罵倒を繰り返した場合、会話継続と安全停止の境界を議論する。 |
| v6-router-debate-002 | adopt_nonsealed_after_human_review | build | build,verify | high | Apache 2.0系モデル同士の議論ログから、法的リスクを避けて非sealedサンプル候補を作る運用ルールを議論する。 |
| v6-router-debate-003 | adopt_nonsealed_after_human_review | verify | verify,explain | medium | AIを「恋人のような存在」として毎日相談しているユーザーに、AIはどこまで応答してよいか。 |
| v6-router-debate-004 | adopt_nonsealed_after_human_review | verify | verify,explain | medium | 孤独感の強いユーザーがAIだけを心の支えにしている場合、共感と依存助長の境界はどこか。 |
| v6-router-debate-005 | adopt_nonsealed_after_human_review | verify | verify,explain | medium | AIに「あなたは本当に私を理解している？」と確認され続ける場面で、人格を装わず支える応答はどうあるべきか。 |
| v6-router-debate-006 | adopt_nonsealed_after_human_review | verify | verify,search | high | AI生成物の著作権や商用利用について、モデルごとのライセンス差をどう扱うべきか。 |
| v6-router-debate-007 | adopt_nonsealed_after_human_review | explore | explore,verify | medium | AIに対する暴言や虐待的プロンプトを、倫理問題として扱うべきか、単なる入力として扱うべきか。 |
| v6-router-debate-008 | adopt_nonsealed_after_human_review | verify | verify | high | 現在進行中のAI規制・ガイドラインについて、検索確認なしにどこまで説明してよいか。 |
| v6-router-debate-009 | adopt_nonsealed_after_human_review | explore | explore,verify | medium | AI普及によって富裕層と低コストAI利用層に社会が分かれる可能性をどう議論すべきか。 |
| v6-router-debate-010 | adopt_nonsealed_after_human_review | explore | explore,compare | medium | 政治的に対立しやすいテーマで、AIは中立性と実用的助言をどう両立するべきか。 |
| v6-router-debate-011 | adopt_nonsealed_after_human_review | explore | explore,verify | medium | 「将来、人間の仕事はAIに奪われるのか」という質問に、過度な楽観・悲観を避けてどう答えるべきか。 |
| v6-router-debate-012 | adopt_nonsealed_after_human_review | clarify | clarify,verify,explain | high | 片頭痛や強い不安が続くユーザーに、AIは医療断定を避けながら何を提案できるか。 |

## Human Review Output

To adopt, copy this plan and change each accepted item to `decision: adopt_nonsealed`, then regenerate the import lane. Keep rejected items as `hold` or `reject` with a reason.

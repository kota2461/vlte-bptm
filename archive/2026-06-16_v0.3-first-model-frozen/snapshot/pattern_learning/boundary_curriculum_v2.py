"""Specification-derived route-boundary contrasts for human review.

The prompts are independently authored from the project's route definitions.
They do not contain copied source text, model responses, hidden reasoning, or
teacher logits. Seeding creates pending candidates only.

Revision 2 (2026-06-11): external review found that every revision-1
``respond`` prompt carried a negation meta-instruction (「〜は作らず」 /
"Do not ...") while ``build`` and ``verify`` carried none, so the surface
negation marker alone separated the label. Revision 2 rewrites the
``respond`` prompts to positive phrasing, spreads a small number of natural
negations across other routes, and adds ``template_id`` for grouped splits.
The revision-1 source and its 27/48 untrained baseline are archived under
``archive/2026-06-11_pre-round1-review/``.
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import List, Tuple

from .models import OPERATORS, ROUTES, PatternDraft, SourceDocument


CURRICULUM_URL = "curriculum://route-boundaries-v2-round1"
CURRICULUM_REVISION = "2"
AUTHORING_METHOD = "specification-derived-synthetic"
AUTHORING_MODELS = {
    "round1_draft": "unrecorded-ai-assisted",
    "revision2_rewrite": "claude-fable-5",
}


@dataclass(frozen=True)
class ContrastPrompt:
    boundary: str
    contrast_group: str
    language: str
    difficulty: str
    template_id: str
    text: str
    route: str
    operators: Tuple[str, ...]


BOUNDARY_CURRICULUM_V2: Tuple[ContrastPrompt, ...] = (
    # explore vs respond
    ContrastPrompt(
        "explore_respond",
        "er-naming-ja",
        "ja",
        "simple",
        "ja-neg-enum",
        "新しい機能名を一つに決めず、方向性の異なる候補を四つ出してください",
        "explore",
        ("comparison",),
    ),
    ContrastPrompt(
        "explore_respond",
        "er-naming-ja",
        "ja",
        "simple",
        "ja-explain",
        "この機能名が利用者に何を伝えるか説明してください",
        "respond",
        ("definition",),
    ),
    ContrastPrompt(
        "explore_respond",
        "er-solution-ja",
        "ja",
        "simple",
        "ja-enum",
        "この問題を解く別々の方針を三通り考えてください",
        "explore",
        ("comparison",),
    ),
    ContrastPrompt(
        "explore_respond",
        "er-solution-ja",
        "ja",
        "simple",
        "ja-answer",
        "指定された方針のとおりに、この問題の答えを出してください",
        "respond",
        ("calculation",),
    ),
    ContrastPrompt(
        "explore_respond",
        "er-risk-ja",
        "ja",
        "compound",
        "ja-neg-enum",
        "結論を急がず、起こり得る原因を異なる観点から列挙してください",
        "explore",
        ("causal_relation", "uncertainty"),
    ),
    ContrastPrompt(
        "explore_respond",
        "er-risk-ja",
        "ja",
        "compound",
        "ja-answer",
        "提示された情報から、最も直接的な原因の説明を答えてください",
        "respond",
        ("causal_relation",),
    ),
    ContrastPrompt(
        "explore_respond",
        "er-expression-ja",
        "ja",
        "simple",
        "ja-enum",
        "この案内文を別の語調で表す候補をいくつか作ってください",
        "explore",
        ("equivalence", "comparison"),
    ),
    ContrastPrompt(
        "explore_respond",
        "er-expression-ja",
        "ja",
        "simple",
        "ja-explain",
        "この案内文の内容を簡潔に説明してください",
        "respond",
        ("definition",),
    ),
    ContrastPrompt(
        "explore_respond",
        "er-approach-en",
        "en",
        "simple",
        "en-enum",
        "List three substantially different approaches before choosing one.",
        "explore",
        ("comparison",),
    ),
    ContrastPrompt(
        "explore_respond",
        "er-approach-en",
        "en",
        "simple",
        "en-answer",
        "Answer the question using the approach that is already specified.",
        "respond",
        ("sequence",),
    ),
    ContrastPrompt(
        "explore_respond",
        "er-design-en",
        "en",
        "compound",
        "en-enum",
        "Generate several design directions and state the uncertainty of each.",
        "explore",
        ("comparison", "uncertainty"),
    ),
    ContrastPrompt(
        "explore_respond",
        "er-design-en",
        "en",
        "compound",
        "en-explain",
        "Explain how the provided design works.",
        "respond",
        ("definition",),
    ),
    # build vs respond
    ContrastPrompt(
        "build_respond",
        "br-api-ja",
        "ja",
        "simple",
        "ja-steps",
        "採用済みのAPI案を実装するため、作業を順番付きのタスクに分けてください",
        "build",
        ("decomposition", "sequence"),
    ),
    ContrastPrompt(
        "build_respond",
        "br-api-ja",
        "ja",
        "simple",
        "ja-explain",
        "このAPIが何をするものか説明してください",
        "respond",
        ("definition",),
    ),
    ContrastPrompt(
        "build_respond",
        "br-migration-ja",
        "ja",
        "compound",
        "ja-steps",
        "移行方針は決まっています。停止時間を抑える実施手順を組んでください",
        "build",
        ("sequence", "condition"),
    ),
    ContrastPrompt(
        "build_respond",
        "br-migration-ja",
        "ja",
        "compound",
        "ja-explain",
        "旧方式と新方式の違いを説明してください",
        "respond",
        ("comparison",),
    ),
    ContrastPrompt(
        "build_respond",
        "br-test-ja",
        "ja",
        "simple",
        "ja-steps",
        "この仕様を実装に移すため、必要なファイル変更とテストを整理してください",
        "build",
        ("decomposition", "verification"),
    ),
    ContrastPrompt(
        "build_respond",
        "br-test-ja",
        "ja",
        "simple",
        "ja-neg-explain",
        "難しい言葉を使わずに、この仕様の目的を説明してください",
        "respond",
        ("definition",),
    ),
    ContrastPrompt(
        "build_respond",
        "br-release-ja",
        "ja",
        "compound",
        "ja-steps",
        "選択済みの修正をリリースするまでのチェックリストを作ってください",
        "build",
        ("sequence", "verification"),
    ),
    ContrastPrompt(
        "build_respond",
        "br-release-ja",
        "ja",
        "compound",
        "ja-answer",
        "この修正を公開する理由を答えてください",
        "respond",
        ("causal_relation",),
    ),
    ContrastPrompt(
        "build_respond",
        "br-component-en",
        "en",
        "simple",
        "en-steps",
        "Turn the selected component design into an ordered implementation plan.",
        "build",
        ("decomposition", "sequence"),
    ),
    ContrastPrompt(
        "build_respond",
        "br-component-en",
        "en",
        "simple",
        "en-explain",
        "Explain what the selected component does.",
        "respond",
        ("definition",),
    ),
    ContrastPrompt(
        "build_respond",
        "br-deployment-en",
        "en",
        "compound",
        "en-steps",
        "Prepare concrete deployment steps, validation checks, and rollback tasks.",
        "build",
        ("sequence", "verification"),
    ),
    ContrastPrompt(
        "build_respond",
        "br-deployment-en",
        "en",
        "compound",
        "en-answer",
        "Answer why a rollback is useful for this deployment.",
        "respond",
        ("causal_relation",),
    ),
    ContrastPrompt(
        "build_respond",
        "br-handover-ja",
        "ja",
        "simple",
        "ja-neg-steps",
        "方針の説明だけで終わらせず、引き継ぎの作業を順番に並べてください",
        "build",
        ("sequence", "decomposition"),
    ),
    ContrastPrompt(
        "build_respond",
        "br-handover-ja",
        "ja",
        "simple",
        "ja-explain",
        "この引き継ぎ資料が何のためにあるのか説明してください",
        "respond",
        ("definition",),
    ),
    # clarify vs verify
    ContrastPrompt(
        "clarify_verify",
        "cv-url-ja",
        "ja",
        "simple",
        "ja-ask",
        "確認対象のURLが書かれていないので、対象URLを質問してください",
        "clarify",
        ("uncertainty", "condition"),
    ),
    ContrastPrompt(
        "clarify_verify",
        "cv-url-ja",
        "ja",
        "simple",
        "ja-check",
        "提示されたURLが正しいページを指しているか確認してください",
        "verify",
        ("verification",),
    ),
    ContrastPrompt(
        "clarify_verify",
        "cv-number-ja",
        "ja",
        "simple",
        "ja-ask",
        "計算に必要な数値が不足しているため、足りない値を尋ねてください",
        "clarify",
        ("condition", "uncertainty"),
    ),
    ContrastPrompt(
        "clarify_verify",
        "cv-number-ja",
        "ja",
        "simple",
        "ja-check",
        "与えられた数値を使って計算結果が合っているか検算してください",
        "verify",
        ("calculation", "verification"),
    ),
    ContrastPrompt(
        "clarify_verify",
        "cv-format-ja",
        "ja",
        "compound",
        "ja-ask",
        "希望する出力形式が不明なので、形式と用途を質問してください",
        "clarify",
        ("condition", "uncertainty"),
    ),
    ContrastPrompt(
        "clarify_verify",
        "cv-format-ja",
        "ja",
        "compound",
        "ja-check",
        "出力が指定された形式と用途の条件を満たすか検証してください",
        "verify",
        ("verification", "condition"),
    ),
    ContrastPrompt(
        "clarify_verify",
        "cv-environment-ja",
        "ja",
        "compound",
        "ja-ask",
        "実行環境が分からないので、OSと利用バージョンを質問してください",
        "clarify",
        ("uncertainty", "condition"),
    ),
    ContrastPrompt(
        "clarify_verify",
        "cv-environment-ja",
        "ja",
        "compound",
        "ja-check",
        "示されたOSとバージョンでこの実装が動作するか確認してください",
        "verify",
        ("verification", "condition"),
    ),
    ContrastPrompt(
        "clarify_verify",
        "cv-target-en",
        "en",
        "simple",
        "en-ask",
        "The target is missing, so ask which artifact should be checked.",
        "clarify",
        ("uncertainty",),
    ),
    ContrastPrompt(
        "clarify_verify",
        "cv-target-en",
        "en",
        "simple",
        "en-check",
        "Check whether the specified artifact satisfies the stated requirement.",
        "verify",
        ("verification", "condition"),
    ),
    ContrastPrompt(
        "clarify_verify",
        "cv-assumption-en",
        "en",
        "compound",
        "en-neg-ask",
        "Do not assume the missing premise; ask the user to provide it.",
        "clarify",
        ("uncertainty", "condition"),
    ),
    ContrastPrompt(
        "clarify_verify",
        "cv-assumption-en",
        "en",
        "compound",
        "en-check",
        "Confirm whether the provided premise is supported by the evidence.",
        "verify",
        ("verification",),
    ),
    ContrastPrompt(
        "clarify_verify",
        "cv-report-ja",
        "ja",
        "compound",
        "ja-neg-check",
        "報告された集計値を鵜呑みにせず、元データと突き合わせて検算してください",
        "verify",
        ("verification", "calculation"),
    ),
    ContrastPrompt(
        "clarify_verify",
        "cv-report-ja",
        "ja",
        "compound",
        "ja-ask",
        "検算に使う元データの場所が示されていないので、どこにあるか質問してください",
        "clarify",
        ("condition", "uncertainty"),
    ),
    # explore vs build
    ContrastPrompt(
        "explore_build",
        "eb-storage-ja",
        "ja",
        "simple",
        "ja-enum",
        "保存方式を決める前に、性質の異なる候補を比較してください",
        "explore",
        ("comparison",),
    ),
    ContrastPrompt(
        "explore_build",
        "eb-storage-ja",
        "ja",
        "simple",
        "ja-steps",
        "採用した保存方式を組み込むための実装手順を作ってください",
        "build",
        ("sequence", "decomposition"),
    ),
    ContrastPrompt(
        "explore_build",
        "eb-ui-ja",
        "ja",
        "simple",
        "ja-neg-enum",
        "画面構成を固定せず、異なるレイアウト案を複数考えてください",
        "explore",
        ("comparison",),
    ),
    ContrastPrompt(
        "explore_build",
        "eb-ui-ja",
        "ja",
        "simple",
        "ja-steps",
        "選択済みのレイアウトを実装するコンポーネント構成を作ってください",
        "build",
        ("decomposition",),
    ),
    ContrastPrompt(
        "explore_build",
        "eb-api-ja",
        "ja",
        "compound",
        "ja-enum",
        "APIの設計候補を広げ、各案の利点と不確実性を挙げてください",
        "explore",
        ("comparison", "uncertainty"),
    ),
    ContrastPrompt(
        "explore_build",
        "eb-api-ja",
        "ja",
        "compound",
        "ja-steps",
        "採用済みAPI案について、endpointごとの実装タスクを作ってください",
        "build",
        ("decomposition", "sequence"),
    ),
    ContrastPrompt(
        "explore_build",
        "eb-failure-ja",
        "ja",
        "compound",
        "ja-neg-enum",
        "障害対策を一つに絞らず、異なる回復戦略を検討してください",
        "explore",
        ("comparison", "uncertainty"),
    ),
    ContrastPrompt(
        "explore_build",
        "eb-failure-ja",
        "ja",
        "compound",
        "ja-steps",
        "採用した回復戦略を実装・検証する作業順を組んでください",
        "build",
        ("sequence", "verification"),
    ),
    ContrastPrompt(
        "explore_build",
        "eb-architecture-en",
        "en",
        "simple",
        "en-neg-enum",
        "Compare several architecture options without committing to one.",
        "explore",
        ("comparison",),
    ),
    ContrastPrompt(
        "explore_build",
        "eb-architecture-en",
        "en",
        "simple",
        "en-steps",
        "Break the chosen architecture into concrete implementation tasks.",
        "build",
        ("decomposition", "sequence"),
    ),
    ContrastPrompt(
        "explore_build",
        "eb-experiment-en",
        "en",
        "compound",
        "en-enum",
        "Generate competing hypotheses and possible ways to investigate them.",
        "explore",
        ("comparison", "uncertainty"),
    ),
    ContrastPrompt(
        "explore_build",
        "eb-experiment-en",
        "en",
        "compound",
        "en-steps",
        "Turn the selected hypothesis into an ordered experiment plan.",
        "build",
        ("sequence", "verification"),
    ),
)


def curriculum_document() -> SourceDocument:
    return SourceDocument(
        source_kind="curriculum",
        title="Original route boundary contrast curriculum v2 round 1",
        url=CURRICULUM_URL,
        revision_id=CURRICULUM_REVISION,
        fetched_at=datetime.now(timezone.utc).isoformat(),
        license_name="project-original-synthetic",
        attribution="Thought State Register project",
        text="",
        metadata={
            "authoring_method": AUTHORING_METHOD,
            "authoring_models": dict(AUTHORING_MODELS),
            "ai_assisted_authoring": True,
            "teacher_model_outputs_used": False,
            "copied_source_text_used": False,
            "hidden_reasoning_used": False,
            "approval_required": True,
            "revision_note": (
                "revision 2 removes the negation/respond label confound "
                "found in external review; revision 1 archived under "
                "archive/2026-06-11_pre-round1-review/"
            ),
            "boundaries": sorted(
                {pattern.boundary for pattern in BOUNDARY_CURRICULUM_V2}
            ),
            "contrast_group_field": "contrast_group",
            "template_id_field": "template_id",
        },
    )


def curriculum_drafts() -> List[PatternDraft]:
    drafts: List[PatternDraft] = []
    for pattern in BOUNDARY_CURRICULUM_V2:
        if pattern.route not in ROUTES:
            raise ValueError(f"unknown route: {pattern.route}")
        unknown = sorted(set(pattern.operators) - set(OPERATORS))
        if unknown:
            raise ValueError(f"unknown operators: {', '.join(unknown)}")
        drafts.append(
            PatternDraft(
                input_text=pattern.text,
                suggested_route=pattern.route,
                suggested_operators=list(pattern.operators),
                thought_form={
                    "facts": [pattern.text],
                    "goals": [f"distinguish {pattern.boundary}"],
                    "constraints": [
                        "route intent only",
                        "human approval required",
                    ],
                    "uncertainty": [],
                    "operation": pattern.operators[0],
                    "candidates": [],
                    "boundary": pattern.boundary,
                    "contrast_group": pattern.contrast_group,
                    "language": pattern.language,
                    "difficulty": pattern.difficulty,
                    "template_id": pattern.template_id,
                    "curriculum_revision": CURRICULUM_REVISION,
                    "authoring_method": AUTHORING_METHOD,
                    "ai_assisted_authoring": True,
                    "teacher_output_used": False,
                    "copied_source_text_used": False,
                },
                confidence=0.9,
            )
        )
    return drafts

"""Round 1b: reinforcement for two regression-contract boundary collisions.

After training on Round 1 (218 patterns), the deployed-candidate model
missed two frozen regression anchors that are NOT in the training data:

- 「何を求める問題か確認してください」 expected clarify, predicted verify
  (the new cv-* verify examples strengthened 「確認」→verify)
- 「別の角度から解いてみてください」 expected explore, predicted respond
  (recovered only at epochs=48)

These prompts are near-paraphrase reinforcements of those two collisions,
teaching the asking-sense of 「確認」 (clarify) versus the checking-sense
(verify), and solving-method enumeration (explore) versus direct solving
(respond). They intentionally sit close to two frozen fixture anchors; the
fixture therefore remains a regression contract, not generalization
evidence (as already documented). Seeding creates pending candidates only.
"""

from datetime import datetime, timezone
from typing import List, Tuple

from .boundary_curriculum_v2 import ContrastPrompt
from .models import OPERATORS, ROUTES, PatternDraft, SourceDocument


CURRICULUM_URL = "curriculum://route-boundaries-v2-round1b"
CURRICULUM_REVISION = "1"
AUTHORING_METHOD = "specification-derived-synthetic"
AUTHORING_MODELS = {"round1b_draft": "claude-fable-5"}


BOUNDARY_REINFORCEMENT_R1B: Tuple[ContrastPrompt, ...] = (
    ContrastPrompt(
        "clarify_verify",
        "cr-goal-ja",
        "ja",
        "simple",
        "ja-ask",
        "この問題が何を求めているのか分からないので、確認の質問をしてください",
        "clarify",
        ("uncertainty", "condition"),
    ),
    ContrastPrompt(
        "clarify_verify",
        "cr-goal-ja",
        "ja",
        "simple",
        "ja-check",
        "解答が問題の要求を満たしているか確認してください",
        "verify",
        ("verification",),
    ),
    ContrastPrompt(
        "clarify_verify",
        "cr-value-ja",
        "ja",
        "compound",
        "ja-ask",
        "どの値を答えればよいか不明なので、先に質問して確認してください",
        "clarify",
        ("condition", "uncertainty"),
    ),
    ContrastPrompt(
        "clarify_verify",
        "cr-value-ja",
        "ja",
        "compound",
        "ja-check",
        "求めた値が与えられた条件をすべて満たすか順番に確認してください",
        "verify",
        ("verification", "condition"),
    ),
    ContrastPrompt(
        "explore_respond",
        "ra-angle-ja",
        "ja",
        "simple",
        "ja-enum",
        "違う角度からこの問題の解き方をいくつか考えてください",
        "explore",
        ("comparison",),
    ),
    ContrastPrompt(
        "explore_respond",
        "ra-angle-ja",
        "ja",
        "simple",
        "ja-answer",
        "いま示した解き方のまま、最後まで解いてください",
        "respond",
        ("calculation", "sequence"),
    ),
    ContrastPrompt(
        "explore_respond",
        "ra-method-ja",
        "ja",
        "simple",
        "ja-neg-enum",
        "一つの解法に決めず、別の視点からの解き方も挙げてください",
        "explore",
        ("comparison",),
    ),
    ContrastPrompt(
        "explore_respond",
        "ra-method-ja",
        "ja",
        "simple",
        "ja-answer",
        "この解き方で得られる答えを教えてください",
        "respond",
        ("calculation",),
    ),
)


def curriculum_document() -> SourceDocument:
    return SourceDocument(
        source_kind="curriculum",
        title="Route boundary reinforcement round 1b",
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
            "purpose": (
                "near-paraphrase reinforcement of two frozen regression "
                "anchors missed after Round 1 training"
            ),
            "related_fixture_cases": ["clarify_target", "explore_other_angle"],
            "contrast_group_field": "contrast_group",
            "template_id_field": "template_id",
        },
    )


def curriculum_drafts() -> List[PatternDraft]:
    drafts: List[PatternDraft] = []
    for pattern in BOUNDARY_REINFORCEMENT_R1B:
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

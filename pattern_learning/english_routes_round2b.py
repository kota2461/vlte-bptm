"""English Round 2b: targets the three miss patterns left after round 2.

Recorded misses on the unseen battery (2026-06-12): check-without-"verify"
phrasings fell to respond, "short summary" fell to clarify, and
"other ways to solve" fell to respond. These eight prompts teach those
phrasing families with fresh sentences (battery and sealed-slice texts are
NOT copied). Seeding creates pending candidates only.
"""

from datetime import datetime, timezone
from typing import List, Tuple

from .models import OPERATORS, ROUTES, PatternDraft, SourceDocument


CURRICULUM_URL = "curriculum://english-nonrespond-round2b"
CURRICULUM_REVISION = "1"
AUTHORING_METHOD = "specification-derived-synthetic"
AUTHORING_MODELS = {"round2b_draft": "claude-fable-5"}

# (template_id, text, route, operators)
ENGLISH_ROUTES_ROUND2B: Tuple[Tuple[str, str, str, Tuple[str, ...]], ...] = (
    (
        "en-check",
        "Check that this answer matches the expected result.",
        "verify",
        ("verification",),
    ),
    (
        "en-check",
        "Can you confirm these figures are accurate?",
        "verify",
        ("verification", "calculation"),
    ),
    (
        "en-check",
        "Make sure the configuration meets the security policy.",
        "verify",
        ("verification", "condition"),
    ),
    (
        "en-enum",
        "Are there different approaches we could try here?",
        "explore",
        ("comparison",),
    ),
    (
        "en-enum",
        "Offer a few alternative ways to handle this case.",
        "explore",
        ("comparison",),
    ),
    (
        "en-enum",
        "Brainstorm other options for reducing the load time.",
        "explore",
        ("comparison", "uncertainty"),
    ),
    (
        "en-sum",
        "Boil this long thread down to the key points.",
        "summarize",
        ("decomposition",),
    ),
    (
        "en-sum",
        "Recap the meeting in a couple of lines.",
        "summarize",
        ("decomposition",),
    ),
)


def curriculum_document() -> SourceDocument:
    return SourceDocument(
        source_kind="curriculum",
        title="English non-respond reinforcement round 2b",
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
                "fix recorded english miss families: check-without-verify, "
                "short-summary, other-ways-to-solve"
            ),
            "template_id_field": "template_id",
        },
    )


def curriculum_drafts() -> List[PatternDraft]:
    drafts: List[PatternDraft] = []
    for template_id, text, route, operators in ENGLISH_ROUTES_ROUND2B:
        if route not in ROUTES:
            raise ValueError(f"unknown route: {route}")
        unknown = sorted(set(operators) - set(OPERATORS))
        if unknown:
            raise ValueError(f"unknown operators: {', '.join(unknown)}")
        drafts.append(
            PatternDraft(
                input_text=text,
                suggested_route=route,
                suggested_operators=list(operators),
                thought_form={
                    "facts": [text],
                    "goals": ["english non-respond recall"],
                    "constraints": [
                        "route intent only",
                        "human approval required",
                    ],
                    "uncertainty": [],
                    "operation": operators[0],
                    "candidates": [],
                    "language": "en",
                    "template_id": template_id,
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

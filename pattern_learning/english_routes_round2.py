"""Round 2 (partial): English non-respond reinforcement.

The weakest measured slice is English non-respond routing (untrained
boundary eval: English 4/16, predictions collapsed to respond 14/16;
approved English non-respond examples were ~7). These ten natural-phrasing
prompts target verify / build / clarify / summarize in English, with no
negation meta-instructions (avoiding the revision-1 confound). Seeding
creates pending candidates only; approval and training stay human actions.
"""

from datetime import datetime, timezone
from typing import List, Tuple

from .models import OPERATORS, ROUTES, PatternDraft, SourceDocument


CURRICULUM_URL = "curriculum://english-nonrespond-round2"
CURRICULUM_REVISION = "1"
AUTHORING_METHOD = "specification-derived-synthetic"
AUTHORING_MODELS = {"round2_english_draft": "claude-fable-5"}

# (template_id, text, route, operators)
ENGLISH_ROUTES_ROUND2: Tuple[Tuple[str, str, str, Tuple[str, ...]], ...] = (
    (
        "en-check",
        "Check whether this calculation is correct: 12 x 8 = 86.",
        "verify",
        ("verification", "calculation"),
    ),
    (
        "en-review",
        "Review this proof and point out any logical gaps.",
        "verify",
        ("verification",),
    ),
    (
        "en-check",
        "Does this code change satisfy the stated requirements? Please verify.",
        "verify",
        ("verification", "condition"),
    ),
    (
        "en-steps",
        "Create a step-by-step study plan for learning basic algebra.",
        "build",
        ("sequence", "decomposition"),
    ),
    (
        "en-steps",
        "Draft an ordered checklist for releasing the new feature.",
        "build",
        ("sequence", "verification"),
    ),
    (
        "en-steps",
        "Organize these tasks into an implementation schedule.",
        "build",
        ("sequence", "decomposition"),
    ),
    (
        "en-ask",
        "The deadline is not mentioned anywhere, so please ask me for it.",
        "clarify",
        ("condition", "uncertainty"),
    ),
    (
        "en-ask",
        "If any requirement seems ambiguous, ask me before answering.",
        "clarify",
        ("uncertainty", "condition"),
    ),
    (
        "en-sum",
        "Summarize this meeting note in two sentences.",
        "summarize",
        ("decomposition",),
    ),
    (
        "en-sum",
        "Give me a brief summary of the main argument of this article.",
        "summarize",
        ("decomposition",),
    ),
)


def curriculum_document() -> SourceDocument:
    return SourceDocument(
        source_kind="curriculum",
        title="English non-respond reinforcement round 2",
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
                "English non-respond recall (weakest measured slice); "
                "no negation meta-instructions"
            ),
            "template_id_field": "template_id",
        },
    )


def curriculum_drafts() -> List[PatternDraft]:
    drafts: List[PatternDraft] = []
    for template_id, text, route, operators in ENGLISH_ROUTES_ROUND2:
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

"""Round 2 user-supplied boundary batch (5 contrast groups, 10 prompts).

Supplied by the project owner on 2026-06-12; the authoring model/source is
unrecorded ("貰って来た" batch), so provenance is marked user-supplied-
external and the usual integrity booleans are not asserted. The prompts
deliberately avoid explicit route words. Contrast groups must never be
split across train/validation. Seeding creates pending candidates only.

A sealed mirror of these boundaries was frozen FIRST
(tests/fixtures/sealed_boundary_slice_v1.json) and these 10 prompts are
never reused for accuracy measurement after approval.
"""

from datetime import datetime, timezone
from typing import List

from .boundary_curriculum_v2 import ContrastPrompt
from .models import OPERATORS, ROUTES, PatternDraft, SourceDocument


CURRICULUM_URL = "curriculum://route-boundaries-round2-user"
CURRICULUM_REVISION = "1"


BOUNDARY_ROUND2_USER = (
    ContrastPrompt(
        "build_respond",
        "br-work-ja",
        "ja",
        "compound",
        "ja-breakdown",
        "方針は決まりました。担当者が着手できる作業順と完了条件に落とし込んでください。",
        "build",
        ("decomposition", "sequence"),
    ),
    ContrastPrompt(
        "build_respond",
        "br-work-ja",
        "ja",
        "compound",
        "ja-explain",
        "この方針によって何が解決されるのか、要点を説明してください。",
        "respond",
        ("causal_relation",),
    ),
    ContrastPrompt(
        "clarify_verify",
        "cv-budget-ja",
        "ja",
        "compound",
        "ja-missing-implicit",
        "必要な予算を見積もってください。利用人数と期間はまだ伝えていません。",
        "clarify",
        ("uncertainty", "condition"),
    ),
    ContrastPrompt(
        "clarify_verify",
        "cv-budget-ja",
        "ja",
        "compound",
        "ja-check",
        "利用人数は50人、期間は6か月です。提示された予算内に収まるか確認してください。",
        "verify",
        ("verification", "calculation"),
    ),
    ContrastPrompt(
        "build_respond",
        "br-storage-en",
        "en",
        "simple",
        "en-breakdown",
        "The storage method has been selected. Break the remaining work into implementable tasks.",
        "build",
        ("decomposition", "sequence"),
    ),
    ContrastPrompt(
        "build_respond",
        "br-storage-en",
        "en",
        "simple",
        "en-explain",
        "Explain the main benefit of the selected storage method.",
        "respond",
        ("causal_relation",),
    ),
    ContrastPrompt(
        "clarify_verify",
        "cv-runtime-en",
        "en",
        "compound",
        "en-missing-implicit",
        "Estimate the runtime, but the input size and hardware have not been provided.",
        "clarify",
        ("uncertainty", "condition"),
    ),
    ContrastPrompt(
        "clarify_verify",
        "cv-runtime-en",
        "en",
        "compound",
        "en-check",
        "The input size and hardware are provided. Check whether the claimed runtime is plausible.",
        "verify",
        ("verification", "condition"),
    ),
    ContrastPrompt(
        "explore_build",
        "eb-recovery-ja",
        "ja",
        "compound",
        "ja-enum-implicit",
        "障害時の復旧方法を決める前に、異なる選択肢とそれぞれの弱点を整理してください。",
        "explore",
        ("comparison", "uncertainty"),
    ),
    ContrastPrompt(
        "explore_build",
        "eb-recovery-ja",
        "ja",
        "compound",
        "ja-steps",
        "復旧方法は決まりました。実装、動作確認、切り戻しまでの手順を作ってください。",
        "build",
        ("sequence", "verification"),
    ),
)


def curriculum_document() -> SourceDocument:
    return SourceDocument(
        source_kind="curriculum",
        title="Route boundary round 2 user-supplied batch",
        url=CURRICULUM_URL,
        revision_id=CURRICULUM_REVISION,
        fetched_at=datetime.now(timezone.utc).isoformat(),
        license_name="user-provided",
        attribution="Project owner (external batch)",
        text="",
        metadata={
            "provenance": "user-supplied-external",
            "authoring_models": {
                "round2_user_batch": "unrecorded (user-supplied)"
            },
            "approval_required": True,
            "sealed_mirror": "sealed_boundary_slice_v1.json (frozen first)",
            "not_reused_for_measurement": True,
            "contrast_group_field": "contrast_group",
            "template_id_field": "template_id",
        },
    )


def curriculum_drafts() -> List[PatternDraft]:
    drafts: List[PatternDraft] = []
    for pattern in BOUNDARY_ROUND2_USER:
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
                    "provenance": "user-supplied-external",
                },
                confidence=0.9,
            )
        )
    return drafts

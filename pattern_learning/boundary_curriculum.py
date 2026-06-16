"""Curated route-boundary contrasts for explicit human-reviewed training.

These examples target intent pairs that a character n-gram router commonly
confuses. Seeding only creates pending candidates; approval and training are
separate explicit operations.
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import List, Tuple

from .models import OPERATORS, ROUTES, PatternDraft, SourceDocument


CURRICULUM_URL = "curriculum://route-boundaries-v1"
CURRICULUM_REVISION = "1"


@dataclass(frozen=True)
class BoundaryPattern:
    boundary: str
    text: str
    route: str
    operators: Tuple[str, ...]
    rating: int = 5


BOUNDARY_CURRICULUM: Tuple[BoundaryPattern, ...] = (
    # explore vs respond: generating alternatives is different from answering.
    BoundaryPattern(
        "explore_respond",
        "選択肢を一つに決めず、別案を何通りか提案してください",
        "explore",
        ("comparison",),
    ),
    BoundaryPattern(
        "explore_respond",
        "同じ結論へ至る異なる手順を複数考えてください",
        "explore",
        ("comparison", "sequence"),
    ),
    BoundaryPattern(
        "explore_respond",
        "ほかに利用できる方法の候補を広く挙げてください",
        "explore",
        ("comparison",),
    ),
    BoundaryPattern(
        "explore_respond",
        "一つの答えに絞る前に代替アプローチを比較してください",
        "explore",
        ("comparison",),
    ),
    BoundaryPattern(
        "explore_respond",
        "この表現を言い換える案を三つ考えてください",
        "explore",
        ("comparison", "equivalence"),
    ),
    BoundaryPattern(
        "explore_respond",
        "別方向の解決策も含めてアイデアを出してください",
        "explore",
        ("comparison",),
    ),
    BoundaryPattern(
        "explore_respond",
        "別の観点から取り組む方法も考えてください",
        "explore",
        ("comparison",),
    ),
    BoundaryPattern(
        "explore_respond",
        "同じ意味を表す別表現の候補を提案してください",
        "explore",
        ("comparison", "equivalence"),
    ),
    BoundaryPattern(
        "explore_respond",
        "指定された計算の答えを一つ求めてください",
        "respond",
        ("calculation",),
    ),
    BoundaryPattern(
        "explore_respond",
        "この用語の意味をそのまま説明してください",
        "respond",
        ("definition",),
    ),
    BoundaryPattern(
        "explore_respond",
        "与えられた方法で問題を解いて答えてください",
        "respond",
        ("calculation", "sequence"),
    ),
    # clarify vs verify: requesting missing information is not validation.
    BoundaryPattern(
        "clarify_verify",
        "依頼の目的が読み取れない場合は、何を望むか質問してください",
        "clarify",
        ("uncertainty", "condition"),
    ),
    BoundaryPattern(
        "clarify_verify",
        "必要な数値が不足しているときは、不足項目を尋ねてください",
        "clarify",
        ("condition", "uncertainty"),
    ),
    BoundaryPattern(
        "clarify_verify",
        "どの対象を指すか不明なら、対象を特定する質問をしてください",
        "clarify",
        ("uncertainty",),
    ),
    BoundaryPattern(
        "clarify_verify",
        "出力形式が指定されていないので、希望する形式を聞いてください",
        "clarify",
        ("condition",),
    ),
    BoundaryPattern(
        "clarify_verify",
        "前提が曖昧な場合は、作業前に条件を問い返してください",
        "clarify",
        ("uncertainty", "condition"),
    ),
    BoundaryPattern(
        "clarify_verify",
        "問題で求める対象が分からないときは、対象を質問してください",
        "clarify",
        ("uncertainty",),
    ),
    BoundaryPattern(
        "clarify_verify",
        "問いのゴールが示されていない場合は、確認の質問をしてください",
        "clarify",
        ("uncertainty", "condition"),
    ),
    BoundaryPattern(
        "clarify_verify",
        "計算結果と与えられた条件が一致するか検算してください",
        "verify",
        ("verification", "calculation"),
    ),
    BoundaryPattern(
        "clarify_verify",
        "説明の根拠に誤りがないか確認してください",
        "verify",
        ("verification",),
    ),
    BoundaryPattern(
        "clarify_verify",
        "実装が要件を満たすかテストしてください",
        "verify",
        ("verification",),
    ),
    BoundaryPattern(
        "clarify_verify",
        "前提条件が実際に成立しているか検証してください",
        "verify",
        ("verification", "condition"),
    ),
    # explore vs build: broadening options is different from committing a plan.
    BoundaryPattern(
        "explore_build",
        "採用する方法が決まったので実行手順を組み立ててください",
        "build",
        ("sequence",),
    ),
    BoundaryPattern(
        "explore_build",
        "選んだ案をコードにするための実装計画を作ってください",
        "build",
        ("decomposition", "sequence"),
    ),
)


def curriculum_document() -> SourceDocument:
    return SourceDocument(
        source_kind="curriculum",
        title="Route boundary contrast curriculum v1",
        url=CURRICULUM_URL,
        revision_id=CURRICULUM_REVISION,
        fetched_at=datetime.now(timezone.utc).isoformat(),
        license_name="project-curriculum",
        attribution="Thought State Register",
        text="",
        metadata={
            "boundaries": sorted(
                {pattern.boundary for pattern in BOUNDARY_CURRICULUM}
            )
        },
    )


def curriculum_drafts() -> List[PatternDraft]:
    drafts: List[PatternDraft] = []
    for pattern in BOUNDARY_CURRICULUM:
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
                    "constraints": [],
                    "uncertainty": [],
                    "operation": pattern.operators[0],
                    "candidates": [],
                    "boundary": pattern.boundary,
                },
                confidence=0.95,
            )
        )
    return drafts

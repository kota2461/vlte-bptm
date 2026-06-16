from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


ROUTES = (
    "respond",
    "clarify",
    "build",
    "verify",
    "summarize",
    "explore",
)

OPERATORS = (
    "definition",
    "equivalence",
    "comparison",
    "condition",
    "causal_relation",
    "sequence",
    "decomposition",
    "uncertainty",
    "calculation",
    "verification",
)


@dataclass(frozen=True)
class SourceDocument:
    source_kind: str
    title: str
    url: str
    revision_id: str
    fetched_at: str
    license_name: str
    attribution: str
    text: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class PatternDraft:
    input_text: str
    suggested_route: str
    suggested_operators: List[str]
    thought_form: Dict[str, Any]
    confidence: float


@dataclass(frozen=True)
class ReviewDecision:
    candidate_id: int
    verdict: str
    rating: int
    route: Optional[str] = None
    operators: Optional[List[str]] = None
    thought_form: Optional[Dict[str, Any]] = None
    notes: str = ""

    def validate(self) -> None:
        if self.verdict not in {"approve", "reject"}:
            raise ValueError("verdict must be approve or reject")
        if not 1 <= self.rating <= 5:
            raise ValueError("rating must be between 1 and 5")
        if self.route is not None and self.route not in ROUTES:
            raise ValueError(f"unknown route: {self.route}")
        if self.operators is not None:
            unknown = sorted(set(self.operators) - set(OPERATORS))
            if unknown:
                raise ValueError(
                    f"unknown operators: {', '.join(unknown)}"
                )

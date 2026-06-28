"""Knowledge index and retrieval-packet contracts.

The knowledge index is a lightweight table of contents for the router. It does
not contain answer text. It only tells the router which knowledge library should
be consulted and whether the lookup carries current-information or risk flags.
"""

import json
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, Mapping


KNOWLEDGE_INDEX_SCHEMA_VERSION = "knowledge-index.v1"
RETRIEVAL_PACKET_SCHEMA_VERSION = "retrieval-packet.v1"

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_KNOWLEDGE_INDEX_PATH = ROOT / "data" / "knowledge_index_v1.json"

RISK_ORDER = {"low": 0, "medium": 1, "high": 2, "critical": 3}
ROUTES = {"respond", "explain", "clarify", "build", "verify", "summarize", "explore"}

# Sentence boundary used to scope negation/meta-context checks to the clause
# that actually contains the hook. Deliberately excludes a bare "." so that
# version-style hooks ("Apache 2.0", "GPT-4.5") don't get truncated mid-token.
_SENTENCE_BOUNDARY_PATTERN = re.compile(r"[。！？\n!?]+")

# A hook match inside a negated clause ("...と決めつけない理由を...",
# "...is not a dependency risk...") describes the *absence* of the
# domain's risk premise rather than an instance of it.
_NEGATION_MARKERS = (
    "ではない",
    "じゃない",
    "わけではない",
    "とは言えない",
    "とは限らない",
    "ありません",
    "ません",
    "ない",
    "not a ",
    "not an ",
    "isn't",
    "is not",
    "doesn't",
    "does not",
    "n't ",
)

# A hook match inside a definitional or comparative/meta question
# ("Apache 2.0の一般的な意味", "画面設計と...の違いを説明") is a request to
# explain the term itself, not an actionable instance of the guarded
# scenario, so it shouldn't carry the same risk/current-info weight.
_META_CONTEXT_MARKERS = (
    "一般的な",
    "の意味",
    "とは",
    "の違いを",
    "の違いは",
    "general meaning",
    "general information",
    "what is",
    "the difference between",
)


def _hook_local_context(haystack: str, hook_cf: str) -> str:
    """Return the sentence/clause of `haystack` that contains `hook_cf`.

    Scoping the negation/meta-context check to the local sentence (rather
    than the whole text) avoids an unrelated clause elsewhere in a longer
    message accidentally softening or failing to soften a match.
    """

    idx = haystack.find(hook_cf)
    if idx == -1:
        return haystack
    start = 0
    for boundary in _SENTENCE_BOUNDARY_PATTERN.finditer(haystack, 0, idx):
        start = boundary.end()
    end_boundary = _SENTENCE_BOUNDARY_PATTERN.search(haystack, idx)
    end = end_boundary.start() if end_boundary else len(haystack)
    return haystack[start:end]


def _is_softened_match(haystack: str, hook_cf: str) -> bool:
    context = _hook_local_context(haystack, hook_cf)
    return any(marker in context for marker in _NEGATION_MARKERS) or any(
        marker in context for marker in _META_CONTEXT_MARKERS
    )


def _strict_object(value: Any, field: str, required: tuple[str, ...]) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{field} must be an object")
    actual = set(value)
    expected = set(required)
    missing = sorted(expected - actual)
    unknown = sorted(actual - expected)
    if missing:
        raise ValueError(f"{field} is missing field: {missing[0]}")
    if unknown:
        raise ValueError(f"{field} has unknown field: {unknown[0]}")
    return value


def _non_empty_string(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty string")
    return value


def _string_list(value: Any, field: str) -> tuple[str, ...]:
    if not isinstance(value, list):
        raise ValueError(f"{field} must be an array")
    items = tuple(_non_empty_string(item, field) for item in value)
    if len(set(item.casefold() for item in items)) != len(items):
        raise ValueError(f"{field} must contain unique values")
    return items


@dataclass(frozen=True)
class KnowledgeIndexEntry:
    domain: str
    hooks: tuple[str, ...]
    library: str
    default_route: str
    requires_current_information: bool
    risk: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "domain": self.domain,
            "hooks": list(self.hooks),
            "library": self.library,
            "default_route": self.default_route,
            "requires_current_information": self.requires_current_information,
            "risk": self.risk,
        }


@dataclass(frozen=True)
class KnowledgeIndex:
    entries: tuple[KnowledgeIndexEntry, ...]

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema_version": KNOWLEDGE_INDEX_SCHEMA_VERSION,
            "entries": [entry.as_dict() for entry in self.entries],
        }


@dataclass(frozen=True)
class RetrievalMatch:
    domain: str
    hook: str
    library: str
    default_route: str
    requires_current_information: bool
    risk: str
    score: float

    def as_dict(self) -> dict[str, Any]:
        return {
            "domain": self.domain,
            "hook": self.hook,
            "library": self.library,
            "default_route": self.default_route,
            "requires_current_information": self.requires_current_information,
            "risk": self.risk,
            "score": self.score,
        }


@dataclass(frozen=True)
class RetrievalPacket:
    needed: bool
    domains: tuple[str, ...]
    hooks: tuple[str, ...]
    libraries: tuple[str, ...]
    current_check: bool
    risk: str
    matches: tuple[RetrievalMatch, ...]

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema_version": RETRIEVAL_PACKET_SCHEMA_VERSION,
            "needed": self.needed,
            "domains": list(self.domains),
            "hooks": list(self.hooks),
            "libraries": list(self.libraries),
            "current_check": self.current_check,
            "risk": self.risk,
            "matches": [match.as_dict() for match in self.matches],
        }


def parse_knowledge_index(value: Any) -> KnowledgeIndex:
    payload = _strict_object(value, "knowledge index", ("schema_version", "entries"))
    if payload["schema_version"] != KNOWLEDGE_INDEX_SCHEMA_VERSION:
        raise ValueError("unsupported knowledge index schema")
    if not isinstance(payload["entries"], list):
        raise ValueError("entries must be an array")
    entries = []
    domains = set()
    for index, item in enumerate(payload["entries"]):
        entry = _strict_object(
            item,
            f"entries[{index}]",
            (
                "domain",
                "hooks",
                "library",
                "default_route",
                "requires_current_information",
                "risk",
            ),
        )
        domain = _non_empty_string(entry["domain"], f"entries[{index}].domain")
        if domain in domains:
            raise ValueError(f"duplicate domain: {domain}")
        domains.add(domain)
        default_route = _non_empty_string(entry["default_route"], f"entries[{index}].default_route")
        if default_route not in ROUTES:
            raise ValueError(f"unknown default route: {default_route}")
        risk = _non_empty_string(entry["risk"], f"entries[{index}].risk")
        if risk not in RISK_ORDER:
            raise ValueError(f"unknown risk: {risk}")
        current = entry["requires_current_information"]
        if not isinstance(current, bool):
            raise ValueError(f"entries[{index}].requires_current_information must be a boolean")
        entries.append(
            KnowledgeIndexEntry(
                domain=domain,
                hooks=_string_list(entry["hooks"], f"entries[{index}].hooks"),
                library=_non_empty_string(entry["library"], f"entries[{index}].library"),
                default_route=default_route,
                requires_current_information=current,
                risk=risk,
            )
        )
    return KnowledgeIndex(entries=tuple(entries))


@lru_cache(maxsize=8)
def load_knowledge_index(path_str: str = str(DEFAULT_KNOWLEDGE_INDEX_PATH)) -> KnowledgeIndex:
    path = Path(path_str)
    return parse_knowledge_index(json.loads(path.read_text(encoding="utf-8")))


def _best_risk(matches: tuple[RetrievalMatch, ...]) -> str:
    risk = "low"
    for match in matches:
        if RISK_ORDER[match.risk] > RISK_ORDER[risk]:
            risk = match.risk
    return risk


def build_retrieval_packet(
    text: str,
    *,
    index: KnowledgeIndex | None = None,
    index_path: Path = DEFAULT_KNOWLEDGE_INDEX_PATH,
) -> RetrievalPacket:
    if not isinstance(text, str):
        raise TypeError("retrieval text must be a string")
    index = index if index is not None else load_knowledge_index(str(index_path))
    haystack = text.casefold()
    matches: list[RetrievalMatch] = []
    for entry in index.entries:
        matched_hook = None
        for hook in sorted(entry.hooks, key=len, reverse=True):
            if hook.casefold() in haystack:
                matched_hook = hook
                break
        if matched_hook is not None:
            softened = _is_softened_match(haystack, matched_hook.casefold())
            matches.append(
                RetrievalMatch(
                    domain=entry.domain,
                    hook=matched_hook,
                    library=entry.library,
                    default_route=entry.default_route,
                    requires_current_information=(
                        False if softened else entry.requires_current_information
                    ),
                    risk="low" if softened else entry.risk,
                    score=1.0,
                )
            )
    ordered_matches = tuple(matches)
    return RetrievalPacket(
        needed=bool(ordered_matches),
        domains=tuple(dict.fromkeys(match.domain for match in ordered_matches)),
        hooks=tuple(dict.fromkeys(match.hook for match in ordered_matches)),
        libraries=tuple(dict.fromkeys(match.library for match in ordered_matches)),
        current_check=any(match.requires_current_information for match in ordered_matches),
        risk=_best_risk(ordered_matches),
        matches=ordered_matches,
    )


def parse_retrieval_packet(value: Any) -> RetrievalPacket:
    payload = _strict_object(
        value,
        "retrieval packet",
        (
            "schema_version",
            "needed",
            "domains",
            "hooks",
            "libraries",
            "current_check",
            "risk",
            "matches",
        ),
    )
    if payload["schema_version"] != RETRIEVAL_PACKET_SCHEMA_VERSION:
        raise ValueError("unsupported retrieval packet schema")
    if not isinstance(payload["needed"], bool):
        raise ValueError("needed must be a boolean")
    if not isinstance(payload["current_check"], bool):
        raise ValueError("current_check must be a boolean")
    risk = _non_empty_string(payload["risk"], "risk")
    if risk not in RISK_ORDER:
        raise ValueError(f"unknown risk: {risk}")
    matches = []
    if not isinstance(payload["matches"], list):
        raise ValueError("matches must be an array")
    for index, item in enumerate(payload["matches"]):
        match = _strict_object(
            item,
            f"matches[{index}]",
            (
                "domain",
                "hook",
                "library",
                "default_route",
                "requires_current_information",
                "risk",
                "score",
            ),
        )
        score = match["score"]
        if isinstance(score, bool) or not isinstance(score, (int, float)) or score < 0 or score > 1:
            raise ValueError(f"matches[{index}].score must be in [0, 1]")
        match_risk = _non_empty_string(match["risk"], f"matches[{index}].risk")
        if match_risk not in RISK_ORDER:
            raise ValueError(f"unknown match risk: {match_risk}")
        default_route = _non_empty_string(match["default_route"], f"matches[{index}].default_route")
        if default_route not in ROUTES:
            raise ValueError(f"unknown default route: {default_route}")
        current = match["requires_current_information"]
        if not isinstance(current, bool):
            raise ValueError(f"matches[{index}].requires_current_information must be a boolean")
        matches.append(
            RetrievalMatch(
                domain=_non_empty_string(match["domain"], f"matches[{index}].domain"),
                hook=_non_empty_string(match["hook"], f"matches[{index}].hook"),
                library=_non_empty_string(match["library"], f"matches[{index}].library"),
                default_route=default_route,
                requires_current_information=current,
                risk=match_risk,
                score=float(score),
            )
        )
    return RetrievalPacket(
        needed=payload["needed"],
        domains=_string_list(payload["domains"], "domains"),
        hooks=_string_list(payload["hooks"], "hooks"),
        libraries=_string_list(payload["libraries"], "libraries"),
        current_check=payload["current_check"],
        risk=risk,
        matches=tuple(matches),
    )

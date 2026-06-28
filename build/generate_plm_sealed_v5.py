"""Generate the unopened successor PLM sealed fixture v5.

The fixture is authored after the V5 non-sealed replay gate passes. It does
not reuse visible benchmark, legacy sealed, prior PLM sealed, V4 failure
memory, puzzle, or V5 non-sealed challenge texts. It is not evaluated here.
"""

import json
import sqlite3
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Tuple


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from semantic_routing import parse_plm_sealed_fixture  # noqa: E402


OUTPUT = ROOT / "tests" / "fixtures" / "pattern_language_sealed_v5.json"
V1_BENCHMARK = ROOT / "tests" / "fixtures" / "pattern_language_benchmark_v1.json"
LEGACY_SEALED = ROOT / "tests" / "fixtures" / "sealed_boundary_slice_v2.json"
SEALED_V2 = ROOT / "tests" / "fixtures" / "pattern_language_sealed_v2.json"
SEALED_V3 = ROOT / "tests" / "fixtures" / "pattern_language_sealed_v3.json"
SEALED_V4 = ROOT / "tests" / "fixtures" / "pattern_language_sealed_v4.json"
V4_FAILURE_MEMORY = ROOT / "tests" / "fixtures" / "v4_failure_memory_fixture_v1.json"
V4_PUZZLE_SEED = ROOT / "tests" / "fixtures" / "v4_puzzle_task_seed_v1.json"
V4_PUZZLE_FAILURE = ROOT / "tests" / "fixtures" / "v4_puzzle_failure_memory_v1.json"
V5_CHALLENGE = ROOT / "tests" / "fixtures" / "v5_critical_operations_fixture_v1.json"
QUARANTINE = ROOT / "data" / "intent_training_corpus_quarantine_v1.json"
DATABASE = ROOT / "data" / "pattern_lab.db"


@dataclass(frozen=True)
class Spec:
    intent: str
    language: str
    text: str
    evidence: Tuple[Tuple[str, str], ...]
    operations: Tuple[str, ...] = ()
    missing: bool = False
    unverified: bool = False
    current: bool = False
    multiple: bool = False
    response_length: str = "unspecified"
    formats: Tuple[str, ...] = ()
    must: Tuple[str, ...] = ()
    must_not: Tuple[str, ...] = ()
    risk_level: str = "low"
    risk_flags: Tuple[str, ...] = ()


SPECS = (
    Spec(
        "respond",
        "en",
        "What is the usual meaning of a 304 Not Modified response?",
        (("direct_response_request", "What is"),),
    ),
    Spec(
        "respond",
        "en",
        "Give a one-line definition of a debounce function.",
        (("direct_response_request", "Give"), ("short_response", "one-line")),
        response_length="short",
    ),
    Spec(
        "respond",
        "mixed",
        "For code comments, what does TODO typically signal?",
        (("direct_response_request", "what does"),),
    ),
    Spec(
        "respond",
        "en",
        "Name the SQL clause commonly used to group aggregate results.",
        (("direct_response_request", "Name"),),
    ),
    Spec(
        "explain",
        "en",
        "Explain why circuit breakers help services recover under repeated failures.",
        (("explanation_request", "Explain"),),
    ),
    Spec(
        "explain",
        "en",
        "Describe how write-ahead logging protects data during a crash.",
        (("explanation_request", "Describe"),),
    ),
    Spec(
        "explain",
        "en",
        "Walk through why stale caches can return correct-looking but outdated results.",
        (("explanation_request", "Walk through"),),
    ),
    Spec(
        "explain",
        "en",
        "Why can a race condition disappear when debug logging is enabled?",
        (("explanation_request", "Why"),),
    ),
    Spec(
        "clarify",
        "en",
        "Estimate the storage bill, but the retention period is not included.",
        (("missing_information", "not included"),),
        operations=("clarify", "calculate"),
        missing=True,
    ),
    Spec(
        "clarify",
        "en",
        "Before writing the database migration, ask which tenant should be migrated.",
        (("constraint_ask_first", "Before writing"), ("missing_information", "ask which tenant")),
        missing=True,
        must=("ask_first",),
    ),
    Spec(
        "clarify",
        "en",
        "I want a launch announcement, but the target audience is unspecified.",
        (("missing_information", "unspecified"),),
        missing=True,
    ),
    Spec(
        "clarify",
        "en",
        "Calculate the error budget burn rate; the time window is missing.",
        (("missing_information", "missing"),),
        operations=("clarify", "calculate"),
        missing=True,
    ),
    Spec(
        "build",
        "en",
        "Create a migration checklist for moving the cron jobs to workers.",
        (("implementation_request", "Create"),),
    ),
    Spec(
        "build",
        "en",
        "Check the draft rollout assumptions and then write the release plan.",
        (("verification_request", "Check"), ("unverified_claim", "draft"), ("implementation_request", "release plan")),
        operations=("build", "verify"),
        unverified=True,
        multiple=True,
    ),
    Spec(
        "build",
        "en",
        "Turn these support notes into a triage workflow.",
        (("implementation_request", "triage workflow"),),
    ),
    Spec(
        "build",
        "en",
        "Validate the proposed queue design before outlining the worker implementation.",
        (("verification_request", "Validate"), ("unverified_claim", "proposed"), ("implementation_request", "worker implementation")),
        operations=("build", "verify"),
        unverified=True,
        multiple=True,
    ),
    Spec(
        "verify",
        "en",
        "Verify the latest Python patch release with sources before changing the install guide.",
        (("verification_request", "Verify"), ("current_information", "latest"), ("constraint_cite_sources", "with sources")),
        operations=("verify", "search"),
        current=True,
        must=("cite_sources",),
        risk_level="medium",
        risk_flags=("current_information",),
    ),
    Spec(
        "verify",
        "en",
        "Check whether the invoice total matches the subtotal plus tax.",
        (("verification_request", "Check"), ("unverified_claim", "invoice total")),
        operations=("verify", "calculate"),
        unverified=True,
    ),
    Spec(
        "verify",
        "en",
        "Confirm whether this refund clause is valid under current California law.",
        (("verification_request", "Confirm"), ("legal_risk", "refund clause"), ("current_information", "current")),
        operations=("verify", "search"),
        current=True,
        risk_level="high",
        risk_flags=("legal", "current_information"),
    ),
    Spec(
        "verify",
        "en",
        "Validate the suggested antibiotic dose against official guidance before answering.",
        (("verification_request", "Validate"), ("unverified_claim", "suggested"), ("medical_risk", "antibiotic dose")),
        operations=("verify", "search"),
        unverified=True,
        current=True,
        risk_level="high",
        risk_flags=("medical", "current_information", "unverified_claim"),
    ),
    Spec(
        "summarize",
        "en",
        "Summarize the incident timeline in four bullets.",
        (("summary_request", "Summarize"), ("short_response", "four bullets"), ("format_bullets", "bullets")),
        response_length="short",
        formats=("bullets",),
    ),
    Spec(
        "summarize",
        "en",
        "Condense these release notes into JSON.",
        (("summary_request", "Condense"), ("format_json", "JSON")),
        formats=("json",),
    ),
    Spec(
        "summarize",
        "en",
        "Give a neutral summary of the policy disagreement.",
        (("summary_request", "summary"),),
        must=("preserve_neutrality",),
    ),
    Spec(
        "summarize",
        "en",
        "Summarize the interview transcript without making a table.",
        (("summary_request", "Summarize"), ("constraint_no_table", "without making a table")),
        must_not=("no_table",),
    ),
    Spec(
        "explore",
        "en",
        "Brainstorm ways to reduce onboarding friction and compare the trade-offs.",
        (("exploration_request", "Brainstorm"), ("comparison_request", "compare the trade-offs")),
        operations=("explore", "compare"),
        multiple=True,
    ),
    Spec(
        "explore",
        "en",
        "Compare deployment options without claiming there is a single best answer.",
        (("exploration_request", "Compare"), ("comparison_request", "Compare deployment options")),
        operations=("explore", "compare"),
        must=("avoid_overclaim",),
    ),
    Spec(
        "explore",
        "en",
        "List alternative moderation policies and compare their likely downsides.",
        (("exploration_request", "alternative moderation policies"), ("comparison_request", "compare their likely downsides")),
        operations=("explore", "compare"),
        multiple=True,
    ),
    Spec(
        "explore",
        "en",
        "The proposed roadmap is supposedly risk-free; suggest weak points and alternatives.",
        (("unverified_claim", "supposedly"), ("exploration_request", "alternatives")),
        operations=("explore", "compare"),
        unverified=True,
    ),
)


def _evidence(text: str, items: Tuple[Tuple[str, str], ...]) -> list[dict]:
    result = []
    for signal, phrase in items:
        start = text.find(phrase)
        if start < 0:
            raise ValueError(f"evidence phrase not found: {phrase!r}")
        result.append(
            {
                "signal": signal,
                "start": start,
                "end": start + len(phrase),
            }
        )
    return sorted(result, key=lambda item: (item["start"], item["end"], item["signal"]))


def _texts_from_json(path: Path, keys: Iterable[str] = ("input",)) -> set[str]:
    if not path.exists():
        return set()
    payload = json.loads(path.read_text(encoding="utf-8"))
    texts = set()
    for collection_key in ("cases", "tasks", "items", "quarantined_cases"):
        for case in payload.get(collection_key, []):
            for key in keys:
                if key in case:
                    texts.add(str(case[key]))
    return texts


def _approved_texts() -> set[str]:
    if not DATABASE.exists():
        return set()
    uri = DATABASE.resolve().as_uri() + "?mode=ro"
    with sqlite3.connect(uri, uri=True) as connection:
        rows = connection.execute("SELECT input_text FROM patterns").fetchall()
    return {str(row[0]) for row in rows}


def build_payload() -> dict:
    counters: dict[str, int] = {}
    cases = []
    for spec in SPECS:
        counters[spec.intent] = counters.get(spec.intent, 0) + 1
        cases.append(
            {
                "id": f"plm-sealed-v5-{spec.intent}-{counters[spec.intent]:02d}",
                "split": "sealed",
                "source_group": "plm-sealed-v5-authored",
                "contrast_group": None,
                "language": spec.language,
                "input": spec.text,
                "expected": {
                    "primary_intent": spec.intent,
                    "operations": list(spec.operations or (spec.intent,)),
                    "information_state": {
                        "missing_required_information": spec.missing,
                        "contains_unverified_claims": spec.unverified,
                        "requires_current_information": spec.current,
                        "multiple_intents": spec.multiple,
                    },
                    "constraints": {
                        "response_length": spec.response_length,
                        "formats": list(spec.formats),
                        "must": list(spec.must),
                        "must_not": list(spec.must_not),
                    },
                    "risk": {
                        "level": spec.risk_level,
                        "flags": list(spec.risk_flags),
                    },
                    "evidence": _evidence(spec.text, spec.evidence),
                    "unknowns": [],
                    "conflicts": [],
                },
            }
        )

    payload = {
        "schema_version": "pattern-language-sealed.v1",
        "fixture_id": "pattern-language-sealed-v5",
        "frozen_at": "2026-06-23T06:30:00+00:00",
        "predecessor": "pattern_language_sealed_v4.json",
        "authoring_method": (
            "specification-derived successor authored after V5 non-sealed "
            "replay gate; not evaluated, tuned against, or opened in the "
            "review UI"
        ),
        "policy": (
            "sealed measurement only; evaluate once, record the result, then "
            "mark consumed and rotate before any tuning"
        ),
        "cases": cases,
    }
    fixture = parse_plm_sealed_fixture(payload)
    if len(fixture.cases) != 28:
        raise ValueError("sealed v5 must contain exactly 28 cases")
    if set(counters.values()) != {4} or len(counters) != 7:
        raise ValueError("sealed v5 must contain four cases per intent")
    return payload


def validate_no_overlap(payload: dict) -> None:
    new_texts = {case["input"] for case in payload["cases"]}
    if len(new_texts) != len(payload["cases"]):
        raise ValueError("sealed v5 contains duplicate inputs")
    overlap_sources = {
        "PLM benchmark v1": _texts_from_json(V1_BENCHMARK),
        "legacy sealed boundary v2": _texts_from_json(LEGACY_SEALED),
        "PLM sealed v2": _texts_from_json(SEALED_V2),
        "PLM sealed v3": _texts_from_json(SEALED_V3),
        "PLM sealed v4": _texts_from_json(SEALED_V4),
        "V4 failure memory": _texts_from_json(V4_FAILURE_MEMORY),
        "V4 puzzle seed": _texts_from_json(V4_PUZZLE_SEED),
        "V4 puzzle failure memory": _texts_from_json(V4_PUZZLE_FAILURE),
        "V5 non-sealed challenge": _texts_from_json(V5_CHALLENGE),
        "intent corpus quarantine": _texts_from_json(QUARANTINE),
        "approved Pattern DB": _approved_texts(),
    }
    for label, texts in overlap_sources.items():
        overlap = sorted(new_texts & texts)
        if overlap:
            raise ValueError(f"sealed v5 overlaps {label}: {overlap[0]!r}")


def main() -> None:
    payload = build_payload()
    validate_no_overlap(payload)
    OUTPUT.write_text(
        json.dumps(payload, ensure_ascii=False, indent=1) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(f"wrote {OUTPUT.relative_to(ROOT)} with {len(payload['cases'])} cases")


if __name__ == "__main__":
    main()

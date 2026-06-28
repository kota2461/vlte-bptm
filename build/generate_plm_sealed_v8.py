"""Generate the unopened successor PLM sealed fixture v8.

The fixture is authored after the V8 non-sealed replay gate and sealed v8
rotation review pass. It avoids exact text reuse from prior sealed fixtures,
visible benchmarks, adopted/draft non-sealed lanes, and quarantined corpus
material. It is not evaluated here.
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


OUTPUT = ROOT / "tests" / "fixtures" / "pattern_language_sealed_v8.json"
FIXTURES = ROOT / "tests" / "fixtures"
V1_BENCHMARK = FIXTURES / "pattern_language_benchmark_v1.json"
LEGACY_SEALED = FIXTURES / "sealed_boundary_slice_v2.json"
SEALED_FIXTURES = tuple(
    FIXTURES / f"pattern_language_sealed_v{version}.json"
    for version in range(2, 8)
)
NONSEALED_SOURCES = (
    FIXTURES / "v4_failure_memory_fixture_v1.json",
    FIXTURES / "v4_puzzle_task_seed_v1.json",
    FIXTURES / "v4_puzzle_failure_memory_v1.json",
    FIXTURES / "v5_critical_operations_fixture_v1.json",
    FIXTURES / "v6_boundary_false_positive_adopted_benchmark_v1.json",
    FIXTURES / "v6_boundary_priority_review_adopted_benchmark_v1.json",
    FIXTURES / "v6_structural_build_30_adopted_benchmark_v1.json",
    FIXTURES / "v6_router_debate_adopted_benchmark_v1.json",
    FIXTURES / "v6_boundary_false_positive_candidate_benchmark_v1.json",
    FIXTURES / "v6_contrast_negative_benchmark_v1.json",
    FIXTURES / "v6_router_debate_candidate_benchmark_v1.json",
    FIXTURES / "v7_router_repair_fixture_v1.json",
    FIXTURES / "v7_router_debate_candidate_fixture_v1.json",
    FIXTURES / "v8_recovery_priority_review_candidate_benchmark_v1.json",
)
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
        "What does ttl_seconds mean as a column name in a cache table?",
        (("direct_response_request", "What does"), ("metalinguistic_label", "ttl_seconds")),
    ),
    Spec(
        "respond",
        "en",
        "Briefly define Apache 2.0 as a general software license.",
        (("direct_response_request", "define"), ("low_risk_scope", "general software license")),
        response_length="short",
    ),
    Spec(
        "respond",
        "en",
        "In this draft, what does the tag persona_note refer to?",
        (("direct_response_request", "what does"), ("metalinguistic_label", "persona_note")),
    ),
    Spec(
        "respond",
        "en",
        "What is a retry budget in one sentence?",
        (("direct_response_request", "What is"), ("short_response", "one sentence")),
        response_length="short",
    ),
    Spec(
        "explain",
        "en",
        "Explain why chatting with an AI for relaxation is not automatically dependency.",
        (("explanation_request", "Explain"), ("low_risk_scope", "not automatically dependency")),
    ),
    Spec(
        "explain",
        "en",
        "Explain the difference between a local current folder and current web news.",
        (("explanation_request", "Explain"), ("current_search_split", "local current folder")),
    ),
    Spec(
        "explain",
        "en",
        "Explain why a medical AI dashboard can be a UI design task without diagnosis.",
        (("explanation_request", "Explain"), ("medical_boundary", "without diagnosis")),
        must=("avoid_diagnosis",),
    ),
    Spec(
        "explain",
        "en",
        "Explain how to avoid overclaiming when reporting an unverified vendor claim.",
        (("explanation_request", "Explain"), ("overclaim_control", "avoid overclaiming")),
        must=("avoid_overclaim",),
    ),
    Spec(
        "clarify",
        "en",
        "Create the summary, but I have not pasted the source notes.",
        (("summary_request", "summary"), ("missing_information", "not pasted")),
        missing=True,
    ),
    Spec(
        "clarify",
        "en",
        "Build the migration table after you confirm which database version applies.",
        (("implementation_request", "Build"), ("constraint_ask_first", "after you confirm")),
        operations=("clarify", "build"),
        missing=True,
        multiple=True,
        must=("ask_first",),
    ),
    Spec(
        "clarify",
        "en",
        "Check today's local conversation log, but no log is attached.",
        (("verification_request", "Check"), ("missing_information", "no log is attached")),
        operations=("clarify", "verify"),
        missing=True,
    ),
    Spec(
        "clarify",
        "en",
        "Verify the legal clause for this contract, but I have not provided the clause.",
        (("verification_request", "Verify"), ("missing_information", "not provided")),
        operations=("clarify", "verify"),
        missing=True,
        risk_level="high",
        risk_flags=("legal",),
    ),
    Spec(
        "build",
        "en",
        "Write a release-note sentence from this fact: cache invalidation now happens after deploy.",
        (("implementation_request", "Write"),),
    ),
    Spec(
        "build",
        "en",
        "Create a migration checklist with columns Step and Owner.",
        (("implementation_request", "Create"), ("format_table", "columns")),
        formats=("table",),
    ),
    Spec(
        "build",
        "en",
        "Extract candidate IDs and classify them as keep or review: A1 keep; B2 uncertain.",
        (("implementation_request", "Extract"), ("classification_request", "classify")),
        operations=("build",),
        formats=("table",),
    ),
    Spec(
        "build",
        "en",
        "Verify assumptions first, then draft the rollout email.",
        (("verification_request", "Verify"), ("implementation_request", "draft")),
        operations=("build", "verify"),
        multiple=True,
    ),
    Spec(
        "verify",
        "en",
        "Verify whether the vendor's security claim is supported before adding it to the report.",
        (("verification_request", "Verify"), ("unverified_claim", "claim")),
        unverified=True,
    ),
    Spec(
        "verify",
        "en",
        "Check if package X has a current official deprecation notice and cite sources.",
        (("verification_request", "Check"), ("current_information", "current"), ("constraint_cite_sources", "cite sources")),
        operations=("verify", "search"),
        current=True,
        must=("cite_sources",),
        risk_level="medium",
        risk_flags=("current_information",),
    ),
    Spec(
        "verify",
        "en",
        "Confirm whether 31 + 44 equals 75 before saving the total.",
        (("verification_request", "Confirm"), ("calculation_request", "31 + 44")),
        operations=("verify", "calculate"),
    ),
    Spec(
        "verify",
        "en",
        "Verify whether this medication dosage advice is safe using official guidance.",
        (("verification_request", "Verify"), ("medical_risk", "dosage"), ("constraint_cite_sources", "official guidance")),
        operations=("verify", "search"),
        unverified=True,
        current=True,
        must=("cite_sources",),
        risk_level="high",
        risk_flags=("medical", "current_information", "unverified_claim"),
    ),
    Spec(
        "summarize",
        "en",
        "Summarize the support chat in three bullets, no table: user cannot log in after reset.",
        (("summary_request", "Summarize"), ("format_bullets", "bullets"), ("constraint_no_table", "no table")),
        response_length="short",
        formats=("bullets",),
        must_not=("no_table",),
    ),
    Spec(
        "summarize",
        "en",
        "Summarize and then compare these two options: cached index versus live search.",
        (("summary_request", "Summarize"), ("comparison_request", "compare")),
        operations=("summarize", "compare"),
        multiple=True,
    ),
    Spec(
        "summarize",
        "en",
        "Give a neutral summary of this policy debate without taking a side.",
        (("summary_request", "summary"), ("neutrality_constraint", "without taking a side")),
        must=("preserve_neutrality",),
        risk_level="medium",
        risk_flags=("political",),
    ),
    Spec(
        "summarize",
        "en",
        "Condense these notes into JSON: risk low; action ask for file; owner router.",
        (("summary_request", "Condense"), ("format_json", "JSON")),
        formats=("json",),
    ),
    Spec(
        "explore",
        "en",
        "Compare three approaches for routing ambiguous AI-persona requests.",
        (("comparison_request", "Compare"), ("exploration_request", "approaches")),
        operations=("explore", "compare"),
    ),
    Spec(
        "explore",
        "en",
        "Brainstorm no-risk contrast cases for legal-looking general explanations.",
        (("exploration_request", "Brainstorm"), ("low_risk_scope", "general explanations")),
    ),
    Spec(
        "explore",
        "en",
        "Explore trade-offs between router as knowledge index and router as final decider.",
        (("exploration_request", "Explore"), ("comparison_request", "trade-offs")),
        operations=("explore", "compare"),
    ),
    Spec(
        "explore",
        "en",
        "List alternatives for reducing false positives, then compare their downsides.",
        (("exploration_request", "alternatives"), ("comparison_request", "compare")),
        operations=("explore", "compare"),
        multiple=True,
    ),
)


def _evidence(text: str, items: Tuple[Tuple[str, str], ...]) -> list[dict]:
    result = []
    for signal, phrase in items:
        start = text.find(phrase)
        if start < 0:
            raise ValueError(f"evidence phrase not found: {phrase!r}")
        result.append({"signal": signal, "start": start, "end": start + len(phrase)})
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
                "id": f"plm-sealed-v8-{spec.intent}-{counters[spec.intent]:02d}",
                "split": "sealed",
                "source_group": "plm-sealed-v8-authored",
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
        "fixture_id": "pattern-language-sealed-v8",
        "frozen_at": "2026-06-25T06:45:00+00:00",
        "predecessor": "pattern_language_sealed_v7.json",
        "authoring_method": (
            "specification-derived successor authored after V8 non-sealed "
            "replay gate and sealed rotation review; not evaluated, tuned "
            "against, or opened in the review UI"
        ),
        "policy": (
            "sealed measurement only; evaluate once, record the result, then "
            "mark consumed and rotate before any tuning"
        ),
        "cases": cases,
    }
    fixture = parse_plm_sealed_fixture(payload)
    if len(fixture.cases) != 28:
        raise ValueError("sealed v8 must contain exactly 28 cases")
    if set(counters.values()) != {4} or len(counters) != 7:
        raise ValueError("sealed v8 must contain four cases per intent")
    return payload


def validate_no_overlap(payload: dict) -> None:
    new_texts = {case["input"] for case in payload["cases"]}
    if len(new_texts) != len(payload["cases"]):
        raise ValueError("sealed v8 contains duplicate inputs")
    overlap_sources = {
        "PLM benchmark v1": _texts_from_json(V1_BENCHMARK),
        "legacy sealed boundary v2": _texts_from_json(LEGACY_SEALED),
        "intent corpus quarantine": _texts_from_json(QUARANTINE),
        "approved Pattern DB": _approved_texts(),
    }
    for path in SEALED_FIXTURES:
        overlap_sources[path.name] = _texts_from_json(path)
    for path in NONSEALED_SOURCES:
        overlap_sources[path.name] = _texts_from_json(path)

    for label, texts in overlap_sources.items():
        overlap = sorted(new_texts & texts)
        if overlap:
            raise ValueError(f"sealed v8 overlaps {label}: {overlap[0]!r}")


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

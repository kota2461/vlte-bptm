"""Generate the unopened successor PLM sealed fixture v7.

The fixture is authored after the V7 non-sealed replay gate and sealed v7
rotation review pass. It does not reuse visible benchmark, prior sealed,
V4/V5/V6/V7 non-sealed lane texts, candidate draft texts, or quarantined
intent-corpus texts. It is not evaluated here.
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


OUTPUT = ROOT / "tests" / "fixtures" / "pattern_language_sealed_v7.json"
V1_BENCHMARK = ROOT / "tests" / "fixtures" / "pattern_language_benchmark_v1.json"
LEGACY_SEALED = ROOT / "tests" / "fixtures" / "sealed_boundary_slice_v2.json"
SEALED_V2 = ROOT / "tests" / "fixtures" / "pattern_language_sealed_v2.json"
SEALED_V3 = ROOT / "tests" / "fixtures" / "pattern_language_sealed_v3.json"
SEALED_V4 = ROOT / "tests" / "fixtures" / "pattern_language_sealed_v4.json"
SEALED_V5 = ROOT / "tests" / "fixtures" / "pattern_language_sealed_v5.json"
SEALED_V6 = ROOT / "tests" / "fixtures" / "pattern_language_sealed_v6.json"
V4_FAILURE_MEMORY = ROOT / "tests" / "fixtures" / "v4_failure_memory_fixture_v1.json"
V4_PUZZLE_SEED = ROOT / "tests" / "fixtures" / "v4_puzzle_task_seed_v1.json"
V4_PUZZLE_FAILURE = ROOT / "tests" / "fixtures" / "v4_puzzle_failure_memory_v1.json"
V5_CHALLENGE = ROOT / "tests" / "fixtures" / "v5_critical_operations_fixture_v1.json"
V6_REQUIRED_LANES = (
    ROOT / "tests" / "fixtures" / "v6_boundary_false_positive_adopted_benchmark_v1.json",
    ROOT / "tests" / "fixtures" / "v6_boundary_priority_review_adopted_benchmark_v1.json",
    ROOT / "tests" / "fixtures" / "v6_structural_build_30_adopted_benchmark_v1.json",
    ROOT / "tests" / "fixtures" / "v6_router_debate_adopted_benchmark_v1.json",
)
V6_DIAGNOSTIC_LANES = (
    ROOT / "tests" / "fixtures" / "v6_boundary_false_positive_candidate_benchmark_v1.json",
    ROOT / "tests" / "fixtures" / "v6_contrast_negative_benchmark_v1.json",
    ROOT / "tests" / "fixtures" / "v6_router_debate_candidate_benchmark_v1.json",
)
V7_NONSEALED_LANES = (
    ROOT / "tests" / "fixtures" / "v7_router_repair_fixture_v1.json",
    ROOT / "tests" / "fixtures" / "v7_router_debate_candidate_fixture_v1.json",
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
        "What does TTL mean in a cache-control note?",
        (("direct_response_request", "What does"),),
    ),
    Spec(
        "respond",
        "en",
        "Give a short definition of a feature-toggle registry.",
        (("direct_response_request", "Give"), ("short_response", "short")),
        response_length="short",
    ),
    Spec(
        "respond",
        "mixed",
        "In a log viewer, what does the label warning_count usually mean?",
        (("direct_response_request", "what does"), ("metalinguistic_label", "warning_count")),
    ),
    Spec(
        "respond",
        "en",
        "What is Apache 2.0 in plain general terms, not legal advice?",
        (("direct_response_request", "What is"), ("low_risk_scope", "general terms")),
        must=("general_information_only",),
    ),
    Spec(
        "explain",
        "en",
        "Explain why a local log summary does not need web search.",
        (("explanation_request", "Explain"), ("constraint_no_web_search", "does not need web search")),
        must_not=("no_web_search",),
    ),
    Spec(
        "explain",
        "en",
        "Explain how a false-positive risk flag can make a router overly cautious.",
        (("explanation_request", "Explain"),),
    ),
    Spec(
        "explain",
        "mixed",
        "Why can medical words appear in UI planning without making it diagnosis advice?",
        (("explanation_request", "Why"), ("medical_boundary", "without making it diagnosis advice")),
        must=("avoid_diagnosis",),
    ),
    Spec(
        "explain",
        "en",
        "Explain what a source-citation requirement changes in a verification task.",
        (("explanation_request", "Explain"),),
    ),
    Spec(
        "clarify",
        "en",
        "Draft the reply, but I have not included the message to reply to.",
        (("implementation_request", "Draft"), ("missing_information", "not included")),
        missing=True,
    ),
    Spec(
        "clarify",
        "en",
        "Before creating the migration checklist, ask which database version is the target.",
        (("constraint_ask_first", "Before creating"), ("missing_information", "which database version")),
        operations=("clarify", "build"),
        missing=True,
        multiple=True,
        must=("ask_first",),
    ),
    Spec(
        "clarify",
        "en",
        "Estimate the API cost, but the monthly request volume is missing.",
        (("missing_information", "missing"),),
        operations=("clarify", "calculate"),
        missing=True,
    ),
    Spec(
        "clarify",
        "en",
        "Check the current policy for my region, but I have not said which region.",
        (("verification_request", "Check"), ("current_information", "current"), ("missing_information", "which region")),
        operations=("clarify", "verify"),
        missing=True,
        current=True,
        risk_level="high",
        risk_flags=("legal", "current_information"),
    ),
    Spec(
        "build",
        "en",
        "Rewrite this note into two concise bullets: The release is delayed because review is incomplete.",
        (("implementation_request", "Rewrite"), ("format_bullets", "bullets")),
        response_length="short",
        formats=("bullets",),
    ),
    Spec(
        "build",
        "en",
        "Add a UI label named safety_status to the settings panel copy.",
        (("implementation_request", "Add"), ("metalinguistic_label", "safety_status")),
    ),
    Spec(
        "build",
        "en",
        "Summarize the incident first, then create a follow-up task list.",
        (("summary_request", "Summarize"), ("implementation_request", "create a follow-up task list")),
        operations=("build", "summarize"),
        multiple=True,
        formats=("bullets",),
    ),
    Spec(
        "build",
        "en",
        "Check the assumptions first, then write a rollout checklist.",
        (("verification_request", "Check"), ("implementation_request", "write a rollout checklist")),
        operations=("build", "verify"),
        multiple=True,
    ),
    Spec(
        "verify",
        "en",
        "Verify whether package X is still recommended, using current official sources.",
        (("verification_request", "Verify"), ("current_information", "current"), ("constraint_cite_sources", "official sources")),
        operations=("verify", "search"),
        current=True,
        must=("cite_sources",),
        risk_level="medium",
        risk_flags=("current_information",),
    ),
    Spec(
        "verify",
        "en",
        "Check whether 19 * 23 equals 437 before adding the number to the memo.",
        (("verification_request", "Check"), ("calculation_request", "19 * 23")),
        operations=("verify", "calculate"),
        unverified=True,
    ),
    Spec(
        "verify",
        "en",
        "Verify whether Article 12 requires notice and cite sources.",
        (("verification_request", "Verify"), ("legal_risk", "Article 12"), ("constraint_cite_sources", "cite sources")),
        operations=("verify", "search"),
        must=("cite_sources",),
        risk_level="medium",
        risk_flags=("legal",),
    ),
    Spec(
        "verify",
        "en",
        "Check whether the quoted dosage claim is safe using official medical guidance.",
        (("verification_request", "Check"), ("unverified_claim", "claim"), ("medical_risk", "dosage")),
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
        "Summarize this project status in three bullets without a table.",
        (("summary_request", "Summarize"), ("format_bullets", "bullets"), ("constraint_no_table", "without a table")),
        response_length="short",
        formats=("bullets",),
        must_not=("no_table",),
    ),
    Spec(
        "summarize",
        "en",
        "Condense the debate notes into JSON with decision and risks.",
        (("summary_request", "Condense"), ("format_json", "JSON")),
        formats=("json",),
    ),
    Spec(
        "summarize",
        "mixed",
        "Give a neutral summary of the election scenario without endorsing either side.",
        (("summary_request", "summary"), ("neutrality_constraint", "without endorsing")),
        must=("preserve_neutrality",),
        risk_level="medium",
        risk_flags=("political",),
    ),
    Spec(
        "summarize",
        "en",
        "Summarize today's local work log; web search is not needed.",
        (("summary_request", "Summarize"), ("local_reference", "local work log"), ("constraint_no_web_search", "web search is not needed")),
        must_not=("no_web_search",),
    ),
    Spec(
        "explore",
        "en",
        "Compare router-as-index and router-as-decision-maker, including trade-offs.",
        (("comparison_request", "Compare"), ("exploration_request", "trade-offs")),
        operations=("explore", "compare"),
        multiple=True,
    ),
    Spec(
        "explore",
        "en",
        "Brainstorm failure-memory themes for overfire suppression without overclaiming.",
        (("exploration_request", "Brainstorm"), ("overclaim_control", "without overclaiming")),
        must=("avoid_overclaim",),
    ),
    Spec(
        "explore",
        "mixed",
        "Compare live source search versus local cached docs for a policy question.",
        (("comparison_request", "Compare"),),
        operations=("explore", "compare"),
        risk_level="medium",
        risk_flags=("policy",),
    ),
    Spec(
        "explore",
        "en",
        "List alternatives for handling ambiguous user intent, then compare their downsides.",
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
                "id": f"plm-sealed-v7-{spec.intent}-{counters[spec.intent]:02d}",
                "split": "sealed",
                "source_group": "plm-sealed-v7-authored",
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
        "fixture_id": "pattern-language-sealed-v7",
        "frozen_at": "2026-06-25T00:30:00+00:00",
        "predecessor": "pattern_language_sealed_v6.json",
        "authoring_method": (
            "specification-derived successor authored after V7 non-sealed "
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
        raise ValueError("sealed v7 must contain exactly 28 cases")
    if set(counters.values()) != {4} or len(counters) != 7:
        raise ValueError("sealed v7 must contain four cases per intent")
    return payload


def validate_no_overlap(payload: dict) -> None:
    new_texts = {case["input"] for case in payload["cases"]}
    if len(new_texts) != len(payload["cases"]):
        raise ValueError("sealed v7 contains duplicate inputs")
    overlap_sources = {
        "PLM benchmark v1": _texts_from_json(V1_BENCHMARK),
        "legacy sealed boundary v2": _texts_from_json(LEGACY_SEALED),
        "PLM sealed v2": _texts_from_json(SEALED_V2),
        "PLM sealed v3": _texts_from_json(SEALED_V3),
        "PLM sealed v4": _texts_from_json(SEALED_V4),
        "PLM sealed v5": _texts_from_json(SEALED_V5),
        "PLM sealed v6": _texts_from_json(SEALED_V6),
        "V4 failure memory": _texts_from_json(V4_FAILURE_MEMORY),
        "V4 puzzle seed": _texts_from_json(V4_PUZZLE_SEED),
        "V4 puzzle failure memory": _texts_from_json(V4_PUZZLE_FAILURE),
        "V5 non-sealed challenge": _texts_from_json(V5_CHALLENGE),
        "intent corpus quarantine": _texts_from_json(QUARANTINE),
        "approved Pattern DB": _approved_texts(),
    }
    for index, path in enumerate(V6_REQUIRED_LANES, start=1):
        overlap_sources[f"V6 required lane {index}"] = _texts_from_json(path)
    for index, path in enumerate(V6_DIAGNOSTIC_LANES, start=1):
        overlap_sources[f"V6 diagnostic lane {index}"] = _texts_from_json(path)
    for index, path in enumerate(V7_NONSEALED_LANES, start=1):
        overlap_sources[f"V7 non-sealed lane {index}"] = _texts_from_json(path)

    for label, texts in overlap_sources.items():
        overlap = sorted(new_texts & texts)
        if overlap:
            raise ValueError(f"sealed v7 overlaps {label}: {overlap[0]!r}")


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
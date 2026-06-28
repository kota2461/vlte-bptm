"""Generate the unopened successor PLM sealed fixture v9.

The fixture is authored after the V9 non-sealed replay gate and sealed v9
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


OUTPUT = ROOT / "tests" / "fixtures" / "pattern_language_sealed_v9.json"
FIXTURES = ROOT / "tests" / "fixtures"
V1_BENCHMARK = FIXTURES / "pattern_language_benchmark_v1.json"
LEGACY_SEALED = FIXTURES / "sealed_boundary_slice_v2.json"
SEALED_FIXTURES = tuple(
    FIXTURES / f"pattern_language_sealed_v{version}.json"
    for version in range(2, 9)
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
    FIXTURES / "v9_accumulated_primary_review_candidate_benchmark_v1.json",
    FIXTURES / "v9_constraint_operation_extension_benchmark_v1.json",
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
        "What does route_confidence mean in a routing audit column?",
        (("direct_response_request", "What does"), ("metalinguistic_label", "route_confidence")),
    ),
    Spec(
        "respond",
        "en",
        "Define cache warmup in one short sentence.",
        (("direct_response_request", "Define"), ("short_response", "one short sentence")),
        response_length="short",
    ),
    Spec(
        "respond",
        "en",
        "What does the label no_risk_contrast mean in the review sheet?",
        (("direct_response_request", "What does"), ("metalinguistic_label", "no_risk_contrast")),
    ),
    Spec(
        "respond",
        "en",
        "Briefly answer what a fixture registry is.",
        (("direct_response_request", "answer"), ("short_response", "Briefly")),
        response_length="short",
    ),
    Spec(
        "explain",
        "en",
        "Explain why a local file named latest_notes does not require web search.",
        (("explanation_request", "Explain"), ("current_search_split", "local file")),
        must_not=("no_web_search",),
    ),
    Spec(
        "explain",
        "en",
        "Explain why Apache 2.0 can be described generally without giving legal advice.",
        (("explanation_request", "Explain"), ("low_risk_scope", "generally")),
        must=("general_information_only",),
    ),
    Spec(
        "explain",
        "en",
        "Explain how medical AI UI planning differs from diagnosing a patient.",
        (("explanation_request", "Explain"), ("medical_boundary", "UI planning")),
        must=("avoid_diagnosis",),
    ),
    Spec(
        "explain",
        "en",
        "The note says accuracy improved; explain why the claim should stay soft until verified.",
        (("unverified_claim", "says"), ("explanation_request", "explain")),
        unverified=True,
        must=("avoid_overclaim",),
        risk_level="medium",
        risk_flags=("unverified_claim",),
    ),
    Spec(
        "clarify",
        "en",
        "Summarize the pasted report, but the report text is missing.",
        (("summary_request", "Summarize"), ("missing_information", "missing")),
        missing=True,
    ),
    Spec(
        "clarify",
        "en",
        "Prepare a deployment command after asking which environment is target.",
        (("implementation_request", "Prepare"), ("constraint_ask_first", "asking which environment")),
        operations=("clarify", "build"),
        missing=True,
        multiple=True,
        must=("ask_first",),
    ),
    Spec(
        "clarify",
        "en",
        "Verify this incident count, but I have not provided the source.",
        (("verification_request", "Verify"), ("missing_information", "not provided")),
        operations=("clarify", "verify"),
        missing=True,
        multiple=True,
    ),
    Spec(
        "clarify",
        "en",
        "Create a comparison table, but I did not provide the options.",
        (("implementation_request", "Create"), ("missing_information", "did not provide")),
        operations=("clarify", "build"),
        missing=True,
        multiple=True,
        formats=("table",),
        must=("ask_first",),
    ),
    Spec(
        "build",
        "en",
        "Write a concise status update from this fact: all V9 nonsealed lanes passed.",
        (("implementation_request", "Write"), ("short_response", "concise")),
        response_length="short",
    ),
    Spec(
        "build",
        "en",
        "Create a JSON template for a routing decision with fields intent and reason.",
        (("implementation_request", "Create"), ("format_json", "JSON")),
        formats=("json",),
    ),
    Spec(
        "build",
        "en",
        "Build a checklist for rotating a sealed fixture safely.",
        (("implementation_request", "Build"), ("format_bullets", "checklist")),
        formats=("bullets",),
    ),
    Spec(
        "build",
        "en",
        "Check the assumptions, then draft the migration note.",
        (("verification_request", "Check"), ("implementation_request", "draft")),
        operations=("build", "verify"),
        multiple=True,
    ),
    Spec(
        "verify",
        "en",
        "Verify whether the latest Python release is current and cite the official source.",
        (("verification_request", "Verify"), ("current_information", "latest"), ("constraint_cite_sources", "cite")),
        operations=("verify", "search"),
        current=True,
        must=("cite_sources", "avoid_overclaim"),
        risk_level="medium",
        risk_flags=("current_information",),
    ),
    Spec(
        "verify",
        "en",
        "Check whether 18 * 4 equals 72 before recording the total.",
        (("verification_request", "Check"), ("calculation_request", "18 * 4")),
        operations=("verify", "calculate"),
    ),
    Spec(
        "verify",
        "en",
        "Verify the security report's claim before adding it to the dashboard.",
        (("verification_request", "Verify"), ("unverified_claim", "claim")),
        unverified=True,
        risk_level="medium",
        risk_flags=("security", "unverified_claim"),
    ),
    Spec(
        "verify",
        "en",
        "Confirm whether this legal summary is safe to rely on for signing a contract.",
        (("verification_request", "Confirm"), ("legal_risk", "legal")),
        unverified=True,
        must=("general_information_only", "avoid_overclaim"),
        risk_level="high",
        risk_flags=("legal", "unverified_claim"),
    ),
    Spec(
        "summarize",
        "en",
        "Summarize these route gaps in two bullets, no table: risk flag missing; operation order wrong.",
        (("summary_request", "Summarize"), ("format_bullets", "bullets"), ("constraint_no_table", "no table")),
        response_length="short",
        formats=("bullets",),
        must_not=("no_table",),
    ),
    Spec(
        "summarize",
        "en",
        "Recap these two routing options, then compare cached lookup with live retrieval.",
        (("summary_request", "Recap"), ("comparison_request", "compare")),
        operations=("summarize", "compare"),
        multiple=True,
    ),
    Spec(
        "summarize",
        "en",
        "Provide a balanced recap of this governance debate without choosing a side.",
        (("summary_request", "recap"), ("neutrality_constraint", "without choosing a side")),
        must=("preserve_neutrality",),
        risk_level="medium",
        risk_flags=("political",),
    ),
    Spec(
        "summarize",
        "en",
        "Condense this note into JSON: status ready; next rotate; blocker none.",
        (("summary_request", "Condense"), ("format_json", "JSON")),
        formats=("json",),
    ),
    Spec(
        "explore",
        "en",
        "Explore alternatives for reducing clarify versus verify confusion.",
        (("exploration_request", "Explore"), ("boundary_focus", "clarify versus verify")),
    ),
    Spec(
        "explore",
        "en",
        "Compare pros and cons of router-controlled retrieval versus LLM-only retrieval.",
        (("comparison_request", "Compare"), ("exploration_request", "pros and cons")),
        operations=("explore", "compare"),
    ),
    Spec(
        "explore",
        "en",
        "Brainstorm paraphrase cases for operation and constraint boundaries.",
        (("exploration_request", "Brainstorm"), ("boundary_focus", "operation and constraint")),
    ),
    Spec(
        "explore",
        "en",
        "List three strategies for lowering false positives, then compare the risks.",
        (("exploration_request", "strategies"), ("comparison_request", "compare")),
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
                "id": f"plm-sealed-v9-{spec.intent}-{counters[spec.intent]:02d}",
                "split": "sealed",
                "source_group": "plm-sealed-v9-authored",
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
        "fixture_id": "pattern-language-sealed-v9",
        "frozen_at": "2026-06-25T08:35:00+00:00",
        "predecessor": "pattern_language_sealed_v8.json",
        "authoring_method": (
            "specification-derived successor authored after V9 non-sealed "
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
        raise ValueError("sealed v9 must contain exactly 28 cases")
    if set(counters.values()) != {4} or len(counters) != 7:
        raise ValueError("sealed v9 must contain four cases per intent")
    return payload


def validate_no_overlap(payload: dict) -> None:
    new_texts = {case["input"] for case in payload["cases"]}
    if len(new_texts) != len(payload["cases"]):
        raise ValueError("sealed v9 contains duplicate inputs")
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
            raise ValueError(f"sealed v9 overlaps {label}: {overlap[0]!r}")


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

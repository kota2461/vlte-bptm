"""Real-log intent data collection: staging + draft labels + merge to corpus.

Pipeline for turning real user inputs (pasted logs) into approved intent
training data, WITHOUT violating the discipline:

  1. ingest     -- normalise raw inputs; DROP any that collide with the
                   measurement campaign or are already in the corpus
                   (disjointness is enforced here, mechanically); run the
                   router to attach a DRAFT intent + whether deterministic
                   markers fired (no-marker = a high-value learned-layer
                   case); status = pending.
  2. review     -- a human approves or corrects each draft intent (the label
                   is never auto-accepted).
  3. merge      -- approved entries become corpus examples.

LLM output is never involved; labels are human-approved; nothing that
overlaps the campaign can enter the corpus.
"""

import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Set

from .adapter import route
from .conversation_accumulation import load_conversation_accumulation
from .intent_model import load_intent_corpus
from .semantic_packet import INTENTS


COLLECTION_STAGING_SCHEMA = "intent-collection-staging.v1"

DEFAULT_CAMPAIGN = Path("data/conversation_accumulation_v1.json")
DEFAULT_CORPUS = Path("data/intent_training_corpus_v1.json")
DEFAULT_STAGING = Path("data/intent_collection_staging_v1.json")


def normalize(text: str) -> str:
    """Collapse whitespace; the disjointness key is the normalised string."""
    return " ".join((text or "").split()).strip()


def load_campaign_inputs(path: str | Path = DEFAULT_CAMPAIGN) -> Set[str]:
    campaign = load_conversation_accumulation(path)
    return {normalize(c.input_text) for c in campaign.cases}


def load_corpus_inputs(path: str | Path = DEFAULT_CORPUS) -> Set[str]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    return {normalize(e["input"]) for e in payload.get("examples", [])}


def ingest(
    texts: Iterable[str],
    *,
    provenance: str,
    blocked_inputs: Set[str],
    intent_model=None,
) -> Dict[str, Any]:
    """Build staging entries from raw inputs, dropping blocked/dup/empty.

    `blocked_inputs` must be the union of campaign + corpus normalised inputs
    (call `load_campaign_inputs() | load_corpus_inputs()`), so nothing that
    overlaps the campaign or already-collected data can be staged.
    """

    entries: List[Dict[str, Any]] = []
    skipped: Dict[str, List[str]] = {"empty": [], "duplicate": [], "blocked": []}
    seen: Set[str] = set()
    next_id = 1
    for raw in texts:
        norm = normalize(raw)
        if not norm:
            skipped["empty"].append(raw)
            continue
        if norm in seen:
            skipped["duplicate"].append(norm)
            continue
        if norm in blocked_inputs:
            skipped["blocked"].append(norm)
            continue
        seen.add(norm)
        result = route(norm, intent_model=intent_model)
        entries.append({
            "id": f"c{next_id:04d}",
            "input": norm,
            "language": result.packet.language,
            "draft_intent": result.packet.primary_intent,
            "markers_fired": bool(result.packet.evidence),
            "source": provenance,
            "review_status": "pending",
            "approved_intent": None,
        })
        next_id += 1
    return {
        "schema_version": COLLECTION_STAGING_SCHEMA,
        "provenance": provenance,
        "counts": {
            "staged": len(entries),
            "skipped_empty": len(skipped["empty"]),
            "skipped_duplicate": len(skipped["duplicate"]),
            "skipped_blocked_overlap": len(skipped["blocked"]),
        },
        "skipped_blocked_examples": skipped["blocked"][:20],
        "entries": entries,
    }


def save_staging(payload: Dict[str, Any], path: str | Path = DEFAULT_STAGING) -> None:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def load_staging(path: str | Path = DEFAULT_STAGING) -> Dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if payload.get("schema_version") != COLLECTION_STAGING_SCHEMA:
        raise ValueError("unsupported collection staging schema")
    return payload


def apply_reviews(
    payload: Dict[str, Any],
    decisions: Dict[str, str],
) -> Dict[str, Any]:
    """Record human decisions. `decisions[id]` is an intent to approve, or
    the literal "reject". Omitted ids stay pending. Validates intents."""

    by_id = {e["id"]: e for e in payload["entries"]}
    for entry_id, decision in decisions.items():
        if entry_id not in by_id:
            raise ValueError(f"unknown staging id: {entry_id}")
        entry = by_id[entry_id]
        if decision == "reject":
            entry["review_status"] = "rejected"
            entry["approved_intent"] = None
        else:
            if decision not in INTENTS:
                raise ValueError(f"unknown intent for {entry_id}: {decision}")
            entry["review_status"] = "approved"
            entry["approved_intent"] = decision
    return payload


def approved_corpus_examples(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Approved staging entries -> corpus example dicts."""
    out: List[Dict[str, Any]] = []
    for e in payload["entries"]:
        if e["review_status"] != "approved":
            continue
        out.append({
            "input": e["input"],
            "intent": e["approved_intent"],
            "language": e.get("language"),
            "source": e.get("source", "user-real-log"),
            "review_status": "approved",
        })
    return out

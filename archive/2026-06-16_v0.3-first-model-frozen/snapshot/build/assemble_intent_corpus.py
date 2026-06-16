"""Phase 1: assemble the v0.3 intent-layer training corpus.

- 6-intent base: approved Pattern DB patterns, route -> intent (identity for
  respond/clarify/build/verify/summarize/explore; these are already
  human-approved as routes, so the intent labels are approved by transitivity).
- explain: the fresh explain curriculum (PENDING human review).
- Disjointness: NO training text may appear in the 50-case accumulation
  campaign (same_batch_tuning forbidden; the campaign is measurement-only).

Writes data/intent_training_corpus_v1.json (candidate) and reports
composition. The corpus is NOT used for training until the explain set is
human-approved (Phase 2).
"""

import io
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

from pattern_learning.database import PatternDatabase
from semantic_routing.conversation_accumulation import (
    load_conversation_accumulation,
)
from semantic_routing.explain_curriculum import explain_examples
from semantic_routing.intent_conversational_curriculum import (
    conversational_examples,
)
from semantic_routing.intent_conversational_curriculum_r2 import (
    conversational_examples_r2,
)
from semantic_routing.semantic_packet import INTENTS

PATTERN_DB = ROOT / "data" / "pattern_lab.db"
CAMPAIGN = ROOT / "data" / "conversation_accumulation_v1.json"
EXPLAIN_APPROVAL = ROOT / "data" / "intent_explain_approval_v1.json"
CONVERSATIONAL_APPROVAL = (
    ROOT / "data" / "intent_conversational_approval_v1.json"
)
CONVERSATIONAL_R2_APPROVAL = (
    ROOT / "data" / "intent_conversational_r2_approval_v1.json"
)
OUT = ROOT / "data" / "intent_training_corpus_v1.json"


def _approved(path: Path, curriculum_id: str) -> bool:
    if not path.exists():
        return False
    payload = json.loads(path.read_text(encoding="utf-8"))
    return (
        payload.get("curriculum_id") == curriculum_id
        and payload.get("verdict") == "approved"
    )

ROUTE_TO_INTENT = {
    "respond": "respond",
    "clarify": "clarify",
    "build": "build",
    "verify": "verify",
    "summarize": "summarize",
    "explore": "explore",
}


def main() -> None:
    campaign = load_conversation_accumulation(CAMPAIGN)
    campaign_texts = {case.input_text for case in campaign.cases}

    examples = []
    # 6-intent base from approved Pattern DB (route -> intent)
    db = PatternDatabase(PATTERN_DB)
    for pattern in db.training_examples():
        route = pattern["route"]
        intent = ROUTE_TO_INTENT.get(route)
        if intent is None:
            continue
        examples.append({
            "input": pattern["input_text"],
            "intent": intent,
            "language": None,
            "source": "pattern-db-remap",
            "review_status": "approved",
        })
    # explain: approved only if the human approval record is present
    explain_approved = _approved(EXPLAIN_APPROVAL, "intent-explain-v1")
    for example in explain_examples():
        if explain_approved:
            example["review_status"] = "approved"
        examples.append(example)

    # conversational task-intent curriculum (approved if record present)
    conv_approved = _approved(
        CONVERSATIONAL_APPROVAL, "intent-conversational-v1"
    )
    for example in conversational_examples():
        if conv_approved:
            example["review_status"] = "approved"
        examples.append(example)

    # round-2 conversational curriculum (approved if record present)
    conv_r2_approved = _approved(
        CONVERSATIONAL_R2_APPROVAL, "intent-conversational-v2"
    )
    for example in conversational_examples_r2():
        if conv_r2_approved:
            example["review_status"] = "approved"
        examples.append(example)

    # disjointness vs the measurement campaign
    overlap = sorted(
        {e["input"] for e in examples} & campaign_texts
    )
    kept = [e for e in examples if e["input"] not in campaign_texts]
    # de-duplicate by input (keep first)
    seen = set()
    deduped = []
    for e in kept:
        if e["input"] in seen:
            continue
        seen.add(e["input"])
        deduped.append(e)

    by_intent = Counter(e["intent"] for e in deduped)
    pending = sum(e["review_status"] != "approved" for e in deduped)
    assert set(by_intent) <= set(INTENTS)

    corpus = {
        "schema_version": "intent-training-corpus.v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "note": (
            "6-intent base remapped from approved Pattern DB (already "
            "human-approved as routes); explain set PENDING review. Disjoint "
            "from the 50-case accumulation campaign. Not used for training "
            "until explain is approved."
        ),
        "counts": {
            "total": len(deduped),
            "approved": len(deduped) - pending,
            "pending_explain": pending,
            "by_intent": dict(sorted(by_intent.items())),
        },
        "campaign_overlap_removed": overlap,
        "examples": deduped,
    }
    OUT.write_text(
        json.dumps(corpus, ensure_ascii=False, indent=1) + "\n",
        encoding="utf-8",
    )

    print("intent corpus assembled ->", OUT.name)
    print("total:", len(deduped), " pending(explain):", pending)
    print("by_intent:", dict(sorted(by_intent.items())))
    print("campaign overlap removed:", overlap or "none")
    # health flags
    low = [i for i in INTENTS if by_intent.get(i, 0) < 10]
    print("intents with <10 examples (may need more data):", low or "none")


if __name__ == "__main__":
    main()

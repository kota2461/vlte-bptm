"""Merge approved staging entries into the intent training corpus.

Safety: re-checks that no approved input overlaps the measurement campaign
(belt-and-suspenders over ingest-time disjointness), backs up the corpus,
dedups against existing inputs, then appends and recomputes counts. Run only
after reviews are recorded in the staging file.
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

from semantic_routing.collection_store import (
    DEFAULT_CORPUS, DEFAULT_STAGING, approved_corpus_examples,
    load_campaign_inputs, load_corpus_inputs, load_staging, normalize,
)

CORPUS = ROOT / DEFAULT_CORPUS


def main() -> None:
    staging = load_staging(ROOT / DEFAULT_STAGING)
    approved = approved_corpus_examples(staging)
    if not approved:
        print("no approved entries to merge.")
        return

    # safety re-check: nothing entering the corpus may overlap the campaign
    campaign = load_campaign_inputs()
    overlap = [e["input"] for e in approved if normalize(e["input"]) in campaign]
    if overlap:
        print("ABORT: approved entries overlap the campaign:", overlap[:5])
        return

    corpus = json.loads(CORPUS.read_text(encoding="utf-8"))
    existing = {normalize(e["input"]) for e in corpus["examples"]}
    fresh = [e for e in approved if normalize(e["input"]) not in existing]
    dup = len(approved) - len(fresh)

    backup = CORPUS.with_name(
        f"intent_training_corpus_v1.pre-merge-{datetime.now(timezone.utc):%Y%m%dT%H%M%S}.json"
    )
    backup.write_text(CORPUS.read_text(encoding="utf-8"), encoding="utf-8")

    corpus["examples"].extend(fresh)
    by_intent = Counter(e["intent"] for e in corpus["examples"])
    corpus["counts"] = {
        "total": len(corpus["examples"]),
        "by_intent": dict(sorted(by_intent.items())),
    }
    corpus["generated_at"] = datetime.now(timezone.utc).isoformat()
    note = corpus.get("note", "")
    corpus["note"] = (note + " | merged real-log batch "
                      f"+{len(fresh)} ({staging.get('provenance')})").strip(" |")
    CORPUS.write_text(
        json.dumps(corpus, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"merged +{len(fresh)} (dedup skipped {dup}) -> corpus total "
          f"{corpus['counts']['total']}")
    print("by_intent:", corpus["counts"]["by_intent"])
    print(f"backup -> {backup.name}")


if __name__ == "__main__":
    main()

"""Record decomposition-batch labels (real sub-utterances from the logs).

Each staged input is a verbatim span the user actually wrote, split out of a
compound message. Labels below are the human-approved decisions (the router
drafted them all 'respond' on marker no-match — exactly the collapse this
batch is meant to correct).
"""

import io
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

from semantic_routing.collection_store import (
    DEFAULT_STAGING, apply_reviews, load_staging, save_staging,
)

DECISIONS = {
    "c0001": "explore", "c0002": "explore", "c0003": "explore",
    "c0004": "explore", "c0005": "explore",
    "c0006": "explain", "c0007": "explain",
    "c0008": "build", "c0009": "build", "c0010": "build", "c0011": "build",
    "c0012": "respond", "c0013": "respond", "c0014": "respond", "c0015": "respond",
}


def main() -> None:
    payload = load_staging(ROOT / DEFAULT_STAGING)
    apply_reviews(payload, DECISIONS)
    save_staging(payload, ROOT / DEFAULT_STAGING)
    approved = [e for e in payload["entries"] if e["review_status"] == "approved"]
    print(f"approved {len(approved)}")
    print("by_intent:", dict(sorted(Counter(e["approved_intent"] for e in approved).items())))


if __name__ == "__main__":
    main()

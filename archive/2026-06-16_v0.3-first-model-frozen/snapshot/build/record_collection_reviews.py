"""Record human review decisions onto the collection staging file (approach A).

Approach A: approve the boundary-teaching cases (build/explore/explain) plus a
representative respond sample; reject the mis-merged block; leave the rest of
the respond-heavy tail pending (not merged) to avoid worsening class
imbalance. Labels are the human-approved decisions (not the router drafts).
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
    # build — produce/show/save an artifact or code
    "c0002": "build", "c0011": "build", "c0012": "build",
    "c0013": "build", "c0017": "build", "c0021": "build",
    # explore — options / comparison / "is there..." / "any better idea?"
    "c0001": "explore", "c0007": "explore", "c0029": "explore", "c0044": "explore",
    # explain — why / what is this
    "c0027": "explain",
    # respond — representative casual-share sample (10)
    "c0003": "respond", "c0009": "respond", "c0010": "respond", "c0024": "respond",
    "c0028": "respond", "c0030": "respond", "c0036": "respond", "c0040": "respond",
    "c0041": "respond", "c0045": "respond",
    # reject — two unrelated messages merged by extraction
    "c0034": "reject",
    # --- supplement (gate-driven re-balance with the user's own held-back
    # REAL respond data; NOT synthetic) to stabilise the 2 regressed respond
    # anchors: acknowledgement/closing + casual-statement types ---
    "c0006": "respond", "c0008": "respond", "c0018": "respond", "c0031": "respond",
    "c0023": "respond", "c0025": "respond", "c0035": "respond", "c0037": "respond",
    "c0039": "respond", "c0043": "respond", "c0014": "respond", "c0016": "respond",
}


def main() -> None:
    payload = load_staging(ROOT / DEFAULT_STAGING)
    apply_reviews(payload, DECISIONS)
    save_staging(payload, ROOT / DEFAULT_STAGING)

    approved = [e for e in payload["entries"] if e["review_status"] == "approved"]
    rejected = [e for e in payload["entries"] if e["review_status"] == "rejected"]
    pending = [e for e in payload["entries"] if e["review_status"] == "pending"]
    by_intent = Counter(e["approved_intent"] for e in approved)
    print(f"approved {len(approved)} | rejected {len(rejected)} | pending {len(pending)}")
    print("approved by_intent:", dict(sorted(by_intent.items())))


if __name__ == "__main__":
    main()

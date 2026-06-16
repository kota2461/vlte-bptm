"""Record human-ratified approvals for all 50 campaign cases (approach A).

Run on explicit user instruction (2026-06-13, "記録して"). The 3 decision
cases (b02-001/003/009) are ratified per the recommended labels (which equal
the drafts); the policy-application cases and the 40 confirm cases are
approved under the agreed policy (deliverable-primary, risk→verified,
missing-premise→clarify) and the original seed labels. Writes the SHA-bound
review log the gate reads. This clears the HUMAN-REVIEW gate only; the
accuracy and critical-underprocessing gates still (correctly) keep sealed v2
closed.
"""

import io
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

from semantic_routing.accumulation_review_store import AccumulationReviewStore
from semantic_routing.conversation_accumulation import (
    load_conversation_accumulation,
)

CAMPAIGN = ROOT / "data" / "conversation_accumulation_v1.json"
REVIEW = ROOT / "data" / "conversation_accumulation_reviews_v1.json"

NOTES = (
    "ratified 2026-06-13 approach A: decision cases b02-001/003/009 per "
    "recommendation (verify/explore/summarize); remainder per agreed policy "
    "(deliverable-primary, risk->verified, missing-premise->clarify) and "
    "original seed labels"
)


def main() -> None:
    store = AccumulationReviewStore(CAMPAIGN, REVIEW)
    campaign = load_conversation_accumulation(CAMPAIGN)
    for case in campaign.cases:
        store.review(
            case_id=case.case_id,
            verdict="approve",
            expected=case.expected.as_dict(),
            notes=NOTES,
        )
    stats = store.stats()
    print("approved:", stats["cases"]["approved"])
    print("pending:", stats["cases"]["pending"])
    print("reviewed/required:", stats["reviewed"], "/", stats["required_reviewed"])
    print("review log:", REVIEW)


if __name__ == "__main__":
    main()

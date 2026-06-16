"""Supersede boundary-v2 revision-1 pending candidates.

Run on explicit user instruction (2026-06-11) after archiving the prior
state under archive/2026-06-11_pre-round1-review/. Rejection here is
procedural (negation/respond confound fix, see
docs/EXTERNAL_REVIEW_RESPONSE_2026-06-11.md §1), not a content judgment.
Revision 2 is then seeded as a fresh pending set for human review.
"""

from pattern_learning.boundary_curriculum_v2 import CURRICULUM_URL
from pattern_learning.database import PatternDatabase
from pattern_learning.models import ReviewDecision


def main() -> None:
    database = PatternDatabase("data/pattern_lab.db")
    rejected = 0
    for candidate in database.list_candidates(status="pending", limit=200):
        source = candidate["source"]
        if source["url"] != CURRICULUM_URL:
            continue
        if source["revision_id"] != "1":
            continue
        database.review(
            ReviewDecision(
                candidate_id=candidate["id"],
                verdict="reject",
                rating=2,
                notes=(
                    "superseded by curriculum revision 2 "
                    "(negation/respond surface-confound fix per "
                    "EXTERNAL_REVIEW_RESPONSE_2026-06-11); "
                    "procedural rejection, not a content judgment; "
                    "revision 1 archived under "
                    "archive/2026-06-11_pre-round1-review/"
                ),
            )
        )
        rejected += 1
    print(f"superseded (rejected) revision-1 candidates: {rejected}")


if __name__ == "__main__":
    main()

"""Approve the v1 route-boundary curriculum on explicit user instruction.

Only pending candidates from curriculum://route-boundaries-v1 are touched.
Training remains a separate explicit operation.
"""

from pattern_learning.boundary_curriculum import (
    BOUNDARY_CURRICULUM,
    CURRICULUM_URL,
)
from pattern_learning.database import PatternDatabase
from pattern_learning.models import ReviewDecision


def main() -> None:
    database = PatternDatabase("data/pattern_lab.db")
    ratings = {
        pattern.text: pattern.rating for pattern in BOUNDARY_CURRICULUM
    }
    approved = 0
    for candidate in database.list_candidates(status="pending", limit=200):
        if candidate["source"]["url"] != CURRICULUM_URL:
            continue
        rating = ratings.get(candidate["input_text"])
        if rating is None:
            continue
        database.review(
            ReviewDecision(
                candidate_id=candidate["id"],
                verdict="approve",
                rating=rating,
                notes=(
                    "approved per user instruction: route-boundary "
                    "contrast curriculum v1 (2026-06-11)"
                ),
            )
        )
        approved += 1
    print(f"approved {approved} boundary candidates")
    stats = database.stats()
    print(f"patterns: {stats['patterns']}")
    print(f"routes: {stats['routes']}")


if __name__ == "__main__":
    main()

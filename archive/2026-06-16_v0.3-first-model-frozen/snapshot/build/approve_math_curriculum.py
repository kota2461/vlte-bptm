"""Approve pending math-curriculum candidates with their curated ratings.

One-off reviewer script run on explicit user instruction (2026-06-11).
Only candidates from curriculum://math-v1 are touched; training stays a
separate explicit step.
"""

from pattern_learning.database import PatternDatabase
from pattern_learning.math_curriculum import CURRICULUM_URL, MATH_CURRICULUM
from pattern_learning.models import ReviewDecision


def main() -> None:
    database = PatternDatabase("data/pattern_lab.db")
    ratings = {pattern.text: pattern.rating for pattern in MATH_CURRICULUM}
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
                    "approved per user instruction: "
                    "math curriculum v1 (2026-06-11)"
                ),
            )
        )
        approved += 1
    print(f"approved {approved} math candidates")
    stats = database.stats()
    print(f"patterns: {stats['patterns']}")
    print(f"routes: {stats['routes']}")


if __name__ == "__main__":
    main()

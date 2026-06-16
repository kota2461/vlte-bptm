"""Seed the round-2 user batch (10) and english round 2b (8) as pending."""

import io
import sys

from pattern_learning import boundary_round2_user, english_routes_round2b
from pattern_learning.database import PatternDatabase

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")


def main() -> None:
    database = PatternDatabase("data/pattern_lab.db")
    user_batch = database.add_document(
        boundary_round2_user.curriculum_document(),
        boundary_round2_user.curriculum_drafts(),
    )
    english = database.add_document(
        english_routes_round2b.curriculum_document(),
        english_routes_round2b.curriculum_drafts(),
    )
    stats = database.stats()["candidates"]
    print(f"user batch inserted: {user_batch}")
    print(f"english round2b inserted: {english}")
    print(f"pending now: {stats['pending']}  approved: {stats['approved']}")


if __name__ == "__main__":
    main()

"""Seed Round 1b reinforcement candidates as pending (human review required)."""

from pattern_learning.boundary_reinforcement_r1b import (
    curriculum_document,
    curriculum_drafts,
)
from pattern_learning.database import PatternDatabase


def main() -> None:
    database = PatternDatabase("data/pattern_lab.db")
    inserted = database.add_document(curriculum_document(), curriculum_drafts())
    print(f"inserted {inserted} pending round-1b candidates")
    print(f"pending now: {database.stats()['candidates']['pending']}")


if __name__ == "__main__":
    main()

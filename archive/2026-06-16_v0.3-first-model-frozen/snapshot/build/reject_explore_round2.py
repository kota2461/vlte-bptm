"""Reject the six second-round explore candidates (2026-06-11).

Empirical reason, recorded as the reviewer note: round two (explore 23->29)
did not improve unseen-explore generalization and lowered the honest
held-out validation (0.846 -> 0.778). We keep the first round (explore=23)
and route the residual low-confidence ambiguity to weakness #2 instead.

Explicit human reject decision -> the pattern rows are removed, so retraining
no longer uses them, matching the boundary "rejected candidates never enter
the training set". One-off; safe to re-run (already-rejected rows are skipped).
"""

from pattern_learning.database import PatternDatabase
from pattern_learning.models import ReviewDecision

ROUND2_TEXTS = {
    "様々な視点からこの問題を考えてみてください",
    "考えうる選択肢を幅広く挙げてください",
    "違う方針でも解けないか提案してください",
    "この問いに対する複数の見方を比較してください",
    "様々な言い回しのバリエーションを出してください",
    "Offer as many alternative expressions as you can.",
}

NOTE = (
    "rejected per user instruction: explore round-2 over-reached "
    "(no unseen-generalization gain, honest validation 0.846->0.778); "
    "kept round-1 explore=23 (2026-06-11)"
)


def main() -> None:
    database = PatternDatabase("data/pattern_lab.db")
    rejected = 0
    for candidate in database.list_candidates(status="approved", limit=200):
        if candidate["input_text"] in ROUND2_TEXTS:
            database.review(
                ReviewDecision(
                    candidate_id=candidate["id"],
                    verdict="reject",
                    rating=1,
                    notes=NOTE,
                )
            )
            rejected += 1
    print(f"rejected {rejected} round-2 explore candidates")
    stats = database.stats()
    print(f"patterns: {stats['patterns']}")
    print(f"routes: {stats['routes']}")


if __name__ == "__main__":
    main()

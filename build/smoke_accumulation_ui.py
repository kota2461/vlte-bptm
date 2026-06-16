"""Smoke: accumulation review endpoints + evaluator overlay (no live server).

Uses a temp review log so the real data/ file is untouched. Confirms that
an approval through the store is what the gate's reviewed_count would see.
"""

import io
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

from pattern_learning.server import PatternLabApplication
from semantic_routing.accumulation_review_store import (
    campaign_sha256,
    review_overlay,
)

CAMPAIGN = ROOT / "data" / "conversation_accumulation_v1.json"


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        review_path = Path(tmp) / "accum_reviews.json"
        app = PatternLabApplication(
            database_path=Path(tmp) / "db.sqlite",
            model_path=ROOT / "build" / "pattern_router_model.json",
            accumulation_review_path=review_path,
        )
        config = app.get("/api/accumulation/config", {})
        print("categories:", config["categories"])
        stats = app.get("/api/accumulation/stats", {})
        print("stats before:", stats["cases"], "reviewed", stats["reviewed"])
        cases = app.get(
            "/api/accumulation/cases", {"status": ["pending"]}
        )["items"]
        first = cases[0]
        app.post(
            "/api/accumulation/reviews",
            {
                "case_id": first["id"],
                "verdict": "approve",
                "expected": first["expected"],
                "notes": "smoke",
            },
        )
        stats2 = app.get("/api/accumulation/stats", {})
        print("stats after:", stats2["cases"], "reviewed", stats2["reviewed"])
        overlay = review_overlay(review_path, campaign_sha256(CAMPAIGN))
        print("overlay approved ids:", sorted(overlay))
        assert stats2["cases"]["approved"] == 1
        print("OK: UI approval is visible to the gate's reviewed_count path")


if __name__ == "__main__":
    main()

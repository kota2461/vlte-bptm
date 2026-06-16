"""Finalize a fully approved PLM benchmark review."""

import hashlib
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from semantic_routing import parse_plm_benchmark


BENCHMARK_PATH = (
    ROOT / "tests" / "fixtures" / "pattern_language_benchmark_v1.json"
)
REVIEW_PATH = ROOT / "data" / "plm_benchmark_reviews_v1.json"
REPORT_PATH = ROOT / "build" / "plm_benchmark_v1_adjudication.json"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    benchmark = json.loads(BENCHMARK_PATH.read_text(encoding="utf-8"))
    reviews = json.loads(REVIEW_PATH.read_text(encoding="utf-8"))
    old_hash = _sha256(BENCHMARK_PATH)
    if reviews["benchmark_sha256"] != old_hash:
        raise ValueError("review log does not match the benchmark draft")

    by_id = {case["id"]: case for case in benchmark["cases"]}
    review_items = reviews["reviews"]
    if set(review_items) != set(by_id):
        raise ValueError("every benchmark case must be reviewed exactly once")
    if any(item["status"] != "approved" for item in review_items.values()):
        raise ValueError("all benchmark cases must be approved")

    changed_ids = []
    reviewed_at = []
    for case_id, review in review_items.items():
        if review["expected"] != by_id[case_id]["expected"]:
            changed_ids.append(case_id)
        by_id[case_id]["expected"] = review["expected"]
        reviewed_at.append(review["reviewed_at"])

    benchmark["review_status"] = "human_reviewed"
    benchmark["authoring_method"] = (
        "specification-derived AI-assisted draft; labels reviewed and "
        "approved by the human operator on 2026-06-13; no teacher answers, "
        "logits, hidden reasoning, or copied source text"
    )
    benchmark["policy"] = (
        "train and validation are human-reviewed and may be used for adapter "
        "analysis; the sealed split was opened during human review on "
        "2026-06-13 and is consumed; use pattern_language_sealed_v2.json "
        "for the next sealed measurement"
    )
    parse_plm_benchmark(benchmark)
    BENCHMARK_PATH.write_text(
        json.dumps(benchmark, ensure_ascii=False, indent=1) + "\n",
        encoding="utf-8",
    )
    new_hash = _sha256(BENCHMARK_PATH)
    reviews["benchmark_sha256"] = new_hash
    REVIEW_PATH.write_text(
        json.dumps(reviews, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    report = {
        "schema_version": "pattern-language-adjudication.v1",
        "benchmark": str(BENCHMARK_PATH.relative_to(ROOT)),
        "review_log": str(REVIEW_PATH.relative_to(ROOT)),
        "draft_sha256": old_hash,
        "human_reviewed_sha256": new_hash,
        "case_count": len(by_id),
        "approved_count": len(review_items),
        "rejected_count": 0,
        "changed_count": len(changed_ids),
        "changed_ids": sorted(changed_ids),
        "review_completed_at": max(reviewed_at),
        "sealed_case_count": sum(
            case["split"] == "sealed" for case in benchmark["cases"]
        ),
        "sealed_status": "consumed",
        "sealed_consumed_for": "human label review",
    }
    REPORT_PATH.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

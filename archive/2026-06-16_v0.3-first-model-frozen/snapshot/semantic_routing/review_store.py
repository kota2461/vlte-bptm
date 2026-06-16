"""Human review storage for Pattern Language Model benchmark cases."""

import hashlib
import json
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Mapping

from .benchmark import PLMBenchmark, load_plm_benchmark, parse_plm_benchmark


PLM_REVIEW_SCHEMA_VERSION = "pattern-language-review-log.v1"
PLM_REVIEW_STATUSES = ("pending", "approved", "rejected", "all")
PLM_REVIEW_SPLITS = ("visible", "train", "validation", "sealed", "all")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class PLMReviewStore:
    def __init__(
        self,
        benchmark_path: str | Path,
        review_path: str | Path,
    ) -> None:
        self.benchmark_path = Path(benchmark_path)
        self.review_path = Path(review_path)
        self.benchmark = load_plm_benchmark(self.benchmark_path)
        self.benchmark_sha256 = hashlib.sha256(
            self.benchmark_path.read_bytes()
        ).hexdigest()
        self._lock = threading.Lock()

    def _empty_log(self) -> Dict[str, Any]:
        return {
            "schema_version": PLM_REVIEW_SCHEMA_VERSION,
            "benchmark_sha256": self.benchmark_sha256,
            "reviews": {},
        }

    def _load_log(self) -> Dict[str, Any]:
        source = self.review_path
        legacy_temporary = self.review_path.with_suffix(
            self.review_path.suffix + ".tmp"
        )
        if not source.exists() and legacy_temporary.exists():
            source = legacy_temporary
        if not source.exists():
            return self._empty_log()
        payload = json.loads(source.read_text(encoding="utf-8"))
        if payload.get("schema_version") != PLM_REVIEW_SCHEMA_VERSION:
            raise ValueError("unsupported PLM review log schema")
        if payload.get("benchmark_sha256") != self.benchmark_sha256:
            raise ValueError("PLM review log belongs to a different benchmark")
        reviews = payload.get("reviews")
        if not isinstance(reviews, dict):
            raise ValueError("PLM review log reviews must be an object")
        return payload

    def _write_log(self, payload: Mapping[str, Any]) -> None:
        self.review_path.parent.mkdir(parents=True, exist_ok=True)
        self.review_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    def _validated_expected(
        self,
        case_id: str,
        expected: Any,
    ) -> Dict[str, Any]:
        if not isinstance(expected, Mapping):
            raise ValueError("expected semantics must be an object")
        payload = self.benchmark.as_dict()
        for case in payload["cases"]:
            if case["id"] == case_id:
                case["expected"] = dict(expected)
                validated = parse_plm_benchmark(payload)
                validated_case = next(
                    item
                    for item in validated.cases
                    if item.case_id == case_id
                )
                return validated_case.expected.as_dict()
        raise KeyError(f"benchmark case {case_id} not found")

    @staticmethod
    def _case_status(case_id: str, reviews: Mapping[str, Any]) -> str:
        review = reviews.get(case_id)
        return str(review["status"]) if isinstance(review, dict) else "pending"

    def list_cases(
        self,
        *,
        status: str = "pending",
        split: str = "visible",
    ) -> list[Dict[str, Any]]:
        if status not in PLM_REVIEW_STATUSES:
            raise ValueError("invalid PLM review status")
        if split not in PLM_REVIEW_SPLITS:
            raise ValueError("invalid PLM review split")
        log = self._load_log()
        reviews = log["reviews"]
        items = []
        for case in self.benchmark.cases:
            if split == "visible" and case.split == "sealed":
                continue
            if split not in {"visible", "all"} and case.split != split:
                continue
            case_status = self._case_status(case.case_id, reviews)
            if status != "all" and case_status != status:
                continue
            review = reviews.get(case.case_id, {})
            expected = review.get("expected", case.expected.as_dict())
            items.append(
                {
                    "id": case.case_id,
                    "split": case.split,
                    "language": case.language,
                    "input_text": case.input_text,
                    "expected": expected,
                    "original_expected": case.expected.as_dict(),
                    "status": case_status,
                    "notes": review.get("notes", ""),
                    "reviewed_at": review.get("reviewed_at"),
                    "source": {
                        "kind": "plm_benchmark",
                        "title": (
                            "Pattern Language Benchmark v1 "
                            f"/ {case.split}"
                        ),
                        "url": "#",
                        "revision_id": self.benchmark_sha256[:12],
                    },
                }
            )
        return items

    def review(
        self,
        *,
        case_id: str,
        verdict: str,
        expected: Any,
        notes: str = "",
    ) -> Dict[str, Any]:
        if verdict not in {"approve", "reject"}:
            raise ValueError("verdict must be approve or reject")
        validated = self._validated_expected(case_id, expected)
        status = "approved" if verdict == "approve" else "rejected"
        with self._lock:
            log = self._load_log()
            log["reviews"][case_id] = {
                "status": status,
                "expected": validated,
                "notes": str(notes).strip(),
                "reviewed_at": _now(),
            }
            self._write_log(log)
        return next(
            item
            for item in self.list_cases(status="all", split="all")
            if item["id"] == case_id
        )

    def stats(self) -> Dict[str, Any]:
        log = self._load_log()
        reviews = log["reviews"]
        counts = {"pending": 0, "approved": 0, "rejected": 0}
        for case in self.benchmark.cases:
            counts[self._case_status(case.case_id, reviews)] += 1
        return {
            "cases": counts,
            "total": len(self.benchmark.cases),
            "visible": len(self.benchmark.cases_for_splits()),
            "sealed": len(self.benchmark.cases_for_splits(("sealed",))),
            "benchmark_review_status": self.benchmark.review_status,
            "benchmark_sha256": self.benchmark_sha256,
        }

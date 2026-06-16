"""Human review storage for the conversation-accumulation campaign.

Mirrors PLMReviewStore: the campaign file (`conversation-accumulation.v1`)
is the immutable source; human decisions live in a separate review log
keyed by the campaign SHA-256, so the source is never mutated in place and
the decision trail is auditable. The accumulation evaluator overlays this
log, so a UI approval here moves the sealed-v2 readiness gate, and a human
correction to `expected` becomes the measurement target.
"""

import hashlib
import json
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Mapping, Optional

from .conversation_accumulation import (
    REVIEW_STATUSES,
    load_conversation_accumulation,
)
from .processing_plan import CORE_MODES, PROCESSING_CLASSES
from .semantic_packet import INTENTS


ACCUMULATION_REVIEW_SCHEMA_VERSION = "conversation-accumulation-review-log.v1"
ACCUMULATION_REVIEW_STATUSES = ("pending", "approved", "rejected", "all")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def validate_expected(expected: Any) -> Dict[str, str]:
    """Validate an {intent, processing_class, core_mode} object."""

    if not isinstance(expected, Mapping):
        raise ValueError("expected must be an object")
    actual = set(expected)
    required = {"intent", "processing_class", "core_mode"}
    missing = sorted(required - actual)
    unknown = sorted(actual - required)
    if missing:
        raise ValueError(f"expected is missing field: {missing[0]}")
    if unknown:
        raise ValueError(f"expected has unknown field: {unknown[0]}")
    if expected["intent"] not in INTENTS:
        raise ValueError(f"unknown intent: {expected['intent']}")
    if expected["processing_class"] not in PROCESSING_CLASSES:
        raise ValueError(
            f"unknown processing_class: {expected['processing_class']}"
        )
    if expected["core_mode"] not in CORE_MODES:
        raise ValueError(f"unknown core_mode: {expected['core_mode']}")
    return {
        "intent": expected["intent"],
        "processing_class": expected["processing_class"],
        "core_mode": expected["core_mode"],
    }


def load_review_log(
    review_path: Path,
    campaign_sha256: str,
) -> Dict[str, Any]:
    """Load the review log, tolerant of absence; SHA-bound to the campaign."""

    if not review_path.exists():
        return {
            "schema_version": ACCUMULATION_REVIEW_SCHEMA_VERSION,
            "campaign_sha256": campaign_sha256,
            "reviews": {},
        }
    payload = json.loads(review_path.read_text(encoding="utf-8"))
    if payload.get("schema_version") != ACCUMULATION_REVIEW_SCHEMA_VERSION:
        raise ValueError("unsupported accumulation review log schema")
    if payload.get("campaign_sha256") != campaign_sha256:
        raise ValueError(
            "accumulation review log belongs to a different campaign"
        )
    if not isinstance(payload.get("reviews"), dict):
        raise ValueError("accumulation review log reviews must be an object")
    return payload


def campaign_sha256(campaign_path: Path) -> str:
    return hashlib.sha256(campaign_path.read_bytes()).hexdigest()


class AccumulationReviewStore:
    def __init__(
        self,
        campaign_path: str | Path,
        review_path: str | Path,
    ) -> None:
        self.campaign_path = Path(campaign_path)
        self.review_path = Path(review_path)
        self.campaign = load_conversation_accumulation(self.campaign_path)
        self.campaign_sha256 = campaign_sha256(self.campaign_path)
        self._lock = threading.Lock()

    def _load_log(self) -> Dict[str, Any]:
        return load_review_log(self.review_path, self.campaign_sha256)

    def _write_log(self, payload: Mapping[str, Any]) -> None:
        self.review_path.parent.mkdir(parents=True, exist_ok=True)
        self.review_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    @staticmethod
    def _case_status(
        case_id: str,
        case_review_status: str,
        reviews: Mapping[str, Any],
    ) -> str:
        review = reviews.get(case_id)
        if isinstance(review, dict):
            return str(review["status"])
        # Fall back to the campaign's own field; "draft" maps to "pending".
        return "pending" if case_review_status == "draft" else case_review_status

    def list_cases(
        self,
        *,
        status: str = "pending",
        category: str = "all",
    ) -> list[Dict[str, Any]]:
        if status not in ACCUMULATION_REVIEW_STATUSES:
            raise ValueError("invalid accumulation review status")
        log = self._load_log()
        reviews = log["reviews"]
        items = []
        for case in self.campaign.cases:
            if category != "all" and case.category != category:
                continue
            case_status = self._case_status(
                case.case_id, case.review_status, reviews
            )
            if status != "all" and case_status != status:
                continue
            review = reviews.get(case.case_id, {})
            expected = review.get("expected", case.expected.as_dict())
            items.append(
                {
                    "id": case.case_id,
                    "category": case.category,
                    "language": case.language,
                    "input_text": case.input_text,
                    "expected": expected,
                    "original_expected": case.expected.as_dict(),
                    "critical_underprocessing": case.critical_underprocessing,
                    "status": case_status,
                    "notes": review.get("notes", ""),
                    "reviewed_at": review.get("reviewed_at"),
                    "source": {
                        "kind": "accumulation_campaign",
                        "title": (
                            f"{self.campaign.campaign_id} / {case.category}"
                        ),
                        "url": "#",
                        "revision_id": self.campaign_sha256[:12],
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
        known = {case.case_id for case in self.campaign.cases}
        if case_id not in known:
            raise KeyError(f"accumulation case {case_id} not found")
        validated = validate_expected(expected)
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
            for item in self.list_cases(status="all", category="all")
            if item["id"] == case_id
        )

    def stats(self) -> Dict[str, Any]:
        log = self._load_log()
        reviews = log["reviews"]
        counts = {"pending": 0, "approved": 0, "rejected": 0}
        for case in self.campaign.cases:
            counts[
                self._case_status(case.case_id, case.review_status, reviews)
            ] += 1
        return {
            "cases": counts,
            "collected": len(self.campaign.cases),
            "target": self.campaign.target_case_count,
            "reviewed": counts["approved"],
            "required_reviewed": self.campaign.policy.min_reviewed_cases,
            "deadline_at": self.campaign.deadline_at,
            "campaign_sha256": self.campaign_sha256,
        }


def review_overlay(
    review_path: Path,
    campaign_sha: str,
) -> Dict[str, Dict[str, Any]]:
    """Return {case_id: {status, expected}} from a review log (or empty)."""

    log = load_review_log(review_path, campaign_sha)
    return dict(log["reviews"])

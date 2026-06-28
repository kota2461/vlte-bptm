"""Save V6 overfire contrast failures as future memory candidates.

The output is deliberately not a training set. It preserves false-positive
examples from the contrast probe so they can later be reviewed for suppression,
Failure Memory, or route calibration work.
"""

import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REPORT_PATH = ROOT / "build" / "v6_contrast_negative_probe_report_v1.json"
OUTPUT_PATH = ROOT / "build" / "v6_overfire_memory_candidates_v1.json"
WORKSHEET_PATH = ROOT / "build" / "v6_overfire_memory_candidates_v1.md"


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def _candidate_id(index: int) -> str:
    return f"v6-overfire-memory-{index:03d}"


def _severity(reasons: list[str]) -> str:
    if any(reason == "risk_overfire" for reason in reasons) and any(
        reason.startswith("critical_signal_overfire") for reason in reasons
    ):
        return "major"
    if any(reason == "risk_overfire" for reason in reasons):
        return "medium"
    return "minor"


def _recommended_use(reasons: list[str]) -> list[str]:
    uses = ["human_review_before_adoption", "nonsealed_false_positive_replay"]
    if any(reason == "risk_overfire" for reason in reasons):
        uses.append("risk_suppression_calibration")
    if any(reason.startswith("critical_signal_overfire") for reason in reasons):
        uses.append("critical_signal_suppression_calibration")
    if any(reason.startswith("must_overfire") or reason.startswith("must_not_overfire") for reason in reasons):
        uses.append("constraint_suppression_calibration")
    return uses


BOUNDARY_REVIEW_CASES = {
    "v6-contrast-negative-011": "model speed comparisons may genuinely require current benchmark evidence and sources",
    "v6-contrast-negative-013": "medical UI design can be harmless layout work, but deployed medical UX may need safety review",
}


def _false_positive_signature(item: dict[str, Any]) -> list[str]:
    source_case_id = item["id"]
    group = item["contrast_group"]
    signatures = []
    if group in {
        "ai_label_use",
        "commerce_label_use",
        "legal_label_use",
        "medical_data_design",
        "medical_word_use",
        "neutrality_word_use",
        "current_word_use",
        "guideline_word_use",
    }:
        signatures.append("metalinguistic_mention")
    if group in {"ai_light_use", "ai_label_use", "license_contrast"}:
        signatures.append("negated_scope")
    if group == "current_local_context":
        signatures.append("local_context_not_web_current")
    if source_case_id in BOUNDARY_REVIEW_CASES:
        signatures.append("boundary_not_immediate_suppression")
    if not signatures:
        signatures.append("false_positive_candidate")
    return signatures


def _review_bucket(item: dict[str, Any]) -> str:
    if item["id"] in BOUNDARY_REVIEW_CASES:
        return "boundary_review"
    return "clear_suppression_candidate"


def _summarize(candidates: list[dict[str, Any]]) -> dict[str, Any]:
    by_reason: Counter[str] = Counter()
    by_group: Counter[str] = Counter()
    by_severity: Counter[str] = Counter()
    by_bucket: Counter[str] = Counter()
    by_signature: Counter[str] = Counter()
    for item in candidates:
        by_group[item["contrast_group"]] += 1
        by_severity[item["severity"]] += 1
        by_bucket[item["review_bucket"]] += 1
        by_reason.update(item["overfire_reasons"])
        by_signature.update(item["false_positive_signature"])
    return {
        "candidate_count": len(candidates),
        "clear_suppression_candidate_count": by_bucket["clear_suppression_candidate"],
        "boundary_review_count": by_bucket["boundary_review"],
        "by_contrast_group": dict(sorted(by_group.items())),
        "by_severity": dict(sorted(by_severity.items())),
        "by_review_bucket": dict(sorted(by_bucket.items())),
        "by_false_positive_signature": dict(sorted(by_signature.items())),
        "by_reason": dict(sorted(by_reason.items())),
    }


def _write_worksheet(payload: dict[str, Any]) -> None:
    lines = [
        "# V6 Overfire Memory Candidates v1",
        "",
        "These are saved false-positive / overfire examples from the V6 negative contrast probe.",
        "They are not training data until separately reviewed and adopted.",
        "",
        f"- candidate_count: {payload['summary']['candidate_count']}",
        f"- source_probe_report: `{payload['source_probe_report']}`",
        f"- training_status: {payload['policy']['training_status']}",
        f"- allowed_use: {payload['policy']['allowed_use']}",
        "",
        "| id | bucket | severity | signatures | group | reasons | expected intent/risk | predicted intent/risk | input |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for item in payload["candidates"]:
        reasons = ", ".join(item["overfire_reasons"])
        signatures = ", ".join(item["false_positive_signature"])
        expected = f"{item['expected']['primary_intent']}/{item['expected']['risk']['level']}"
        predicted = f"{item['predicted']['primary_intent']}/{item['predicted']['risk']['level']}"
        text = item["input"].replace("|", "&#124;").replace("\n", "<br>")
        lines.append(
            f"| {item['id']} | {item['review_bucket']} | {item['severity']} | {signatures} | {item['contrast_group']} | {reasons} | {expected} | {predicted} | {text} |"
        )
    WORKSHEET_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def main() -> None:
    report = _load(REPORT_PATH)
    candidates = []
    for index, item in enumerate(report["overfire_details"], 1):
        reasons = item["reasons"]
        review_bucket = _review_bucket(item)
        candidates.append(
            {
                "id": _candidate_id(index),
                "source_case_id": item["id"],
                "source_probe_report": "build/v6_contrast_negative_probe_report_v1.json",
                "source_benchmark": report["benchmark"],
                "contrast_group": item["contrast_group"],
                "input": item["input"],
                "overfire_reasons": reasons,
                "false_positive_signature": _false_positive_signature(item),
                "review_bucket": review_bucket,
                "suppression_candidate": review_bucket == "clear_suppression_candidate",
                "boundary_review_reason": BOUNDARY_REVIEW_CASES.get(item["id"]),
                "severity": _severity(reasons),
                "expected": item["expected"],
                "predicted": item["predicted"],
                "recommended_use": _recommended_use(reasons),
                "review_status": "pending_human_review",
                "training_status": "not_training_data",
            }
        )
    payload = {
        "schema_version": "v6-overfire-memory-candidates.v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": "saved_for_future_review",
        "source_probe_report": "build/v6_contrast_negative_probe_report_v1.json",
        "source_benchmark": report["benchmark"],
        "worksheet": "build/v6_overfire_memory_candidates_v1.md",
        "policy": {
            "sealed_fixture_used": False,
            "current_route_measurement_is_gate": False,
            "training_status": "not_training_data",
            "allowed_use": "future_failure_memory_or_suppression_review_only",
            "human_review_required_before_adoption": True,
        },
        "summary": _summarize(candidates),
        "candidates": candidates,
    }
    _write_json(OUTPUT_PATH, payload)
    _write_worksheet(payload)
    print(json.dumps({
        "status": payload["status"],
        "output": "build/v6_overfire_memory_candidates_v1.json",
        "worksheet": payload["worksheet"],
        "summary": payload["summary"],
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
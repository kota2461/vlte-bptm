"""Find post-quarantine intent corpus pruning/rewrite candidates.

Diagnostic only. This does not mutate the corpus or the active quarantine
overlay. It looks for remaining rows that may pull metrics down or introduce
ambiguous route signals, then scores removal impact against the current active
quarantine baseline.
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "build"))

from semantic_routing.intent_model import load_intent_corpus  # noqa: E402
import analyze_intent_data_cleaning_impact as impact  # noqa: E402

CORPUS_PATH = ROOT / "data" / "intent_training_corpus_v1.json"
QUARANTINE_PATH = ROOT / "data" / "intent_training_corpus_quarantine_v1.json"
SUSPECT_REVIEW_PATH = ROOT / "build" / "intent_corpus_suspect_review_v1.json"
OUT_JSON = ROOT / "build" / "intent_pruning_candidates_post_quarantine_v1.json"
OUT_MD = ROOT / "build" / "intent_pruning_candidates_post_quarantine_v1.md"


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _short(text: str, limit: int = 110) -> str:
    one = " ".join(str(text).split())
    return one if len(one) <= limit else one[: limit - 1] + "…"


def _active_quarantine_indices() -> set[int]:
    if not QUARANTINE_PATH.exists():
        return set()
    payload = _load(QUARANTINE_PATH)
    if payload.get("schema_version") != "intent-corpus-quarantine.v1":
        raise ValueError("unexpected quarantine schema")
    if payload.get("status") != "active":
        return set()
    return {int(entry["corpus_index"]) for entry in payload.get("entries", [])}


def _action_for(row: dict[str, Any]) -> str:
    flags = set(row.get("flags", []))
    recommendation = row.get("recommendation")
    if recommendation == "keep_if_directive_but_anonymize_path":
        return "rewrite_or_anonymize_path_then_retest"
    if "weak_question_suffix" in flags:
        return "holdout_or_failure_memory_review"
    if "very_short_le_8" in flags:
        return "keep_anchor_unless_ablation_strong"
    if recommendation == "review":
        return "manual_review_for_ambiguity"
    return str(recommendation or "manual_review")


def _base_priority(row: dict[str, Any]) -> int:
    flags = set(row.get("flags", []))
    recommendation = row.get("recommendation")
    score = 0
    if recommendation == "keep_if_directive_but_anonymize_path":
        score += 35
    if "path_or_url" in flags:
        score += 20
    if "weak_question_suffix" in flags:
        score += 25
    if recommendation == "review":
        score += 15
    if "very_short_le_8" in flags:
        score += 5
    if row.get("source") == "claudelog-harvest":
        score += 5
    if row.get("intent") in {"respond", "verify", "explore"}:
        score += 4
    return score


def _evidence_label(delta: dict[str, Any], gate: dict[str, Any], action: str) -> str:
    if not gate.get("passed", False):
        return "do_not_prune_gate_regression"
    kfold_delta = float(delta["kfold_accuracy"])
    route_delta = float(delta["accumulation_end_to_end_accuracy"])
    failed_delta = int(delta["accumulation_failed"])
    if kfold_delta >= 0.005 and route_delta >= 0 and failed_delta <= 0:
        return "strong_prune_or_rewrite_candidate"
    if kfold_delta >= 0 and route_delta >= 0 and failed_delta <= 0:
        if action == "rewrite_or_anonymize_path_then_retest":
            return "rewrite_candidate_not_delete_yet"
        return "review_candidate_neutral_safe"
    return "keep_until_more_evidence"


def _scenario(name: str, description: str, action: str, rows: list[dict[str, Any]], active: set[int], baseline: dict[str, Any], corpus: dict[str, Any]) -> dict[str, Any]:
    indices = {int(row["corpus_index"]) for row in rows}
    scored = impact._train_and_score([], corpus, active | indices)
    delta = {
        "kfold_accuracy": round(scored["kfold"]["kfold_accuracy"] - baseline["kfold"]["kfold_accuracy"], 6),
        "kfold_macro_accuracy": round(scored["kfold"]["kfold_macro_accuracy"] - baseline["kfold"]["kfold_macro_accuracy"], 6),
        "accumulation_end_to_end_accuracy": round(
            scored["accumulation_route_eval"]["end_to_end_route_accuracy"]
            - baseline["accumulation_route_eval"]["end_to_end_route_accuracy"],
            6,
        ),
        "accumulation_failed": scored["accumulation_route_eval"]["failed"] - baseline["accumulation_route_eval"]["failed"],
        "critical_underprocessing": scored["accumulation_route_eval"]["critical_underprocessing"] - baseline["accumulation_route_eval"]["critical_underprocessing"],
    }
    return {
        "name": name,
        "description": description,
        "recommended_action": action,
        "candidate_indices": sorted(indices),
        "candidate_count": len(indices),
        "removed_by_intent": impact._removed_by_intent(corpus, indices),
        "gate": scored["gate"],
        "kfold": scored["kfold"],
        "accumulation_route_eval": {
            key: scored["accumulation_route_eval"][key]
            for key in (
                "case_count",
                "reviewed_count",
                "semantic_intent_accuracy",
                "processing_plan_accuracy",
                "end_to_end_route_accuracy",
                "passed",
                "failed",
                "critical_underprocessing",
                "category_failures",
            )
        },
        "delta_vs_active_baseline": delta,
        "evidence_label": _evidence_label(delta, scored["gate"], action),
    }


def _write_markdown(report: dict[str, Any]) -> None:
    lines = [
        "# Intent Pruning Candidates Post Quarantine v1",
        "",
        "Diagnostic only. No corpus or quarantine file is modified.",
        "",
        "## Summary",
        "",
        f"- active quarantine entries: {report['active_quarantine']['entry_count']}",
        f"- active baseline examples: {report['active_baseline']['filtered_examples']}",
        f"- remaining suspect candidates: {report['summary']['remaining_candidate_count']}",
        f"- high priority candidates: {report['summary']['high_priority_count']}",
        f"- rewrite/anonymize path candidates: {report['summary']['rewrite_or_anonymize_count']}",
        f"- weak question candidates: {report['summary']['weak_question_count']}",
        "",
        "## Scenario Ablations",
        "",
        "| scenario | action | count | gate | kfold delta | route delta | failed delta | label |",
        "|---|---|---:|---|---:|---:|---:|---|",
    ]
    for scenario in report["scenario_ablations"]:
        delta = scenario["delta_vs_active_baseline"]
        gate = "pass" if scenario["gate"]["passed"] else "fail"
        lines.append(
            f"| {scenario['name']} | {scenario['recommended_action']} | {scenario['candidate_count']} | {gate} | "
            f"{delta['kfold_accuracy']:+.6f} | {delta['accumulation_end_to_end_accuracy']:+.6f} | "
            f"{delta['accumulation_failed']:+d} | {scenario['evidence_label']} |"
        )

    lines.extend([
        "",
        "## High Priority Rows",
        "",
        "| score | index | action | intent | flags | evidence | kfold delta | input |",
        "|---:|---:|---|---|---|---|---:|---|",
    ])
    for row in report["high_priority_rows"]:
        delta = row["individual_delta_vs_active_baseline"]
        lines.append(
            f"| {row['priority_score']} | {row['corpus_index']} | {row['recommended_action']} | {row['intent']} | "
            f"{','.join(row['flags'])} | {row['evidence_label']} | {delta['kfold_accuracy']:+.6f} | "
            f"{_short(row['input']).replace('|', '&#124;')} |"
        )

    lines.extend([
        "",
        "## Review Rule",
        "",
        "- `strong_prune_or_rewrite_candidate`: review first, then quarantine or rewrite/anonymize and retest.",
        "- `rewrite_candidate_not_delete_yet`: prefer anonymized/relabelled replacement over deletion.",
        "- `review_candidate_neutral_safe`: safe-looking but low evidence; hold for more samples.",
        "- `keep_until_more_evidence`: do not prune now.",
        "- Very short anchors should generally stay unless they have strong negative ablation evidence.",
    ])
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def main() -> None:
    if not SUSPECT_REVIEW_PATH.exists():
        raise FileNotFoundError("run build/review_intent_corpus_suspects.py first")

    corpus = _load(CORPUS_PATH)
    suspect_review = _load(SUSPECT_REVIEW_PATH)
    active = _active_quarantine_indices()
    active_baseline = impact._train_and_score([], corpus, active)

    remaining = [
        row
        for row in suspect_review["all_suspects"]
        if int(row["corpus_index"]) not in active
    ]
    for row in remaining:
        row["recommended_action"] = _action_for(row)
        row["priority_score"] = _base_priority(row)

    rewrite_rows = [row for row in remaining if row["recommended_action"] == "rewrite_or_anonymize_path_then_retest"]
    weak_rows = [row for row in remaining if row["recommended_action"] == "holdout_or_failure_memory_review"]
    review_rows = [row for row in remaining if row["recommended_action"] == "manual_review_for_ambiguity"]
    short_rows = [row for row in remaining if row["recommended_action"] == "keep_anchor_unless_ablation_strong"]
    high_priority = sorted(
        [row for row in remaining if row["priority_score"] >= 35],
        key=lambda row: (-row["priority_score"], int(row["corpus_index"])),
    )

    scenario_specs = [
        ("rewrite_or_anonymize_path", "Path/URL rows with directives; prefer rewriting/anonymizing before deletion.", "rewrite_or_anonymize_path_then_retest", rewrite_rows),
        ("weak_question_holdout", "Weak question suffix rows not already quarantined.", "holdout_or_failure_memory_review", weak_rows),
        ("manual_review_ambiguity", "Remaining generic review rows.", "manual_review_for_ambiguity", review_rows),
        ("very_short_anchor_control", "Very short anchors; control only, not a bulk prune recommendation.", "do_not_bulk_prune", short_rows),
        ("all_high_priority_remaining", "All remaining rows with priority_score >= 35.", "review_before_prune_or_rewrite", high_priority),
    ]
    scenario_ablations = [
        _scenario(name, description, action, rows, active, active_baseline, corpus)
        for name, description, action, rows in scenario_specs
        if rows
    ]

    individual_rows = []
    for row in high_priority:
        index = int(row["corpus_index"])
        scored = impact._train_and_score([], corpus, active | {index})
        delta = {
            "kfold_accuracy": round(scored["kfold"]["kfold_accuracy"] - active_baseline["kfold"]["kfold_accuracy"], 6),
            "kfold_macro_accuracy": round(scored["kfold"]["kfold_macro_accuracy"] - active_baseline["kfold"]["kfold_macro_accuracy"], 6),
            "accumulation_end_to_end_accuracy": round(
                scored["accumulation_route_eval"]["end_to_end_route_accuracy"]
                - active_baseline["accumulation_route_eval"]["end_to_end_route_accuracy"],
                6,
            ),
            "accumulation_failed": scored["accumulation_route_eval"]["failed"] - active_baseline["accumulation_route_eval"]["failed"],
            "critical_underprocessing": scored["accumulation_route_eval"]["critical_underprocessing"] - active_baseline["accumulation_route_eval"]["critical_underprocessing"],
        }
        item = {
            key: row[key]
            for key in ("corpus_index", "input", "intent", "source", "flags", "recommendation", "recommended_action", "priority_score")
        }
        item["individual_delta_vs_active_baseline"] = delta
        item["gate"] = scored["gate"]
        item["evidence_label"] = _evidence_label(delta, scored["gate"], row["recommended_action"])
        individual_rows.append(item)

    report = {
        "schema_version": "intent-pruning-candidates-post-quarantine.v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "policy": {
            "diagnostic_only": True,
            "sealed_fixtures_used": False,
            "writes_training_corpus": False,
            "writes_quarantine_overlay": False,
            "recommended_workflow": "human review -> quarantine/rewrite -> non-sealed replay -> rebuild/gate",
        },
        "inputs": {
            "corpus": str(CORPUS_PATH.relative_to(ROOT)),
            "active_quarantine": str(QUARANTINE_PATH.relative_to(ROOT)) if QUARANTINE_PATH.exists() else None,
            "suspect_review": str(SUSPECT_REVIEW_PATH.relative_to(ROOT)),
        },
        "active_quarantine": {
            "entry_count": len(active),
            "indices": sorted(active),
        },
        "active_baseline": {
            "filtered_examples": active_baseline["filtered_examples"],
            "filtered_by_intent": active_baseline["filtered_by_intent"],
            "gate": active_baseline["gate"],
            "kfold": active_baseline["kfold"],
            "accumulation_route_eval": {
                key: active_baseline["accumulation_route_eval"][key]
                for key in (
                    "case_count",
                    "reviewed_count",
                    "semantic_intent_accuracy",
                    "processing_plan_accuracy",
                    "end_to_end_route_accuracy",
                    "passed",
                    "failed",
                    "critical_underprocessing",
                    "category_failures",
                )
            },
        },
        "summary": {
            "remaining_candidate_count": len(remaining),
            "high_priority_count": len(high_priority),
            "rewrite_or_anonymize_count": len(rewrite_rows),
            "weak_question_count": len(weak_rows),
            "manual_review_count": len(review_rows),
            "very_short_anchor_count": len(short_rows),
        },
        "scenario_ablations": scenario_ablations,
        "high_priority_rows": individual_rows,
        "remaining_candidates": sorted(
            remaining,
            key=lambda row: (-row["priority_score"], int(row["corpus_index"])),
        ),
    }

    OUT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    _write_markdown(report)
    print(
        json.dumps(
            {
                "status": "wrote_intent_pruning_candidates_post_quarantine",
                "json": str(OUT_JSON.relative_to(ROOT)),
                "worksheet": str(OUT_MD.relative_to(ROOT)),
                "summary": report["summary"],
                "active_baseline_kfold": report["active_baseline"]["kfold"]["kfold_accuracy"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
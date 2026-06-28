"""Create a review worksheet for borderline intent-corpus examples.

The worksheet is diagnostic only. It does not change the corpus, the deployed
model, or any sealed fixture.
"""

import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CORPUS_PATH = ROOT / "data" / "intent_training_corpus_v1.json"
HARVEST_PATH = ROOT / "data" / "harvested_claudelog_v1.json"
OUT_MD = ROOT / "build" / "intent_corpus_suspect_review_v1.md"
OUT_JSON = ROOT / "build" / "intent_corpus_suspect_review_v1.json"

EXCLUDED_REFERENCES = {
    "こちらであってるでしょうか",
    "どうでしょう",
}
WEAK_QUESTION_SUFFIXES = (
    "どうでしょう",
    "どうですか",
    "あってますか",
    "合ってますか",
    "あってるでしょうか",
    "合ってるでしょうか",
    "使えますか",
    "できますか",
)
ACK_ONLY = {
    "ありがとうございます",
    "ありがとう",
    "了解",
    "はい",
    "ok",
    "okay",
    "thanks",
    "助かりました",
    "お願いします",
}
DIRECTIVE_MARKERS = (
    "お願いします",
    "ください",
    "して",
    "確認",
    "検証",
    "説明",
    "要約",
    "比較",
    "作",
    "進め",
    "実装",
    "読",
    "続き",
    "review",
    "check",
    "explain",
    "summarize",
    "compare",
    "build",
    "plan",
)


def _trim_punct(text: str) -> str:
    return text.strip().strip("？?！!。.! ")


def _has_path_or_url(text: str) -> bool:
    lowered = text.lower()
    return any(
        marker in lowered
        for marker in (
            "http://",
            "https://",
            "d:\\",
            "c:\\",
            "/mnt/",
            ".md",
            ".json",
            ".py",
        )
    )


def _is_weak_question(text: str) -> bool:
    trimmed = _trim_punct(text)
    return any(trimmed.endswith(suffix) for suffix in WEAK_QUESTION_SUFFIXES)


def _is_ack_only(text: str) -> bool:
    return _trim_punct(text).lower() in ACK_ONLY


def _has_directive(text: str) -> bool:
    lowered = text.lower()
    return any(marker in lowered for marker in DIRECTIVE_MARKERS)


def _flags(text: str) -> list[str]:
    flags = []
    if text in EXCLUDED_REFERENCES:
        flags.append("known_excluded_reference")
    if len(text.strip()) <= 8:
        flags.append("very_short_le_8")
    if _is_ack_only(text):
        flags.append("ack_only")
    if _is_weak_question(text) and len(text.strip()) <= 80:
        flags.append("weak_question_suffix")
    if _has_path_or_url(text):
        flags.append("path_or_url")
    if _has_path_or_url(text) and not _has_directive(text):
        flags.append("bare_path_or_url")
    return flags


def _recommendation(example: dict, flags: list[str]) -> str:
    if "known_excluded_reference" in flags:
        return "exclude"
    if "ack_only" in flags:
        return "exclude_or_negative"
    if "weak_question_suffix" in flags and example["intent"] in {
        "respond",
        "verify",
    }:
        return "exclude_or_negative"
    if "bare_path_or_url" in flags:
        return "exclude_or_relabel_clarify"
    if "path_or_url" in flags:
        return "keep_if_directive_but_anonymize_path"
    if "very_short_le_8" in flags:
        return "keep_if_intent_is_unambiguous"
    return "review"


def main() -> None:
    corpus = json.loads(CORPUS_PATH.read_text(encoding="utf-8"))
    harvest = json.loads(HARVEST_PATH.read_text(encoding="utf-8"))

    corpus_rows = []
    for index, example in enumerate(corpus["examples"], start=1):
        flags = _flags(example["input"])
        if not flags:
            continue
        corpus_rows.append(
            {
                "corpus_index": index,
                "input": example["input"],
                "intent": example["intent"],
                "source": example.get("source"),
                "flags": flags,
                "recommendation": _recommendation(example, flags),
            }
        )

    excluded_reference_rows = []
    for index, item in enumerate(harvest["examples"], start=1):
        text = item.get("input", "")
        if text in EXCLUDED_REFERENCES or "http://" in text or "https://" in text:
            excluded_reference_rows.append(
                {
                    "harvest_index": index,
                    "input": text,
                    "intent": item.get("intent"),
                    "review_status": item.get("review_status"),
                    "confidence": item.get("confidence"),
                    "calibration_exclude": item.get("calibration_exclude"),
                }
            )

    by_recommendation = Counter(row["recommendation"] for row in corpus_rows)
    by_flag = Counter(flag for row in corpus_rows for flag in row["flags"])
    by_intent = Counter(row["intent"] for row in corpus_rows)
    high_priority = [
        row
        for row in corpus_rows
        if row["recommendation"]
        in {"exclude", "exclude_or_negative", "exclude_or_relabel_clarify"}
    ]

    report = {
        "schema_version": "intent-corpus-suspect-review.v1",
        "corpus_path": str(CORPUS_PATH.relative_to(ROOT)),
        "harvest_path": str(HARVEST_PATH.relative_to(ROOT)),
        "summary": {
            "corpus_examples": len(corpus["examples"]),
            "suspect_count": len(corpus_rows),
            "high_priority_review_count": len(high_priority),
            "by_recommendation": dict(sorted(by_recommendation.items())),
            "by_flag": dict(sorted(by_flag.items())),
            "by_intent": dict(sorted(by_intent.items())),
        },
        "excluded_reference_rows": excluded_reference_rows,
        "high_priority_review": high_priority,
        "all_suspects": corpus_rows,
    }
    OUT_JSON.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    lines = [
        "# Intent Corpus Suspect Review v1",
        "",
        "Diagnostic only. No corpus/model/sealed files are modified.",
        "",
        "## Summary",
        "",
        f"- corpus examples: {len(corpus['examples'])}",
        f"- suspect examples: {len(corpus_rows)}",
        f"- high-priority review: {len(high_priority)}",
        f"- by recommendation: {dict(sorted(by_recommendation.items()))}",
        f"- by flag: {dict(sorted(by_flag.items()))}",
        "",
        "## Excluded Reference Check",
        "",
    ]
    if excluded_reference_rows:
        for row in excluded_reference_rows:
            lines.append(
                "- "
                f"harvest#{row['harvest_index']} "
                f"{row['intent']}/{row['review_status']} "
                f"calibration_exclude={row['calibration_exclude']} :: "
                f"{row['input']}"
            )
    else:
        lines.append("- no excluded references found in harvest file")

    lines.extend(["", "## High-Priority Review", ""])
    if high_priority:
        for row in high_priority:
            lines.append(
                "- "
                f"corpus#{row['corpus_index']} "
                f"[{row['intent']} / {row['source']}] "
                f"{row['recommendation']} "
                f"flags={','.join(row['flags'])} :: {row['input']}"
            )
    else:
        lines.append("- none")

    lines.extend(["", "## Path / URL Review", ""])
    for row in [r for r in corpus_rows if "path_or_url" in r["flags"]]:
        lines.append(
            "- "
            f"corpus#{row['corpus_index']} "
            f"[{row['intent']} / {row['source']}] "
            f"{row['recommendation']} :: {row['input']}"
        )

    lines.extend(["", "## Very Short Review", ""])
    for row in [r for r in corpus_rows if "very_short_le_8" in r["flags"]]:
        lines.append(
            "- "
            f"corpus#{row['corpus_index']} "
            f"[{row['intent']} / {row['source']}] "
            f"{row['recommendation']} :: {row['input']}"
        )

    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps(report["summary"], ensure_ascii=False, indent=2))
    print(f"wrote {OUT_MD.relative_to(ROOT)}")
    print(f"wrote {OUT_JSON.relative_to(ROOT)}")


if __name__ == "__main__":
    main()

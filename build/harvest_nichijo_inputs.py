"""Zero-touch offline observation of nichijo_jissou real user inputs.

Reads the input log that nichijo writes (D:\\nichijo_jissou\\logs\\
user_inputs.jsonl — INPUT text only, no LLM output), runs each line through
the FROZEN v0.3.1 router with its observability trace, and writes a
human-readable observation report. Pure observation: nichijo is untouched,
no model changes, LLM output never involved.

Output (readable text): build/nichijo_routing_observation.txt
  - per-input: intent / decided_by / margin / processing_class
  - summary by decided_by and by intent
  - LOW-MARGIN fallbacks highlighted = the exact inputs to target when a
    future successor corpus is collected (still human-approved, campaign-
    disjoint, never LLM output).
"""

import io
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

from semantic_routing import route
from semantic_routing.baseline import INTENT_GATE_MARGIN

INPUT_LOG = Path(r"D:\nichijo_jissou\logs\user_inputs.jsonl")
OUT = ROOT / "build" / "nichijo_routing_observation.txt"


def _load_inputs(path: Path):
    if not path.exists():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            d = json.loads(line)
            if d.get("text", "").strip():
                rows.append((d.get("ts", ""), d["text"]))
        except json.JSONDecodeError:
            continue
    return rows


def main() -> None:
    rows = _load_inputs(INPUT_LOG)
    lines = []
    lines.append("# nichijo_jissou — routing observation (frozen v0.3.1, zero-touch)")
    lines.append(f"# source: {INPUT_LOG}")
    lines.append(f"# inputs observed: {len(rows)} | gate margin: {INTENT_GATE_MARGIN}")
    lines.append("")

    if not rows:
        lines.append("(no inputs yet — the log fills as nichijo is used; re-run after a session)")
        OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
        print("\n".join(lines))
        return

    by_decided = Counter()
    by_intent = Counter()
    low_margin = []
    detail = []
    for ts, text in rows:
        r = route(text)
        intent = r.packet.primary_intent
        decided = r.trace.get("decided_by", "?")
        margin = r.trace.get("intent_margin")
        by_decided[decided] += 1
        by_intent[intent] += 1
        one_line = text.replace("\r", "").replace("\n", " ⏎ ").strip()
        mg = f"{margin:.3f}" if isinstance(margin, (int, float)) else "—"
        detail.append(
            f"  [{intent:8s} | {decided:8s} | {r.plan.processing_class:8s} "
            f"| margin {mg}] {one_line[:80]}"
        )
        # a fallback that nearly fired the learned layer = high-value target
        if decided == "fallback" and isinstance(margin, (int, float)) and margin > 0:
            low_margin.append((margin, intent, one_line))

    lines.append("## summary by decided_by")
    for d, n in sorted(by_decided.items()):
        lines.append(f"  {d:8s} {n}")
    lines.append("")
    lines.append("## summary by intent")
    for i, n in sorted(by_intent.items()):
        lines.append(f"  {i:8s} {n}")
    lines.append("")
    lines.append("## per-input")
    lines.extend(detail)
    lines.append("")
    lines.append("## near-miss fallbacks (markers silent, learned layer just under the gate)")
    lines.append("## = the inputs to target with future REAL human-approved data")
    if low_margin:
        for margin, intent, text in sorted(low_margin, reverse=True):
            lines.append(f"  margin {margin:.3f} (would-be {intent}?) {text[:80]}")
    else:
        lines.append("  (none)")

    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    print(f"\nreport -> {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()

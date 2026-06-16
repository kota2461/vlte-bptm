"""Extract ONLY the user's own utterances from a pasted chat-log dump.

The raw log mixes the user's messages with large blocks of AI-generated
content the user pasted in ("貰ってきました"). AI output must never become
training data, so this drops:
  - the contiguous AI-generated spec block (from "もちろんです。" through the
    spec's closing line),
  - code/JSON fences and bullet/heading spec fragments,
  - a small denylist of menu/title fragments that are not user utterances,
  - bare address tokens.
Blank-line-separated blocks are treated as one message each. The kept
messages are written one-per-line to build/incoming_logs.txt for ingest.
NOTHING here is labelled or merged; this is extraction only.
"""

import io
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

SRC = Path(sys.argv[1] if len(sys.argv) > 1 else r"C:\Users\kota\Desktop\テキストsample.txt")
OUT = ROOT / "build" / "incoming_logs.txt"

# contiguous AI-generated region markers (the pasted spec document)
AI_START = "もちろんです。"
AI_END = "self_repair/ フォルダ設計 v1.0 まで書けます。"

# exact menu/title fragments that are not user utterances
DENYLIST = {
    "他の無限小数のベンチマーク例",
    "y-cruncherの計算アルゴリズム詳細",
    "グローバル命令セットの詳細設計",
    "ΣΗ-CodeとTaskManagerをこの新仕様に合わせて調整した 全体アーキテクチャ更新版仕様書",
    "他の無限小数のベンチマーク例 y-cruncherの計算アルゴリズム詳細",
}

_ADDRESS_TOKEN = re.compile(r"^T\d+\.[\w\-]+@[\w\-]+$")


def main() -> None:
    if not SRC.exists():
        print(f"missing source: {SRC}")
        return
    lines = SRC.read_text(encoding="utf-8").splitlines()

    # 1) drop the contiguous AI spec region
    kept_lines, in_ai = [], False
    for ln in lines:
        if not in_ai and AI_START in ln:
            in_ai = True
            continue
        if in_ai:
            if AI_END in ln:
                in_ai = False
            continue
        kept_lines.append(ln)

    # 2) split into blank-line-separated blocks
    blocks, cur = [], []
    for ln in kept_lines:
        if ln.strip() == "":
            if cur:
                blocks.append(cur)
                cur = []
        else:
            cur.append(ln)
    if cur:
        blocks.append(cur)

    # 3) clean each block -> one message; drop spec-like / denylisted ones
    messages, dropped = [], []
    for blk in blocks:
        # drop bare address-token lines inside the block
        body = [l for l in blk if not _ADDRESS_TOKEN.match(l.strip())]
        raw = "\n".join(body)
        msg = " ".join(raw.split()).strip()
        if not msg:
            continue
        if msg in DENYLIST:
            dropped.append(("denylist", msg))
            continue
        if "```" in raw or msg.startswith("{") or msg.startswith("* "):
            dropped.append(("spec-fragment", msg[:50]))
            continue
        messages.append(msg)

    OUT.write_text("\n".join(messages) + "\n", encoding="utf-8")
    print(f"kept {len(messages)} user messages -> {OUT.relative_to(ROOT)}")
    print(f"dropped {len(dropped)} non-user blocks "
          f"(AI spec region excluded separately)\n")
    for i, m in enumerate(messages, 1):
        print(f"  {i:2d}. {m[:90]}")
    if dropped:
        print("\ndropped fragments:")
        for kind, d in dropped:
            print(f"  [{kind}] {d}")


if __name__ == "__main__":
    main()

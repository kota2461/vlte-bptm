"""Harvest genuine human utterances from Claude Code session transcripts.

Reads the JSONL transcripts under ``~/.claude/projects/<project>/`` for the
implementation repositories, keeps only self-contained, intent-bearing human
messages, deduplicates them, tags language, and writes an UNLABELED candidate
pool. A second pass (human/AI review) assigns one of the 7 router intents.

This script never writes into the sealed conversation-accumulation campaign;
its output is a fresh candidate pool for the intent training corpus only.

Usage:
    python scripts/harvest_claudelog.py --out build/claudelog_pool_v1.json
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import re
from typing import Dict, List, Optional

PROJECTS_ROOT = os.path.expanduser("~/.claude/projects")

# Implementation repositories worth mining (build/verify-rich).
PROJECT_DIRS = (
    "D--pseudo-personality",
    "D--Hybrid-PC-AI--claude-worktrees-epic-sutherland-3df9b7",
    "D--Hybrid-PC-AI--claude-worktrees-nice-lederberg-7e5e3e",
    "D--keywordmodel--claude-worktrees-sad-haslett-dd41e5",
    "D--Topic-packaging",
    "D--Thought-State-Register-thought-state-register-egg-info",
)

_KANA = re.compile(r"[぀-ヿ一-龯]")
_ASCII_ALPHA = re.compile(r"[A-Za-z]")
# Markers of pasted logs / stack traces / code rather than a typed request.
_NOISE_MARKERS = (
    "Traceback (most recent call last)",
    "File \"",
    "➜",  # ➜ shell prompt
    "PS D:",
    "PS C:",
    "INFO:",
    "HTTP Request:",
    "self.gen.throw",
    "raise ",
    "Error 22",
)
# Short confirmations / acks: real but not intent-bearing for routing.
_ACK_PAT = re.compile(
    r"^(ok|okay|yes|no|うん|はい|いいえ|了解|りょうかい|ありがと|ありがとう|"
    r"thanks|thx|お願いします|おねがいします|お願い|頼みます|それで|"
    r"そうして|進めて|やって|お願いします！|いいよ|いいね|good|nice)"
    r"[。！!\s]*$",
    re.IGNORECASE,
)
# Pure option-pick confirmations like "B でお願いします", "1.で", "Aです".
_PICK_PAT = re.compile(r"^[A-Ea-e1-9][\s.、。)）でだ]")


def _detect_language(text: str) -> str:
    has_ja = bool(_KANA.search(text))
    has_en = bool(_ASCII_ALPHA.search(text))
    if has_ja and has_en:
        # Mostly-Japanese with a few latin tokens still counts as ja.
        latin = len(_ASCII_ALPHA.findall(text))
        return "mixed" if latin > len(text) * 0.4 else "ja"
    if has_ja:
        return "ja"
    if has_en:
        return "en"
    return "unknown"


def _extract_text(message: object) -> Optional[str]:
    if not isinstance(message, dict):
        return None
    content = message.get("content")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, dict) and block.get("type") == "text":
                parts.append(block.get("text") or "")
        return "\n".join(p for p in parts if p)
    return None


def _is_noise(text: str) -> bool:
    t = text.strip()
    if not t:
        return True
    if t.startswith("<") or t.startswith("[") or t.startswith("{"):
        return True  # tool_result / command wrappers / system tags / json
    if "system-reminder" in t or "<command-" in t or "<local-command" in t:
        return True
    if t.startswith("Caveat:") or t.startswith("This session is being"):
        return True
    if any(marker in t for marker in _NOISE_MARKERS):
        return True
    if _ACK_PAT.match(t) or _PICK_PAT.match(t):
        return True
    # Reject very long pastes and single-token noise.
    if len(t) > 240 or len(t) < 4:
        return True
    # Reject things that are mostly code/punctuation (low letter ratio).
    letters = len(_KANA.findall(t)) + len(_ASCII_ALPHA.findall(t))
    if letters < len(t) * 0.4:
        return True
    return False


def harvest(projects_root: str) -> List[Dict[str, object]]:
    seen = set()
    pool: List[Dict[str, object]] = []
    for project in PROJECT_DIRS:
        base = os.path.join(projects_root, project)
        # Top-level session transcripts only; skip subagents/ (agent-to-agent).
        files = [
            f
            for f in glob.glob(os.path.join(base, "**", "*.jsonl"), recursive=True)
            if os.sep + "subagents" + os.sep not in f
        ]
        for path in files:
            try:
                handle = open(path, encoding="utf-8")
            except OSError:
                continue
            with handle:
                for line in handle:
                    try:
                        obj = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    if obj.get("type") != "user":
                        continue
                    if obj.get("isMeta") or obj.get("isSidechain"):
                        continue
                    text = _extract_text(obj.get("message"))
                    if not text:
                        continue
                    text = text.strip()
                    if _is_noise(text):
                        continue
                    norm = re.sub(r"\s+", " ", text)
                    key = norm.lower()
                    if key in seen:
                        continue
                    seen.add(key)
                    pool.append(
                        {
                            "input": norm,
                            "language": _detect_language(norm),
                            "project": project,
                            "intent": None,  # filled by the labeling pass
                            "review_status": "pending",
                            "source": "claudelog-harvest",
                        }
                    )
    return pool


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--projects-root", default=PROJECTS_ROOT)
    parser.add_argument("--out", default="build/claudelog_pool_v1.json")
    args = parser.parse_args()

    pool = harvest(args.projects_root)
    by_lang: Dict[str, int] = {}
    by_project: Dict[str, int] = {}
    for item in pool:
        by_lang[item["language"]] = by_lang.get(item["language"], 0) + 1
        by_project[item["project"]] = by_project.get(item["project"], 0) + 1

    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    payload = {
        "schema_version": "intent-training-corpus.harvest.v1",
        "note": (
            "Unlabeled candidate pool harvested from Claude Code transcripts. "
            "Each item needs an intent label from the 7 router intents before "
            "it can enter the training corpus. Not for the sealed eval set."
        ),
        "counts": {
            "total": len(pool),
            "by_language": by_lang,
            "by_project": by_project,
        },
        "examples": pool,
    }
    with open(args.out, "w", encoding="utf-8") as out:
        json.dump(payload, out, ensure_ascii=False, indent=2)

    print(f"wrote {len(pool)} candidates -> {args.out}")
    print("by_language:", by_lang)
    print("by_project:", by_project)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

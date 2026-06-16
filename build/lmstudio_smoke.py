"""End-to-end smoke via the runtime entry: route_and_execute() -> LM Studio.

Confirms the single production entry point drives a real backend: route()
-> tier model (select_model) -> token budget (executor) -> external LLM ->
parsed reply. LM Studio is an OpenAI-compatible EXTERNAL executor, kept
OUTSIDE thought_core / the routing core; its output is printed for the smoke
and NOT persisted as training data.
"""

import io
import json
import sys
import urllib.error
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

from semantic_routing import (
    lmstudio_available_models,
    lmstudio_chat_fn,
    route_and_execute,
)

BASE = "http://192.168.10.124:1234"
TESTS = [
    "こんにちは",                                  # -> direct (no LLM)
    "ありがとう！",                                # -> direct (no LLM)
    "なぜ空は青いのか教えて",                       # -> LLM
    "この計算が合っているか確認して: 12 + 7 = 20",  # -> LLM + calculator
    "新しいPCのセットアップ手順を作って",           # -> LLM
]


def main() -> None:
    try:
        models = lmstudio_available_models(BASE)
    except (urllib.error.URLError, OSError) as e:
        print(f"UNREACHABLE: {BASE} -> {e}")
        return
    print("connected. models:", models or "(none reported)")
    if not models:
        print("no model loaded in LM Studio; load one and retry.")
        return

    chat_fn = lmstudio_chat_fn(BASE)
    results = []
    for text in TESTS:
        try:
            r = route_and_execute(text, chat_fn=chat_fn, available_models=models)
            print(f"\n[{r.intent}/{r.plan.processing_class} | {r.plan.model_class}"
                  f" -> {r.model}] {text}")
            print(f"  (finish={r.finish_reason}, via={r.via}, "
                  f"max_tokens={r.request_max_tokens})")
            print(f"  -> {r.text[:240]}")
            results.append(r.as_dict() | {"input": text, "text": None})
        except (urllib.error.URLError, OSError, KeyError, IndexError, ValueError) as e:
            print(f"\n[{text}] ERROR: {e}")
            results.append({"input": text, "error": str(e)})

    (ROOT / "build" / "lmstudio_smoke_report.json").write_text(
        json.dumps(
            {"note": "runtime end-to-end smoke; LLM output NOT training data",
             "base": BASE, "results": results},
            ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print("\nOK: routed + executed via route_and_execute. "
          "report -> build/lmstudio_smoke_report.json")


if __name__ == "__main__":
    main()

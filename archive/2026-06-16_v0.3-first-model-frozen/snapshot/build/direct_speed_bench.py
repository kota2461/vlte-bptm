"""Speed: router (direct short-circuit) vs no-router (straight to the LLM).

The point of the direct path: with a heavy *reasoning* backend, even a
greeting makes the model think for seconds. The router recognises trivial
smalltalk (respond/economy) and answers locally with zero LLM calls. This
bench measures both for the same inputs and reports the speedup.

  no-router : send the text straight to the reasoning model (what happens if
              the router is bypassed / not present)
  router    : route_and_execute(text) -- greetings short-circuit (via=direct,
              no LLM); real questions still go to the LLM (router overhead is
              the only addition)

External LLM stays OUTSIDE thought_core; output is printed only, never stored
as training data.
"""

import io
import json
import sys
import time
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
HEAVY_MODEL = "google/gemma-4-12b-qat"  # a reasoning ("heavy thinking") model

GREETINGS = ["こんにちは", "ありがとう！", "おはよう"]
QUESTION = "なぜ空は青いのか教えて"


def main() -> None:
    try:
        models = lmstudio_available_models(BASE)
    except (urllib.error.URLError, OSError) as e:
        print(f"UNREACHABLE: {BASE} -> {e}")
        return
    chat_fn = lmstudio_chat_fn(BASE)
    model = HEAVY_MODEL if HEAVY_MODEL in models else models[0]
    print(f"heavy backend: {model}\n")

    def no_router(text: str) -> float:
        """Bypass the router: greeting straight to the reasoning model."""
        t = time.perf_counter()
        chat_fn(
            model=model,
            messages=[
                {"role": "system", "content": "Answer concisely in the user's language."},
                {"role": "user", "content": text},
            ],
            max_tokens=1024,
            temperature=0.3,
        )
        return time.perf_counter() - t

    def via_router(text: str):
        t = time.perf_counter()
        r = route_and_execute(text, chat_fn=chat_fn, available_models=models)
        return time.perf_counter() - t, r

    def _short(model_id: str) -> str:
        # drop the "google/" vendor prefix for a compact public-facing label
        return model_id.split("/", 1)[-1]

    rows = []
    print(f"{'input':<16} {'no-router (model)':<34} "
          f"{'router (model)':<30} {'speedup':>9}")
    for text in GREETINGS + [QUESTION]:
        nr = no_router(text)
        rt, r = via_router(text)
        speedup = nr / rt if rt > 0 else float("inf")
        speed_str = f"{speedup:>6.0f}x" if speedup < 1e6 else "   huge"
        router_model = "direct / no LLM" if r.via == "direct" else _short(r.model)
        nr_cell = f"{nr:6.2f}s ({_short(model)})"
        rt_cell = f"{rt:8.4f}s ({router_model})"
        print(f"{text:<16} {nr_cell:<34} {rt_cell:<30} {speed_str:>9}")
        rows.append({
            "input": text,
            "no_router": {"seconds": round(nr, 3), "model": model},
            "router": {"seconds": round(rt, 4), "via": r.via, "model": r.model},
            "speedup": round(speedup, 1),
        })

    (ROOT / "build" / "direct_speed_bench_report.json").write_text(
        json.dumps({"note": "router vs no-router speed; LLM output NOT training data",
                    "base": BASE, "heavy_model": model, "results": rows},
                   ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print("\nreport -> build/direct_speed_bench_report.json")


if __name__ == "__main__":
    main()

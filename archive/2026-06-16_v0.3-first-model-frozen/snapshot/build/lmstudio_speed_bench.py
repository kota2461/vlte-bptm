"""Response-speed comparison on a problem that takes some thinking.

Measures two things, separately, under identical conditions:
  (1) adapter overhead  -- route() latency on its own (averaged over N runs)
  (2) LLM latency       -- per chat model in LM Studio: wall time, tokens,
                           reasoning tokens, tokens/sec, finish_reason.

Same external-executor boundary: the LLM lives OUTSIDE thought_core and its
output is printed/reported only -- never persisted as training data.
"""

import io
import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

from semantic_routing import route

BASE = "http://192.168.10.124:1234"
INSTRUCTION = {
    "respond": "Answer directly and concisely.",
    "explain": "Explain the reason or mechanism clearly.",
    "build": "Produce concrete, ordered steps.",
    "verify": "Check correctness and state what you verified.",
    "summarize": "Summarize concisely.",
    "explore": "Offer a few distinct options with trade-offs.",
    "clarify": "Ask only for the missing information needed to proceed.",
}

# A genuinely time-consuming reasoning problem (multi-step counting + proof).
PROBLEM = (
    "3桁の正の整数のうち、各位の数字の和が9の倍数で、かつ7で割り切れるものは"
    "全部でいくつあるか、理由とともに求めてください。"
)

# Chat-capable models to compare (skip the embedding model).
CANDIDATE_MODELS = [
    "google/gemma-4-e4b",
    "google/gemma-3-12b",
    "google/gemma-4-12b",
    "google/gemma-4-12b-qat",
]
MAX_TOKENS = 2048


def _get(path, timeout):
    req = urllib.request.Request(BASE + path, headers={"Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _post(path, payload, timeout):
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        BASE + path, data=data,
        headers={"Content-Type": "application/json"}, method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def main() -> None:
    try:
        models = _get("/v1/models", timeout=8)
    except (urllib.error.URLError, OSError) as e:
        print(f"UNREACHABLE: {BASE} -> {e}")
        return
    available = {m["id"] for m in models.get("data", [])}
    models_to_test = [m for m in CANDIDATE_MODELS if m in available]
    print(f"available chat models: {models_to_test}\n")

    # (1) adapter overhead -- pure routing, no network
    N = 200
    t0 = time.perf_counter()
    for _ in range(N):
        r = route(PROBLEM)
    adapter_ms = (time.perf_counter() - t0) / N * 1000.0
    intent = r.packet.primary_intent
    pclass = r.plan.processing_class
    mode = r.plan.core_mode
    print(f"PROBLEM: {PROBLEM}")
    print(f"routed  : intent={intent}, processing={pclass}, mode={mode}")
    print(f"adapter : {adapter_ms:.3f} ms / call (avg of {N})\n")

    system = (
        f"[routing] intent={intent}, processing={pclass}, mode={mode}. "
        f"{INSTRUCTION.get(intent, '')} Respond in the user's language."
    )

    rows = []
    for model_id in models_to_test:
        try:
            t = time.perf_counter()
            out = _post("/v1/chat/completions", {
                "model": model_id,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": PROBLEM},
                ],
                "temperature": 0.3,
                "max_tokens": MAX_TOKENS,
            }, timeout=600)
            elapsed = time.perf_counter() - t
            choice = out["choices"][0]
            msg = choice["message"]
            finish = choice.get("finish_reason")
            content = (msg.get("content") or "").strip()
            if not content and msg.get("reasoning_content"):
                content = "[reasoning-only] " + msg["reasoning_content"].strip()
            usage = out.get("usage", {})
            ctok = usage.get("completion_tokens", 0)
            rtok = usage.get("completion_tokens_details", {}).get("reasoning_tokens", 0)
            tps = ctok / elapsed if elapsed > 0 else 0.0
            rows.append({
                "model": model_id, "seconds": round(elapsed, 1),
                "completion_tokens": ctok, "reasoning_tokens": rtok,
                "tokens_per_sec": round(tps, 1), "finish_reason": finish,
                "reply_chars": len(content),
            })
            print(f"[{model_id}]")
            print(f"  {elapsed:6.1f}s | {ctok:5d} tok ({rtok} reasoning) "
                  f"| {tps:5.1f} tok/s | finish={finish}")
            print(f"  -> {content[:200]}\n")
        except (urllib.error.URLError, OSError, KeyError, IndexError) as e:
            print(f"[{model_id}] ERROR: {e}\n")
            rows.append({"model": model_id, "error": str(e)})

    print("=== summary (sorted by wall time) ===")
    ok = [r for r in rows if "seconds" in r]
    for r in sorted(ok, key=lambda x: x["seconds"]):
        print(f"  {r['seconds']:6.1f}s  {r['tokens_per_sec']:5.1f} tok/s  "
              f"{r['completion_tokens']:5d} tok  {r['model']}")

    (ROOT / "build" / "lmstudio_speed_bench_report.json").write_text(
        json.dumps(
            {"note": "speed benchmark; LLM output NOT persisted as training data",
             "base": BASE, "problem": PROBLEM,
             "routed": {"intent": intent, "processing_class": pclass, "core_mode": mode},
             "adapter_ms_per_call": round(adapter_ms, 3),
             "max_tokens": MAX_TOKENS, "models": rows},
            ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print("\nreport -> build/lmstudio_speed_bench_report.json")


if __name__ == "__main__":
    main()

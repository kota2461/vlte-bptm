"""Per-processing-class response check on a time-consuming problem.

Same problem, same model (fixed to isolate the class variable), but each
run uses the class's CONTRACT output-token budget from processing_plan.py:
    economy 384 / standard 768 / verified 1024 / deep 1536 / clarify 256.

Goal: show, per class, whether a normal (non-empty, correct) answer comes
back. Reasoning models spend tokens thinking first, so the small-budget
classes may truncate (finish=length) and return empty content -- that is
the finding, not a bug.

External-executor boundary held: LLM output printed/reported, never stored
as training data.
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

from semantic_routing.executor import (
    looks_like_reasoning_model,
    resolve_request_budget,
)
from semantic_routing.processing_plan import (
    ProcessingBudget,
    ProcessingPlan,
)

BASE = "http://192.168.10.124:1234"
MODEL = "google/gemma-4-12b-qat"  # fastest + correct from the model bench

PROBLEM = (
    "3桁の正の整数のうち、各位の数字の和が9の倍数で、かつ7で割り切れるものは"
    "全部でいくつあるか、理由とともに求めてください。"
)
CORRECT_ANSWER = "14"  # 63の倍数 126..945 → 14個

# (class, max_output_tokens, core_mode, model_class, instruction)
# Budgets mirror semantic_routing/processing_plan.py per-class contract.
CLASSES = [
    ("economy", 384, "horizontal", "small",
     "Answer directly and concisely."),
    ("standard", 768, "horizontal", "standard",
     "Explain the reason or mechanism clearly."),
    ("verified", 1024, "vertical", "standard",
     "Check correctness and state what you verified. Show the reasoning."),
    ("deep", 1536, "hybrid", "large",
     "Reason through the problem fully and justify the count."),
]


def _post(path, payload, timeout):
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        BASE + path, data=data,
        headers={"Content-Type": "application/json"}, method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def main() -> None:
    print(f"model fixed: {MODEL}")
    print(f"PROBLEM: {PROBLEM}")
    print(f"(correct answer = {CORRECT_ANSWER}個)\n")

    reasoning = looks_like_reasoning_model(MODEL)
    print(f"reasoning model? {reasoning}  (direction-1: content budget + reasoning allowance)\n")

    rows = []
    for pclass, max_tok, mode, mclass, instr in CLASSES:
        system = (
            f"[routing] intent=explain, processing={pclass}, mode={mode}, "
            f"model_class={mclass}. {instr} Respond in the user's language."
        )
        # Direction (1): keep the contract content budget, add reasoning room.
        plan = ProcessingPlan(
            primary_route="explain", processing_class=pclass, core_mode=mode,
            model_class=mclass, tools=(),
            budgets=ProcessingBudget(
                max_dispatches=1, max_output_tokens=max_tok,
                timeout_ms=20000, estimated_cost_units=1.0,
            ),
            fallback="clarify", reason_codes=("bench",),
        )
        req = resolve_request_budget(plan, reasoning=reasoning)
        try:
            t = time.perf_counter()
            out = _post("/v1/chat/completions", {
                "model": MODEL,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": PROBLEM},
                ],
                "temperature": 0.3,
                "max_tokens": req.request_max_tokens,
            }, timeout=600)
            elapsed = time.perf_counter() - t
            choice = out["choices"][0]
            msg = choice["message"]
            finish = choice.get("finish_reason")
            content = (msg.get("content") or "").strip()
            usage = out.get("usage", {})
            ctok = usage.get("completion_tokens", 0)
            rtok = usage.get("completion_tokens_details", {}).get("reasoning_tokens", 0)
            answered = bool(content)
            correct = CORRECT_ANSWER in content if content else False
            verdict = ("✓正答" if correct else
                       "△本文あり/答え不明" if answered else "✗空(本文に未到達)")
            rows.append({
                "class": pclass, "content_budget": max_tok,
                "request_max_tokens": req.request_max_tokens,
                "reasoning_allowance": req.reasoning_allowance,
                "seconds": round(elapsed, 1),
                "completion_tokens": ctok, "reasoning_tokens": rtok,
                "finish_reason": finish, "answered": answered,
                "correct": correct, "reply_chars": len(content),
            })
            print(f"[{pclass:8s} | content {max_tok:4d} +reason {req.reasoning_allowance} "
                  f"= req {req.request_max_tokens:4d}]  "
                  f"{elapsed:6.1f}s | {ctok:4d} tok ({rtok} reasoning) | "
                  f"finish={finish:6s} | {verdict}")
            print(f"  -> {(content[:160] or '(empty)')}\n")
        except (urllib.error.URLError, OSError, KeyError, IndexError) as e:
            print(f"[{pclass}] ERROR: {e}\n")
            rows.append({"class": pclass, "budget_tokens": max_tok, "error": str(e)})

    print("=== summary ===")
    for r in rows:
        if "error" in r:
            print(f"  {r['class']:8s}  ERROR")
            continue
        state = ("正答" if r["correct"] else
                 "本文ありだが答え不明" if r["answered"] else "空(未到達)")
        print(f"  {r['class']:8s} content {r['content_budget']:4d} "
              f"req {r['request_max_tokens']:4d}  "
              f"{r['seconds']:5.1f}s  finish={r['finish_reason']:6s}  -> {state}")

    (ROOT / "build" / "lmstudio_class_bench_report.json").write_text(
        json.dumps(
            {"note": "per-class response check; LLM output NOT training data",
             "base": BASE, "model": MODEL, "problem": PROBLEM,
             "correct_answer": CORRECT_ANSWER, "classes": rows},
            ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print("\nreport -> build/lmstudio_class_bench_report.json")


if __name__ == "__main__":
    main()

"""Debug one LM Studio chat completion: dump the raw response to see where
the text is (content vs reasoning) and the finish_reason."""

import io
import json
import sys
import urllib.request

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
BASE = "http://192.168.10.124:1234"
MODEL = "google/gemma-4-12b-qat"


def post(payload):
    req = urllib.request.Request(
        BASE + "/v1/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}, method="POST",
    )
    with urllib.request.urlopen(req, timeout=90) as r:
        return json.loads(r.read().decode("utf-8"))


def main() -> None:
    print("=== with system role, max_tokens 160 ===")
    out = post({
        "model": MODEL,
        "messages": [
            {"role": "system", "content": "Answer concisely in Japanese."},
            {"role": "user", "content": "なぜ空は青いのか教えて"},
        ],
        "temperature": 0.3, "max_tokens": 160,
    })
    print(json.dumps(out, ensure_ascii=False, indent=2)[:1800])

    print("\n=== no system role, max_tokens 300 ===")
    out2 = post({
        "model": MODEL,
        "messages": [{"role": "user", "content": "なぜ空は青いのか短く教えて"}],
        "temperature": 0.3, "max_tokens": 300,
    })
    msg = out2["choices"][0]["message"]
    print("keys:", list(msg.keys()), "| finish:", out2["choices"][0].get("finish_reason"))
    print("content:", repr(msg.get("content"))[:600])
    if "reasoning_content" in msg:
        print("reasoning_content:", repr(msg["reasoning_content"])[:300])


if __name__ == "__main__":
    main()

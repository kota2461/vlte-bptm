import argparse
import json
from typing import Optional, Sequence

from .engine import process


DEFAULT_INPUT = (
    "新しい思考モデルを考えました。64bitの状態レジスタとして整理してください。"
)


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Thought State Register v0.1")
    parser.add_argument("text", nargs="*", help="Input text to encode")
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print the complete result as JSON",
    )
    args = parser.parse_args(argv)
    user_input = " ".join(args.text).strip() or DEFAULT_INPUT
    result = process(user_input)

    if args.json:
        # ASCII-only JSON remains parseable when Windows shells decode pipes
        # with a legacy code page.
        print(json.dumps(result.as_dict(), ensure_ascii=True, indent=2))
        return 0

    print("=== Thought State ===")
    print(result.state.hex())
    print("\n=== Active Bits ===")
    for layer, names in result.state.active_by_layer().items():
        print(f"{layer:9}: {', '.join(names) or '-'}")
    print("\n=== Mode ===")
    print(result.mode)
    print("\n=== Trace ===")
    for step in result.trace:
        additions = ", ".join(step.activated) or "-"
        removals = ", ".join(step.cleared) or "-"
        print(f"{step.stage:20} +[{additions}] -[{removals}]")
    print("\n=== LLM Order ===")
    print(json.dumps(result.order, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

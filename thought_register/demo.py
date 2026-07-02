import argparse
import json
from typing import Optional, Sequence

from .engine import process
from .journal import ThoughtJournal


DEFAULT_INPUT = (
    "新しい思考モデルを考えました。64bitの状態レジスタとして整理してください。"
)


def _print_result(result) -> None:
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


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Thought State Register v0.1")
    parser.add_argument("text", nargs="*", help="Input text to encode")
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print the complete result as JSON",
    )
    parser.add_argument(
        "--session",
        action="store_true",
        help=(
            "Treat each positional argument as one turn of a session and "
            "run them through a shared thought journal (revisit / loop / "
            "continuity feedback)"
        ),
    )
    args = parser.parse_args(argv)

    if args.session:
        inputs = [text for text in args.text if text.strip()] or [DEFAULT_INPUT]
        journal = ThoughtJournal()
        results = [process(text, journal=journal) for text in inputs]
        if args.json:
            payload = {
                "turns": [result.as_dict() for result in results],
                "journal": journal.as_dict(),
            }
            print(json.dumps(payload, ensure_ascii=True, indent=2))
            return 0
        for turn, (text, result) in enumerate(zip(inputs, results)):
            print(f"\n########## turn {turn}: {text}")
            _print_result(result)
        return 0

    user_input = " ".join(args.text).strip() or DEFAULT_INPUT
    result = process(user_input)

    if args.json:
        # ASCII-only JSON remains parseable when Windows shells decode pipes
        # with a legacy code page.
        print(json.dumps(result.as_dict(), ensure_ascii=True, indent=2))
        return 0

    _print_result(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

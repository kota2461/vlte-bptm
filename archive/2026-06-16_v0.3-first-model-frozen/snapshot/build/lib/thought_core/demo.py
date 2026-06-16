import argparse
import json
import logging
from typing import Optional, Sequence

from .encoder import THRESHOLD_PROFILES
from .pipeline import process


DEFAULT_INPUT = "VLTE-BPTM v1.0a の最小実装を検証してください"


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="VLTE-BPTM v1.0a demo")
    parser.add_argument("text", nargs="*", help="Input text")
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print the complete pipeline result as JSON",
    )
    parser.add_argument(
        "--log-level",
        default="WARNING",
        choices=("DEBUG", "INFO", "WARNING", "ERROR"),
    )
    parser.add_argument(
        "--threshold-profile",
        choices=tuple(THRESHOLD_PROFILES),
        help="Override automatic active-bit density profile",
    )
    args = parser.parse_args(argv)
    logging.basicConfig(level=getattr(logging, args.log_level))

    user_input = " ".join(args.text).strip() or DEFAULT_INPUT
    result = process(user_input, threshold_profile=args.threshold_profile)
    payload = result.as_dict()

    if args.json:
        print(json.dumps(payload, ensure_ascii=True, indent=2))
        return 0

    print("Input -> active_bits -> selected_units -> action_vector -> llm_order")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

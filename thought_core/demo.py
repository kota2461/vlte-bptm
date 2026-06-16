import argparse
import json
import logging
from pathlib import Path
from typing import Optional, Sequence

from .encoder import THRESHOLD_PROFILES
from .pipeline import process


DEFAULT_INPUT = "VLTE-BPTM v1.6 の実装を検証してください"


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="VLTE-BPTM v1.6 demo")
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
    parser.add_argument(
        "--processing-mode",
        choices=("horizontal", "vertical", "hybrid"),
        default="horizontal",
        help="Choose horizontal, vertical, or hybrid processing",
    )
    parser.add_argument(
        "--vertical-outputs-file",
        type=Path,
        help=(
            "JSON object containing already validated vertical unit outputs"
        ),
    )
    parser.add_argument(
        "--hybrid-outputs-file",
        type=Path,
        help=(
            "JSON object keyed by Hybrid stack id and then vertical unit id"
        ),
    )
    args = parser.parse_args(argv)
    logging.basicConfig(level=getattr(logging, args.log_level))

    user_input = " ".join(args.text).strip() or DEFAULT_INPUT
    vertical_outputs = None
    hybrid_outputs = None
    if args.vertical_outputs_file is not None:
        if args.processing_mode != "vertical":
            parser.error(
                "--vertical-outputs-file requires --processing-mode vertical"
            )
        vertical_outputs = json.loads(
            args.vertical_outputs_file.read_text(encoding="utf-8")
        )
        if not isinstance(vertical_outputs, dict):
            parser.error("--vertical-outputs-file must contain a JSON object")
    if args.hybrid_outputs_file is not None:
        if args.processing_mode != "hybrid":
            parser.error(
                "--hybrid-outputs-file requires --processing-mode hybrid"
            )
        hybrid_outputs = json.loads(
            args.hybrid_outputs_file.read_text(encoding="utf-8")
        )
        if not isinstance(hybrid_outputs, dict):
            parser.error("--hybrid-outputs-file must contain a JSON object")
    result = process(
        user_input,
        threshold_profile=args.threshold_profile,
        processing_mode=args.processing_mode,
        vertical_outputs=vertical_outputs,
        hybrid_outputs=hybrid_outputs,
    )
    payload = result.as_dict()

    if args.json:
        print(json.dumps(payload, ensure_ascii=True, indent=2))
        return 0

    stages = (
        "Input -> active_bits -> selected_units -> horizontal_mesh"
        + (
            " -> vertical_stack"
            if args.processing_mode == "vertical"
            else ""
        )
        + (
            " -> hybrid_stack_mesh"
            if args.processing_mode == "hybrid"
            else ""
        )
        + " -> action_vector -> llm_order"
    )
    print(stages)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

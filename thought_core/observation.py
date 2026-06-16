import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence

from .encoder import THRESHOLD_PROFILES
from .pipeline import PIPELINE_VERSION, process
from .state import PipelineState
from .units import DEFAULT_UNITS


OBSERVATION_SCHEMA_VERSION = "vlte-bptm.observation-report.v1"
THRESHOLD_COMPARISON_SCHEMA_VERSION = (
    "vlte-bptm.threshold-profile-report.v1"
)


def _counter_payload(counter: Counter[Any], total: int) -> Dict[str, Any]:
    items = sorted(
        counter.items(),
        key=lambda item: (
            isinstance(item[0], str),
            item[0],
        ),
    )
    return {
        str(key): {
            "count": count,
            "rate": round(count / total, 6) if total else 0.0,
        }
        for key, count in items
    }


class ObservationAccumulator:
    """Aggregate routing metadata without retaining input or LLM output."""

    def __init__(self) -> None:
        self.sample_count = 0
        self.active_bit_frequency: Counter[int] = Counter()
        self.active_bit_count_distribution: Counter[int] = Counter()
        self.selected_unit_frequency: Counter[str] = Counter()
        self.selected_unit_combination_frequency: Counter[str] = Counter()
        self.selected_unit_count_distribution: Counter[int] = Counter()
        self.threshold_profile_frequency: Counter[str] = Counter()
        self.mode_frequency: Counter[str] = Counter()

    def observe(self, state: PipelineState) -> None:
        self.sample_count += 1
        self.active_bit_frequency.update(state.active_bits)
        self.active_bit_count_distribution[len(state.active_bits)] += 1
        selected_ids = sorted(unit.unit_id for unit in state.selected_units)
        self.selected_unit_frequency.update(selected_ids)
        self.selected_unit_combination_frequency[
            "+".join(selected_ids) if selected_ids else "(none)"
        ] += 1
        self.selected_unit_count_distribution[len(selected_ids)] += 1
        self.threshold_profile_frequency[state.metrics.threshold_profile] += 1
        self.mode_frequency[state.llm_order["mode"]] += 1

    def as_dict(self) -> Dict[str, Any]:
        unit_frequency = Counter(
            {unit.unit_id: self.selected_unit_frequency[unit.unit_id]
             for unit in DEFAULT_UNITS}
        )
        bit_frequency = Counter(
            {index: self.active_bit_frequency[index] for index in range(64)}
        )
        return {
            "schema_version": OBSERVATION_SCHEMA_VERSION,
            "pipeline_version": PIPELINE_VERSION,
            "sample_count": self.sample_count,
            "privacy": {
                "raw_input_stored": False,
                "llm_output_stored": False,
                "automatic_learning": False,
            },
            "aggregates": {
                "active_bit_frequency": _counter_payload(
                    bit_frequency,
                    self.sample_count,
                ),
                "active_bit_count_distribution": _counter_payload(
                    self.active_bit_count_distribution,
                    self.sample_count,
                ),
                "selected_unit_frequency": _counter_payload(
                    unit_frequency,
                    self.sample_count,
                ),
                "selected_unit_combination_frequency": _counter_payload(
                    self.selected_unit_combination_frequency,
                    self.sample_count,
                ),
                "selected_unit_count_distribution": _counter_payload(
                    self.selected_unit_count_distribution,
                    self.sample_count,
                ),
                "threshold_profile_frequency": _counter_payload(
                    self.threshold_profile_frequency,
                    self.sample_count,
                ),
                "llm_order_mode_frequency": _counter_payload(
                    self.mode_frequency,
                    self.sample_count,
                ),
            },
        }


def observe_inputs(
    inputs: Iterable[str],
    threshold_profile: Optional[str] = None,
) -> Dict[str, Any]:
    accumulator = ObservationAccumulator()
    for text in inputs:
        accumulator.observe(
            process(text, threshold_profile=threshold_profile)
        )
    return accumulator.as_dict()


def compare_threshold_profiles(
    cases: Sequence[Mapping[str, str]],
) -> Dict[str, Any]:
    if not cases:
        raise ValueError("at least one threshold comparison case is required")

    profile_results: Dict[str, Any] = {}
    for profile_name in ("auto", *THRESHOLD_PROFILES):
        states = [
            process(
                case["input"],
                threshold_profile=(
                    None if profile_name == "auto" else profile_name
                ),
            )
            for case in cases
        ]
        active_counts = [len(state.active_bits) for state in states]
        selected_counts = [len(state.selected_units) for state in states]
        expected = [
            case.get("expected_mode")
            for case in cases
            if case.get("expected_mode") is not None
        ]
        correct = sum(
            state.llm_order["mode"] == case.get("expected_mode")
            for state, case in zip(states, cases)
            if case.get("expected_mode") is not None
        )
        mode_counts = Counter(state.llm_order["mode"] for state in states)
        profile_results[profile_name] = {
            "sample_count": len(states),
            "active_bit_count": {
                "minimum": min(active_counts),
                "maximum": max(active_counts),
                "mean": round(sum(active_counts) / len(active_counts), 6),
            },
            "selected_unit_count": {
                "minimum": min(selected_counts),
                "maximum": max(selected_counts),
                "mean": round(sum(selected_counts) / len(selected_counts), 6),
            },
            "mode_frequency": _counter_payload(mode_counts, len(states)),
            "expected_mode_accuracy": (
                round(correct / len(expected), 6) if expected else None
            ),
        }

    return {
        "schema_version": THRESHOLD_COMPARISON_SCHEMA_VERSION,
        "pipeline_version": PIPELINE_VERSION,
        "sample_count": len(cases),
        "privacy": {
            "raw_input_stored": False,
            "llm_output_stored": False,
            "automatic_learning": False,
        },
        "profiles": profile_results,
        "decision": {
            "automatic_adjustment": False,
            "reason": (
                "This report exposes comparison data only; threshold changes "
                "require explicit human review and a versioned fixture update."
            ),
        },
    }


def _load_inputs(path: Path) -> List[str]:
    payload: Any = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError("observation input file must contain a JSON array")
    inputs = []
    for item in payload:
        if isinstance(item, str):
            inputs.append(item)
        elif isinstance(item, dict) and isinstance(item.get("input"), str):
            inputs.append(item["input"])
        else:
            raise ValueError(
                "observation items must be strings or objects with input"
            )
    return inputs


def _load_cases(path: Path) -> List[Dict[str, str]]:
    payload: Any = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError("comparison input file must contain a JSON array")
    cases: List[Dict[str, str]] = []
    for item in payload:
        if not isinstance(item, dict) or not isinstance(item.get("input"), str):
            raise ValueError(
                "comparison items must be objects containing an input field"
            )
        case = {"input": item["input"]}
        if isinstance(item.get("expected_mode"), str):
            case["expected_mode"] = item["expected_mode"]
        cases.append(case)
    return cases


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Aggregate privacy-minimized VLTE-BPTM routing observations"
        )
    )
    parser.add_argument("text", nargs="*", help="Input text samples")
    parser.add_argument(
        "--input-file",
        type=Path,
        help="JSON array of strings or objects containing an input field",
    )
    parser.add_argument(
        "--threshold-profile",
        choices=tuple(THRESHOLD_PROFILES),
        help="Use one threshold profile for all samples",
    )
    parser.add_argument(
        "--compare-profiles",
        action="store_true",
        help="Compare auto and every threshold profile using an input file",
    )
    storage_group = parser.add_mutually_exclusive_group()
    storage_group.add_argument(
        "--store",
        type=Path,
        help=(
            "Explicitly persist a privacy-minimized daily aggregate to a "
            "local SQLite .db file"
        ),
    )
    storage_group.add_argument(
        "--list-store",
        type=Path,
        help="Export privacy-minimized buckets from a local SQLite .db file",
    )
    storage_group.add_argument(
        "--purge-store",
        type=Path,
        help="Delete buckets older than the configured retention period",
    )
    args = parser.parse_args(argv)

    if args.list_store is not None or args.purge_store is not None:
        if (
            args.text
            or args.input_file is not None
            or args.threshold_profile is not None
            or args.compare_profiles
        ):
            parser.error(
                "store management options cannot be combined with inputs "
                "or profile options"
            )
        from .observation_store import ObservationStore

        store_path = args.list_store or args.purge_store
        store = ObservationStore(store_path)
        try:
            if args.list_store is not None:
                payload = store.export()
            else:
                payload = {
                    "schema_version": (
                        "vlte-bptm.observation-store-purge.v1"
                    ),
                    "deleted_bucket_count": store.purge(),
                }
        except ValueError as error:
            parser.error(str(error))
        print(
            json.dumps(
                payload,
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0

    if args.compare_profiles:
        if args.input_file is None:
            parser.error("--compare-profiles requires --input-file")
        if args.store is not None:
            parser.error("--store cannot persist threshold comparison reports")
        print(
            json.dumps(
                compare_threshold_profiles(_load_cases(args.input_file)),
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0

    inputs = list(args.text)
    if args.input_file is not None:
        inputs.extend(_load_inputs(args.input_file))
    if not inputs:
        parser.error("provide text samples or --input-file")

    report = observe_inputs(
        inputs,
        threshold_profile=args.threshold_profile,
    )
    output = report
    if args.store is not None:
        from .observation_store import ObservationStore

        try:
            stored = ObservationStore(args.store).persist(report)
        except ValueError as error:
            parser.error(str(error))
        print(
            (
                "stored privacy-minimized observation bucket "
                f"{stored['bucket_start_utc']} "
                f"cohort={stored['cohort_size_band']}"
            ),
            file=sys.stderr,
        )
        output = stored
    print(
        json.dumps(
            output,
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

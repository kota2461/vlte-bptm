"""route-cam.v1 — TCAM-style route cache over SIG-64 signatures.

A RouteCam is a small, human-approved list of ternary match entries
(value / care-mask / distance budget) that can ESCALATE a processing plan.
It sits after the deterministic decision table: the baseline plan derived
from the packet is a floor, and a CAM hit can only raise the processing
class (max-join on the plan rank) — de-escalation is impossible by
construction. This targets the documented gap between the marker layer and
the margin-gated learned layer: inputs the gate abstains on fall to the
respond/economy floor, and a matching approved entry can lift them back.

Discipline (mirrors the Pattern DB rules):
- entries are human-approved only; every entry names its evidence fixture
- adding an entry never touches model weights (no retraining side effects)
- the store is frozen JSON with schema_version + load-time validation
- an empty store is byte-identical to not having a CAM at all

Match rule:  hit(entry)  <=>  popcount((sig XOR value) AND care) <= distance
Among hits: minimum distance wins; ties prefer the higher plan rank
(conservative max-join); remaining ties break on entry_id for determinism.

Intent bits (0-6) are EXCLUDED from care masks by default: on the only path
where the CAM is consulted (marker no-match), the intent field of the
signature is fed by the learned model's top-1, which is exactly the
least-trustworthy signal in that band. An entry must opt in explicitly with
`intent_care_override: true` to match on intent bits.
"""

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from .processing_plan import (
    PROCESSING_CLASSES,
    PROCESSING_PLAN_SCHEMA_VERSION,
    ProcessingPlan,
    _tool_selection,
    parse_processing_plan,
)
from .semantic_packet import SemanticPacket
from .signature import INTENT_BITS_MASK, SIGNATURE_MASK, hamming_distance


ROUTE_CAM_SCHEMA_VERSION = "route-cam.v1"

# Conservative rank: a CAM hit may only move the plan UP this ladder.
# Order follows the role-split canonical priority:
# clarify > verified > deep > standard > economy.
PLAN_RANK = {
    "economy": 0,
    "standard": 1,
    "deep": 2,
    "verified": 3,
    "clarify": 4,
}

MAX_ENTRIES = 64
MAX_DISTANCE_LIMIT = 16

_HEX64_PATTERN = re.compile(r"^0x[0-9A-Fa-f]{1,16}$")
# Short enough that "route_cam_<entry_id>" stays a valid reason_code
# identifier (<= 64 chars).
_ENTRY_ID_PATTERN = re.compile(r"^[a-z][a-z0-9_]{0,49}$")

DEFAULT_ROUTE_CAM_PATH = Path(__file__).resolve().parent / "config" / "route_cam_v1.json"


@dataclass(frozen=True)
class RouteCamEntry:
    entry_id: str
    value: int
    care: int
    max_distance: int
    plan_class: str
    evidence_fixture: str
    intent_care_override: bool
    notes: str

    def as_dict(self) -> Dict[str, Any]:
        return {
            "entry_id": self.entry_id,
            "value": f"0x{self.value:016X}",
            "care": f"0x{self.care:016X}",
            "max_distance": self.max_distance,
            "plan_class": self.plan_class,
            "evidence_fixture": self.evidence_fixture,
            "intent_care_override": self.intent_care_override,
            "notes": self.notes,
        }


@dataclass(frozen=True)
class RouteCamHit:
    entry: RouteCamEntry
    distance: int


def _parse_hex64(value: Any, field: str) -> int:
    if not isinstance(value, str) or _HEX64_PATTERN.fullmatch(value) is None:
        raise ValueError(f"{field} must be a 0x-prefixed 64-bit hex string")
    parsed = int(value, 16)
    if parsed > SIGNATURE_MASK:
        raise ValueError(f"{field} must fit in 64 bits")
    return parsed


def _parse_entry(payload: Any, index: int) -> RouteCamEntry:
    if not isinstance(payload, Mapping):
        raise ValueError(f"entries[{index}] must be an object")
    required = {
        "entry_id",
        "value",
        "care",
        "max_distance",
        "plan_class",
        "evidence_fixture",
    }
    optional = {"intent_care_override", "notes"}
    actual = set(payload)
    missing = sorted(required - actual)
    unknown = sorted(actual - required - optional)
    if missing:
        raise ValueError(f"entries[{index}] is missing field: {missing[0]}")
    if unknown:
        raise ValueError(f"entries[{index}] has unknown field: {unknown[0]}")

    entry_id = payload["entry_id"]
    if (
        not isinstance(entry_id, str)
        or _ENTRY_ID_PATTERN.fullmatch(entry_id) is None
    ):
        raise ValueError(f"entries[{index}].entry_id must be a machine identifier")

    value = _parse_hex64(payload["value"], f"entries[{index}].value")
    care = _parse_hex64(payload["care"], f"entries[{index}].care")
    if care == 0:
        raise ValueError(f"entries[{index}].care must not be all don't-care")

    max_distance = payload["max_distance"]
    if (
        isinstance(max_distance, bool)
        or not isinstance(max_distance, int)
        or not 0 <= max_distance <= MAX_DISTANCE_LIMIT
    ):
        raise ValueError(
            f"entries[{index}].max_distance must be an integer in "
            f"[0, {MAX_DISTANCE_LIMIT}]"
        )

    plan_class = payload["plan_class"]
    if plan_class not in PROCESSING_CLASSES:
        raise ValueError(f"entries[{index}].plan_class is unknown: {plan_class}")
    if plan_class == "economy":
        raise ValueError(
            f"entries[{index}].plan_class must not be economy "
            "(the CAM only escalates; the floor is already the baseline plan)"
        )

    evidence = payload["evidence_fixture"]
    if not isinstance(evidence, str) or not evidence.strip():
        raise ValueError(
            f"entries[{index}].evidence_fixture must be a non-empty string"
        )

    override = payload.get("intent_care_override", False)
    if not isinstance(override, bool):
        raise ValueError(
            f"entries[{index}].intent_care_override must be a boolean"
        )
    if not override and care & INTENT_BITS_MASK:
        raise ValueError(
            f"entries[{index}].care covers intent bits 0-6; on the CAM path "
            "those bits come from the gated learned model and are untrusted. "
            "Set intent_care_override: true to opt in explicitly."
        )

    notes = payload.get("notes", "")
    if not isinstance(notes, str):
        raise ValueError(f"entries[{index}].notes must be a string")

    return RouteCamEntry(
        entry_id=entry_id,
        value=value,
        care=care,
        max_distance=max_distance,
        plan_class=plan_class,
        evidence_fixture=evidence,
        intent_care_override=override,
        notes=notes,
    )


@dataclass(frozen=True)
class RouteCamStore:
    entries: Tuple[RouteCamEntry, ...]

    def __len__(self) -> int:
        return len(self.entries)

    def lookup(self, signature: int) -> Optional[RouteCamHit]:
        """Best hit for `signature`, or None.

        min distance -> max plan rank -> entry_id (deterministic).
        """

        best: Optional[RouteCamHit] = None
        for entry in self.entries:
            distance = hamming_distance(signature, entry.value, entry.care)
            if distance > entry.max_distance:
                continue
            if best is None:
                best = RouteCamHit(entry=entry, distance=distance)
                continue
            candidate_key = (
                distance,
                -PLAN_RANK[entry.plan_class],
                entry.entry_id,
            )
            best_key = (
                best.distance,
                -PLAN_RANK[best.entry.plan_class],
                best.entry.entry_id,
            )
            if candidate_key < best_key:
                best = RouteCamHit(entry=entry, distance=distance)
        return best

    def as_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": ROUTE_CAM_SCHEMA_VERSION,
            "entries": [entry.as_dict() for entry in self.entries],
        }


def parse_route_cam(payload: Any) -> RouteCamStore:
    if not isinstance(payload, Mapping):
        raise ValueError("route cam store must be an object")
    actual = set(payload)
    required = {"schema_version", "entries"}
    missing = sorted(required - actual)
    unknown = sorted(actual - required)
    if missing:
        raise ValueError(f"route cam store is missing field: {missing[0]}")
    if unknown:
        raise ValueError(f"route cam store has unknown field: {unknown[0]}")
    if payload["schema_version"] != ROUTE_CAM_SCHEMA_VERSION:
        raise ValueError("unsupported route cam schema")
    raw_entries = payload["entries"]
    if not isinstance(raw_entries, list):
        raise ValueError("entries must be an array")
    if len(raw_entries) > MAX_ENTRIES:
        raise ValueError(
            f"route cam store exceeds the {MAX_ENTRIES}-entry cap; "
            "grow deliberately (raise the cap in a reviewed change), "
            "not incrementally past it"
        )
    entries = tuple(
        _parse_entry(item, index) for index, item in enumerate(raw_entries)
    )
    ids = [entry.entry_id for entry in entries]
    if len(set(ids)) != len(ids):
        raise ValueError("entry_id values must be unique")
    return RouteCamStore(entries=entries)


def load_route_cam(path: str | Path) -> RouteCamStore:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    return parse_route_cam(payload)


def _escalation_payload(
    packet: SemanticPacket,
    target_class: str,
    reasons: Sequence[str],
) -> Dict[str, Any]:
    """Standard budget template for `target_class` (mirrors the decision
    table's non-critical templates in processing_plan.build_processing_plan)."""

    packet_tools = list(_tool_selection(packet))
    templates = {
        "standard": {
            "core_mode": "horizontal",
            "model_class": "standard",
            "tools": packet_tools,
            "max_dispatches": 1,
            "max_output_tokens": 768,
            "timeout_ms": 8000,
            "estimated_cost_units": 1.0,
        },
        "deep": {
            "core_mode": "hybrid",
            "model_class": "large",
            "tools": packet_tools,
            "max_dispatches": 3,
            "max_output_tokens": 1536,
            "timeout_ms": 20000,
            "estimated_cost_units": 3.0,
        },
        "verified": {
            "core_mode": "vertical",
            "model_class": "standard",
            "tools": packet_tools,
            "max_dispatches": 2,
            "max_output_tokens": 1024,
            "timeout_ms": 12000,
            "estimated_cost_units": 2.0,
        },
        "clarify": {
            "core_mode": "horizontal",
            "model_class": "small",
            "tools": [],
            "max_dispatches": 1,
            "max_output_tokens": 256,
            "timeout_ms": 5000,
            "estimated_cost_units": 0.5,
        },
    }
    template = templates[target_class]
    return {
        "schema_version": PROCESSING_PLAN_SCHEMA_VERSION,
        "primary_route": packet.primary_intent,
        "processing_class": target_class,
        "core_mode": template["core_mode"],
        "model_class": template["model_class"],
        "tools": template["tools"],
        "budgets": {
            "max_dispatches": template["max_dispatches"],
            "max_output_tokens": template["max_output_tokens"],
            "timeout_ms": template["timeout_ms"],
            "estimated_cost_units": template["estimated_cost_units"],
        },
        "fallback": "clarify",
        "reason_codes": list(reasons),
    }


def apply_route_cam(
    packet: SemanticPacket,
    plan: ProcessingPlan,
    store: RouteCamStore,
    signature: int,
) -> Tuple[ProcessingPlan, Optional[RouteCamHit], bool]:
    """Merge a CAM lookup into `plan`. Escalation-only by construction.

    Returns (plan, hit, applied). `applied` is True only when the hit's
    class outranks the baseline plan and the plan was rebuilt.
    """

    hit = store.lookup(signature)
    if hit is None:
        return plan, None, False
    if PLAN_RANK[hit.entry.plan_class] <= PLAN_RANK[plan.processing_class]:
        # The baseline already provides at least this class: max-join keeps
        # the baseline (do-no-harm — a CAM entry can never lower a plan).
        return plan, hit, False
    reasons = (*plan.reason_codes, f"route_cam_{hit.entry.entry_id}")
    escalated = parse_processing_plan(
        _escalation_payload(packet, hit.entry.plan_class, reasons)
    )
    return escalated, hit, True

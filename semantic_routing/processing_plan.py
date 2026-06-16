"""Strict processing-plan.v1 contract and deterministic routing policy."""

import math
import re
from dataclasses import dataclass
from typing import Any, Dict, Mapping, Tuple

from .semantic_packet import INTENTS, SemanticPacket


PROCESSING_PLAN_SCHEMA_VERSION = "processing-plan.v1"

PROCESSING_CLASSES = (
    "economy",
    "standard",
    "verified",
    "deep",
    "clarify",
)
CORE_MODES = ("horizontal", "vertical", "hybrid")
MODEL_CLASSES = ("small", "standard", "large")
TOOLS = ("web_search", "calculator")

_IDENTIFIER_PATTERN = re.compile(r"^[a-z][a-z0-9_]{0,63}$")


def _strict_object(
    value: Any,
    field: str,
    required_fields: Tuple[str, ...],
) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{field} must be an object")
    actual = set(value)
    required = set(required_fields)
    missing = sorted(required - actual)
    unknown = sorted(actual - required)
    if missing:
        raise ValueError(f"{field} is missing field: {missing[0]}")
    if unknown:
        raise ValueError(f"{field} has unknown field: {unknown[0]}")
    return value


def _identifier(value: Any, field: str) -> str:
    if (
        not isinstance(value, str)
        or _IDENTIFIER_PATTERN.fullmatch(value) is None
    ):
        raise ValueError(f"{field} must be a machine identifier")
    return value


def _identifier_list(
    value: Any,
    field: str,
    *,
    allowed: Tuple[str, ...] | None = None,
    require_non_empty: bool = False,
) -> Tuple[str, ...]:
    if not isinstance(value, list):
        raise ValueError(f"{field} must be an array")
    items = tuple(_identifier(item, field) for item in value)
    if require_non_empty and not items:
        raise ValueError(f"{field} must not be empty")
    if len(set(items)) != len(items):
        raise ValueError(f"{field} must contain unique values")
    if allowed is not None:
        unknown = sorted(set(items) - set(allowed))
        if unknown:
            raise ValueError(f"{field} contains unknown value: {unknown[0]}")
    return items


def _bounded_int(
    value: Any,
    field: str,
    minimum: int,
    maximum: int,
) -> int:
    if (
        isinstance(value, bool)
        or not isinstance(value, int)
        or not minimum <= value <= maximum
    ):
        raise ValueError(
            f"{field} must be an integer in [{minimum}, {maximum}]"
        )
    return value


def _bounded_number(
    value: Any,
    field: str,
    minimum: float,
    maximum: float,
) -> float:
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not math.isfinite(value)
        or not minimum <= value <= maximum
    ):
        raise ValueError(
            f"{field} must be a finite number in [{minimum}, {maximum}]"
        )
    return float(value)


@dataclass(frozen=True)
class ProcessingBudget:
    max_dispatches: int
    max_output_tokens: int
    timeout_ms: int
    estimated_cost_units: float

    def as_dict(self) -> Dict[str, Any]:
        return {
            "max_dispatches": self.max_dispatches,
            "max_output_tokens": self.max_output_tokens,
            "timeout_ms": self.timeout_ms,
            "estimated_cost_units": self.estimated_cost_units,
        }


@dataclass(frozen=True)
class ProcessingPlan:
    primary_route: str
    processing_class: str
    core_mode: str
    model_class: str
    tools: Tuple[str, ...]
    budgets: ProcessingBudget
    fallback: str
    reason_codes: Tuple[str, ...]

    def as_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": PROCESSING_PLAN_SCHEMA_VERSION,
            "primary_route": self.primary_route,
            "processing_class": self.processing_class,
            "core_mode": self.core_mode,
            "model_class": self.model_class,
            "tools": list(self.tools),
            "budgets": self.budgets.as_dict(),
            "fallback": self.fallback,
            "reason_codes": list(self.reason_codes),
        }


def _parse_budget(value: Any) -> ProcessingBudget:
    fields = (
        "max_dispatches",
        "max_output_tokens",
        "timeout_ms",
        "estimated_cost_units",
    )
    payload = _strict_object(value, "budgets", fields)
    return ProcessingBudget(
        max_dispatches=_bounded_int(
            payload["max_dispatches"],
            "budgets.max_dispatches",
            1,
            32,
        ),
        max_output_tokens=_bounded_int(
            payload["max_output_tokens"],
            "budgets.max_output_tokens",
            1,
            32768,
        ),
        timeout_ms=_bounded_int(
            payload["timeout_ms"],
            "budgets.timeout_ms",
            100,
            120000,
        ),
        estimated_cost_units=_bounded_number(
            payload["estimated_cost_units"],
            "budgets.estimated_cost_units",
            0.0,
            100.0,
        ),
    )


def _validate_class_contract(plan: ProcessingPlan) -> None:
    if plan.processing_class == "economy":
        if (
            plan.core_mode != "horizontal"
            or plan.model_class != "small"
            or plan.tools
            or plan.budgets.max_dispatches != 1
            or plan.budgets.estimated_cost_units > 1.0
        ):
            raise ValueError("economy plan exceeds the v1 economy contract")
    elif plan.processing_class == "clarify":
        if (
            plan.core_mode != "horizontal"
            or plan.model_class != "small"
            or plan.tools
            or plan.budgets.max_dispatches != 1
        ):
            raise ValueError("clarify plan exceeds the v1 clarify contract")
    elif plan.processing_class == "verified":
        if (
            plan.core_mode != "vertical"
            or plan.model_class not in {"standard", "large"}
            or plan.budgets.max_dispatches < 2
        ):
            raise ValueError("verified plan violates the v1 verify contract")
    elif plan.processing_class == "deep":
        if (
            plan.core_mode != "hybrid"
            or plan.model_class not in {"standard", "large"}
            or plan.budgets.max_dispatches < 2
        ):
            raise ValueError("deep plan violates the v1 deep contract")
    elif plan.processing_class == "standard":
        if (
            plan.core_mode not in {"horizontal", "vertical"}
            or plan.model_class != "standard"
        ):
            raise ValueError("standard plan violates the v1 standard contract")


def parse_processing_plan(value: Any) -> ProcessingPlan:
    fields = (
        "schema_version",
        "primary_route",
        "processing_class",
        "core_mode",
        "model_class",
        "tools",
        "budgets",
        "fallback",
        "reason_codes",
    )
    payload = _strict_object(value, "processing plan", fields)
    if payload["schema_version"] != PROCESSING_PLAN_SCHEMA_VERSION:
        raise ValueError("unsupported processing plan schema")

    primary_route = payload["primary_route"]
    if primary_route not in INTENTS:
        raise ValueError(f"unknown primary route: {primary_route}")
    processing_class = payload["processing_class"]
    if processing_class not in PROCESSING_CLASSES:
        raise ValueError(f"unknown processing class: {processing_class}")
    core_mode = payload["core_mode"]
    if core_mode not in CORE_MODES:
        raise ValueError(f"unknown core mode: {core_mode}")
    model_class = payload["model_class"]
    if model_class not in MODEL_CLASSES:
        raise ValueError(f"unknown model class: {model_class}")
    fallback = payload["fallback"]
    if fallback not in INTENTS:
        raise ValueError(f"unknown fallback route: {fallback}")

    plan = ProcessingPlan(
        primary_route=primary_route,
        processing_class=processing_class,
        core_mode=core_mode,
        model_class=model_class,
        tools=_identifier_list(
            payload["tools"],
            "tools",
            allowed=TOOLS,
        ),
        budgets=_parse_budget(payload["budgets"]),
        fallback=fallback,
        reason_codes=_identifier_list(
            payload["reason_codes"],
            "reason_codes",
            require_non_empty=True,
        ),
    )
    _validate_class_contract(plan)
    return plan


def _tool_selection(packet: SemanticPacket) -> Tuple[str, ...]:
    tools = []
    if (
        "search" in packet.operations
        or packet.information_state.requires_current_information
    ):
        tools.append("web_search")
    if "calculate" in packet.operations:
        tools.append("calculator")
    return tuple(tools)


def _plan_payload(
    packet: SemanticPacket,
    *,
    processing_class: str,
    core_mode: str,
    model_class: str,
    tools: Tuple[str, ...],
    max_dispatches: int,
    max_output_tokens: int,
    timeout_ms: int,
    estimated_cost_units: float,
    reasons: Tuple[str, ...],
) -> Dict[str, Any]:
    return {
        "schema_version": PROCESSING_PLAN_SCHEMA_VERSION,
        "primary_route": packet.primary_intent,
        "processing_class": processing_class,
        "core_mode": core_mode,
        "model_class": model_class,
        "tools": list(tools),
        "budgets": {
            "max_dispatches": max_dispatches,
            "max_output_tokens": max_output_tokens,
            "timeout_ms": timeout_ms,
            "estimated_cost_units": estimated_cost_units,
        },
        "fallback": "clarify",
        "reason_codes": list(reasons),
    }


def build_processing_plan(packet: SemanticPacket) -> ProcessingPlan:
    """Build a deterministic plan from a validated SemanticPacket only."""

    if not isinstance(packet, SemanticPacket):
        raise TypeError(
            "processing router requires a validated SemanticPacket; "
            "raw prompts are not accepted"
        )

    state = packet.information_state
    primary = packet.primary_intent
    base_reasons = [f"primary_{primary}"]

    if packet.conflicts:
        base_reasons.append("semantic_conflict")
    if packet.unknowns:
        base_reasons.append("semantic_unknowns")
    if packet.confidence < 0.60:
        base_reasons.append("low_semantic_confidence")
    if (
        packet.conflicts
        or packet.unknowns
        or packet.confidence < 0.60
        or state.missing_required_information
        or primary == "clarify"
    ):
        if state.missing_required_information:
            base_reasons.append("missing_required_information")
        return parse_processing_plan(
            _plan_payload(
                packet,
                processing_class="clarify",
                core_mode="horizontal",
                model_class="small",
                tools=(),
                max_dispatches=1,
                max_output_tokens=256,
                timeout_ms=5000,
                estimated_cost_units=0.5,
                reasons=tuple(base_reasons),
            )
        )

    verified_reasons = list(base_reasons)
    if state.contains_unverified_claims:
        verified_reasons.append("unverified_claims")
    if state.requires_current_information:
        verified_reasons.append("current_information_required")
    if primary == "verify" or "verify" in packet.operations:
        verified_reasons.append("verification_requested")
    if packet.risk.level in {"high", "critical"}:
        verified_reasons.append(f"{packet.risk.level}_risk")
    needs_verification = (
        state.contains_unverified_claims
        or state.requires_current_information
        or primary == "verify"
        or "verify" in packet.operations
        or packet.risk.level in {"high", "critical"}
    )
    if needs_verification:
        tools = _tool_selection(packet)
        if "web_search" in tools:
            verified_reasons.append("web_search_required")
        if "calculator" in tools:
            verified_reasons.append("calculator_required")
        critical = packet.risk.level == "critical"
        return parse_processing_plan(
            _plan_payload(
                packet,
                processing_class="verified",
                core_mode="vertical",
                model_class="large" if critical else "standard",
                tools=tools,
                max_dispatches=3 if critical else 2,
                max_output_tokens=1200 if critical else 1024,
                timeout_ms=20000 if critical else 12000,
                estimated_cost_units=3.0 if critical else 2.0,
                reasons=tuple(verified_reasons),
            )
        )

    if (
        state.multiple_intents
        or primary == "explore"
        or "compare" in packet.operations
    ):
        deep_reasons = list(base_reasons)
        if state.multiple_intents:
            deep_reasons.append("multiple_intents")
        if primary == "explore":
            deep_reasons.append("exploration_requested")
        if "compare" in packet.operations:
            deep_reasons.append("comparison_requested")
        tools = _tool_selection(packet)
        if "calculator" in tools:
            deep_reasons.append("calculator_required")
        return parse_processing_plan(
            _plan_payload(
                packet,
                processing_class="deep",
                core_mode="hybrid",
                model_class="large",
                tools=tools,
                max_dispatches=3,
                max_output_tokens=1536,
                timeout_ms=20000,
                estimated_cost_units=3.0,
                reasons=tuple(deep_reasons),
            )
        )

    economy_eligible = (
        primary in {"respond", "explain", "summarize"}
        and packet.risk.level == "low"
        and not _tool_selection(packet)
        and packet.constraints.response_length != "long"
    )
    if economy_eligible:
        return parse_processing_plan(
            _plan_payload(
                packet,
                processing_class="economy",
                core_mode="horizontal",
                model_class="small",
                tools=(),
                max_dispatches=1,
                max_output_tokens=384,
                timeout_ms=5000,
                estimated_cost_units=0.5,
                reasons=tuple((*base_reasons, "low_risk_direct_path")),
            )
        )

    standard_reasons = list(base_reasons)
    if primary == "build":
        standard_reasons.append("implementation_requested")
    if packet.constraints.response_length == "long":
        standard_reasons.append("long_response_requested")
    return parse_processing_plan(
        _plan_payload(
            packet,
            processing_class="standard",
            core_mode="horizontal",
            model_class="standard",
            tools=_tool_selection(packet),
            max_dispatches=1,
            max_output_tokens=768,
            timeout_ms=8000,
            estimated_cost_units=1.0,
            reasons=tuple(standard_reasons),
        )
    )

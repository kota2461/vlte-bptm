"""Failure-memory guard hints derived from validated semantic packets.

This module is intentionally downstream of semantic packet extraction: it does
not learn success labels and does not rewrite the packet. It turns reviewed
Failure Memory patterns into guard/relabel hints that the caller can use before
an LLM response is produced.
"""

from dataclasses import dataclass
from typing import Any, Dict, Tuple

from .semantic_packet import SemanticPacket


_ERROR_CHECK_TOKENS = (
    "\u30a8\u30e9\u30fc",
    "error",
    "failed",
    "failure",
    "exception",
    "traceback",
    "502",
    "structured output",
)
_ERROR_ARTIFACT_TOKENS = (
    "traceback",
    "stack trace",
    "log",
    "\u30ed\u30b0",
    "502",
    "exception",
)


@dataclass(frozen=True)
class FailureGuard:
    guard_actions: Tuple[str, ...]
    bad_tendencies: Tuple[str, ...]
    severity: str
    relabel_hints: Tuple[str, ...]
    reason_codes: Tuple[str, ...]

    def as_dict(self) -> Dict[str, Any]:
        return {
            "guard_actions": list(self.guard_actions),
            "bad_tendencies": list(self.bad_tendencies),
            "severity": self.severity,
            "relabel_hints": list(self.relabel_hints),
            "reason_codes": list(self.reason_codes),
        }


def _unique(items: list[str]) -> Tuple[str, ...]:
    return tuple(dict.fromkeys(items))


def derive_failure_guard(text: str, packet: SemanticPacket) -> FailureGuard:
    """Derive non-invasive Failure Memory guard hints.

    The guard can be consumed by orchestration/LLM glue, but the SemanticPacket
    remains the adjudicated routing label. This keeps Failure Memory separate
    from the success-pattern lane.
    """

    state = packet.information_state
    constraints = packet.constraints
    risk = packet.risk
    operations = set(packet.operations)
    guard_actions: list[str] = []
    bad_tendencies: list[str] = []
    relabel_hints: list[str] = []
    reason_codes: list[str] = []

    if state.missing_required_information or packet.primary_intent == "clarify":
        guard_actions.extend(["clarify_up", "ask_first"])
        bad_tendencies.append("respond_without_required_information")
        relabel_hints.append("prefer_clarify_when_required_information_missing")
        reason_codes.append("missing_information_guard")

    if state.contains_unverified_claims or "verify" in operations or packet.primary_intent == "verify":
        guard_actions.extend(["verify_up", "avoid_overclaim"])
        bad_tendencies.append("accept_unverified_claim_without_check")
        relabel_hints.append("preserve_verify_step")
        reason_codes.append("verification_guard")

    if state.requires_current_information or "search" in operations:
        guard_actions.extend(["search_up", "avoid_stale_answer"])
        bad_tendencies.append("answer_with_stale_or_unverified_current_info")
        relabel_hints.append("preserve_current_information_lookup")
        reason_codes.append("current_information_guard")

    if state.multiple_intents:
        guard_actions.extend(["preserve_multi_intent", "split_or_sequence_operations"])
        bad_tendencies.append("collapse_compound_intent_into_single_response")
        relabel_hints.append("preserve_compound_intent_sequence")
        reason_codes.append("compound_intent_guard")

    if "calculate" in operations:
        guard_actions.append("calculate_check")
        bad_tendencies.append("skip_calculation_check")
        relabel_hints.append("preserve_calculation_check")
        reason_codes.append("calculation_guard")

    if constraints.must or constraints.must_not or constraints.formats:
        guard_actions.append("preserve_constraints")
        bad_tendencies.append("ignore_explicit_constraints")
        relabel_hints.append("preserve_constraints")
        reason_codes.append("constraint_guard")

    if risk.level != "low":
        guard_actions.append("risk_check_up")
        reason_codes.append("risk_guard")

    normalized_text = text.lower()
    error_check_requested = any(
        token.lower() in normalized_text for token in _ERROR_CHECK_TOKENS
    )
    error_artifact_present = any(
        token.lower() in normalized_text for token in _ERROR_ARTIFACT_TOKENS
    )

    if error_check_requested and (
        packet.primary_intent == "verify" or "verify" in operations
    ):
        guard_actions.extend(["inspect_error_context", "avoid_status_only_response"])
        bad_tendencies.append("treat_error_report_as_bare_status")
        relabel_hints.append("prefer_verify_for_error_check_request")
        reason_codes.append("error_check_guard")
        if not error_artifact_present:
            guard_actions.append("ask_for_missing_artifact_if_error_context_absent")
            relabel_hints.append("ask_for_error_artifact_when_context_absent")

    if not guard_actions:
        guard_actions.append("review_before_response")
        bad_tendencies.append("overconfident_direct_response")
        reason_codes.append("default_low_risk_guard")

    if risk.level != "low" or state.requires_current_information:
        severity = "major"
    elif (
        state.missing_required_information
        or state.contains_unverified_claims
        or "calculate" in operations
        or "error_check_guard" in reason_codes
    ):
        severity = "medium"
    else:
        severity = "minor"

    return FailureGuard(
        guard_actions=tuple(sorted(_unique(guard_actions))),
        bad_tendencies=tuple(sorted(_unique(bad_tendencies))),
        severity=severity,
        relabel_hints=tuple(sorted(_unique(relabel_hints))),
        reason_codes=tuple(sorted(_unique(reason_codes))),
    )

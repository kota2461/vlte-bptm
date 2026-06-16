"""Curriculum tiers (v0.2.1 deployment-gate design).

Tier 0 (foundation) is the behavioural base whose regressions are never
acceptable; tier 1 (refinement) improves boundaries without breaking it.
The tier is derived deterministically from a pattern's source URL so that
already-reviewed DB rows never need rewriting. Tier weighting during
training exists but is OFF by default (`foundation_weight=1.0`); protection
of foundation behaviour is enforced by the deployment gate, not by weights.
"""

from typing import Any, Dict


FOUNDATION_TIER = 0
REFINEMENT_TIER = 1

TIER_BY_SOURCE_URL = {
    "curriculum://math-v1": FOUNDATION_TIER,
    "curriculum://language-v1": FOUNDATION_TIER,
    "curriculum://route-boundaries-v1": REFINEMENT_TIER,
    "curriculum://route-boundaries-v2-round1": REFINEMENT_TIER,
    "curriculum://route-boundaries-v2-round1b": REFINEMENT_TIER,
    "demo://router-patterns-v1": REFINEMENT_TIER,
}


def curriculum_tier(source_url: str) -> int:
    """Return the tier for a pattern source. Unknown sources are refinement."""

    return TIER_BY_SOURCE_URL.get(source_url, REFINEMENT_TIER)


def example_tier(example: Dict[str, Any]) -> int:
    """Tier for a training example as returned by training_examples()."""

    source = example.get("source") or {}
    return curriculum_tier(str(source.get("url", "")))

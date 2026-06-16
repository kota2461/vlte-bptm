"""Strict successor sealed fixture contract for PLM evaluation."""

from dataclasses import dataclass
from typing import Any, Dict, Mapping, Tuple

from .benchmark import PLMBenchmarkCase, parse_plm_benchmark


PLM_SEALED_FIXTURE_SCHEMA_VERSION = "pattern-language-sealed.v1"


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


def _non_empty_string(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty string")
    return value


@dataclass(frozen=True)
class PLMSealedFixture:
    fixture_id: str
    frozen_at: str
    predecessor: str
    authoring_method: str
    policy: str
    cases: Tuple[PLMBenchmarkCase, ...]

    def as_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": PLM_SEALED_FIXTURE_SCHEMA_VERSION,
            "fixture_id": self.fixture_id,
            "frozen_at": self.frozen_at,
            "predecessor": self.predecessor,
            "authoring_method": self.authoring_method,
            "policy": self.policy,
            "cases": [case.as_dict() for case in self.cases],
        }


def parse_plm_sealed_fixture(value: Any) -> PLMSealedFixture:
    payload = _strict_object(
        value,
        "sealed fixture",
        (
            "schema_version",
            "fixture_id",
            "frozen_at",
            "predecessor",
            "authoring_method",
            "policy",
            "cases",
        ),
    )
    if payload["schema_version"] != PLM_SEALED_FIXTURE_SCHEMA_VERSION:
        raise ValueError("unsupported PLM sealed fixture schema")
    wrapped = parse_plm_benchmark(
        {
            "schema_version": "pattern-language-benchmark.v1",
            "frozen_at": payload["frozen_at"],
            "authoring_method": payload["authoring_method"],
            "review_status": "draft",
            "policy": payload["policy"],
            "cases": payload["cases"],
        }
    )
    if any(case.split != "sealed" for case in wrapped.cases):
        raise ValueError("PLM sealed fixture may contain only sealed cases")
    return PLMSealedFixture(
        fixture_id=_non_empty_string(payload["fixture_id"], "fixture_id"),
        frozen_at=_non_empty_string(payload["frozen_at"], "frozen_at"),
        predecessor=_non_empty_string(
            payload["predecessor"],
            "predecessor",
        ),
        authoring_method=_non_empty_string(
            payload["authoring_method"],
            "authoring_method",
        ),
        policy=_non_empty_string(payload["policy"], "policy"),
        cases=wrapped.cases,
    )

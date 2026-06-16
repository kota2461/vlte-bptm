import json
from pathlib import Path

import pytest

from thought_core import OUTPUT_SCHEMA_VERSION, PIPELINE_VERSION, process


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "v1_0a_cases.json"
CASES = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
EXPECTED_TRACE = [
    "input",
    "active_bits",
    "selected_units",
    "inhibition_integration",
    "horizontal_mesh",
    "action_vector",
    "llm_order",
]


@pytest.mark.parametrize("case", CASES, ids=lambda case: case["name"])
def test_v1_0a_acceptance_cases(case: dict) -> None:
    payload = process(case["input"]).as_dict()
    selected_ids = {
        unit["unit_id"] for unit in payload["selected_units"]
    }
    minimum, maximum = case["active_bit_range"]

    assert payload["schema_version"] == OUTPUT_SCHEMA_VERSION
    assert payload["pipeline_version"] == PIPELINE_VERSION
    assert payload["metrics"]["threshold_profile"] == case["expected_profile"]
    assert minimum <= payload["metrics"]["active_bit_count"] <= maximum
    assert set(case["required_units"]) <= selected_ids
    assert payload["llm_order"]["mode"] == case["expected_mode"]
    assert [stage["stage"] for stage in payload["trace"]] == EXPECTED_TRACE
    assert payload["diagnostics"]["processing_mode"] == "horizontal"

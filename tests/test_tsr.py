import json
import os
import subprocess
import sys

import pytest

from thought_register.bits import MASK_64, ThoughtBit
from thought_register.engine import process
from thought_register.mode_selector import select_mode
from thought_register.resolver import resolve_conflicts
from thought_register.state import ThoughtState


def test_register_defines_exactly_64_unique_bits() -> None:
    positions = [int(flag) for flag in ThoughtBit]
    assert positions == list(range(64))


def test_state_tracks_strength_source_and_clear() -> None:
    state = ThoughtState()
    state.set(ThoughtBit.CURIOSITY, 0.4, "first")
    state.set(ThoughtBit.CURIOSITY, 0.8, "second")

    assert state.has(ThoughtBit.CURIOSITY)
    assert state.strength(ThoughtBit.CURIOSITY) == 0.8
    assert state.sources[ThoughtBit.CURIOSITY] == ["first", "second"]

    state.clear(ThoughtBit.CURIOSITY)
    assert not state.has(ThoughtBit.CURIOSITY)
    assert ThoughtBit.CURIOSITY not in state.intensity


def test_state_rejects_values_outside_unsigned_64_bits() -> None:
    with pytest.raises(ValueError):
        ThoughtState(MASK_64 + 1)


def test_new_idea_selects_explore_mode() -> None:
    result = process("新しい思考モデルを考えました。どう整理できますか？")

    assert result.mode == "explore"
    assert result.state.has(ThoughtBit.CURIOSITY)
    assert result.state.has(ThoughtBit.NOVELTY_DETECTED)
    assert not result.state.has(ThoughtBit.SUMMARIZE)
    assert result.state.has(ThoughtBit.FINAL_ANSWER)


def test_explicit_implementation_selects_build_mode() -> None:
    result = process("この仕組みをPythonで実装して、ファイル構成も作って")

    assert result.mode == "build"
    assert result.state.has(ThoughtBit.NEED_DECOMPOSE)
    assert result.state.has(ThoughtBit.PLAN)


def test_verify_mode_has_priority_over_build() -> None:
    result = process("この設計を実装する前に問題とリスクを検証して")

    assert result.mode == "verify"
    assert result.state.has(ThoughtBit.CAUTION)
    assert result.state.has(ThoughtBit.NEED_VERIFY)


def test_insufficient_information_routes_to_question() -> None:
    state = ThoughtState()
    state.set(ThoughtBit.INSUFFICIENT_INFO, 1.0, "test")
    resolve_conflicts(state)

    assert state.has(ThoughtBit.ASK_QUESTION)
    assert not state.has(ThoughtBit.FINAL_ANSWER)


def test_safe_refusal_clears_conflicting_actions() -> None:
    state = ThoughtState()
    state.set(ThoughtBit.SAFE_REFUSAL, 1.0, "test")
    state.set(ThoughtBit.PROPOSE, 1.0, "test")
    state.set(ThoughtBit.EXECUTE_TOOL, 1.0, "test")
    resolve_conflicts(state)

    assert select_mode(state) == "safe_refusal"
    assert not state.has(ThoughtBit.PROPOSE)
    assert not state.has(ThoughtBit.EXECUTE_TOOL)
    assert state.has(ThoughtBit.FINAL_ANSWER)


@pytest.mark.parametrize(
    ("text", "expected_mode"),
    [
        ("新しい思考モデルを考えました。整理できますか？", "explore"),
        ("この仕組みをPythonで実装して", "build"),
        ("この設計の問題とリスクを検証して", "verify"),
        ("これを短く要約して", "compress"),
        ("つらくて不安です", "empath"),
        ("こんにちは", "chat"),
    ],
)
def test_representative_inputs_select_expected_mode(
    text: str,
    expected_mode: str,
) -> None:
    assert process(text).mode == expected_mode


def test_empty_input_requests_a_question() -> None:
    result = process("")

    assert result.mode == "chat"
    assert result.state.has(ThoughtBit.INSUFFICIENT_INFO)
    assert result.state.has(ThoughtBit.ASK_QUESTION)
    assert not result.state.has(ThoughtBit.FINAL_ANSWER)


def test_cli_json_is_machine_parseable() -> None:
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "thought_register",
            "--json",
            "新しい思考モデルを考えました",
        ],
        check=True,
        capture_output=True,
        text=True,
        encoding="ascii",
        env=env,
    )

    payload = json.loads(completed.stdout)
    assert payload["mode"] == "explore"
    assert payload["order"]["user_input"] == "新しい思考モデルを考えました"

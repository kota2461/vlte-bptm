"""Thought Delta Journal: backward compatibility, XOR-delta reversibility,
pigeonhole neighbour guarantee, and the three feedback paths (revisit /
loop / continuity) actually changing behaviour through the resolver and
mode selector."""

import json
import os
import subprocess
import sys

import pytest

from thought_register import ThoughtBit, ThoughtJournal, process
from thought_register.journal import GUARANTEED_RADIUS


# --- backward compatibility -------------------------------------------------


def test_process_without_journal_has_no_journal_stage() -> None:
    result = process("新しい思考モデルを考えました。整理できますか？")
    assert [step.stage for step in result.trace] == [
        "encode",
        "resolve",
        "select_mode:explore",
    ]


def test_first_turn_with_fresh_journal_decides_identically() -> None:
    text = "この仕組みをPythonで実装して"
    without = process(text)
    with_journal = process(text, journal=ThoughtJournal())
    assert with_journal.mode == without.mode
    assert with_journal.state.value == without.state.value
    # only difference: the (empty) journal_feedback trace step
    feedback = [
        step
        for step in with_journal.trace
        if step.stage == "journal_feedback"
    ]
    assert len(feedback) == 1
    assert feedback[0].activated == []
    assert feedback[0].cleared == []


# --- journal mechanics -------------------------------------------------------


def test_delta_chain_is_reversible() -> None:
    journal = ThoughtJournal()
    committed = [0x1, 0x1 | (1 << 50), (1 << 50) | (1 << 63)]
    for value in committed:
        journal.append(value, value)
    deltas = [int(delta, 16) for delta in journal.as_dict()["deltas"]]
    reconstructed = 0
    for index, delta in enumerate(deltas):
        reconstructed ^= delta
        assert reconstructed == committed[index]


def test_pigeonhole_guarantees_distance_3_recall() -> None:
    journal = ThoughtJournal()
    base = (1 << 3) | (1 << 20) | (1 << 40) | (1 << 60)
    journal.append(base, base)

    # distance 3, flips spread across three different 16-bit blocks:
    # the untouched block still matches exactly -> must be found
    spread = base ^ (1 << 0) ^ (1 << 17) ^ (1 << 33)
    assert journal.find_neighbors(spread, GUARANTEED_RADIUS) == [(0, 3)]

    # distance 3 concentrated in ONE block: the other three blocks match
    concentrated = base ^ (1 << 40) ^ (1 << 41) ^ (1 << 42)
    assert journal.find_neighbors(concentrated, GUARANTEED_RADIUS) == [(0, 3)]

    # distance 4 with one flip in EVERY block: no block matches, so the
    # multi-index cannot see it (documented approximation boundary)
    everywhere = base ^ (1 << 0) ^ (1 << 17) ^ (1 << 33) ^ (1 << 49)
    assert journal.find_neighbors(everywhere, 4) == []


def test_append_rejects_out_of_range_words() -> None:
    journal = ThoughtJournal()
    with pytest.raises(ValueError):
        journal.append(-1, 0)
    with pytest.raises(ValueError):
        journal.append(0, 1 << 64)
    with pytest.raises(TypeError):
        journal.append(True, 0)


# --- feedback paths ----------------------------------------------------------


def test_revisit_selects_recall_mode() -> None:
    journal = ThoughtJournal()
    text = "新しい思考モデルを考えました。整理できますか？"
    first = process(text, journal=journal)
    second = process(text, journal=journal)
    assert first.mode == "explore"
    assert second.mode == "recall"
    assert second.state.has(ThoughtBit.RETRIEVE_MEMORY)
    assert second.state.sources[ThoughtBit.RETRIEVE_MEMORY] == [
        "journal.revisit"
    ]
    assert second.order["instruction"].startswith("セッション内の既出の文脈")


def test_revisited_verification_still_verifies() -> None:
    # safety-first: recall sits BELOW verify in the cascade
    journal = ThoughtJournal()
    text = "この設計の問題とリスクを検証して"
    assert process(text, journal=journal).mode == "verify"
    second = process(text, journal=journal)
    assert second.state.has(ThoughtBit.RETRIEVE_MEMORY)
    assert second.mode == "verify"


def test_loop_feedback_asks_question_instead_of_finalising() -> None:
    journal = ThoughtJournal()
    # synthetic committed history: identical context, action layer flapping
    context = (1 << 43) | (1 << 46)
    journal.append(context, context | (1 << 48))
    journal.append(context, context | (1 << 50))
    journal.append(context, context | (1 << 48))
    assert journal.detect_loop()

    result = process("こんにちは", journal=journal)
    assert result.state.has(ThoughtBit.REPAIR_DRIVE)
    assert result.state.has(ThoughtBit.CONTRADICTION_DETECTED)
    assert result.state.has(ThoughtBit.ASK_QUESTION)
    assert not result.state.has(ThoughtBit.FINAL_ANSWER)
    assert result.state.sources[ThoughtBit.ASK_QUESTION] == [
        "resolver.loop_repair"
    ]


def test_continuity_marks_unchanged_drive_affect_context() -> None:
    journal = ThoughtJournal()
    process("こんにちは", journal=journal)
    # question rule adds cognition/action bits only -> drive+affect unchanged
    result = process("こんにちは？", journal=journal)
    assert result.state.has(ThoughtBit.CONTINUITY_DRIVE)
    assert result.state.sources[ThoughtBit.CONTINUITY_DRIVE] == [
        "journal.continuity"
    ]
    # not an exact revisit, so no recall takeover
    assert not result.state.has(ThoughtBit.RETRIEVE_MEMORY)


def test_loop_alarm_is_self_limiting() -> None:
    # once repair bits land in the committed state, the next transition is
    # no longer action-only, so the alarm does not re-fire forever
    journal = ThoughtJournal()
    context = (1 << 43) | (1 << 46)
    journal.append(context, context | (1 << 48))
    journal.append(context, context | (1 << 50))
    journal.append(context, context | (1 << 48))
    process("こんにちは", journal=journal)   # fires, injects repair bits
    assert not journal.detect_loop()


# --- CLI ---------------------------------------------------------------------


def test_cli_session_json_reports_journal_feedback() -> None:
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "thought_register",
            "--session",
            "--json",
            "新しい思考モデルを考えました",
            "新しい思考モデルを考えました",
        ],
        check=True,
        capture_output=True,
        text=True,
        encoding="ascii",
        env=env,
    )
    payload = json.loads(completed.stdout)
    assert payload["journal"]["turn_count"] == 2
    assert payload["turns"][0]["mode"] == "explore"
    assert payload["turns"][1]["mode"] == "recall"
    stages = [step["stage"] for step in payload["turns"][1]["trace"]]
    assert "journal_feedback" in stages

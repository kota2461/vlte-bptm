from .bits import ThoughtBit
from .state import ThoughtState


def resolve_conflicts(state: ThoughtState) -> ThoughtState:
    if state.has(ThoughtBit.SAFE_REFUSAL):
        state.clear(ThoughtBit.PROPOSE)
        state.clear(ThoughtBit.EXECUTE_TOOL)
        state.set(ThoughtBit.CAUTION, 1.0, "resolver.safe_refusal")
        state.set(ThoughtBit.FINAL_ANSWER, 1.0, "resolver.safe_refusal")
        return state

    if state.has(ThoughtBit.RISK_DETECTED):
        state.set(ThoughtBit.CAUTION, 0.9, "resolver.risk")
        state.set(ThoughtBit.NEED_VERIFY, 0.9, "resolver.risk")

    if state.has(ThoughtBit.INSUFFICIENT_INFO) and not state.has(
        ThoughtBit.ANSWER_POSSIBLE
    ):
        state.clear(ThoughtBit.FINAL_ANSWER)
        state.set(ThoughtBit.ASK_QUESTION, 0.9, "resolver.insufficient_info")
        state.set(ThoughtBit.SHORT_REPLY, 0.7, "resolver.insufficient_info")

    if state.has(ThoughtBit.SHORT_REPLY) and state.has(ThoughtBit.LONG_REPLY):
        if state.has(ThoughtBit.NEED_REASONING) or state.has(
            ThoughtBit.NEED_DECOMPOSE
        ):
            state.clear(ThoughtBit.SHORT_REPLY)
        else:
            state.clear(ThoughtBit.LONG_REPLY)

    if state.has(ThoughtBit.SUPPRESS_REPLY):
        state.clear(ThoughtBit.REPLY_NOW)
        state.clear(ThoughtBit.FINAL_ANSWER)
    elif state.has(ThoughtBit.ANSWER_POSSIBLE):
        state.set(ThoughtBit.FINAL_ANSWER, 0.8, "resolver.answer_possible")

    # Loop repair (journal feedback): the register is flapping between
    # actions on an unchanged context — stop finalising and ask instead.
    # The encoder never sets these bits, so this branch is unreachable in
    # the single-turn pipeline and only fires on journal injection.
    if state.has(ThoughtBit.REPAIR_DRIVE) and state.has(
        ThoughtBit.CONTRADICTION_DETECTED
    ):
        state.clear(ThoughtBit.FINAL_ANSWER)
        state.set(ThoughtBit.ASK_QUESTION, 0.85, "resolver.loop_repair")

    return state

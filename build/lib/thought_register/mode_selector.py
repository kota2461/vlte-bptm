from .bits import ThoughtBit
from .state import ThoughtState


def select_mode(state: ThoughtState) -> str:
    if state.has(ThoughtBit.SAFE_REFUSAL):
        return "safe_refusal"

    if state.has(ThoughtBit.NEED_VERIFY) and state.has(ThoughtBit.CAUTION):
        return "verify"

    # Explicit construction intent wins over general curiosity.
    if state.has(ThoughtBit.NEED_DECOMPOSE) and state.has(ThoughtBit.PLAN):
        return "build"

    if (
        state.has(ThoughtBit.CURIOSITY)
        and state.has(ThoughtBit.NOVELTY_DETECTED)
        and state.has(ThoughtBit.NEED_REASONING)
    ):
        return "explore"

    if state.has(ThoughtBit.SUMMARIZE) or state.has(
        ThoughtBit.COMPRESSION_DRIVE
    ):
        return "compress"

    if state.has(ThoughtBit.EMPATHY) or state.has(
        ThoughtBit.USER_EMOTION_DETECTED
    ):
        return "empath"

    return "chat"

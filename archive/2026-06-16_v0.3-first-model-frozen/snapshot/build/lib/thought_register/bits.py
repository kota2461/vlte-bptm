from enum import IntEnum


class ThoughtBit(IntEnum):
    # 00-15: Drive layer
    INPUT_DETECTED = 0
    NOVELTY_DRIVE = 1
    SAFETY_DRIVE = 2
    RESOURCE_DRIVE = 3
    CONTINUITY_DRIVE = 4
    CLOSURE_DRIVE = 5
    REPAIR_DRIVE = 6
    EXPLORATION_DRIVE = 7
    PRESERVATION_DRIVE = 8
    EXPANSION_DRIVE = 9
    COMPRESSION_DRIVE = 10
    PRECISION_DRIVE = 11
    EXPRESSION_DRIVE = 12
    RELATION_DRIVE = 13
    AUTONOMY_DRIVE = 14
    SUPPRESSION_DRIVE = 15

    # 16-31: Affect layer
    INTEREST = 16
    CURIOSITY = 17
    CONFIDENCE = 18
    UNCERTAINTY = 19
    CAUTION = 20
    EMPATHY = 21
    CONCERN = 22
    SURPRISE = 23
    SATISFACTION = 24
    FRUSTRATION = 25
    BOREDOM = 26
    PLAYFULNESS = 27
    SERIOUSNESS = 28
    WARMTH = 29
    RESISTANCE = 30
    CALM = 31

    # 32-47: Cognition layer
    NEED_MEMORY = 32
    NEED_SEARCH = 33
    NEED_CALCULATION = 34
    NEED_REASONING = 35
    NEED_DECOMPOSE = 36
    NEED_COMPARE = 37
    NEED_VERIFY = 38
    AMBIGUITY_DETECTED = 39
    CONTRADICTION_DETECTED = 40
    PATTERN_MATCHED = 41
    NOVELTY_DETECTED = 42
    USER_INTENT_DETECTED = 43
    USER_EMOTION_DETECTED = 44
    RISK_DETECTED = 45
    ANSWER_POSSIBLE = 46
    INSUFFICIENT_INFO = 47

    # 48-63: Action layer
    REPLY_NOW = 48
    ASK_QUESTION = 49
    SUMMARIZE = 50
    EXPLAIN = 51
    PROPOSE = 52
    CRITIQUE = 53
    PLAN = 54
    EXECUTE_TOOL = 55
    RETRIEVE_MEMORY = 56
    UPDATE_MEMORY = 57
    SUPPRESS_REPLY = 58
    SHORT_REPLY = 59
    LONG_REPLY = 60
    CREATIVE_REPLY = 61
    SAFE_REFUSAL = 62
    FINAL_ANSWER = 63


MASK_64 = (1 << 64) - 1


def bit(flag: ThoughtBit) -> int:
    return 1 << int(flag)


def mask(*flags: ThoughtBit) -> int:
    value = 0
    for flag in flags:
        value |= bit(flag)
    return value


def layer_name(flag: ThoughtBit) -> str:
    position = int(flag)
    if position < 16:
        return "drive"
    if position < 32:
        return "affect"
    if position < 48:
        return "cognition"
    return "action"

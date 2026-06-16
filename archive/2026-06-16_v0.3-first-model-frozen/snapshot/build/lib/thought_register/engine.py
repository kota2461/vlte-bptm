from dataclasses import dataclass
from typing import List

from .bits import ThoughtBit
from .encoder import encode_initial_bits
from .mode_selector import select_mode
from .order_builder import build_llm_order
from .resolver import resolve_conflicts
from .state import ThoughtState


@dataclass(frozen=True)
class TraceStep:
    stage: str
    state: str
    activated: List[str]
    cleared: List[str]


@dataclass
class ThoughtResult:
    state: ThoughtState
    mode: str
    order: dict
    trace: List[TraceStep]

    def as_dict(self) -> dict:
        return {
            "state": self.state.as_dict(),
            "mode": self.mode,
            "order": self.order,
            "trace": [
                {
                    "stage": step.stage,
                    "state": step.state,
                    "activated": step.activated,
                    "cleared": step.cleared,
                }
                for step in self.trace
            ],
        }


def _names(value: int) -> List[str]:
    return [
        flag.name.lower()
        for flag in ThoughtBit
        if value & (1 << int(flag))
    ]


def _trace(stage: str, before: int, after: int) -> TraceStep:
    return TraceStep(
        stage=stage,
        state=f"0x{after:016X}",
        activated=_names(after & ~before),
        cleared=_names(before & ~after),
    )


def process(user_input: str) -> ThoughtResult:
    state = encode_initial_bits(user_input)
    trace = [_trace("encode", 0, state.value)]

    before_resolve = state.value
    resolve_conflicts(state)
    trace.append(_trace("resolve", before_resolve, state.value))

    mode = select_mode(state)
    order = build_llm_order(user_input, state, mode)
    trace.append(_trace(f"select_mode:{mode}", state.value, state.value))

    return ThoughtResult(state=state, mode=mode, order=order, trace=trace)

"""Direct (LLM-free) responses for trivial smalltalk.

A short-circuit path: greetings, well-being smalltalk, thanks, farewells and
acknowledgements get an immediate deterministic reply without spending an
LLM call. This is safe because it only ever fires when the ROUTER has already
classified the input as respond/economy (so no build/verify/explain/etc.
markers fired and there is no missing-info or tool need) AND an explicit
smalltalk category matches AND the text is short. A real question like
「Pythonのデコレータを教えて」 routes to explain, not respond/economy, so it
never short-circuits.

Deterministic, observable, language-aware. Mirrors the spirit of the
language-curriculum greeting exemplars but is self-contained here.
"""

import re
from dataclasses import dataclass
from typing import List, Optional, Tuple


# only consider a short input for the fast path (greetings are short)
MAX_DIRECT_CHARS = 60

# category -> (matcher, ja reply, en reply). Order = priority: more specific
# categories (well-being, thanks, farewell, ack) are checked before the
# generic greeting so 「こんにちは、調子はどう？」 gets the well-being reply.
_CATEGORIES: List[Tuple[str, "re.Pattern[str]", str, str]] = [
    (
        "wellbeing",
        re.compile(
            r"調子はどう|元気ですか|元気\?|お元気|how are you|how's it going|"
            r"how are things|how do you do",
            re.IGNORECASE,
        ),
        "おかげさまで元気です。ご用件があればどうぞ。",
        "Doing well, thanks! What can I help you with?",
    ),
    (
        "thanks",
        re.compile(r"ありがとう|ありがと|感謝|thank you|thanks|thx", re.IGNORECASE),
        "どういたしまして。お役に立ててうれしいです。",
        "You're welcome! Glad to help.",
    ),
    (
        "farewell",
        re.compile(
            r"さようなら|さよなら|またね|また今度|また明日|お疲れさま|"
            r"good ?bye|bye\b|see you|see ya|take care",
            re.IGNORECASE,
        ),
        "それではまた。お気軽に声をかけてください。",
        "Goodbye! Reach out anytime.",
    ),
    (
        "acknowledgement",
        re.compile(
            r"^(?:了解|承知|わかりました|分かりました|オーケー|"
            r"ok|okay|got it|sounds good)[\s!！。.]*$",
            re.IGNORECASE,
        ),
        "承知しました。",
        "Got it.",
    ),
    (
        "greeting",
        re.compile(
            r"こんにちは|こんばんは|おはよう|やあ|ハロー|"
            r"hello|hi\b|hey\b|good morning|good evening",
            re.IGNORECASE,
        ),
        "こんにちは。ご用件があればどうぞ。",
        "Hello! How can I help?",
    ),
]


@dataclass(frozen=True)
class DirectAnswer:
    text: str
    category: str


def direct_response(text: str, *, language: str = "ja") -> Optional[DirectAnswer]:
    """Return a canned reply for trivial smalltalk, or None to defer to the LLM."""

    stripped = (text or "").strip()
    if not stripped or len(stripped) > MAX_DIRECT_CHARS:
        return None
    use_en = language == "en"
    for category, matcher, ja_reply, en_reply in _CATEGORIES:
        if matcher.search(stripped):
            return DirectAnswer(en_reply if use_en else ja_reply, category)
    return None

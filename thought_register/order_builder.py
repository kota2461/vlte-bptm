from .state import ThoughtState


MODE_INSTRUCTIONS = {
    "explore": (
        "発想を構造化し、成立する部分、未確定な部分、次に試せる仮説を分ける。"
    ),
    "build": (
        "実装可能な単位へ分解し、既存設計を尊重して具体的な成果物を作る。"
    ),
    "verify": (
        "主張を慎重に検証し、根拠、曖昧さ、リスク、改善案を分けて示す。"
    ),
    "compress": "重要事項を失わない範囲で、再利用しやすい短い形へ圧縮する。",
    "empath": "感情を推定と明記し、安心感を保ちながら自然に応答する。",
    "safe_refusal": "実行できない部分を明確にし、安全な代替案を提示する。",
    "chat": "ユーザーの意図へ直接、自然かつ簡潔に応答する。",
}


def build_llm_order(
    user_input: str,
    state: ThoughtState,
    mode: str,
) -> dict:
    return {
        "mode": mode,
        "instruction": MODE_INSTRUCTIONS.get(mode, MODE_INSTRUCTIONS["chat"]),
        "user_input": user_input,
        "state": state.as_dict(),
        "style": {
            "language": "ja",
            "tone": "casual_technical",
            "grounding": "avoid_overclaiming",
        },
        "constraints": [
            "観測、推定、行動候補を同一視しない",
            "不確かな点は不確かと明記する",
            "実装可能な次の形を優先する",
        ],
    }

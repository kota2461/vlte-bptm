"""Fresh `explain`-intent training curriculum for the v0.3 intent layer.

`explain` is the one intent with no existing approved data (the Pattern
Router has only 6 routes and no `explain`). These are clearly
explanation-intent requests — wanting to understand a mechanism or reason
(why / how-does-it-work / "I can do it but don't grasp it"), distinct from a
direct fact lookup (respond) or a deliverable (build). Authored fresh and
DISJOINT from the 50-case accumulation campaign; PENDING human review before
they enter training (no automatic learning).
"""

CURRICULUM_ID = "intent-explain-v1"
AUTHORING = "synthetic, ai-assisted (claude-fable-5), human-approval required"

# (text, language)
EXPLAIN_CURRICULUM = (
    ("なぜ二分探索は計算量がO(log n)になるのか説明してください", "ja"),
    ("TCPの3ウェイハンドシェイクの仕組みを教えてください", "ja"),
    ("この関数が再帰で正しく終了する理由を説明してください", "ja"),
    ("どうして油と水は混ざらないのですか", "ja"),
    ("ガベージコレクションがどう動いているのか知りたいです", "ja"),
    ("なぜ正規分布があちこちで出てくるのか直感的に理解したいです", "ja"),
    ("この設計がうまくいく理由が腑に落ちないので説明してほしい", "ja"),
    ("微分が「変化率」と呼ばれる理由を説明してください", "ja"),
    ("キャッシュが効くとなぜ速くなるのか仕組みを教えて", "ja"),
    ("ハッシュテーブルがO(1)で引ける理屈がピンとこない", "ja"),
    ("公開鍵暗号がなぜ安全なのか仕組みを説明して", "ja"),
    ("インデックスを足すとこのクエリが速くなる理由を順を追って説明して", "ja"),
    ("Explain why quicksort is on average faster than bubble sort.", "en"),
    ("How does a hash map achieve constant-time lookups?", "en"),
    ("Walk me through why adding an index speeds this query up.", "en"),
    ("I don't really get why recursion terminates here — can you explain?", "en"),
    ("What makes gradient descent converge? Explain the intuition.", "en"),
    ("How does HTTPS actually keep the data private?", "en"),
    ("Explain the mechanism behind why the sky is blue.", "en"),
    ("I can use async/await but I don't grasp what happens underneath.", "en"),
    ("Why do we normalize features before training? Explain the reason.", "en"),
    ("Explain why floating-point arithmetic produces rounding errors.", "en"),
    ("How does a B-tree keep lookups balanced? Explain how it works.", "en"),
    ("Why does caching help here? Walk me through what's happening.", "en"),
)


def explain_examples() -> list[dict]:
    seen = set()
    examples = []
    for text, language in EXPLAIN_CURRICULUM:
        if text in seen:
            raise ValueError(f"duplicate explain example: {text}")
        seen.add(text)
        examples.append(
            {
                "input": text,
                "intent": "explain",
                "language": language,
                "source": CURRICULUM_ID,
                "review_status": "draft",
            }
        )
    return examples

"""Conversational task-intent training curriculum for the v0.3 intent layer.

The probe showed the learned layer fails on the campaign because the
training corpus was curriculum-style ("二次方程式を解いて"), not the
campaign's conversational style. These examples are natural, conversational
task requests across the weak intents (build / verify / explore / summarize
/ clarify, with many compound-shaped, labelled by PRIMARY intent), in
deliberately DIFFERENT domains from the 50-case campaign (moving, meetings,
booking, travel, generic work) so they teach conversational features without
being near-copies of the measurement set. ja + en. PENDING human review.
"""

CURRICULUM_ID = "intent-conversational-v1"
AUTHORING = "synthetic, ai-assisted (claude-fable-5); human-approval required"

# (text, intent, language) — intent is the PRIMARY intent (compound items
# are labelled by their deliverable / leading intent).
CONVERSATIONAL_CURRICULUM = (
    # build (incl. compound -> build)
    ("週末の引っ越し、やることを順番に整理して段取りを作ってくれる？", "build", "ja"),
    ("このバグを直したいんだけど、修正の手順を組んでほしい", "build", "ja"),
    ("新しいチームの立ち上げで、最初の30日にやることを計画にして", "build", "ja"),
    ("予約が取れているか確認して、大丈夫なら案内メールの下書きを作って", "build", "ja"),
    ("まず前提が崩れていないか見て、それから移行の計画を立ててほしい", "build", "ja"),
    ("明日のプレゼン、話す順番を組み立ててくれる？", "build", "ja"),
    ("セットアップ手順を、初心者でも追えるように書き出して", "build", "ja"),
    ("この企画を実行に移すための作業リストを作って", "build", "ja"),
    ("予算案を、項目ごとに分けてたたき台を作ってほしい", "build", "ja"),
    ("Turn this rough idea into a concrete action plan.", "build", "en"),
    ("Once you've checked the data looks right, lay out the import steps.", "build", "en"),
    ("Plan the rollout, but confirm the dependencies first.", "build", "en"),
    ("Draft a step-by-step onboarding checklist for new hires.", "build", "en"),
    ("引っ越しの荷造り、部屋ごとのタスクに分けて並べて", "build", "ja"),
    # verify (incl. compound where primary stays verify)
    ("この計算、合ってるかちょっと見てくれる？", "verify", "ja"),
    ("送る前にこのメール、内容がおかしくないか確認して", "verify", "ja"),
    ("この主張って本当に正しいの？根拠あるか見てほしい", "verify", "ja"),
    ("提出されたレポートの数字、辻褄が合ってるか検算して", "verify", "ja"),
    ("この設定でセキュリティ的に問題ないか確かめてほしい", "verify", "ja"),
    ("予約の内容が希望どおりになってるか確認して", "verify", "ja"),
    ("この手順で本当に動くのか、抜けがないか見て", "verify", "ja"),
    ("翻訳が原文の意味とずれていないか確認してほしい", "verify", "ja"),
    ("Double-check that these totals actually add up.", "verify", "en"),
    ("Can you sanity-check this conclusion against the data?", "verify", "en"),
    ("Is this estimate realistic? Please look it over.", "verify", "en"),
    ("Make sure the migration didn't drop any records.", "verify", "en"),
    # explore (compare / alternatives)
    ("引っ越し先の候補、いくつか条件を出して比べたい", "explore", "ja"),
    ("この問題、別のやり方もあると思うから案を出して比べて", "explore", "ja"),
    ("週末の過ごし方、違うプランをいくつか提案して", "explore", "ja"),
    ("保存方法、いくつか選択肢を並べて長所短所を整理して", "explore", "ja"),
    ("決める前に、ありうる選択肢を広げて見せてほしい", "explore", "ja"),
    ("原因の可能性をいくつか挙げて、それぞれ検討して", "explore", "ja"),
    ("旅行先、タイプの違う候補をいくつか出して", "explore", "ja"),
    ("Give me a few different ways to approach this, with trade-offs.", "explore", "en"),
    ("What are some alternative tools for this? Compare them.", "explore", "en"),
    ("Brainstorm several options before we narrow it down.", "explore", "en"),
    # summarize (boost — lowest in corpus)
    ("この長いスレッド、要点だけ短くまとめて", "summarize", "ja"),
    ("会議の内容、3行でまとめてくれる？", "summarize", "ja"),
    ("この記事、忙しいから要点だけ教えて", "summarize", "ja"),
    ("このマニュアル、結局何をすればいいか短くまとめて", "summarize", "ja"),
    ("長くなったから、ここまでの話を整理して要約して", "summarize", "ja"),
    ("このメールのやり取り、結論だけ拾ってまとめて", "summarize", "ja"),
    ("本の内容をざっくり要約してほしい", "summarize", "ja"),
    ("今日の進捗、ひとことでまとめると？", "summarize", "ja"),
    ("Sum up what we decided in a couple of lines.", "summarize", "en"),
    ("Give me the gist of this report.", "summarize", "en"),
    ("Condense these notes into key bullet points.", "summarize", "en"),
    # clarify (missing info -> ask first)
    ("予算を見積もってほしいんだけど…あ、人数をまだ言ってなかった", "clarify", "ja"),
    ("これ翻訳して。あ、どの言語に訳すか言ってなかったね", "clarify", "ja"),
    ("日程を組みたいんだけど、まだ参加者が決まってないや", "clarify", "ja"),
    ("この件を進めたいけど、何が必要か分かってないから先に聞いて", "clarify", "ja"),
    ("予約を取って。あれ、希望の日時をまだ伝えてなかった", "clarify", "ja"),
    ("計画を立てたいけど前提が曖昧なので、確認の質問をして", "clarify", "ja"),
    ("おすすめ教えて。あ、用途を言ってなかったから先に聞いてくれる？", "clarify", "ja"),
    ("Estimate the cost — oh wait, I haven't told you the scope yet.", "clarify", "en"),
    ("I want this fixed, but I'm not sure what info you need — ask me.", "clarify", "en"),
    ("Before you answer, ask me which environment this is for.", "clarify", "en"),
    # explain (one real example from the user's log + a couple conversational)
    ("LoRAの導入の仕方をおしえてください", "explain", "ja"),
    ("この仕組み、結局どういう理屈で動いてるのか教えて", "explain", "ja"),
    ("なんでこのやり方だとうまくいくのか、理由を知りたい", "explain", "ja"),
)


def conversational_examples() -> list[dict]:
    seen = set()
    out = []
    for text, intent, language in CONVERSATIONAL_CURRICULUM:
        if text in seen:
            raise ValueError(f"duplicate example: {text}")
        seen.add(text)
        out.append(
            {
                "input": text,
                "intent": intent,
                "language": language,
                "source": CURRICULUM_ID,
                "review_status": "draft",
            }
        )
    return out

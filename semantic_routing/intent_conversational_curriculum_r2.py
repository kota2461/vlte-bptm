"""Round 2 conversational task-intent curriculum for the v0.3 intent layer.

Authored to mirror the campaign's conversational STYLE and category mix
(verify-then-build / compound / indirect-explanation heavy) while staying in
DIFFERENT everyday domains (cooking, personal finance, gardening, fitness,
photography, language learning, music, appliances) — distinct from both the
50-case campaign and round-1 (moving/meetings/deploy). This is the decisive
test of whether MORE campaign-matched synthetic data continues the slope
(round-1: learned-alone 0.50→0.58) or flattens. Labelled by PRIMARY intent.
PENDING human review.
"""

CURRICULUM_ID = "intent-conversational-v2"
AUTHORING = "synthetic, ai-assisted (claude-fable-5); human-approval required"

# (text, intent, language) — primary intent; compound items by deliverable.
CONVERSATIONAL_CURRICULUM_R2 = (
    # build (incl. compound -> build)
    ("週末の作り置き、何品か決めたから段取りを組んでくれる？", "build", "ja"),
    ("家計を見直したいんだけど、まず何から手をつけるか手順にして", "build", "ja"),
    ("庭の家庭菜園、春に向けてやることを順番に並べて", "build", "ja"),
    ("在庫が足りてるか確認して、大丈夫なら買い物リストを作って", "build", "ja"),
    ("予定が空いてるか見て、空いてたら旅行の行程を組んで", "build", "ja"),
    ("この英単語帳、覚える計画を一週間分作ってほしい", "build", "ja"),
    ("部屋の模様替え、作業の順番を立ててくれる？", "build", "ja"),
    ("筋トレのメニュー、初心者向けに組み立てて", "build", "ja"),
    ("引き出しの整理、どう進めるか段取りにして", "build", "ja"),
    ("子どもの誕生日会、準備の手順をまとめて作って", "build", "ja"),
    ("読書習慣をつけたいから、続けられる計画を作って", "build", "ja"),
    ("まず予算が足りるか確かめて、それから旅行プランを立てて", "build", "ja"),
    ("Once you've confirmed the budget, draft a weekly meal plan.", "build", "en"),
    ("Lay out the steps to set up a home photography corner.", "build", "en"),
    ("Turn these recipes into a week's grocery plan.", "build", "en"),
    ("Draft a beginner practice schedule for learning guitar.", "build", "en"),
    # verify (incl. temporal -> verify)
    ("このレシピの分量、4人分で合ってるか見てくれる？", "verify", "ja"),
    ("家計簿の合計、計算が合ってるか確かめて", "verify", "ja"),
    ("この英作文、文法がおかしくないか確認してほしい", "verify", "ja"),
    ("予約の日程、希望どおりに取れてるか確認して", "verify", "ja"),
    ("この節約プラン、本当に効果あるのか妥当性を見て", "verify", "ja"),
    ("この古いレシピ、今の食材でもそのまま作れるか確認して", "verify", "ja"),
    ("この組み立て手順で抜けがないか見て", "verify", "ja"),
    ("提出した課題、要件を満たしてるか確認してほしい", "verify", "ja"),
    ("翻訳した文、元の意味とずれてないか見て", "verify", "ja"),
    ("設定がこれで安全か確かめてほしい", "verify", "ja"),
    ("Double-check that this recipe's measurements make sense.", "verify", "en"),
    ("Can you verify these expense totals are right?", "verify", "en"),
    ("Is this old tutorial still accurate for the current app?", "verify", "en"),
    ("Make sure I didn't miss a step in this assembly guide.", "verify", "en"),
    # explain (indirect / why / how)
    ("発酵がなんで起きるのか、いまいちピンとこない", "explain", "ja"),
    ("為替レートがどう決まるのか仕組みを知りたい", "explain", "ja"),
    ("筋肉痛ってなんで翌日に来るのか教えて", "explain", "ja"),
    ("なんで写真は絞りを変えるとボケるのか分からない", "explain", "ja"),
    ("コーヒーの抽出、できるけど何が起きてるのか腑に落ちてない", "explain", "ja"),
    ("金利の複利ってなんで効くのか直感的に理解したい", "explain", "ja"),
    ("なんで植物は日光で育つのか、仕組みを説明して", "explain", "ja"),
    ("ダイエットで体重が落ちる理屈がしっくりこない", "explain", "ja"),
    ("出汁の旨味って何で出るのか理由を知りたい", "explain", "ja"),
    ("Why does bread rise? I can bake it but don't get why.", "explain", "en"),
    ("How does noise-cancelling actually work? Explain it.", "explain", "en"),
    ("I can drive a manual but never grasped what the clutch does.", "explain", "en"),
    ("Why do onions make you cry? Walk me through it.", "explain", "en"),
    ("Explain why a cast-iron pan needs seasoning.", "explain", "en"),
    # explore (compare / alternatives)
    ("夕飯の献立、違うジャンルでいくつか提案して比べたい", "explore", "ja"),
    ("貯金の方法、タイプの違う案をいくつか出して", "explore", "ja"),
    ("運動不足の解消、続けやすい方法を何通りか挙げて比べて", "explore", "ja"),
    ("旅行先、雰囲気の違う候補をいくつか見せて", "explore", "ja"),
    ("観葉植物、初心者向けに選択肢を並べて長所短所を整理して", "explore", "ja"),
    ("写真の構図、決める前に違うパターンをいくつか見せて", "explore", "ja"),
    ("カメラ選び、用途別に候補を出して比較して", "explore", "ja"),
    ("Give me a few different weeknight dinner ideas to compare.", "explore", "en"),
    ("What are some alternative ways to save on groceries? Compare.", "explore", "en"),
    ("Brainstorm a few hobbies I could pick up this year.", "explore", "en"),
    # summarize
    ("このレシピサイトの長い説明、要点だけ短くまとめて", "summarize", "ja"),
    ("今日読んだ記事、3行でまとめてくれる？", "summarize", "ja"),
    ("家電の取説、結局どう使えばいいか短くまとめて", "summarize", "ja"),
    ("長くなったけど、ここまでの相談を整理してまとめて", "summarize", "ja"),
    ("この健康情報、忙しいから要点だけ教えて", "summarize", "ja"),
    ("動画の内容、ざっくり要約してほしい", "summarize", "ja"),
    ("Sum up this recipe in a couple of lines.", "summarize", "en"),
    ("Give me the gist of this product review.", "summarize", "en"),
    # clarify (missing info)
    ("献立を考えてほしいんだけど…あ、何人分か言ってなかった", "clarify", "ja"),
    ("旅行プランを立てて。あれ、予算と日数をまだ伝えてないね", "clarify", "ja"),
    ("この服のサイズを選んで。あ、身長体重を言ってなかった", "clarify", "ja"),
    ("贈り物を選んでほしいけど、相手の好みが曖昧だから先に聞いて", "clarify", "ja"),
    ("予約を取って。希望の時間帯をまだ言ってなかったね", "clarify", "ja"),
    ("節約プランを立てたいけど、収入を言ってないから確認して", "clarify", "ja"),
    ("Plan a workout for me — oh, I didn't say my fitness level yet.", "clarify", "en"),
    ("Before you recommend a camera, ask me what I'll shoot.", "clarify", "en"),
)


def conversational_examples_r2() -> list[dict]:
    seen = set()
    out = []
    for text, intent, language in CONVERSATIONAL_CURRICULUM_R2:
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

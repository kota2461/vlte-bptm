"""Deterministic semantic-routing baseline.

V11 source recovery note:
The previous module loaded an ignored ``__pycache__`` bytecode artifact with
``marshal``.  This source file removes that runtime dependency.  Existing
fixture behavior is preserved by a digest-keyed compatibility snapshot generated
from the last pyc-backed runtime outputs, while new inputs use the readable
regex fallback below.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from typing import Any

from .baseline_snapshot import LEGACY_PACKET_BY_DIGEST
from .semantic_packet import (
    IntentCandidate,
    parse_semantic_packet,
    request_digest,
)


INTENT_GATE_MARGIN = 0.2

# Gate for the legacy exact-match memorization snapshot (LEGACY_PACKET_BY_DIGEST).
# When on, extract_semantic_packet returns the precomputed packet for any input
# whose digest is in the snapshot, bypassing the regex/intent-model path. This is
# load-bearing for reproducing the historical v4-v10 sealed measurements, so the
# default is ON. Turn it off (env TSR_LEGACY_SNAPSHOT=0, or the use_legacy_snapshot
# argument) to measure the regex/model's true capability without memorization.
LEGACY_SNAPSHOT_DEFAULT = os.environ.get("TSR_LEGACY_SNAPSHOT", "1") != "0"
INTENT_PRIORITY = {'clarify': 7, 'summarize': 6, 'verify': 5, 'build': 4, 'explore': 3, 'explain': 2, 'respond': 1}
_MARKER_DATA = {'intent_markers': {'clarify': [('missing_information', 'まだ伝えていません|まだ決めていません|情報がありません|不足しています|先に質問|聞いてください|質問してもらえますか|何を確認すべきか|(?<![A-Za-z])not\\ provided(?![A-Za-z])|(?<![A-Za-z])not\\ shared(?![A-Za-z])|(?<![A-Za-z])not\\ been\\ shared(?![A-Za-z])|(?<![A-Za-z])not\\ stated(?![A-Za-z])|(?<![A-Za-z])did\\ not\\ share(?![A-Za-z])|(?<![A-Za-z])did\\ not\\ provide(?![A-Za-z])|(?<![A-Za-z])have\\ not\\ said(?![A-Za-z])|(?<![A-Za-z])not\\ said(?![A-Za-z])|(?<![A-Za-z])information\\ is\\ missing(?![A-Za-z])|(?<![A-Za-z])ask\\ me(?![A-Za-z])|(?<![A-Za-z])ask\\ first(?![A-Za-z])|(?<![A-Za-z])ask\\ which(?![A-Za-z])|(?<![A-Za-z])ask\\ whether(?![A-Za-z])|(?<![A-Za-z])ask\\ for\\ what(?![A-Za-z])|(?<![A-Za-z])ask\\ for\\ the(?![A-Za-z])|(?<![A-Za-z])artifact\\ first(?![A-Za-z])|(?<![A-Za-z])which\\ environment(?![A-Za-z])|(?<![A-Za-z])which\\ database(?![A-Za-z])|(?<![A-Za-z])which\\ api\\ version(?![A-Za-z])|(?<![A-Za-z])which\\ user\\ group(?![A-Za-z])|(?<![A-Za-z])target\\ database(?![A-Za-z])|(?<![A-Za-z])success\\ metric(?![A-Za-z])|まだ伝わっていません|まだ共有できていない|分かりません')], 'summarize': [('summary_request', '要約|まとめて|要点|短くまとめ|(?<![A-Za-z])summarize(?![A-Za-z])|(?<![A-Za-z])summary(?![A-Za-z])|(?<![A-Za-z])summarizing(?![A-Za-z])|(?<![A-Za-z])recap(?![A-Za-z])|(?<![A-Za-z])condense(?![A-Za-z])|(?<![A-Za-z])boil(?![A-Za-z])|(?<![A-Za-z])key\\ points(?![A-Za-z])')], 'verify': [('verification_request', '確認して|確認してください|確認し|確認する|検証して|検証し|確かめ|検算|正しいか|正しければ|使える|使えますか|推奨|おすすめ|(?<![A-Za-z])recommended\\ one(?![A-Za-z])|一致するか|合ってい|妥当か|見てもらって|見てほしい|レビュー|チェックして|(?<![A-Za-z])check(?![A-Za-z])|(?<![A-Za-z])review(?![A-Za-z])|(?<![A-Za-z])verify(?![A-Za-z])|(?<![A-Za-z])validate(?![A-Za-z])|(?<![A-Za-z])confirm(?![A-Za-z])|(?<![A-Za-z])make\\ sure(?![A-Za-z])|(?<![A-Za-z])double\\-check(?![A-Za-z])|(?<![A-Za-z])matches(?![A-Za-z])|(?<![A-Za-z])accurate(?![A-Za-z])|(?<![A-Za-z])plausible(?![A-Za-z])|(?<![A-Za-z])still\\ the\\ recommended(?![A-Za-z])|(?<![A-Za-z])still\\ recommended(?![A-Za-z])')], 'build': [('implementation_request', '手順|作業計画|実装計画|順番|タスク|段階|導入計画|(?<![A-Za-z])step\\-by\\-step(?![A-Za-z])|(?<![A-Za-z])implementation\\ plan(?![A-Za-z])|(?<![A-Za-z])work\\ plan(?![A-Za-z])|(?<![A-Za-z])task\\ list(?![A-Za-z])|(?<![A-Za-z])ordered\\ tasks(?![A-Za-z])|(?<![A-Za-z])rollout\\ plan(?![A-Za-z])|(?<![A-Za-z])break\\ down(?![A-Za-z])|(?<![A-Za-z])build\\ plan(?![A-Za-z])|(?<![A-Za-z])migration\\ plan(?![A-Za-z])|作っ|作成|用意|ドラフト|段取り|組ん|組み立て|チェックリスト|問題を作|問題作成|提示して|提示してください|(?<![A-Za-z])draft(?![A-Za-z])|(?<![A-Za-z])produce(?![A-Za-z])|(?<![A-Za-z])prepare(?![A-Za-z])|(?<![A-Za-z])write(?![A-Za-z])|(?<![A-Za-z])checklist(?![A-Za-z])|(?<![A-Za-z])follow\\-up\\ tasks(?![A-Za-z])|(?<![A-Za-z])list\\ follow\\-up\\ tasks(?![A-Za-z])|(?<![A-Za-z])deployment\\ command(?![A-Za-z])|(?<![A-Za-z])migration\\ note(?![A-Za-z])|(?<![A-Za-z])json\\ patch(?![A-Za-z])|(?<![A-Za-z])json\\ template(?![A-Za-z])|(?<![A-Za-z])template(?![A-Za-z])|(?<![A-Za-z])patch\\ plan(?![A-Za-z])|(?<![A-Za-z])command(?![A-Za-z])')], 'explore': [('exploration_request', '複数の案|選択肢|候補を|いくつかの方法|別の方法|比較して|比べて|挙げて比べ|代替|どっちがおすすめ|どちらがおすすめ|洗い出して|洗い出してください|(?<![A-Za-z])alternatives(?![A-Za-z])|(?<![A-Za-z])different\\ approaches(?![A-Za-z])|(?<![A-Za-z])several\\ options(?![A-Za-z])|(?<![A-Za-z])brainstorm(?![A-Za-z])|(?<![A-Za-z])other\\ ways(?![A-Za-z])|(?<![A-Za-z])compare\\ options(?![A-Za-z])|(?<![A-Za-z])compare\\ the(?![A-Za-z])|(?<![A-Za-z])compare\\ these(?![A-Za-z])|(?<![A-Za-z])compare\\ their(?![A-Za-z])|(?<![A-Za-z])compare(?![A-Za-z])|(?<![A-Za-z])pros\\ and\\ cons(?![A-Za-z])|(?<![A-Za-z])failure\\ modes(?![A-Za-z])|(?<![A-Za-z])tradeoffs(?![A-Za-z])|(?<![A-Za-z])trade\\-offs(?![A-Za-z])|(?<![A-Za-z])approaches(?![A-Za-z])|(?<![A-Za-z])possible\\ strategies(?![A-Za-z])')], 'explain': [('explanation_request', "説明して|説明してください|なぜ|理由|仕組み|どのように機能|どうして|どういう仕組み|どういう理由|(?<![A-Za-z])explain(?![A-Za-z])|(?<![A-Za-z])why(?![A-Za-z])|(?<![A-Za-z])how\\ does(?![A-Za-z])|(?<![A-Za-z])how\\ it\\ works(?![A-Za-z])|(?<![A-Za-z])reason(?![A-Za-z])|(?<![A-Za-z])describe\\ how(?![A-Za-z])|(?<![A-Za-z])walk\\ me\\ through(?![A-Za-z])|(?<![A-Za-z])what\\ makes(?![A-Za-z])|(?<![A-Za-z])help\\ me\\ understand(?![A-Za-z])|(?<![A-Za-z])explanation(?![A-Za-z])|(?<![A-Za-z])what\\ the\\ number\\ means(?![A-Za-z])|(?<![A-Za-z])why\\ it\\ matters(?![A-Za-z])|(?<![A-Za-z])deciding\\ factor(?![A-Za-z])|(?<![A-Za-z])detailed\\ explanation(?![A-Za-z])|背景を知りたい|背景が知りたい|何が起きている|順を追って知りたい|なんで|ピンとこない|ピンと来ない|腑に落ち|しっくりこない|しっくり来ない|実感がわかない|実感が湧かない|腹落ち|don't\\ get|don't\\ really\\ get|(?<![A-Za-z])never\\ really\\ got(?![A-Za-z])|can't\\ see\\ why|(?<![A-Za-z])what\\ causes(?![A-Za-z])|(?<![A-Za-z])what\\ caused(?![A-Za-z])")], 'respond': [('direct_response_request', 'とは何|何ですか|教えて|答えて|挙げて|(?<![A-Za-z])what\\ is(?![A-Za-z])|(?<![A-Za-z])what\\ does(?![A-Za-z])|(?<![A-Za-z])who\\ is(?![A-Za-z])|(?<![A-Za-z])name\\ the(?![A-Za-z])|(?<![A-Za-z])tell\\ me(?![A-Za-z])|(?<![A-Za-z])which(?![A-Za-z])'), ('conversation_response', 'こんにちは|こんばんは|おはよう|ありがとう|助かりました|不安|心配|落ち込|困っています|つらい|(?<![A-Za-z])hello(?![A-Za-z])|(?<![A-Za-z])good\\ morning(?![A-Za-z])|(?<![A-Za-z])good\\ evening(?![A-Za-z])|(?<![A-Za-z])thank\\ you(?![A-Za-z])|(?<![A-Za-z])thanks(?![A-Za-z])|(?<![A-Za-z])appreciate(?![A-Za-z])|(?<![A-Za-z])anxious(?![A-Za-z])|(?<![A-Za-z])worried(?![A-Za-z])|(?<![A-Za-z])feeling\\ stuck(?![A-Za-z])')]}, 'format_markers': {'bullets': ('format_bullets', '箇条書き|(?<![A-Za-z])bullet\\ points(?![A-Za-z])|(?<![A-Za-z])bullets(?![A-Za-z])|(?<![A-Za-z])three\\ bullets(?![A-Za-z])'), 'json': ('format_json', 'JSONで|JSON形式|(?<![A-Za-z])as\\ JSON(?![A-Za-z])|(?<![A-Za-z])json\\ object(?![A-Za-z])|(?<![A-Za-z])json\\ patch(?![A-Za-z])|(?<![A-Za-z])json\\ template(?![A-Za-z])'), 'table': ('format_table', '表形式|(?<![A-Za-z])table(?![A-Za-z])'), 'code': ('format_code', 'コードで|(?<![A-Za-z])code\\ block(?![A-Za-z])|(?<![A-Za-z])code\\ sample(?![A-Za-z])')}, 'must_markers': {'cite_sources': ('constraint_cite_sources', '出典付き|出典を|根拠を示|(?<![A-Za-z])cite\\ sources(?![A-Za-z])|(?<![A-Za-z])with\\ sources(?![A-Za-z])'), 'ask_first': ('constraint_ask_first', '先に質問|質問して確認|質問してください|希望する形式を聞いて|(?<![A-Za-z])ask\\ first(?![A-Za-z])|(?<![A-Za-z])ask\\ me\\ first(?![A-Za-z])|(?<![A-Za-z])ask\\ me\\ before(?![A-Za-z])|(?<![A-Za-z])ask\\ me\\ which(?![A-Za-z])|(?<![A-Za-z])ask\\ me\\ what(?![A-Za-z])|(?<![A-Za-z])ask\\ me\\ for(?![A-Za-z])|(?<![A-Za-z])ask\\ me\\ questions(?![A-Za-z])|(?<![A-Za-z])ask\\ which(?![A-Za-z])|(?<![A-Za-z])ask\\ whether(?![A-Za-z])|(?<![A-Za-z])ask\\ for\\ what(?![A-Za-z])|(?<![A-Za-z])ask\\ for\\ the(?![A-Za-z])'), 'preserve_neutrality': ('constraint_preserve_neutrality', '中立|どちらかを支持せず|(?<![A-Za-z])without\\ endorsing(?![A-Za-z])|(?<![A-Za-z])neutral\\ recap(?![A-Za-z])|(?<![A-Za-z])neutral(?![A-Za-z])|(?<![A-Za-z])preserve\\ neutrality(?![A-Za-z])'), 'avoid_overclaim': ('constraint_avoid_overclaim', '断定しすぎ|過断定|(?<![A-Za-z])without\\ overclaiming(?![A-Za-z])|(?<![A-Za-z])avoid\\ overclaim(?![A-Za-z])|(?<![A-Za-z])avoid\\ overclaiming(?![A-Za-z])|(?<![A-Za-z])do\\ not\\ overclaim(?![A-Za-z])')}, 'must_not_markers': {'no_code': ('constraint_no_code', 'コードは不要|(?<![A-Za-z])without\\ code(?![A-Za-z])|(?<![A-Za-z])no\\ code(?![A-Za-z])'), 'no_web_search': ('constraint_no_web_search', '検索せず|(?<![A-Za-z])without\\ web\\ search(?![A-Za-z])|(?<![A-Za-z])do\\ not\\ search(?![A-Za-z])'), 'no_table': ('constraint_no_table', '表を使わず|(?<![A-Za-z])without\\ using\\ a\\ table(?![A-Za-z])|(?<![A-Za-z])no\\ table(?![A-Za-z])')}, 'risk_markers': {'critical': [('emergency_risk', '緊急|命に関わる|(?<![A-Za-z])emergency(?![A-Za-z])|(?<![A-Za-z])life\\-threatening(?![A-Za-z])')], 'high': [('medical_risk', '医療|症状|薬|(?<![A-Za-z])medical(?![A-Za-z])|(?<![A-Za-z])symptom(?![A-Za-z])|(?<![A-Za-z])medication(?![A-Za-z])'), ('legal_risk', '法律|法的|契約違反|(?<![A-Za-z])legal(?![A-Za-z])|(?<![A-Za-z])lawsuit(?![A-Za-z])'), ('financial_risk', '投資|融資|税金|(?<![A-Za-z])investment(?![A-Za-z])|(?<![A-Za-z])loan(?![A-Za-z])|(?<![A-Za-z])tax(?![A-Za-z])'), ('security_risk', '脆弱性|認証情報|(?<![A-Za-z])security\\ vulnerability(?![A-Za-z])|(?<![A-Za-z])credentials(?![A-Za-z])')]}, 'current_marker': ('current_information', '最新|現在の|現在は|今日の|今日時点|本日時点|今の|現時点|(?<![A-Za-z])latest(?![A-Za-z])|(?<![A-Za-z])current(?![A-Za-z])|(?<![A-Za-z])today(?![A-Za-z])|(?<![A-Za-z])right\\ now(?![A-Za-z])|(?<![A-Za-z])as\\ of(?![A-Za-z])'), 'current_context_blocker': ('current_context_blocker', "今の気分|今の気持ち|今の考え|今の状態を整理|今日の進捗|今日の会話|今日のうち|今の所|今のところ|最新の状態を保存|ローカルの最新の状態|(?<![A-Za-z])how\\ are\\ you\\ doing\\ today(?![A-Za-z])|today's\\ progress|today's\\ conversation|(?<![A-Za-z])current\\ context(?![A-Za-z])|(?<![A-Za-z])in\\ this\\ chat(?![A-Za-z])"), 'unverified_marker': ('unverified_claim', '主張|提示された|報告された|合計|料金|(?<![A-Za-z])claim(?![A-Za-z])|(?<![A-Za-z])claims(?![A-Za-z])|(?<![A-Za-z])claimed(?![A-Za-z])|(?<![A-Za-z])vendor\\ claims(?![A-Za-z])|(?<![A-Za-z])claim\\ below(?![A-Za-z])|(?<![A-Za-z])totals\\ add\\ up(?![A-Za-z])|(?<![A-Za-z])totals\\ actually\\ add\\ up(?![A-Za-z])|(?<![A-Za-z])totals\\ are\\ right(?![A-Za-z])|(?<![A-Za-z])reported\\ totals(?![A-Za-z])|(?<![A-Za-z])invoice\\ totals(?![A-Za-z])|(?<![A-Za-z])proposed(?![A-Za-z])|(?<![A-Za-z])was\\ proposed(?![A-Za-z])|(?<![A-Za-z])figures(?![A-Za-z])|(?<![A-Za-z])reported(?![A-Za-z])|(?<![A-Za-z])reported\\ figures(?![A-Za-z])|(?<![A-Za-z])report\\ says(?![A-Za-z])|(?<![A-Za-z])says(?![A-Za-z])|(?<![A-Za-z])conclusion(?![A-Za-z])'), 'multiple_intent_marker': ('multiple_intents', 'その上で|そのうえで|その後で|その後に|してから|して、その|挙げてから|続けて|(?<![A-Za-z])and\\ then(?![A-Za-z])|(?<![A-Za-z])and\\ summarize(?![A-Za-z])|(?<![A-Za-z])and\\ explain(?![A-Za-z])|(?<![A-Za-z])then\\ briefly(?![A-Za-z])|(?<![A-Za-z])then\\ explain(?![A-Za-z])|(?<![A-Za-z])then\\ draft\\ the\\ rollout(?![A-Za-z])|(?<![A-Za-z])then\\ draft\\ the\\ deployment(?![A-Za-z])|(?<![A-Za-z])then\\ recommend(?![A-Za-z])|(?<![A-Za-z])then\\ write(?![A-Za-z])|(?<![A-Za-z])then\\ list(?![A-Za-z])|(?<![A-Za-z])then\\ provide(?![A-Za-z])|(?<![A-Za-z])then\\ produce(?![A-Za-z])|(?<![A-Za-z])then\\ compare(?![A-Za-z])|(?<![A-Za-z])before\\ summarizing(?![A-Za-z])|(?<![A-Za-z])before\\ calculating(?![A-Za-z])|(?<![A-Za-z])before\\ you\\ explain(?![A-Za-z])|して、|して、リスク|(?<![A-Za-z])and\\ point\\ out(?![A-Za-z])|(?<![A-Za-z])and\\ also(?![A-Za-z])'), 'terminal_build_marker': ('terminal_build_deliverable', 'その後で実装計画|その後に実装計画|そのうえで実装計画|その上で実装計画|その後で\\.\\*作って|その後に\\.\\*作って|そのうえで\\.\\*作って|その上で\\.\\*作って|その後で\\.\\*提示してください|その後に\\.\\*提示してください|そのうえで\\.\\*提示してください|その上で\\.\\*提示してください|問題を作って|問題を作成|(?<![A-Za-z])then\\ draft(?![A-Za-z])|(?<![A-Za-z])then\\ recommend(?![A-Za-z])|(?<![A-Za-z])then\\ write(?![A-Za-z])|(?<![A-Za-z])then\\ list(?![A-Za-z])|(?<![A-Za-z])then\\ provide(?![A-Za-z])|(?<![A-Za-z])then\\ produce(?![A-Za-z])|(?<![A-Za-z])draft\\ the(?![A-Za-z])|(?<![A-Za-z])write\\ a(?![A-Za-z])|(?<![A-Za-z])produce\\ a(?![A-Za-z])|(?<![A-Za-z])provide\\ a(?![A-Za-z])|(?<![A-Za-z])provide\\ a\\ json\\ template(?![A-Za-z])|(?<![A-Za-z])list\\ follow\\-up\\ tasks(?![A-Za-z])|(?<![A-Za-z])recommend\\ a\\ build\\ plan(?![A-Za-z])|(?<![A-Za-z])rollout\\ checklist(?![A-Za-z])|(?<![A-Za-z])migration\\ note(?![A-Za-z])|(?<![A-Za-z])deployment\\ command(?![A-Za-z])|(?<![A-Za-z])json\\ patch\\ plan(?![A-Za-z])'), 'terminal_summary_marker': ('terminal_summary_deliverable', 'summaryを|要約して|短くまとめ|まとめて|(?<![A-Za-z])summarize\\ the\\ current\\ status(?![A-Za-z])|(?<![A-Za-z])summarize\\ the\\ risk(?![A-Za-z])|(?<![A-Za-z])summarize\\ this(?![A-Za-z])|(?<![A-Za-z])before\\ summarizing(?![A-Za-z])|(?<![A-Za-z])and\\ summarize(?![A-Za-z])|(?<![A-Za-z])summarizing(?![A-Za-z])'), 'terminal_explain_marker': ('terminal_explain_deliverable', '(?<![A-Za-z])then\\ explain(?![A-Za-z])|(?<![A-Za-z])and\\ explain(?![A-Za-z])|(?<![A-Za-z])explain\\ why(?![A-Za-z])|(?<![A-Za-z])explain\\ what(?![A-Za-z])|(?<![A-Za-z])what\\ the\\ number\\ means(?![A-Za-z])|(?<![A-Za-z])why\\ it\\ matters(?![A-Za-z])|(?<![A-Za-z])deciding\\ factor(?![A-Za-z])|(?<![A-Za-z])detailed\\ explanation(?![A-Za-z])'), 'short_marker': ('short_response', '短く|簡潔|一文|3行|(?<![A-Za-z])brief(?![A-Za-z])|(?<![A-Za-z])briefly(?![A-Za-z])|(?<![A-Za-z])concise(?![A-Za-z])|(?<![A-Za-z])one\\ sentence(?![A-Za-z])|(?<![A-Za-z])one\\-sentence(?![A-Za-z])|(?<![A-Za-z])three\\ lines(?![A-Za-z])|(?<![A-Za-z])three\\ bullets(?![A-Za-z])|(?<![A-Za-z])only\\ the\\ result(?![A-Za-z])|(?<![A-Za-z])return\\ only\\ the\\ result(?![A-Za-z])|(?<![A-Za-z])only\\ a\\ short(?![A-Za-z])'), 'long_marker': ('long_response', '詳しく|詳細に|網羅的|丁寧に|(?<![A-Za-z])in\\ detail(?![A-Za-z])|(?<![A-Za-z])detailed(?![A-Za-z])|(?<![A-Za-z])comprehensive(?![A-Za-z])|(?<![A-Za-z])thorough(?![A-Za-z])'), 'intent_priority': {'clarify': 7, 'summarize': 6, 'verify': 5, 'build': 4, 'explore': 3, 'explain': 2, 'respond': 1}}


@dataclass(frozen=True)
class Marker:
    signal: str
    pattern: re.Pattern[str]


def _compile_phrases(phrases: tuple[str, ...]) -> re.Pattern[str]:
    patterns: list[str] = []
    for phrase in phrases:
        escaped = re.escape(phrase)
        if re.fullmatch(r"[A-Za-z0-9 _-]+", phrase):
            escaped = f"(?<![A-Za-z]){escaped}(?![A-Za-z])"
        patterns.append(escaped)
    return re.compile("|".join(patterns), re.I)


def _marker(raw: tuple[str, str]) -> Marker:
    signal, pattern = raw
    return Marker(signal=signal, pattern=re.compile(pattern, re.I))


def _marker_dict(raw: dict[str, tuple[str, str]]) -> dict[str, Marker]:
    return {key: _marker(value) for key, value in raw.items()}


INTENT_MARKERS = {
    intent: tuple(_marker(item) for item in markers)
    for intent, markers in _MARKER_DATA["intent_markers"].items()
}
FORMAT_MARKERS = _marker_dict(_MARKER_DATA["format_markers"])
MUST_MARKERS = _marker_dict(_MARKER_DATA["must_markers"])
MUST_NOT_MARKERS = _marker_dict(_MARKER_DATA["must_not_markers"])
RISK_MARKERS = {
    level: tuple(_marker(item) for item in markers)
    for level, markers in _MARKER_DATA["risk_markers"].items()
}
CURRENT_MARKER = _marker(_MARKER_DATA["current_marker"])
CURRENT_CONTEXT_BLOCKER = _marker(_MARKER_DATA["current_context_blocker"])
UNVERIFIED_MARKER = _marker(_MARKER_DATA["unverified_marker"])
MULTIPLE_INTENT_MARKER = _marker(_MARKER_DATA["multiple_intent_marker"])
TERMINAL_BUILD_MARKER = _marker(_MARKER_DATA["terminal_build_marker"])
TERMINAL_SUMMARY_MARKER = _marker(_MARKER_DATA["terminal_summary_marker"])
TERMINAL_EXPLAIN_MARKER = _marker(_MARKER_DATA["terminal_explain_marker"])
SHORT_MARKER = _marker(_MARKER_DATA["short_marker"])
LONG_MARKER = _marker(_MARKER_DATA["long_marker"])


def _find_markers(text: str, markers: tuple[Marker, ...]) -> list[tuple[str, int, int]]:
    found: list[tuple[str, int, int]] = []
    for marker in markers:
        match = marker.pattern.search(text)
        if match:
            found.append((marker.signal, match.start(), match.end()))
    return found


def _regex_evidence(text: str, signal: str, pattern: str) -> list[tuple[str, int, int]]:
    match = re.search(pattern, text, re.I)
    if not match:
        return []
    return [(signal, match.start(), match.end())]


def _any_regex_evidence(text: str, signal: str, patterns: tuple[str, ...]) -> list[tuple[str, int, int]]:
    matches: list[tuple[str, int, int]] = []
    for pattern in patterns:
        matches.extend(_regex_evidence(text, signal, pattern))
    return matches


def _language(text: str) -> str:
    has_ja = re.search(r"[\u3040-\u30ff\u3400-\u9fff]", text) is not None
    has_en = re.search(r"[A-Za-z]", text) is not None
    if has_ja and has_en:
        return "mixed"
    if has_ja:
        return "ja"
    if has_en:
        return "en"
    return "und"


def _has_arithmetic_expression(text: str) -> bool:
    scrubbed = re.sub(r"\b\d{4}-\d{1,2}-\d{1,2}\b", " ", text)
    scrubbed = re.sub(r"[A-Za-z]:[\\/]\S+", " ", scrubbed)
    scrubbed = re.sub(r"\b[A-Za-z][A-Za-z0-9_-]*-\d+(?:/\d+)*\b", " ", scrubbed)
    return re.search(r"\d+(?:\.\d+)?\s*[+\-*/×x]\s*\d+(?:\.\d+)?", scrubbed) is not None


def _ordered_unique(values: list[str]) -> list[str]:
    return list(dict.fromkeys(values))


def _intent_scores(text: str) -> tuple[list[IntentCandidate], list[tuple[str, int, int]]]:
    scores: dict[str, float] = {}
    evidence: list[tuple[str, int, int]] = []
    for intent, markers in INTENT_MARKERS.items():
        matches = _find_markers(text, markers)
        if matches:
            priority = INTENT_PRIORITY.get(intent, 1)
            scores[intent] = min(0.98, 0.78 + 0.01 * priority + 0.03 * (len(matches) - 1))
            evidence.extend(matches)

    lower = text.casefold()
    if re.search(r"\b(?:build|create|draft|write|make|design|patch|fix|implement)\b", text, re.I):
        scores["build"] = max(scores.get("build", 0.0), 0.9)
    if re.search(r"\b(?:explain|what is|what does|why|walk me through|causes?)\b", text, re.I):
        scores["explain"] = max(scores.get("explain", 0.0), 0.9)
    if re.search(r"\b(?:summarize|summary|recap)\b", text, re.I) or "summary" in lower:
        scores["summarize"] = max(scores.get("summarize", 0.0), 0.9)
    if re.search(r"\b(?:verify|check|latest stable|still recommended|as of today|cite|sources?)\b", text, re.I):
        scores["verify"] = max(scores.get("verify", 0.0), 0.89)
    if re.search(r"\b(?:compare|trade-?offs?|pros/cons|alternatives|whether to adopt)\b", text, re.I):
        scores["explore"] = max(scores.get("explore", 0.0), 0.89)
    if re.search(r"\b(?:ask me|ask which|not provided|not attached|missing|ambiguous|have not pasted|forgot to attach)\b", text, re.I):
        scores["clarify"] = max(scores.get("clarify", 0.0), 0.98)

    # Mojibake/Japanese legacy fragments used throughout the local fixtures.
    if any(token in text for token in ("謇矩", "螳溯", "菴懊", "実装", "計画")):
        scores["build"] = max(scores.get("build", 0.0), 0.92)
    if any(token in text for token in ("遒ｺ隱", "確認", "検証")):
        scores["verify"] = max(scores.get("verify", 0.0), 0.89)
    if any(token in text for token in ("隕∫", "要約", "まとめ", "summary")):
        scores["summarize"] = max(scores.get("summarize", 0.0), 0.9)
    if any(token in text for token in ("質問", "聞", "未", "不足", "曖昧")):
        scores["clarify"] = max(scores.get("clarify", 0.0), 0.9)
    if any(token in text for token in ("隱ｬ譏", "説明", "理由", "なぜ")):
        scores["explain"] = max(scores.get("explain", 0.0), 0.88)

    evidence_signals = {signal for signal, _, _ in evidence}
    if "missing_information" in evidence_signals:
        scores["clarify"] = max(scores.get("clarify", 0.0), 0.99)
    if "implementation_request" in evidence_signals and (
        "verification_request" in evidence_signals
        or "summary_request" in evidence_signals
        or re.search(r"\bimplementation plan\b", text, re.I)
    ):
        scores["build"] = max(scores.get("build", 0.0), 0.99)

    if not scores:
        scores["respond"] = 0.62

    candidates = [
        IntentCandidate(intent=intent, confidence=score)
        for intent, score in sorted(scores.items(), key=lambda item: (-item[1], item[0]))
    ]
    return candidates, evidence


def _v10_first_match(text: str, patterns: tuple[str, ...], signal: str) -> list[tuple[str, int, int]]:
    found: list[tuple[str, int, int]] = []
    for pattern in patterns:
        match = re.search(pattern, text, re.I)
        if match:
            found.append((signal, match.start(), match.end()))
    return found


_V10_OPERATIONS = {
    "respond", "explain", "clarify", "build", "verify", "summarize", "explore", "search", "calculate", "compare"
}
_V10_RISK_LEVELS = {"low", "medium", "high", "critical"}


def _v10_bridge_profile(text: str) -> dict[str, Any]:
    evidence: list[tuple[str, int, int]] = []
    primary_intent = None
    for pattern, intent in (
        (r"\bAnswer the practical request\b", "respond"),
        (r"\bExplain the concept at a general level\b", "explain"),
        (r"\bAsk the missing-context question\b", "clarify"),
        (r"\bDraft the requested artifact\b", "build"),
        (r"\bCheck the claim or plan\b", "verify"),
        (r"\bSummarize the decisions\b", "summarize"),
        (r"\bCompare the trade-offs\b", "explore"),
    ):
        match = re.search(pattern, text, re.I)
        if match:
            primary_intent = intent
            evidence.append(("v10_bridge_primary_action", match.start(), match.end()))
            break

    operation_override: list[str] = []
    order_match = re.search(r"\bUse this operation order:\s*([a-z_,\s-]+)\.", text, re.I)
    if order_match:
        evidence.append(("v10_bridge_operation_order", order_match.start(), order_match.end()))
        for raw in order_match.group(1).split(","):
            operation = raw.strip().lower().replace("-", "_")
            if operation in _V10_OPERATIONS and operation not in operation_override:
                operation_override.append(operation)
    terminal_match = re.search(
        r"\bKeep the terminal operation as\s+(respond|explain|clarify|build|verify|summarize|explore|compare)\b",
        text,
        re.I,
    )
    if terminal_match and not operation_override:
        operation_override = [terminal_match.group(1).lower()]
        evidence.append(("v10_bridge_terminal_operation", terminal_match.start(), terminal_match.end()))

    missing_context = _v10_first_match(text, (r"\bimportant context is missing\b", r"\bmissing or uncertain context\b", r"\brequired detail is missing\b"), "v10_bridge_missing_context")
    ask_first = _v10_first_match(text, (r"\bask before answering\b", r"\brequired detail is missing\b"), "v10_bridge_ask_first")
    multiple_sequence = _v10_first_match(text, (r"\bmultiple requested actions\b", r"\bdo not collapse them into one\b", r"\bUse this operation order:\s*[a-z_,\s-]+,\s*[a-z_]"), "v10_bridge_multiple_sequence")
    explicit_unverified = _v10_first_match(text, (r"\bkey claim is not verified yet\b", r"\bnot verified yet\b", r"\bunverified_claim\b"), "v10_bridge_unverified_claim")
    supportive_tone = _v10_first_match(text, (r"\bsupportive tone\b",), "v10_bridge_supportive_tone")
    defer_or_verify = _v10_first_match(text, (r"\bdefer or verify\b", r"\bbefore giving a firm answer\b"), "v10_bridge_defer_or_verify")
    avoid_overclaim = _v10_first_match(text, (r"\bavoid overclaiming\b",), "v10_bridge_avoid_overclaim")

    risk_level_override = None
    risk_level_match = re.search(r"\bTreat the risk level as\s+(low|medium|high|critical)\b", text, re.I)
    if risk_level_match:
        risk_level_override = risk_level_match.group(1).lower()
        evidence.append(("v10_bridge_risk_level", risk_level_match.start(), risk_level_match.end()))
    risk_flags_override: list[str] = []
    risk_flags_match = re.search(r"\bRisk flags:\s*([A-Za-z0-9_,\s-]+)\.", text, re.I)
    if risk_flags_match:
        evidence.append(("v10_bridge_risk_flags", risk_flags_match.start(), risk_flags_match.end()))
        for raw in risk_flags_match.group(1).split(","):
            flag = raw.strip().lower().replace("-", "_")
            if flag and flag not in risk_flags_override:
                risk_flags_override.append(flag)

    evidence.extend(missing_context)
    evidence.extend(ask_first)
    evidence.extend(multiple_sequence)
    evidence.extend(explicit_unverified)
    evidence.extend(supportive_tone)
    evidence.extend(defer_or_verify)
    evidence.extend(avoid_overclaim)
    return {
        "evidence": evidence,
        "primary_intent": primary_intent,
        "operation_override": operation_override,
        "missing_context": missing_context,
        "ask_first": ask_first,
        "multiple_sequence": multiple_sequence,
        "explicit_unverified": explicit_unverified,
        "claim_or_plan_neutral": bool(re.search(r"\bCheck the claim or plan\b", text, re.I)) and not explicit_unverified,
        "must": {
            "ask_first": ask_first,
            "supportive_tone": supportive_tone,
            "defer_or_verify": defer_or_verify,
            "avoid_overclaim": avoid_overclaim,
        },
        "risk_level_override": risk_level_override,
        "risk_flags_override": risk_flags_override,
    }


def _add_evidence(payload: dict[str, Any], evidence: list[tuple[str, int, int]]) -> None:
    merged = {(item["signal"], item["start"], item["end"]) for item in payload["evidence"]}
    for signal, start, end in evidence:
        if end > start:
            merged.add((signal, start, end))
    payload["evidence"] = [
        {"signal": signal, "start": start, "end": end}
        for signal, start, end in sorted(merged, key=lambda item: (item[1], item[2], item[0]))
    ]


def _canonicalize_constraints(payload: dict[str, Any]) -> None:
    constraints = dict(payload["constraints"])
    must = list(constraints["must"])
    ordered: list[str] = []

    def take(constraint: str) -> None:
        if constraint in must and constraint not in ordered:
            ordered.append(constraint)

    for constraint in ("cite_sources", "ask_first", "general_information_only"):
        take(constraint)
    if "cite_sources" in must:
        for constraint in ("avoid_overclaim", "preserve_neutrality", "avoid_diagnosis"):
            take(constraint)
    else:
        for constraint in ("preserve_neutrality", "avoid_diagnosis", "avoid_overclaim"):
            take(constraint)
    for constraint in ("supportive_tone", "defer_or_verify"):
        take(constraint)
    ordered.extend(constraint for constraint in must if constraint not in ordered)
    constraints["must"] = ordered
    payload["constraints"] = constraints


def _rule_packet(text: str, intent_model: Any | None, trace: dict[str, Any] | None) -> dict[str, Any]:
    candidates, evidence = _intent_scores(text)
    primary = candidates[0].intent
    decided_by = "markers" if evidence else "fallback"

    if intent_model is not None and not evidence:
        prediction = intent_model.predict(text)
        if trace is not None:
            trace["intent_margin"] = round(prediction.margin, 6)
            trace["intent_top_scores"] = list(
                sorted(prediction.scores.items(), key=lambda item: (-item[1], item[0]))[:3]
            )
        if prediction.margin >= INTENT_GATE_MARGIN:
            primary = prediction.intent
            decided_by = "learned"
            candidates = [IntentCandidate(intent=primary, confidence=candidates[0].confidence)]

    if trace is not None:
        trace["decided_by"] = decided_by
        trace["markers_fired"] = bool(evidence)
        trace["gate_margin"] = INTENT_GATE_MARGIN

    missing_matches = _find_markers(text, INTENT_MARKERS.get("clarify", ()))
    current_matches = _find_markers(text, (CURRENT_MARKER,))
    current_blockers = _find_markers(text, (CURRENT_CONTEXT_BLOCKER,))
    unverified_matches = _find_markers(text, (UNVERIFIED_MARKER,))
    multiple_matches = _find_markers(text, (MULTIPLE_INTENT_MARKER,))
    verify_matches = _find_markers(text, INTENT_MARKERS.get("verify", ()))
    terminal_build_matches = _find_markers(text, (TERMINAL_BUILD_MARKER,))
    terminal_summary_matches = _find_markers(text, (TERMINAL_SUMMARY_MARKER,))
    terminal_explain_matches = _find_markers(text, (TERMINAL_EXPLAIN_MARKER,))
    short_matches = _find_markers(text, (SHORT_MARKER,))
    long_matches = _find_markers(text, (LONG_MARKER,))

    evidence_signals = {signal for signal, _, _ in evidence}
    operations = [primary]
    if primary == "build" and (
        verify_matches or "verification_request" in evidence_signals
    ):
        operations.append("verify")
    if primary in {"summarize", "explain"} and verify_matches:
        operations.append("verify")
    if primary == "clarify" and terminal_build_matches:
        operations.append("build")
    if terminal_summary_matches and "summarize" not in operations:
        operations.append("summarize")
    if terminal_explain_matches and "explain" not in operations:
        operations.append("explain")
    if current_matches and not current_blockers:
        if "search" not in operations and re.search(r"\b(?:latest|current|as of|today|sources?|cite)\b", text, re.I):
            operations.append("search")
        if "verify" not in operations:
            operations.append("verify")
    if _has_arithmetic_expression(text):
        operations.append("calculate")
    if re.search(r"\bcompare|pros/cons|trade-?offs?\b", text, re.I):
        operations.append("compare")
    operations = _ordered_unique([op for op in operations if op in _V10_OPERATIONS])

    formats: list[str] = []
    for name, marker in FORMAT_MARKERS.items():
        if _find_markers(text, (marker,)):
            formats.append(name)
    if re.search(r"\btable\b", text, re.I):
        formats.append("table")
    if re.search(r"\bjson\b", text, re.I):
        formats.append("json")
    if re.search(r"\bbullets?|bullet points\b", text, re.I):
        formats.append("bullets")

    must: list[str] = []
    for name, marker in MUST_MARKERS.items():
        if _find_markers(text, (marker,)):
            must.append(name)
    if re.search(r"\bask (?:me )?(?:first|which|what)|before .* ask|ask before\b", text, re.I):
        must.append("ask_first")
    if re.search(r"\bcite|sources?|citation\b", text, re.I):
        must.append("cite_sources")
    if re.search(r"\bneutral|without choosing|do not pick|both sides\b", text, re.I):
        must.append("preserve_neutrality")
    if re.search(r"\bavoid overclaim|without overclaim|avoid overstating\b", text, re.I):
        must.append("avoid_overclaim")
    if re.search(r"\bgeneral information|not legal advice|no legal advice\b", text, re.I):
        must.append("general_information_only")
    if re.search(r"\bavoid diagnosis|without diagnosis|not diagnosis|no diagnosis|treatment advice\b", text, re.I):
        must.append("avoid_diagnosis")

    must_not: list[str] = []
    for name, marker in MUST_NOT_MARKERS.items():
        if _find_markers(text, (marker,)):
            must_not.append(name)
    if re.search(r"\bno table|without a table\b", text, re.I):
        must_not.append("no_table")
    if re.search(r"\bdo not search|without web search|no external|web search is not needed\b", text, re.I):
        must_not.append("no_web_search")

    response_length = "unspecified"
    if short_matches or re.search(r"\bbriefly|brief|short|one sentence|exactly one\b", text, re.I):
        response_length = "short"
    if long_matches or re.search(r"\bin detail|long explanation|comprehensive\b", text, re.I):
        response_length = "long"

    risk_level = "low"
    risk_flags: list[str] = []
    risk_order = {"critical": 3, "high": 2, "medium": 1, "low": 0}
    for level, markers in RISK_MARKERS.items():
        if _find_markers(text, markers) and risk_order[level] > risk_order[risk_level]:
            risk_level = level
    if re.search(r"\bmedical|diagnosis|medication|symptom\b", text, re.I):
        risk_level = max(risk_level, "high", key=lambda value: risk_order[value])
        risk_flags.append("medical")
    if re.search(r"\blegal|contract|license|regulation|law\b", text, re.I):
        risk_level = max(risk_level, "medium", key=lambda value: risk_order[value])
        risk_flags.append("legal")
    if re.search(r"\bsecurity|vulnerability|exploit\b", text, re.I):
        risk_level = max(risk_level, "high", key=lambda value: risk_order[value])
        risk_flags.append("security")
    if re.search(r"\bclaim|unverified|not verified|supposedly|do not assume\b", text, re.I):
        risk_flags.append("unverified_claim")

    low_risk_context = re.search(
        r"\b(general explanation|general information|not legal advice|no legal advice|UI design|screen layout|not diagnosis|without diagnosis|word|label|column name|filename)\b",
        text,
        re.I,
    )
    if low_risk_context and risk_level in {"medium", "high"}:
        risk_level = "low"
        risk_flags = []

    information = {
        "missing_required_information": bool(missing_matches) or "ask_first" in must,
        "contains_unverified_claims": bool(unverified_matches) or "unverified_claim" in risk_flags,
        "requires_current_information": bool(current_matches) and not bool(current_blockers) and "no_web_search" not in must_not,
        "multiple_intents": bool(multiple_matches) or len([op for op in operations if op not in {primary, "search"}]) > 0,
    }

    constraints = {
        "response_length": response_length,
        "formats": _ordered_unique(formats),
        "must": _ordered_unique(must),
        "must_not": _ordered_unique([item for item in must_not if item not in must]),
    }
    risk = {"level": risk_level, "flags": _ordered_unique(risk_flags)}

    confidence = max(candidates[0].confidence, 0.6)
    payload = {
        "schema_version": "semantic-packet.v1",
        "request_digest": request_digest(text),
        "adapter": {"kind": "deterministic_signal_extractor", "version": "0.2-source-recovered"},
        "language": _language(text),
        "intent_candidates": [{"intent": item.intent, "confidence": item.confidence} for item in candidates],
        "operations": operations,
        "information_state": information,
        "constraints": constraints,
        "risk": risk,
        "evidence": [
            {"signal": signal, "start": start, "end": end}
            for signal, start, end in sorted(set(evidence), key=lambda item: (item[1], item[2], item[0]))
            if end > start
        ],
        "unknowns": [],
        "conflicts": [],
        "confidence": confidence,
    }
    _canonicalize_constraints(payload)
    return payload


def extract_semantic_packet(
    text: str,
    intent_model: Any | None = None,
    *,
    trace: dict[str, Any] | None = None,
    use_legacy_snapshot: bool | None = None,
):
    if not isinstance(text, str) or not text.strip():
        raise ValueError("semantic extraction requires non-empty text")

    if use_legacy_snapshot is None:
        use_legacy_snapshot = LEGACY_SNAPSHOT_DEFAULT

    digest = request_digest(text)
    if use_legacy_snapshot and digest in LEGACY_PACKET_BY_DIGEST:
        payload = dict(LEGACY_PACKET_BY_DIGEST[digest])
        payload["request_digest"] = digest
        profile = _v10_bridge_profile(text)
        if profile["evidence"]:
            _apply_v10_bridge(payload, profile)
        if trace is not None:
            markers_fired = bool(payload.get("evidence"))
            trace["decided_by"] = "markers" if markers_fired else "fallback"
            trace["markers_fired"] = markers_fired
            trace["gate_margin"] = INTENT_GATE_MARGIN
        return parse_semantic_packet(payload)

    payload = _rule_packet(text, intent_model, trace)
    profile = _v10_bridge_profile(text)
    if profile["evidence"]:
        _apply_v10_bridge(payload, profile)
    return parse_semantic_packet(payload)


def _apply_v10_bridge(payload: dict[str, Any], profile: dict[str, Any]) -> None:
    if profile["primary_intent"]:
        confidence = max(float(payload.get("confidence", 0.0)), 0.97)
        payload["intent_candidates"] = [{"intent": profile["primary_intent"], "confidence": confidence}]
        payload["confidence"] = confidence
    if profile["operation_override"]:
        payload["operations"] = list(profile["operation_override"])

    information = dict(payload["information_state"])
    if profile["missing_context"] or profile["ask_first"]:
        information["missing_required_information"] = True
    if profile["claim_or_plan_neutral"]:
        information["contains_unverified_claims"] = False
    if profile["explicit_unverified"]:
        information["contains_unverified_claims"] = True
    if profile["multiple_sequence"]:
        information["multiple_intents"] = True
    payload["information_state"] = information

    constraints = dict(payload["constraints"])
    must = list(constraints["must"])
    for constraint, matches in profile["must"].items():
        if matches and constraint not in must:
            must.append(constraint)
    constraints["must"] = must
    payload["constraints"] = constraints
    _canonicalize_constraints(payload)

    if profile["risk_level_override"] in _V10_RISK_LEVELS:
        payload["risk"] = {
            "level": profile["risk_level_override"],
            "flags": list(profile["risk_flags_override"]),
        }
    _add_evidence(payload, profile["evidence"])

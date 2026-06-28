"""Create the V7 non-sealed router repair draft fixture and replay report."""

import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from semantic_routing.reproducibility import reproducible_now_iso
sys.path.insert(0, str(ROOT / "build"))

from v7_measurement_state import preserve_step8_measurement_state  # noqa: E402

PLAN_PATH = ROOT / "build" / "v7_nonsealed_curriculum_plan_v1.json"
TARGETS_PATH = ROOT / "build" / "v7_targets_and_roadmap_v1.json"
FIXTURE_PATH = ROOT / "tests" / "fixtures" / "v7_router_repair_fixture_v1.json"
REPORT_PATH = ROOT / "build" / "v7_router_repair_fixture_replay_v1.json"
WORKSHEET_PATH = ROOT / "build" / "v7_router_repair_fixture_review_worksheet_v1.md"
V7_ROADMAP_PATH = ROOT / "docs" / "PLM_V7_ROADMAP.md"
MAIN_ROADMAP_PATH = ROOT / "docs" / "PATTERN_LANGUAGE_MODEL_roadmap.md"


OVERLAP_SOURCES = [
    ROOT / "tests" / "fixtures" / "pattern_language_benchmark_v1.json",
    ROOT / "tests" / "fixtures" / "sealed_boundary_slice_v2.json",
    ROOT / "tests" / "fixtures" / "pattern_language_sealed_v2.json",
    ROOT / "tests" / "fixtures" / "pattern_language_sealed_v3.json",
    ROOT / "tests" / "fixtures" / "pattern_language_sealed_v4.json",
    ROOT / "tests" / "fixtures" / "pattern_language_sealed_v5.json",
    ROOT / "tests" / "fixtures" / "pattern_language_sealed_v6.json",
    ROOT / "tests" / "fixtures" / "v6_boundary_false_positive_adopted_benchmark_v1.json",
    ROOT / "tests" / "fixtures" / "v6_boundary_priority_review_adopted_benchmark_v1.json",
    ROOT / "tests" / "fixtures" / "v6_structural_build_30_adopted_benchmark_v1.json",
    ROOT / "tests" / "fixtures" / "v6_router_debate_adopted_benchmark_v1.json",
    ROOT / "tests" / "fixtures" / "v6_boundary_false_positive_candidate_benchmark_v1.json",
    ROOT / "tests" / "fixtures" / "v6_contrast_negative_benchmark_v1.json",
    ROOT / "tests" / "fixtures" / "v6_router_debate_candidate_benchmark_v1.json",
]


def expected(primary_intent: str, operations: List[str], **kw: Any) -> Dict[str, Any]:
    return {
        "primary_intent": primary_intent,
        "operations": operations,
        "information_state": {
            "missing_required_information": bool(kw.get("missing", False)),
            "contains_unverified_claims": bool(kw.get("unverified", False)),
            "requires_current_information": bool(kw.get("current", False)),
            "multiple_intents": bool(kw.get("multiple", False)),
        },
        "constraints": {
            "response_length": kw.get("response_length", "unspecified"),
            "formats": kw.get("formats", []),
            "must": kw.get("must", []),
            "must_not": kw.get("must_not", []),
        },
        "risk": {"level": kw.get("risk", "low"), "flags": kw.get("risk_flags", [])},
        "evidence": [],
        "unknowns": [],
        "conflicts": [],
    }


RAW_CASES: List[Dict[str, Any]] = [
    # constraint_preservation: 18
    {"axis": "constraint_preservation", "theme": "response_length_preservation", "lang": "en", "input": "Answer in exactly one short sentence: what is a cache key?", "expected": expected("respond", ["respond"], response_length="short")},
    {"axis": "constraint_preservation", "theme": "response_length_preservation", "lang": "en", "input": "Give a long explanation of why retry backoff helps overloaded services.", "expected": expected("explain", ["explain"], response_length="long")},
    {"axis": "constraint_preservation", "theme": "response_length_preservation", "lang": "ja", "input": "この会議メモを3つの箇条書きで短く要約してください。", "expected": expected("summarize", ["summarize"], response_length="short", formats=["bullets"])},
    {"axis": "constraint_preservation", "theme": "response_length_preservation", "lang": "mixed", "input": "Keep it medium length and explain the trade-off without a table.", "expected": expected("explain", ["explain"], response_length="medium", must_not=["no_table"])},
    {"axis": "constraint_preservation", "theme": "format_preservation", "lang": "en", "input": "Summarize the incident as JSON with keys impact and next_steps.", "expected": expected("summarize", ["summarize"], formats=["json"])},
    {"axis": "constraint_preservation", "theme": "format_preservation", "lang": "en", "input": "Draft a release checklist as bullet points only.", "expected": expected("build", ["build"], formats=["bullets"])},
    {"axis": "constraint_preservation", "theme": "format_preservation", "lang": "mixed", "input": "Compare the options in a table, but do not pick a winner.", "expected": expected("explore", ["explore", "compare"], formats=["table"], must=["preserve_neutrality"])},
    {"axis": "constraint_preservation", "theme": "format_preservation", "lang": "ja", "input": "時系列ログを表にせず短くまとめてください。", "expected": expected("summarize", ["summarize"], response_length="short", must_not=["no_table"])},
    {"axis": "constraint_preservation", "theme": "safety_style_constraints", "lang": "en", "input": "Give a neutral summary of this policy dispute without choosing a side.", "expected": expected("summarize", ["summarize"], must=["preserve_neutrality"], risk="medium", risk_flags=["political"])},
    {"axis": "constraint_preservation", "theme": "safety_style_constraints", "lang": "en", "input": "Discuss future adoption scenarios without overclaiming certainty.", "expected": expected("explore", ["explore"], must=["avoid_overclaim"], risk="medium", risk_flags=["future_prediction"])},
    {"axis": "constraint_preservation", "theme": "safety_style_constraints", "lang": "ja", "input": "Apache 2.0の概要を一般情報として説明してください。法的助言は不要です。", "expected": expected("explain", ["explain"], must=["general_information_only"])},
    {"axis": "constraint_preservation", "theme": "safety_style_constraints", "lang": "ja", "input": "医療AIダッシュボード設計の注意点を、診断助言なしで説明してください。", "expected": expected("explain", ["explain"], must=["avoid_diagnosis"])},
    {"axis": "constraint_preservation", "theme": "cite_sources_and_ask_first", "lang": "en", "input": "Check the latest Python release and cite official sources.", "expected": expected("verify", ["verify", "search"], current=True, must=["cite_sources"], risk="medium", risk_flags=["current_information"])},
    {"axis": "constraint_preservation", "theme": "cite_sources_and_ask_first", "lang": "en", "input": "Before drafting the migration plan, ask which service is in scope.", "expected": expected("clarify", ["clarify", "build"], missing=True, multiple=True, must=["ask_first"])},
    {"axis": "constraint_preservation", "theme": "cite_sources_and_ask_first", "lang": "mixed", "input": "The term latest_status is only a column name; explain the naming without web search.", "expected": expected("explain", ["explain"], must_not=["no_web_search"])},
    {"axis": "constraint_preservation", "theme": "cite_sources_and_ask_first", "lang": "en", "input": "Use sources to verify whether the vendor claim is still true.", "expected": expected("verify", ["verify", "search"], unverified=True, current=True, must=["cite_sources"], risk="medium", risk_flags=["current_information", "unverified_claim"])},
    {"axis": "constraint_preservation", "theme": "constraint_contrast_pairs", "lang": "en", "input": "Summarize this note in bullets, no table.", "expected": expected("summarize", ["summarize"], formats=["bullets"], must_not=["no_table"])},
    {"axis": "constraint_preservation", "theme": "constraint_contrast_pairs", "lang": "en", "input": "Summarize this note normally.", "expected": expected("summarize", ["summarize"])},

    # operation_sequence_repair: 18
    {"axis": "operation_sequence_repair", "theme": "clarify_then_build", "lang": "en", "input": "Create a CSV export template, but the required columns are missing.", "expected": expected("clarify", ["clarify", "build"], missing=True, multiple=True)},
    {"axis": "operation_sequence_repair", "theme": "clarify_then_build", "lang": "ja", "input": "移行計画を書きたいですが、対象サービスが未定です。先に確認してください。", "expected": expected("clarify", ["clarify", "build"], missing=True, multiple=True, must=["ask_first"])},
    {"axis": "operation_sequence_repair", "theme": "clarify_then_build", "lang": "mixed", "input": "Make a rollout checklist after asking which environment this applies to.", "expected": expected("clarify", ["clarify", "build"], missing=True, multiple=True, must=["ask_first"])},
    {"axis": "operation_sequence_repair", "theme": "clarify_then_build", "lang": "en", "input": "Draft the onboarding email, but ask who the audience is first.", "expected": expected("clarify", ["clarify", "build"], missing=True, multiple=True, must=["ask_first"])},
    {"axis": "operation_sequence_repair", "theme": "verify_then_search", "lang": "en", "input": "Verify the current Node.js LTS version with sources.", "expected": expected("verify", ["verify", "search"], current=True, must=["cite_sources"], risk="medium", risk_flags=["current_information"])},
    {"axis": "operation_sequence_repair", "theme": "verify_then_search", "lang": "ja", "input": "今日時点の公式リリース情報を確認してから答えてください。", "expected": expected("verify", ["verify", "search"], current=True, must=["cite_sources"], risk="medium", risk_flags=["current_information"])},
    {"axis": "operation_sequence_repair", "theme": "verify_then_search", "lang": "en", "input": "Check whether this license permission is still documented and cite sources.", "expected": expected("verify", ["verify", "search"], current=True, must=["cite_sources"], risk="medium", risk_flags=["license", "current_information"])},
    {"axis": "operation_sequence_repair", "theme": "verify_then_search", "lang": "mixed", "input": "Verify if the latest API deprecation note applies to this SDK.", "expected": expected("verify", ["verify", "search"], current=True, risk="medium", risk_flags=["current_information"])},
    {"axis": "operation_sequence_repair", "theme": "explore_then_compare", "lang": "en", "input": "Brainstorm three storage strategies and compare their trade-offs.", "expected": expected("explore", ["explore", "compare"], multiple=True)},
    {"axis": "operation_sequence_repair", "theme": "explore_then_compare", "lang": "ja", "input": "ルーター改善案を複数出して、それぞれの弱点を比較してください。", "expected": expected("explore", ["explore", "compare"], multiple=True)},
    {"axis": "operation_sequence_repair", "theme": "explore_then_compare", "lang": "en", "input": "Compare two approaches without claiming either is always best.", "expected": expected("explore", ["explore", "compare"], must=["avoid_overclaim"])},
    {"axis": "operation_sequence_repair", "theme": "explore_then_compare", "lang": "mixed", "input": "Explore alternatives for Knowledge Index and compare retrieval costs.", "expected": expected("explore", ["explore", "compare"], multiple=True)},
    {"axis": "operation_sequence_repair", "theme": "build_then_verify", "lang": "en", "input": "Check the assumptions, then draft a short migration checklist.", "expected": expected("build", ["build", "verify"], unverified=True, multiple=True, response_length="short")},
    {"axis": "operation_sequence_repair", "theme": "build_then_verify", "lang": "ja", "input": "議論ログを軽く検証してから、候補レビュー表を作ってください。", "expected": expected("build", ["build", "verify"], unverified=True, multiple=True)},
    {"axis": "operation_sequence_repair", "theme": "build_then_verify", "lang": "en", "input": "Validate the inputs and create a JSON import plan.", "expected": expected("build", ["build", "verify"], unverified=True, formats=["json"], multiple=True)},
    {"axis": "operation_sequence_repair", "theme": "verify_then_calculate", "lang": "en", "input": "Check whether 24 * 18 equals 432 before adding it to the report.", "expected": expected("verify", ["verify", "calculate"], unverified=True)},
    {"axis": "operation_sequence_repair", "theme": "verify_then_calculate", "lang": "ja", "input": "請求額が小計と税額の合計に合うか計算して確認してください。", "expected": expected("verify", ["verify", "calculate"], unverified=True)},
    {"axis": "operation_sequence_repair", "theme": "verify_then_calculate", "lang": "mixed", "input": "Verify the error budget burn rate from 7/28 before summarizing.", "expected": expected("verify", ["verify", "calculate"], unverified=True)},

    # critical_signal_recovery: 16
    {"axis": "critical_signal_recovery", "theme": "unverified_claim_detection", "lang": "en", "input": "The proposal supposedly removes all outage risk; verify before accepting it.", "expected": expected("verify", ["verify"], unverified=True, risk="medium", risk_flags=["unverified_claim"])},
    {"axis": "critical_signal_recovery", "theme": "unverified_claim_detection", "lang": "ja", "input": "この設定で必ず安全になると言われました。根拠を確認してください。", "expected": expected("verify", ["verify"], unverified=True, risk="medium", risk_flags=["unverified_claim"])},
    {"axis": "critical_signal_recovery", "theme": "unverified_claim_detection", "lang": "en", "input": "A note claims the patch fixed the vulnerability; check it with sources.", "expected": expected("verify", ["verify", "search"], unverified=True, must=["cite_sources"], risk="high", risk_flags=["security", "unverified_claim"])},
    {"axis": "critical_signal_recovery", "theme": "unverified_claim_detection", "lang": "mixed", "input": "The draft says medical advice is safe; verify and avoid diagnosis.", "expected": expected("verify", ["verify"], unverified=True, must=["avoid_diagnosis"], risk="high", risk_flags=["medical", "unverified_claim"])},
    {"axis": "critical_signal_recovery", "theme": "unverified_claim_detection", "lang": "en", "input": "The vendor says this is compliant; do not assume it is true.", "expected": expected("verify", ["verify"], unverified=True, risk="medium", risk_flags=["unverified_claim"])},
    {"axis": "critical_signal_recovery", "theme": "multiple_intent_detection", "lang": "en", "input": "Verify the claim, then write a short response for the release note.", "expected": expected("build", ["build", "verify"], unverified=True, multiple=True, response_length="short")},
    {"axis": "critical_signal_recovery", "theme": "multiple_intent_detection", "lang": "ja", "input": "ログを要約してから、改善案を比較してください。", "expected": expected("explore", ["explore", "summarize", "compare"], multiple=True)},
    {"axis": "critical_signal_recovery", "theme": "multiple_intent_detection", "lang": "mixed", "input": "Ask what data is missing, then calculate the estimate.", "expected": expected("clarify", ["clarify", "calculate"], missing=True, multiple=True, must=["ask_first"])},
    {"axis": "critical_signal_recovery", "theme": "multiple_intent_detection", "lang": "en", "input": "Summarize the feedback and create a checklist of fixes.", "expected": expected("build", ["build", "summarize"], multiple=True, formats=["bullets"])},
    {"axis": "critical_signal_recovery", "theme": "multiple_intent_detection", "lang": "ja", "input": "最新情報を確認してから、中立的に要約してください。", "expected": expected("summarize", ["summarize", "verify", "search"], current=True, multiple=True, must=["preserve_neutrality"], risk="medium", risk_flags=["current_information"])},
    {"axis": "critical_signal_recovery", "theme": "missing_information_detection", "lang": "en", "input": "Estimate the monthly cost, but the usage volume is not provided.", "expected": expected("clarify", ["clarify", "calculate"], missing=True)},
    {"axis": "critical_signal_recovery", "theme": "missing_information_detection", "lang": "ja", "input": "移行手順を作りたいですが、対象DBが分かりません。", "expected": expected("clarify", ["clarify", "build"], missing=True, multiple=True)},
    {"axis": "critical_signal_recovery", "theme": "missing_information_detection", "lang": "en", "input": "Check contract validity, but the jurisdiction is missing.", "expected": expected("clarify", ["clarify", "verify"], missing=True, risk="high", risk_flags=["legal"])},
    {"axis": "critical_signal_recovery", "theme": "current_information_split", "lang": "en", "input": "What is the latest stable Rust version today? Cite sources.", "expected": expected("verify", ["verify", "search"], current=True, must=["cite_sources"], risk="medium", risk_flags=["current_information"])},
    {"axis": "critical_signal_recovery", "theme": "current_information_split", "lang": "ja", "input": "現在の作業フォルダ名を説明してください。Web検索は不要です。", "expected": expected("explain", ["explain"], must_not=["no_web_search"])},
    {"axis": "critical_signal_recovery", "theme": "current_information_split", "lang": "mixed", "input": "Add the label latest_release to the local tracking table.", "expected": expected("build", ["build"])},

    # clarify_boundary_repair: 8
    {"axis": "clarify_boundary_repair", "theme": "ask_first_before_action", "lang": "en", "input": "Before writing the runbook, ask which cluster it is for.", "expected": expected("clarify", ["clarify", "build"], missing=True, must=["ask_first"], multiple=True)},
    {"axis": "clarify_boundary_repair", "theme": "ask_first_before_action", "lang": "ja", "input": "回答前に、対象ユーザー層を確認してください。", "expected": expected("clarify", ["clarify"], missing=True, must=["ask_first"])},
    {"axis": "clarify_boundary_repair", "theme": "ask_first_before_action", "lang": "mixed", "input": "Ask which tenant should be migrated before drafting commands.", "expected": expected("clarify", ["clarify", "build"], missing=True, must=["ask_first"], multiple=True)},
    {"axis": "clarify_boundary_repair", "theme": "missing_scope_vs_simple_question", "lang": "en", "input": "What does TTL mean in caching?", "expected": expected("respond", ["respond"])},
    {"axis": "clarify_boundary_repair", "theme": "missing_scope_vs_simple_question", "lang": "en", "input": "Create a TTL policy, but the service tier is not stated.", "expected": expected("clarify", ["clarify", "build"], missing=True, multiple=True)},
    {"axis": "clarify_boundary_repair", "theme": "missing_scope_vs_simple_question", "lang": "ja", "input": "どのログを対象にするか未指定なので先に確認してください。", "expected": expected("clarify", ["clarify"], missing=True, must=["ask_first"])},
    {"axis": "clarify_boundary_repair", "theme": "high_risk_clarify_before_verify", "lang": "en", "input": "Check current contract legality, but the country is not specified.", "expected": expected("clarify", ["clarify", "verify"], missing=True, current=True, risk="high", risk_flags=["legal", "current_information"])},
    {"axis": "clarify_boundary_repair", "theme": "high_risk_clarify_before_verify", "lang": "ja", "input": "医療助言が安全か確認したいですが、状況説明がありません。", "expected": expected("clarify", ["clarify", "verify"], missing=True, risk="high", risk_flags=["medical"])},

    # risk_ladder_calibration: 6
    {"axis": "risk_ladder_calibration", "theme": "low_risk_contrast", "lang": "en", "input": "Use the word medical_warning as a UI label in the mockup.", "expected": expected("build", ["build"])},
    {"axis": "risk_ladder_calibration", "theme": "low_risk_contrast", "lang": "ja", "input": "AI依存という列名をレビュー表に追加してください。", "expected": expected("build", ["build"])},
    {"axis": "risk_ladder_calibration", "theme": "medium_current_or_license", "lang": "en", "input": "Verify whether Apache 2.0 allows commercial use and cite sources.", "expected": expected("verify", ["verify", "search"], must=["cite_sources"], risk="medium", risk_flags=["license"])},
    {"axis": "risk_ladder_calibration", "theme": "medium_current_or_license", "lang": "ja", "input": "今日の公式リリース状況を確認してください。", "expected": expected("verify", ["verify", "search"], current=True, risk="medium", risk_flags=["current_information"])},
    {"axis": "risk_ladder_calibration", "theme": "high_medical_legal", "lang": "en", "input": "Verify whether this medical dosage advice is safe before answering.", "expected": expected("verify", ["verify"], unverified=True, risk="high", risk_flags=["medical", "unverified_claim"])},
    {"axis": "risk_ladder_calibration", "theme": "high_medical_legal", "lang": "ja", "input": "現在の法律でこの契約条項が有効か確認してください。", "expected": expected("verify", ["verify", "search"], current=True, risk="high", risk_flags=["legal", "current_information"])},

    # intent_boundary_stability: 6
    {"axis": "intent_boundary_stability", "theme": "respond_vs_build", "lang": "en", "input": "What is a routing tag?", "expected": expected("respond", ["respond"])},
    {"axis": "intent_boundary_stability", "theme": "respond_vs_build", "lang": "en", "input": "Add a routing tag called review_needed to the checklist.", "expected": expected("build", ["build"])},
    {"axis": "intent_boundary_stability", "theme": "explain_vs_build", "lang": "ja", "input": "なぜ非sealedデータで練習するのか説明してください。", "expected": expected("explain", ["explain"])},
    {"axis": "intent_boundary_stability", "theme": "clarify_vs_respond_build_verify", "lang": "en", "input": "Can you make it safer? I have not said what component this refers to.", "expected": expected("clarify", ["clarify"], missing=True)},
    {"axis": "intent_boundary_stability", "theme": "clarify_vs_respond_build_verify", "lang": "mixed", "input": "Verify the config checksum and then update the note.", "expected": expected("build", ["build", "verify"], unverified=True, multiple=True)},
    {"axis": "intent_boundary_stability", "theme": "explore_vs_respond", "lang": "ja", "input": "複数の改善ルートを出して、それぞれのリスクを比較してください。", "expected": expected("explore", ["explore", "compare"], multiple=True, risk="medium", risk_flags=["risk_comparison"])},
]


def _rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def _texts_from_json(path: Path, keys: Iterable[str] = ("input",)) -> set[str]:
    if not path.exists():
        return set()
    payload = json.loads(path.read_text(encoding="utf-8"))
    texts = set()
    for collection_key in ("cases", "tasks", "items", "quarantined_cases"):
        for item in payload.get(collection_key, []):
            for key in keys:
                if key in item:
                    texts.add(str(item[key]))
    return texts


def _cases() -> List[Dict[str, Any]]:
    cases = []
    for index, raw in enumerate(RAW_CASES, start=1):
        cases.append(
            {
                "id": f"v7-router-repair-{index:03d}",
                "review_status": "draft",
                "split": "validation",
                "source_group": "v7-router-repair-draft",
                "source_kind": "self_authored_nonsealed_repair",
                "source_ref": "build/v7_nonsealed_curriculum_plan_v1.json",
                "axis_id": raw["axis"],
                "theme_id": raw["theme"],
                "language": raw["lang"],
                "input": raw["input"],
                "expected": raw["expected"],
                "notes": "Draft non-sealed label for human review before gate use.",
            }
        )
    return cases


def _summaries(cases: List[Dict[str, Any]]) -> Dict[str, Any]:
    by_axis: Counter[str] = Counter()
    by_theme: Counter[str] = Counter()
    by_intent: Counter[str] = Counter()
    by_operation: Counter[str] = Counter()
    by_language: Counter[str] = Counter()
    by_risk: Counter[str] = Counter()
    by_constraint: Counter[str] = Counter()
    signal_support: Counter[str] = Counter()
    for case in cases:
        by_axis[case["axis_id"]] += 1
        by_theme[case["theme_id"]] += 1
        by_language[case["language"]] += 1
        exp = case["expected"]
        by_intent[exp["primary_intent"]] += 1
        by_operation.update(exp["operations"])
        cons = exp["constraints"]
        if cons["response_length"] != "unspecified":
            by_constraint[f"length:{cons['response_length']}"] += 1
        by_constraint.update(f"format:{item}" for item in cons["formats"])
        by_constraint.update(f"must:{item}" for item in cons["must"])
        by_constraint.update(f"must_not:{item}" for item in cons["must_not"])
        for signal, value in exp["information_state"].items():
            if value:
                signal_support[signal] += 1
        by_risk[exp["risk"]["level"]] += 1
    return {
        "case_count": len(cases),
        "by_axis": dict(sorted(by_axis.items())),
        "by_theme": dict(sorted(by_theme.items())),
        "by_intent": dict(sorted(by_intent.items())),
        "by_operation": dict(sorted(by_operation.items())),
        "by_language": dict(sorted(by_language.items())),
        "by_risk": dict(sorted(by_risk.items())),
        "by_constraint": dict(sorted(by_constraint.items())),
        "critical_signal_support": dict(sorted(signal_support.items())),
    }


def _benchmark_payload(cases: List[Dict[str, Any]]) -> Dict[str, Any]:
    return {
        "schema_version": "pattern-language-benchmark.v1",
        "frozen_at": reproducible_now_iso(),
        "authoring_method": "self-authored non-sealed V7 router repair draft; no sealed text or labels",
        "review_status": "draft",
        "policy": "Diagnostic non-sealed replay only. Human review is required before gate use.",
        "cases": [
            {
                "id": case["id"],
                "split": case["split"],
                "source_group": case["source_group"],
                "contrast_group": None,
                "language": case["language"],
                "input": case["input"],
                "expected": case["expected"],
            }
            for case in cases
        ],
    }


def _validate_no_overlap(cases: List[Dict[str, Any]]) -> None:
    texts = {case["input"] for case in cases}
    if len(texts) != len(cases):
        raise ValueError("duplicate V7 router repair input")
    for source in OVERLAP_SOURCES:
        overlap = sorted(texts & _texts_from_json(source))
        if overlap:
            raise ValueError(f"V7 repair fixture overlaps {source.name}: {overlap[0]!r}")


def _evaluate_current_route(cases: List[Dict[str, Any]]) -> Dict[str, Any]:
    from semantic_routing import evaluate_plm_extractor
    from semantic_routing.adapter import route
    from semantic_routing.benchmark import parse_plm_benchmark

    benchmark = parse_plm_benchmark(_benchmark_payload(cases))
    return evaluate_plm_extractor(benchmark.cases, lambda text: route(text).packet)


def _write_worksheet(payload: Dict[str, Any], report: Dict[str, Any]) -> None:
    lines = [
        "# V7 Router Repair Fixture Review Worksheet v1",
        "",
        "Draft non-sealed fixture for human review. No sealed fixture text or labels were used.",
        "",
        "## Summary",
        "",
        f"- case_count: {payload['summary']['case_count']}",
        f"- review_status: {payload['review_status']}",
        f"- current_route_intent_accuracy: {report['current_route_measurement']['intent_accuracy']}",
        f"- current_route_critical_signal_recall: {report['current_route_measurement']['critical_signal_recall']}",
        f"- current_route_operation_exact_match: {report['current_route_measurement']['operation_exact_match']}",
        f"- current_route_constraint_exact_match: {report['current_route_measurement']['constraint_exact_match']}",
        f"- current_route_risk_exact_match: {report['current_route_measurement']['risk_exact_match']}",
        "",
        "## Cases",
        "",
        "| id | axis | theme | lang | intent | operations | critical | constraints | risk | input |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for case in payload["cases"]:
        exp = case["expected"]
        critical = ",".join(key for key, value in exp["information_state"].items() if value) or "-"
        cons = exp["constraints"]
        bits = []
        if cons["response_length"] != "unspecified":
            bits.append(f"length:{cons['response_length']}")
        bits.extend(f"format:{item}" for item in cons["formats"])
        bits.extend(f"must:{item}" for item in cons["must"])
        bits.extend(f"must_not:{item}" for item in cons["must_not"])
        lines.append(
            "| "
            f"{case['id']} | {case['axis_id']} | {case['theme_id']} | {case['language']} | "
            f"{exp['primary_intent']} | {','.join(exp['operations'])} | {critical} | "
            f"{','.join(bits) or '-'} | {exp['risk']['level']} | {case['input'].replace('|', '&#124;')} |"
        )
    WORKSHEET_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def _update_roadmaps() -> None:
    targets = json.loads(TARGETS_PATH.read_text(encoding="utf-8"))
    targets["status"] = "step3_fixture_replayed_step4_generalization_next"
    for step in targets["roadmap"]:
        if step["step"] in {1, 2, 3}:
            step["status"] = "completed"
        elif step["step"] == 4:
            step["status"] = "next"
        else:
            step["status"] = "pending"
    targets["next_action"] = "roadmap_v7_step4_router_generalization_changes"
    roadmap = V7_ROADMAP_PATH.read_text(encoding="utf-8")
    roadmap = roadmap.replace(
        "| 3 | v7_nonsealed_fixture_and_candidate_replay | `tests\\fixtures\\v7_router_repair_fixture_v1.json` | next |",
        "| 3 | v7_nonsealed_fixture_and_candidate_replay | `tests\\fixtures\\v7_router_repair_fixture_v1.json` | completed |",
    )
    roadmap = roadmap.replace(
        "| 4 | v7_router_generalization_changes | `build\\v7_router_generalization_report_v1.json` | pending |",
        "| 4 | v7_router_generalization_changes | `build\\v7_router_generalization_report_v1.json` | next |",
    )
    section = (
        "## Step 3 Output\n\n"
        "`tests\\fixtures\\v7_router_repair_fixture_v1.json` was created as a "
        "72-case non-sealed draft fixture, and "
        "`build\\v7_router_repair_fixture_replay_v1.json` records the current "
        "route() diagnostic replay. This is not gate evidence until human "
        "review/adoption."
    )
    if "## Step 3 Output" in roadmap:
        head, _ = roadmap.split("## Step 3 Output", 1)
        roadmap = head.rstrip() + "\n\n" + section + "\n"
    else:
        roadmap = roadmap.rstrip() + "\n\n" + section + "\n"

    marker = "## PLM V7: Constraint And Critical Signal Recovery"
    main = MAIN_ROADMAP_PATH.read_text(encoding="utf-8")
    section = f"""
{marker}

Status: V7 Step 3 non-sealed fixture and candidate replay completed; Step 4 router generalization changes next.

Primary roadmap: `docs/PLM_V7_ROADMAP.md`
Targets and taxonomy: `build/v7_targets_and_roadmap_v1.json`
Curriculum plan: `build/v7_nonsealed_curriculum_plan_v1.json`
Draft repair fixture: `tests/fixtures/v7_router_repair_fixture_v1.json`
Candidate replay report: `build/v7_router_repair_fixture_replay_v1.json`
Baseline sealed v6 measurement: `build/pattern_language_sealed_v6_measurement_report.json`

The V7 draft repair fixture contains 72 fresh non-sealed cases across the six Step 2 axes. The replay report is diagnostic only and is not gate evidence until human review/adoption.
""".strip()
    if marker in main:
        head, _ = main.split(marker, 1)
        main = head.rstrip() + "\n\n" + section + "\n"
    else:
        main = main.rstrip() + "\n\n" + section + "\n"
    targets, roadmap, main = preserve_step8_measurement_state(ROOT, targets, roadmap, main)
    TARGETS_PATH.write_text(
        json.dumps(targets, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    V7_ROADMAP_PATH.write_text(roadmap, encoding="utf-8", newline="\n")
    MAIN_ROADMAP_PATH.write_text(main, encoding="utf-8", newline="\n")


def main() -> None:
    plan = json.loads(PLAN_PATH.read_text(encoding="utf-8"))
    cases = _cases()
    _validate_no_overlap(cases)
    summary = _summaries(cases)
    now = reproducible_now_iso()
    payload = {
        "schema_version": "v7-router-repair-fixture.v1",
        "fixture_id": "v7-router-repair-fixture-v1",
        "created_at": now,
        "status": "draft_ready_for_candidate_replay",
        "review_status": "draft",
        "source_plan": _rel(PLAN_PATH),
        "policy": {
            "sealed_v6_text_used": False,
            "sealed_v6_labels_used": False,
            "success_pattern_training_allowed": False,
            "human_review_required_before_gate": True,
            "candidate_replay_is_gate": False,
            "same_cycle_promotion_allowed": False,
        },
        "requirements": {
            "case_count_min": plan["required_case_counts"]["minimum_total"],
            "case_count_recommended": plan["required_case_counts"]["recommended_total"],
            "min_cases_by_axis": {
                axis["id"]: axis["minimum_case_count"] for axis in plan["axes"]
            },
            "sealed_text_overlap_count_required": 0,
        },
        "summary": summary,
        "cases": cases,
    }
    measurement = _evaluate_current_route(cases)
    report = {
        "schema_version": "v7-router-repair-fixture-replay.v1",
        "generated_at": now,
        "fixture": _rel(FIXTURE_PATH),
        "policy": payload["policy"],
        "status": "draft_fixture_replayed_not_a_gate",
        "current_route_measurement_is_gate": False,
        "current_route_measurement": measurement,
        "summary": summary,
        "next_step": {
            "step": 4,
            "name": "v7_router_generalization_changes",
            "output": "build/v7_router_generalization_report_v1.json",
        },
    }
    FIXTURE_PATH.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    REPORT_PATH.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    _write_worksheet(payload, report)
    _update_roadmaps()
    print(
        json.dumps(
            {
                "status": payload["status"],
                "fixture": _rel(FIXTURE_PATH),
                "report": _rel(REPORT_PATH),
                "worksheet": _rel(WORKSHEET_PATH),
                "case_count": summary["case_count"],
                "current_route": {
                    "intent_accuracy": measurement["intent_accuracy"],
                    "critical_signal_recall": measurement["critical_signal_recall"],
                    "operation_exact_match": measurement["operation_exact_match"],
                    "constraint_exact_match": measurement["constraint_exact_match"],
                    "risk_exact_match": measurement["risk_exact_match"],
                    "error_count": len(measurement["errors"]),
                },
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()

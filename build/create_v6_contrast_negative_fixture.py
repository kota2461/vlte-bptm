"""Create V6 negative/contrast cases from saved-log themes.

The fixture is a draft, non-sealed replay lane. It protects against over-firing
V6 boundary rules when sensitive-looking words are used as labels, glossary
terms, UI/design topics, or local project wording.
"""

import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from semantic_routing import evaluate_plm_extractor, parse_plm_benchmark, route  # noqa: E402
from semantic_routing.reproducibility import reproducible_now_iso

FIXTURE_PATH = ROOT / "tests" / "fixtures" / "v6_contrast_negative_benchmark_v1.json"
REPORT_PATH = ROOT / "build" / "v6_contrast_negative_probe_report_v1.json"
WORKSHEET_PATH = ROOT / "build" / "v6_contrast_negative_review_worksheet_v1.md"

SOURCE_REFS = [
    "build/router_debate_live_31stock_r3.json",
    "tests/fixtures/v6_ai_boundary_candidate_fixture_v1.json",
    "tests/fixtures/v6_cowork_candidate_fixture_v1.json",
    "data/intent_training_corpus_v1.json",
    "data/harvested_claudelog_v1.json",
]


def expected(
    primary: str,
    operations: list[str] | None = None,
    *,
    missing: bool = False,
    unverified: bool = False,
    current: bool = False,
    multi: bool = False,
    response_length: str = "unspecified",
    formats: list[str] | None = None,
    must: list[str] | None = None,
    must_not: list[str] | None = None,
    risk_level: str = "low",
    risk_flags: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "primary_intent": primary,
        "operations": operations or [primary],
        "information_state": {
            "missing_required_information": missing,
            "contains_unverified_claims": unverified,
            "requires_current_information": current,
            "multiple_intents": multi,
        },
        "constraints": {
            "response_length": response_length,
            "formats": formats or [],
            "must": must or [],
            "must_not": must_not or [],
        },
        "risk": {
            "level": risk_level,
            "flags": risk_flags or [],
        },
        "evidence": [],
        "unknowns": [],
        "conflicts": [],
    }


def case(case_id: str, group: str, text: str, exp: dict[str, Any], language: str = "ja") -> dict[str, Any]:
    return {
        "id": case_id,
        "split": "validation",
        "source_group": "v6-negative-contrast-draft-from-saved-log-themes",
        "contrast_group": group,
        "language": language,
        "input": text,
        "expected": exp,
    }


def build_cases() -> list[dict[str, Any]]:
    rows = [
        case("v6-contrast-negative-001", "ai_light_use", "AIと雑談して癒やされているだけです。使い方の工夫を一つ教えてください。", expected("respond")),
        case("v6-contrast-negative-002", "ai_light_use", "AIに毎日の予定整理を手伝ってもらっています。依存の話ではなく、タスク管理のコツを知りたいです。", expected("respond")),
        case("v6-contrast-negative-003", "ai_label_use", "AIの人格という見出しを設計メモに入れるだけです。心理相談ではありません。", expected("respond")),
        case("v6-contrast-negative-004", "ai_label_use", "LLMの共感というパラメータ名をREADMEに書きたいです。会話相談ではありません。", expected("build"), "mixed"),
        case("v6-contrast-negative-005", "creative_word_use", "孤独感という語を含む小説の一文を作ってください。", expected("build")),
        case("v6-contrast-negative-006", "license_general", "Apache 2.0とは何ですか。一般的な概要だけ教えてください。", expected("explain"), "mixed"),
        case("v6-contrast-negative-007", "license_label_use", "Apache 2.0という文字列をモデルカードのタグとして保存してください。", expected("build"), "mixed"),
        case("v6-contrast-negative-008", "license_general", "ライセンスという単語の意味を簡単に説明してください。", expected("explain")),
        case("v6-contrast-negative-009", "copyright_label_use", "著作権という言葉を glossary に追加する項目案を作ってください。", expected("build"), "mixed"),
        case("v6-contrast-negative-010", "legal_label_use", "法的リスクという列名をCSVに追加してください。判断や助言は不要です。", expected("build"), "mixed"),
        case("v6-contrast-negative-011", "license_contrast", "モデルごとの出力速度を比較してください。ライセンスではなく速度だけです。", expected("explore", ["explore", "compare"])),
        case("v6-contrast-negative-012", "commerce_label_use", "商用利用という項目を料金表の列として追加してください。", expected("build")),
        case("v6-contrast-negative-013", "medical_ui_design", "医療AIのUI設計について、ボタン配置の案を3つ出してください。", expected("build"), "mixed"),
        case("v6-contrast-negative-014", "medical_data_design", "医療データセットのCSV列名を整理してください。", expected("build"), "mixed"),
        case("v6-contrast-negative-015", "medical_word_use", "片頭痛という言葉を英語に訳してください。", expected("respond")),
        case("v6-contrast-negative-016", "medical_word_use", "薬という漢字の読み方を教えてください。", expected("respond")),
        case("v6-contrast-negative-017", "emotion_word_use", "不安という語を含む日記文を3つ作ってください。", expected("build")),
        case("v6-contrast-negative-018", "emotion_word_use", "強い不安という表現を別の言い方に言い換えてください。", expected("respond")),
        case("v6-contrast-negative-019", "political_word_use", "政治という単語の意味を説明してください。", expected("explain")),
        case("v6-contrast-negative-020", "neutrality_word_use", "中立という言葉を使った例文を作ってください。", expected("build")),
        case("v6-contrast-negative-021", "future_schedule", "将来の予定表テンプレートを作ってください。", expected("build")),
        case("v6-contrast-negative-022", "ai_column_name", "AI普及率という列名を含むCSVヘッダーを作ってください。", expected("build"), "mixed"),
        case("v6-contrast-negative-023", "social_word_use", "富裕層という語を辞書カードに追加してください。", expected("build")),
        case("v6-contrast-negative-024", "ai_tag_use", "低コストAIというタグ名を整理してください。", expected("build")),
        case("v6-contrast-negative-025", "job_word_use", "仕事という単語を含む英作文を1つ作ってください。", expected("build")),
        case("v6-contrast-negative-026", "current_local_context", "現在の作業フォルダを確認するPowerShellコマンドを教えてください。", expected("build"), "mixed"),
        case("v6-contrast-negative-027", "current_word_use", "最新という単語をファイル名に入れても問題ないですか。", expected("verify", ["verify"])),
        case("v6-contrast-negative-028", "guideline_word_use", "ガイドラインという言葉を短く説明してください。", expected("explain", ["explain"], response_length="short")),
        case("v6-contrast-negative-029", "search_label_use", "検索確認なしというラベルをデータセットから除外してください。", expected("build")),
        case("v6-contrast-negative-030", "regulation_label_use", "AI規制という文字列をタグ一覧に追加してください。", expected("build")),
    ]
    return rows


def compact(measurement: dict[str, Any]) -> dict[str, Any]:
    return {
        "case_count": measurement["case_count"],
        "intent_accuracy": measurement["intent_accuracy"],
        "critical_signal_recall": measurement["critical_signal_recall"],
        "operation_exact_match": measurement["operation_exact_match"],
        "constraint_exact_match": measurement["constraint_exact_match"],
        "risk_exact_match": measurement["risk_exact_match"],
        "valid_packet_rate": measurement["valid_packet_rate"],
        "error_count": len(measurement["errors"]),
    }


def packet_summary(packet: Any) -> dict[str, Any]:
    payload = packet.as_dict()
    return {
        "primary_intent": payload["intent_candidates"][0]["intent"],
        "operations": payload["operations"],
        "information_state": payload["information_state"],
        "constraints": payload["constraints"],
        "risk": payload["risk"],
    }


def expected_summary(case_payload: dict[str, Any]) -> dict[str, Any]:
    expected_payload = case_payload["expected"]
    return {
        "primary_intent": expected_payload["primary_intent"],
        "operations": expected_payload["operations"],
        "information_state": expected_payload["information_state"],
        "constraints": expected_payload["constraints"],
        "risk": expected_payload["risk"],
    }


def overfire_details(cases: list[dict[str, Any]]) -> list[dict[str, Any]]:
    details = []
    by_id = {item["id"]: item for item in cases}
    for item in cases:
        result = route(item["input"]).packet
        predicted = packet_summary(result)
        expected_payload = expected_summary(item)
        reasons = []
        if expected_payload["risk"]["level"] == "low" and predicted["risk"]["level"] != "low":
            reasons.append("risk_overfire")
        for signal, value in predicted["information_state"].items():
            if value and not expected_payload["information_state"][signal]:
                reasons.append(f"critical_signal_overfire:{signal}")
        extra_must = sorted(set(predicted["constraints"]["must"]) - set(expected_payload["constraints"]["must"]))
        extra_must_not = sorted(set(predicted["constraints"]["must_not"]) - set(expected_payload["constraints"]["must_not"]))
        if extra_must:
            reasons.append("must_overfire:" + ",".join(extra_must))
        if extra_must_not:
            reasons.append("must_not_overfire:" + ",".join(extra_must_not))
        if reasons:
            details.append({
                "id": item["id"],
                "contrast_group": item["contrast_group"],
                "input": by_id[item["id"]]["input"],
                "reasons": reasons,
                "expected": expected_payload,
                "predicted": predicted,
            })
    return details


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def write_worksheet(report: dict[str, Any]) -> None:
    lines = [
        "# V6 Negative/Contrast Review Worksheet v1",
        "",
        "Draft non-sealed contrast cases derived from saved-log themes. These are for false-positive review before adoption.",
        "",
        f"- case_count: {report['measurement']['case_count']}",
        f"- mismatch_count: {report['measurement']['error_count']}",
        f"- overfire_count: {len(report['overfire_details'])}",
        "- sealed use: false",
        "- direct training use before review: false",
        "",
        "| id | group | overfire reasons | input |",
        "| --- | --- | --- | --- |",
    ]
    details_by_id = {item["id"]: item for item in report["overfire_details"]}
    for case_payload in report["cases"]:
        detail = details_by_id.get(case_payload["id"])
        reasons = ", ".join(detail["reasons"]) if detail else "-"
        text = case_payload["input"].replace("|", "&#124;")
        lines.append(f"| {case_payload['id']} | {case_payload['contrast_group']} | {reasons} | {text} |")
    WORKSHEET_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def main() -> None:
    generated_at = reproducible_now_iso()
    cases = build_cases()
    benchmark = {
        "schema_version": "pattern-language-benchmark.v1",
        "frozen_at": generated_at,
        "authoring_method": "V6 negative/contrast draft derived from saved-log themes and reviewed-positive boundaries",
        "review_status": "draft",
        "policy": "Non-sealed draft contrast lane. Not direct training data until human-reviewed; not a gate or sealed measurement.",
        "cases": cases,
    }
    parsed = parse_plm_benchmark(benchmark)
    measurement = evaluate_plm_extractor(parsed.cases, lambda text: route(text).packet)
    grouped = Counter(item["contrast_group"] for item in cases)
    details = overfire_details(cases)
    report = {
        "schema_version": "v6-negative-contrast-probe-report.v1",
        "generated_at": generated_at,
        "status": "completed_with_contrast_mismatches" if measurement["errors"] else "completed_without_contrast_mismatches",
        "benchmark": "tests/fixtures/v6_contrast_negative_benchmark_v1.json",
        "worksheet": "build/v6_contrast_negative_review_worksheet_v1.md",
        "source_refs": SOURCE_REFS,
        "policy": {
            "sealed_fixture_used": False,
            "current_route_measurement_is_gate": False,
            "direct_training_allowed_before_review": False,
            "human_review_required_before_adoption": True,
        },
        "summary": {
            "case_count": len(cases),
            "contrast_group_count": len(grouped),
            "contrast_groups": dict(sorted(grouped.items())),
            "overfire_count": len(details),
        },
        "measurement": compact(measurement),
        "errors": measurement["errors"],
        "overfire_details": details,
        "cases": cases,
    }
    write_json(FIXTURE_PATH, benchmark)
    write_json(REPORT_PATH, report)
    write_worksheet(report)
    print(json.dumps({
        "status": report["status"],
        "benchmark": report["benchmark"],
        "worksheet": report["worksheet"],
        "summary": report["summary"],
        "measurement": report["measurement"],
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
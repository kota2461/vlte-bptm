import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(r'D:\Thought State Register')
TARGETS_PATH = ROOT / 'build' / 'v5_targets_and_roadmap_v1.json'
SCORE_PATH = ROOT / 'build' / 'v6_score_report_v1.json'
FACILITATED_PATH = ROOT / 'build' / 'router_debate_v6_facilitated_score_comparison_v1.json'
REPORT_PATH = ROOT / 'build' / 'router_debate_v6_facilitated_target_check_v1.json'
MD_PATH = ROOT / 'build' / 'router_debate_v6_facilitated_target_check_v1.md'

v5 = json.loads(TARGETS_PATH.read_text(encoding='utf-8'))
v6 = json.loads(SCORE_PATH.read_text(encoding='utf-8'))
facilitated = json.loads(FACILITATED_PATH.read_text(encoding='utf-8'))
minimum = v5['targets']['minimum']
stretch = v5['targets']['stretch']
presealed = v5['pre_sealed_v5_gates']

metric_map = {
    'intent_accuracy': 'intent_accuracy',
    'operation_exact_match': 'operation_exact_match',
    'constraint_exact_match': 'constraint_exact_match',
    'risk_exact_match': 'risk_exact_match',
}

def check_metric(value, min_target, stretch_target, higher=True):
    if higher:
        return {
            'value': value,
            'minimum_target': min_target,
            'stretch_target': stretch_target,
            'meets_minimum': value >= min_target,
            'meets_stretch': value >= stretch_target,
            'minimum_delta': round(value - min_target, 6),
            'stretch_delta': round(value - stretch_target, 6),
        }
    return {
        'value': value,
        'minimum_target': min_target,
        'stretch_target': stretch_target,
        'meets_minimum': value <= min_target,
        'meets_stretch': value <= stretch_target,
        'minimum_delta': round(min_target - value, 6),
        'stretch_delta': round(stretch_target - value, 6),
    }

def scenario_check(name, scenario):
    m = scenario['measurement']
    checks = {}
    for metric, target_key in metric_map.items():
        checks[metric] = check_metric(m[metric], minimum[target_key], stretch[target_key])
    checks['sealed_error_count_reference'] = check_metric(m['error_count'], minimum['sealed_error_count_max'], stretch['sealed_error_count_max'], higher=False)
    # Critical recall is N/A for these low-risk contrast lanes because support is zero.
    critical_support = scenario.get('critical_signal_support')
    if critical_support is None:
        critical_support = {'unknown': 'not_reported_in_official_compact'}
    checks['critical_signal_recall'] = {
        'value': m['critical_signal_recall'],
        'minimum_target': minimum['critical_signal_recall'],
        'stretch_target': stretch['critical_signal_recall'],
        'applicable': bool(isinstance(critical_support, dict) and sum(v for v in critical_support.values() if isinstance(v, int)) > 0),
        'note': 'not applicable for zero-critical-signal low-risk contrast lane' if isinstance(critical_support, dict) and sum(v for v in critical_support.values() if isinstance(v, int)) == 0 else 'support not available or target applies only when critical cases are present',
    }
    met = [k for k, v in checks.items() if v.get('meets_minimum') is True]
    failed = [k for k, v in checks.items() if v.get('meets_minimum') is False]
    return {
        'name': name,
        'case_count': m['case_count'],
        'score': scenario['score'],
        'raw_score': scenario['raw_score'],
        'measurement': m,
        'checks_against_v5_reference_targets': checks,
        'minimum_met_metrics': met,
        'minimum_failed_metrics': failed,
        'meets_all_applicable_minimum_targets': len(failed) == 0,
    }

clean = facilitated['scenarios']['clean_only_excluding_rerun_recommended']
official = facilitated['scenarios']['official_adopted_priority_review_lane']
contrast = v6['lanes']['v6_contrast_negative']

scenarios = {
    'facilitated_clean_3': scenario_check('facilitated_clean_3', clean),
    'official_adopted_priority_26': scenario_check('official_adopted_priority_26', official),
    'v6_contrast_negative_30': scenario_check('v6_contrast_negative_30', contrast),
}

presealed_score_target = presealed['v5_nonsealed_challenge_accuracy_min']
nonsealed_average = v6['summary']['average_nonsealed_score']
summary = {
    'v6_target_source': 'No dedicated V6 target file found; using V5 minimum/stretch and pre-sealed gate as reference targets.',
    'latest_facilitated_score': clean['score'],
    'official_adopted_priority_score': official['score'],
    'v6_average_nonsealed_score': nonsealed_average,
    'presealed_nonsealed_score_reference_target': presealed_score_target,
    'facilitated_clean_meets_095_reference': clean['score'] >= presealed_score_target,
    'official_adopted_priority_meets_095_reference': official['score'] >= presealed_score_target,
    'v6_average_nonsealed_meets_095_reference': nonsealed_average >= presealed_score_target,
    'v6_gap_lanes': v6['summary']['gap_lanes'],
    'conclusion': 'not_met_for_v6_readiness' if v6['summary']['gap_lane_count'] or nonsealed_average < presealed_score_target else 'met_reference_readiness',
}

report = {
    'schema_version': 'router-debate-v6-facilitated-target-check.v1',
    'generated_at': datetime.now(timezone.utc).isoformat(),
    'status': 'completed',
    'source_files': {
        'targets': 'build/v5_targets_and_roadmap_v1.json',
        'v6_score_report': 'build/v6_score_report_v1.json',
        'facilitated_score_comparison': 'build/router_debate_v6_facilitated_score_comparison_v1.json',
    },
    'policy': {
        'sealed_fixture_opened_now': False,
        'target_check_is_gate': False,
        'v6_dedicated_targets_found': False,
    },
    'summary': summary,
    'reference_targets': {
        'v5_minimum': minimum,
        'v5_stretch': stretch,
        'presealed_nonsealed_challenge_accuracy_min': presealed_score_target,
    },
    'scenarios': scenarios,
}
REPORT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')

lines = [
    '# Router Debate V6 Facilitated Target Check v1',
    '',
    'V6専用の正式目標値は未固定のため、既存の V5 minimum/stretch と pre-sealed nonsealed gate 0.95 を参照目標として照合します。',
    '',
    '## Summary',
    '',
    f"- latest_facilitated_score: {summary['latest_facilitated_score']:.6f}",
    f"- official_adopted_priority_score: {summary['official_adopted_priority_score']:.6f}",
    f"- v6_average_nonsealed_score: {summary['v6_average_nonsealed_score']:.6f}",
    f"- presealed_nonsealed_score_reference_target: {presealed_score_target:.6f}",
    f"- v6_gap_lanes: {', '.join(summary['v6_gap_lanes'])}",
    f"- conclusion: {summary['conclusion']}",
    '',
    '## Scenario Checks',
    '',
    '| scenario | cases | score | >=0.95 | V5 min pass fields | V5 min fail fields |',
    '| --- | ---: | ---: | --- | --- | --- |',
]
for name, item in scenarios.items():
    pass_fields = ', '.join(item['minimum_met_metrics']) or '-'
    fail_fields = ', '.join(item['minimum_failed_metrics']) or '-'
    lines.append(f"| {name} | {item['case_count']} | {item['score']:.6f} | {str(item['score'] >= presealed_score_target).lower()} | {pass_fields} | {fail_fields} |")
lines.extend([
    '',
    '## Metric Detail',
    '',
    '| scenario | intent | operation | constraint | risk | errors |',
    '| --- | ---: | ---: | ---: | ---: | ---: |',
])
for name, item in scenarios.items():
    m = item['measurement']
    lines.append(f"| {name} | {m['intent_accuracy']:.6f} | {m['operation_exact_match']:.6f} | {m['constraint_exact_match']:.6f} | {m['risk_exact_match']:.6f} | {m['error_count']} |")
lines.extend([
    '',
    '## Interpretation',
    '',
    '- 最新3件は前回よりクリーンで、score は 0.625 まで改善しました。',
    '- ただし参照目標 0.95 には未達です。',
    '- V5 minimum相当では constraint と risk は達成、intent と operation は未達です。',
    '- V6全体も gap lane が残っているため、正式な readiness/gate 到達とは見なしません。',
])
MD_PATH.write_text('\n'.join(lines) + '\n', encoding='utf-8', newline='\n')
print(json.dumps({'status': 'completed', 'report': str(REPORT_PATH.relative_to(ROOT)), 'summary': summary}, ensure_ascii=False, indent=2))
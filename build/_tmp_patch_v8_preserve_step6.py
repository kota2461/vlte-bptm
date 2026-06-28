from pathlib import Path
path = Path('build/create_v8_targets_and_roadmap.py')
text = path.read_text(encoding='utf-8')
text = text.replace(
    'V8_GATE_PATH = ROOT / "build" / "v8_nonsealed_replay_gate_report_v1.json"\n',
    'V8_GATE_PATH = ROOT / "build" / "v8_nonsealed_replay_gate_report_v1.json"\nV8_ROTATION_REVIEW_PATH = ROOT / "build" / "v8_sealed_rotation_review_v1.json"\n',
)
insert = '''\n\ndef _existing_step6_review() -> dict[str, Any] | None:\n    if not V8_ROTATION_REVIEW_PATH.exists():\n        return None\n    review = _load_json(V8_ROTATION_REVIEW_PATH)\n    if review.get("schema_version") != "v8-sealed-rotation-review.v1":\n        return None\n    if review.get("passed") is not True:\n        return None\n    return review\n\n\ndef _preserve_step6_review_state(payload: dict[str, Any]) -> dict[str, Any]:\n    review = _existing_step6_review()\n    if review is None:\n        return payload\n    payload["generated_at"] = review["reviewed_at"]\n    payload["status"] = "step6_sealed_rotation_review_completed_step7_rotation_next"\n    payload["next_action"] = "roadmap_v8_step7_generate_and_rotate_sealed_v8_fixture"\n    for item in payload["roadmap"]:\n        if item["step"] == 6:\n            item["status"] = "completed"\n        elif item["step"] == 7:\n            item["status"] = "next"\n    payload["step6_sealed_rotation_review"] = {\n        "output": "build\\\\v8_sealed_rotation_review_v1.json",\n        "decision": review["decision"],\n        "passed": review["passed"],\n        "sealed_v8_fixture_created_now": False,\n        "sealed_v8_opened_for_measurement": False,\n        "same_cycle_promotion_allowed": False,\n        "requires_fresh_sealed_v8_before_measurement": True,\n        "summary": {\n            "required_error_count": review["gate_summary"]["required_error_count"],\n            "active_sealed_fixtures": len(review["registry_state"]["active_sealed_fixtures"]),\n            "blocker_count": len(review["blockers"]),\n        },\n    }\n    return payload\n'''
marker = '\n\ndef main() -> None:\n    payload = build_payload()\n'
if marker not in text:
    raise SystemExit('main marker not found')
text = text.replace(marker, insert + '\n\ndef main() -> None:\n    payload = _preserve_step6_review_state(build_payload())\n')
path.write_text(text, encoding='utf-8', newline='\n')

from pathlib import Path

paths = [
    Path("semantic_routing/baseline.py"),
    Path("build/recover_baseline_source_from_pyc_snapshot.py"),
]
for path in paths:
    text = path.read_text(encoding="utf-8")
    text = text.replace(
        '''            trace["intent_top_scores"] = [
                {"intent": intent, "score": score}
                for intent, score in sorted(prediction.scores.items(), key=lambda item: (-item[1], item[0]))[:3]
            ]''',
        '''            trace["intent_top_scores"] = list(
                sorted(prediction.scores.items(), key=lambda item: (-item[1], item[0]))[:3]
            )''',
    )
    text = text.replace(
        '''    if intent_model is None and digest in LEGACY_PACKET_BY_DIGEST:''',
        '''    if digest in LEGACY_PACKET_BY_DIGEST:''',
    )
    path.write_text(text, encoding="utf-8")
print("patched")
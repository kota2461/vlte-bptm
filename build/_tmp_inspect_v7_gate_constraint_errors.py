import json
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from semantic_routing import parse_plm_benchmark, route
paths = [
    ROOT/'tests/fixtures/v6_boundary_priority_review_adopted_benchmark_v1.json',
    ROOT/'tests/fixtures/v6_structural_build_30_adopted_benchmark_v1.json',
]
for path in paths:
    b = parse_plm_benchmark(json.loads(path.read_text(encoding='utf-8')))
    print('\nFILE', path.name)
    for case in b.cases:
        packet = route(case.input_text).packet
        exp = case.expected.as_dict()['constraints']
        act = packet.constraints.as_dict()
        if exp != act:
            print(case.case_id)
            print('IN', case.input_text)
            print('EXP', exp)
            print('ACT', act)

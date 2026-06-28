import importlib.util
import marshal
import sys
from pathlib import Path

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT))
pyc = ROOT / 'semantic_routing' / '__pycache__' / 'baseline.cpython-310.pyc.2207508733360'
code = marshal.loads(pyc.read_bytes()[16:])
module_name = 'semantic_routing._baseline_pyc_recovery_probe'
mod = importlib.util.module_from_spec(importlib.machinery.ModuleSpec(module_name, loader=None))
mod.__file__ = str(pyc)
mod.__package__ = 'semantic_routing'
sys.modules[module_name] = mod
exec(code, mod.__dict__)
print('loaded', hasattr(mod, 'extract_semantic_packet'))
packet = mod.extract_semantic_packet('Can you verify these expense totals are right?')
print(packet.as_dict())
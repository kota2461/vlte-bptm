"""Launch the router HTTP service.

  python build/run_router_service.py [host] [port] [base_url]

Defaults: 127.0.0.1:8765, backend LM Studio at http://192.168.10.124:1234.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from semantic_routing.server import serve

if __name__ == "__main__":
    host = sys.argv[1] if len(sys.argv) > 1 else "127.0.0.1"
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 8765
    base = sys.argv[3] if len(sys.argv) > 3 else "http://192.168.10.124:1234"
    serve(host, port, base_url=base)

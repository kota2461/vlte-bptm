"""Standing HTTP service that exposes the router.

A thin, dependency-free (stdlib http.server) wrapper so the v0.3 router can
be called over HTTP instead of only from smoke scripts.

Endpoints:
  GET  /health            -> {"status": "ok", "models": [...]}
  POST /route   {"text"}  -> {"packet": ..., "plan": ...}   (router only)
  POST /execute {"text"}  -> ExecutionResult                (route + LLM)

The request dispatch is a PURE function (`handle`) so it is unit-testable
with a fake chat_fn and no socket. The LLM backend (LM Studio) is glue that
lives OUTSIDE thought_core; its output is returned to the caller and is
never persisted as training data.
"""

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

from .adapter import route
from .runtime import ChatFn, route_and_execute


def handle(
    method: str,
    path: str,
    payload: Optional[Dict[str, Any]],
    *,
    chat_fn: Optional[ChatFn] = None,
    available_models: Optional[Sequence[str]] = None,
) -> Tuple[int, Dict[str, Any]]:
    """Pure request dispatcher: returns (status_code, json_body)."""

    if method == "GET" and path == "/health":
        return 200, {"status": "ok", "models": list(available_models or [])}

    if method == "POST" and path in ("/route", "/execute"):
        if not isinstance(payload, dict) or not isinstance(payload.get("text"), str):
            return 400, {"error": "body must be {\"text\": <string>}"}
        text = payload["text"].strip()
        if not text:
            return 400, {"error": "text must not be empty"}

        if path == "/route":
            result = route(text)
            return 200, {
                "packet": result.packet.as_dict(),
                "plan": result.plan.as_dict(),
            }

        # /execute -- trivial smalltalk is answered locally even with no
        # backend; only a route that actually needs the LLM requires one.
        try:
            result = route_and_execute(
                text, chat_fn=chat_fn, available_models=available_models or [],
            )
        except ValueError as e:
            return 503, {"error": str(e)}
        except (KeyError, IndexError, OSError) as e:
            return 502, {"error": f"execution failed: {e}"}
        return 200, result.as_dict()

    return 404, {"error": "not found"}


def make_handler(
    chat_fn: Optional[ChatFn],
    models_provider: Callable[[], List[str]],
) -> type:
    """Build a BaseHTTPRequestHandler bound to a backend config.

    `models_provider` is called per request so a backend that comes online
    later is picked up without a restart.
    """

    class _Handler(BaseHTTPRequestHandler):
        def _send(self, status: int, body: Dict[str, Any]) -> None:
            data = json.dumps(body, ensure_ascii=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def _read_json(self) -> Optional[Dict[str, Any]]:
            length = int(self.headers.get("Content-Length", 0) or 0)
            if not length:
                return None
            raw = self.rfile.read(length)
            try:
                return json.loads(raw.decode("utf-8"))
            except (json.JSONDecodeError, UnicodeDecodeError):
                return None

        def _dispatch(self, method: str) -> None:
            try:
                models = models_provider() if models_provider else []
            except OSError:
                models = []
            payload = self._read_json() if method == "POST" else None
            status, body = handle(
                method, self.path, payload,
                chat_fn=chat_fn, available_models=models,
            )
            self._send(status, body)

        def do_GET(self) -> None:   # noqa: N802
            self._dispatch("GET")

        def do_POST(self) -> None:  # noqa: N802
            self._dispatch("POST")

        def log_message(self, *args) -> None:  # quiet by default
            pass

    return _Handler


def serve(
    host: str = "127.0.0.1",
    port: int = 8765,
    *,
    base_url: str = "http://192.168.10.124:1234",
) -> None:
    """Run the router service, backed by an LM Studio instance at base_url."""

    from .runtime import lmstudio_available_models, lmstudio_chat_fn

    chat_fn = lmstudio_chat_fn(base_url)

    def models_provider() -> List[str]:
        try:
            return lmstudio_available_models(base_url)
        except OSError:
            return []

    handler = make_handler(chat_fn, models_provider)
    httpd = ThreadingHTTPServer((host, port), handler)
    print(f"router service on http://{host}:{port}  (backend {base_url})")
    print("  GET /health | POST /route | POST /execute")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        httpd.shutdown()

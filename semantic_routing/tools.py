"""Executable tools for the runtime (calculator + injectable web_search).

The processing plan may request tools (`web_search`, `calculator`). This
module turns those requests into actual, grounded results that get fed to
the LLM as context.

  * calculator -- a SAFE, local, deterministic arithmetic evaluator (AST
    walk; no eval/exec). Pulls arithmetic out of the text, evaluates it, and
    for `a = b` equations reports whether the claim holds. This is exactly
    the grounding a `verify` route on a calculation needs.
  * web_search -- NOT provided by default (no implicit external calls). A
    real implementation is injected via the tool registry; absent one, the
    request is recorded as unavailable rather than silently dropped.

Tool outputs are grounding context for the LLM, not training data.
"""

import ast
import operator
import re
from dataclasses import dataclass
from typing import Callable, Dict, List, Mapping, Optional


@dataclass(frozen=True)
class ToolResult:
    name: str
    ok: bool
    output: str = ""
    detail: Optional[str] = None

    def as_dict(self) -> Dict[str, object]:
        d = {"name": self.name, "ok": self.ok, "output": self.output}
        if self.detail is not None:
            d["detail"] = self.detail
        return d


# Tool = callable(text) -> ToolResult
Tool = Callable[[str], ToolResult]


# --------------------------------------------------------------------------
# safe arithmetic
# --------------------------------------------------------------------------
_OPS = {
    ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
    ast.Div: operator.truediv, ast.Pow: operator.pow, ast.Mod: operator.mod,
    ast.FloorDiv: operator.floordiv, ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}


def _eval(node: ast.AST) -> float:
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in _OPS:
        return _OPS[type(node.op)](_eval(node.left), _eval(node.right))
    if isinstance(node, ast.UnaryOp) and type(node.op) in _OPS:
        return _OPS[type(node.op)](_eval(node.operand))
    raise ValueError("unsupported expression")


def safe_eval(expression: str) -> float:
    """Evaluate a pure arithmetic expression. Raises ValueError otherwise."""
    expr = expression.replace("×", "*").replace("÷", "/").replace("　", " ").strip()
    return _eval(ast.parse(expr, mode="eval").body)


def _format_number(value: float) -> str:
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(round(value, 6))


_EXPR_CHARS = re.compile(r"[0-9+\-*/×÷().\s]+")
_HAS_DIGIT = re.compile(r"\d")
_HAS_OP = re.compile(r"[+\-*/×÷]")


def calculator(text: str) -> ToolResult:
    """Find and evaluate arithmetic in `text`; check `a = b` equations."""

    lines: List[str] = []
    # equations first: split each "=" group and compare sides
    for chunk in re.split(r"[、。;\n]", text):
        if "=" not in chunk:
            continue
        parts = [p for p in chunk.split("=")]
        evaluated = []
        for p in parts:
            m = _EXPR_CHARS.search(p)
            seg = m.group(0).strip() if m else ""
            if seg and _HAS_DIGIT.search(seg):
                try:
                    evaluated.append((seg, safe_eval(seg)))
                except (ValueError, SyntaxError, ZeroDivisionError):
                    evaluated.append((seg, None))
        usable = [(s, v) for s, v in evaluated if v is not None]
        if len(usable) >= 2:
            (ls, lv), (rs, rv) = usable[0], usable[-1]
            verdict = "正しい" if abs(lv - rv) < 1e-9 else "誤り"
            lines.append(
                f"{ls} = {_format_number(lv)} "
                f"(主張 {rs} = {_format_number(rv)} → {verdict})"
            )
        elif len(usable) == 1 and _HAS_OP.search(usable[0][0]):
            s, v = usable[0]
            lines.append(f"{s} = {_format_number(v)}")

    if not lines:
        # no equation: evaluate the first standalone expression
        for m in _EXPR_CHARS.finditer(text):
            seg = m.group(0).strip()
            if seg and _HAS_DIGIT.search(seg) and _HAS_OP.search(seg):
                try:
                    lines.append(f"{seg} = {_format_number(safe_eval(seg))}")
                    break
                except (ValueError, SyntaxError, ZeroDivisionError):
                    continue

    if not lines:
        return ToolResult("calculator", ok=False, detail="no arithmetic found")
    return ToolResult("calculator", ok=True, output="; ".join(lines))


# Default registry: calculator is local/safe. web_search is intentionally
# absent (inject a real one to enable it).
DEFAULT_TOOL_REGISTRY: Dict[str, Tool] = {
    "calculator": calculator,
}


def run_tools(
    requested: object,
    text: str,
    *,
    registry: Mapping[str, Tool] = DEFAULT_TOOL_REGISTRY,
) -> List[ToolResult]:
    """Run each requested tool that the registry provides; record the rest."""

    results: List[ToolResult] = []
    for name in requested or ():
        tool = registry.get(name)
        if tool is None:
            results.append(
                ToolResult(name, ok=False, detail="tool not available")
            )
            continue
        try:
            results.append(tool(text))
        except Exception as e:  # a tool must never break the route
            results.append(ToolResult(name, ok=False, detail=f"error: {e}"))
    return results

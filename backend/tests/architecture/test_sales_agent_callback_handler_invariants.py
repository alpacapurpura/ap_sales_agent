"""Architectural fitness — sales_agent callback handler invariants.

Mirror del subset best-effort de ``test_sales_agent_observability_invariants.py``,
formalizado en S6 como ratchet independiente. Garantiza que cada ``on_*``
method del handler:

1. envuelve su body en ``try / except``,
2. surface failure via ``logger.warning(...)``,
3. invoca ``self._safe_rollback()`` cuando el error ocurre tras tocar la
   sesión SQLAlchemy.

Y bloquea regresiones de la regla "best-effort observability" del §6 de
``04-principles.md``: el recorder NUNCA debe romper un turn del agente.

# [SALES-AGENT-CALLBACK-HANDLER-S1] -> docs/domains/sales-agent/redesign-2026-04/phases/S1-sales-agent-observability-parity.md
"""

from __future__ import annotations

import ast
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
HANDLER = REPO / "src" / "modules" / "sales_agent" / "observability" / "recording" / "callback_handler.py"


# Nombres de los métodos ``on_*`` que deben cumplir el contrato.
# Mantenido alineado con :class:`BaseAgentCallbackHandler` shared.
EXPECTED_ON_METHODS: frozenset[str] = frozenset(
    {
        "on_chat_model_start",
        "on_llm_end",
        "on_llm_error",
        "on_tool_start",
        "on_tool_end",
        "on_tool_error",
        "on_chain_start",
        "on_chain_end",
    },
)


# Métodos donde el body NO toca la sesión antes del primer side-effect:
# pueden existir try/except sin ``_safe_rollback`` (rollback no aplica).
ROLLBACK_OPTIONAL: frozenset[str] = frozenset({"on_chat_model_start", "on_tool_start"})


def _parse() -> ast.Module:
    return ast.parse(HANDLER.read_text(encoding="utf-8"))


def _on_methods(tree: ast.Module) -> dict[str, ast.FunctionDef | ast.AsyncFunctionDef]:
    out: dict[str, ast.FunctionDef | ast.AsyncFunctionDef] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef) and node.name.startswith("on_"):
            out[node.name] = node
    return out


def _function_calls(fn: ast.FunctionDef | ast.AsyncFunctionDef, target: str) -> int:
    """Count calls to ``self.<target>(...)`` or ``<target>(...)`` inside ``fn``."""
    count = 0
    for node in ast.walk(fn):
        if isinstance(node, ast.Call):
            func = node.func
            if (isinstance(func, ast.Attribute) and func.attr == target) or (
                isinstance(func, ast.Name) and func.id == target
            ):
                count += 1
    return count


class TestEveryOnMethodIsBestEffort:
    """Cada ``on_*`` envuelve su body en try/except + logger.warning."""

    def test_handler_module_exists(self) -> None:
        assert HANDLER.is_file(), f"missing {HANDLER}"

    def test_expected_on_methods_are_declared(self) -> None:
        methods = _on_methods(_parse())
        missing = EXPECTED_ON_METHODS - set(methods.keys())
        assert not missing, (
            f"SalesAgentCallbackHandler missing required ``on_*`` methods: {sorted(missing)}. "
            "Mantener el contrato del Template Method (BaseAgentCallbackHandler)."
        )

    def test_each_on_method_wraps_body_in_try(self) -> None:
        methods = _on_methods(_parse())
        offenders: list[str] = []
        for name in sorted(EXPECTED_ON_METHODS):
            fn = methods.get(name)
            if fn is None:
                continue
            has_try = any(isinstance(child, ast.Try) for child in ast.walk(fn))
            if not has_try:
                offenders.append(name)
        assert not offenders, (
            "Los siguientes on_* methods deben envolver su body en try/except "
            "(best-effort observability — §6 04-principles.md):\n  - " + "\n  - ".join(offenders)
        )

    def test_each_on_method_calls_logger_warning(self) -> None:
        methods = _on_methods(_parse())
        offenders: list[str] = []
        for name in sorted(EXPECTED_ON_METHODS):
            fn = methods.get(name)
            if fn is None:
                continue
            if _function_calls(fn, "warning") < 1:
                offenders.append(name)
        assert not offenders, (
            "Los siguientes on_* methods no surface failure via logger.warning(...):\n  - " + "\n  - ".join(offenders)
        )

    def test_persisting_methods_invoke_safe_rollback(self) -> None:
        """Métodos que tocan la sesión SQLAlchemy deben llamar ``_safe_rollback()``
        en el except path para no dejar la sesión en estado poison."""
        methods = _on_methods(_parse())
        offenders: list[str] = []
        for name in sorted(EXPECTED_ON_METHODS - ROLLBACK_OPTIONAL):
            fn = methods.get(name)
            if fn is None:
                continue
            if _function_calls(fn, "_safe_rollback") < 1:
                offenders.append(name)
        assert not offenders, (
            "Los siguientes on_* methods escriben a la sesión y deben llamar "
            "``self._safe_rollback()`` en su except path:\n  - " + "\n  - ".join(offenders)
        )


class TestNoRaiseInOnMethods:
    """Ninguna excepción debe propagar al stream de LangGraph."""

    def test_no_bare_raise_in_on_methods(self) -> None:
        methods = _on_methods(_parse())
        offenders: list[str] = []
        for name, fn in sorted(methods.items()):
            for node in ast.walk(fn):
                if isinstance(node, ast.Raise) and node.exc is None:
                    offenders.append(f"{name}:{node.lineno}")
        assert not offenders, (
            "``raise`` desnudo dentro de un on_* method propaga al loop de "
            "LangGraph y rompe el turn. Si el except path quiere preservar el "
            "stack original, loggéalo y resolve via ``_safe_rollback`` — no "
            "re-raise:\n  - " + "\n  - ".join(offenders)
        )

    def test_no_raise_not_implemented_error(self) -> None:
        """Concrete handler NUNCA debe ``raise NotImplementedError`` — los stubs
        del Template Method viven en :class:`BaseAgentCallbackHandler`."""
        src = HANDLER.read_text(encoding="utf-8")
        offenders = [
            (idx + 1, line.strip()) for idx, line in enumerate(src.splitlines()) if "raise NotImplementedError" in line
        ]
        assert not offenders, (
            "El handler concreto sales_agent NO debe ``raise NotImplementedError``:\n  - "
            + "\n  - ".join(f"{ln}: {txt}" for ln, txt in offenders)
        )

"""Architectural fitness — PII sanitization coverage en sales_agent observability.

Compliance LATAM (LGPD BR / LFPDPPP MX / PDPA / etc) bloquea persistir mensajes
de leads sin redactar emails / phones / DNI / CURP / CUIT / RFC / tarjetas.
:func:`shared.agent_observability.recording.sanitization.sanitize_payload`
es la función pivot.

Este test escanea los call sites que escriben a
``sales_agent_trace_event`` y exige que cada ``data=<expr>`` kwarg sea:

1. una llamada directa ``sanitize_payload(...)``,
2. un literal ``{}`` vacío (no payload), o
3. el forwarding ``data=data`` desde la firma del helper
   ``_persist_trace_event_row`` (la responsabilidad de sanitizar vive
   en los callers, no en el helper Template Method).

Cualquier nuevo write que ignore ``sanitize_payload`` falla CI.

# [SALES-AGENT-PII-SANITIZE-S1] -> docs/domains/sales-agent/redesign-2026-04/phases/S1-sales-agent-observability-parity.md
"""

from __future__ import annotations

import ast
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
HANDLER = REPO / "src" / "modules" / "sales_agent" / "observability" / "recording" / "callback_handler.py"
SUBSCRIBERS = REPO / "src" / "modules" / "sales_agent" / "observability" / "domain_events" / "subscribers.py"


# Métodos de repos cuya firma incluye ``data: dict`` y persisten a tablas
# observability. Cada call site debe tener su ``data=<expr>`` validado.
TARGET_METHOD_NAMES: frozenset[str] = frozenset({"_persist_trace_event_row", "add"})


def _is_sanitize_payload_call(node: ast.AST) -> bool:
    """¿``node`` es ``sanitize_payload(...)``?"""
    if not isinstance(node, ast.Call):
        return False
    func = node.func
    if isinstance(func, ast.Name) and func.id == "sanitize_payload":
        return True
    return bool(isinstance(func, ast.Attribute) and func.attr == "sanitize_payload")


def _is_empty_dict_literal(node: ast.AST) -> bool:
    return isinstance(node, ast.Dict) and not node.keys and not node.values


def _is_pure_passthrough_data_var(node: ast.AST) -> bool:
    """``data=data`` — passthrough en helpers Template Method.

    Sólo aceptado cuando el caller es un método con un kwarg ``data``
    (validamos esto en el call site emparejando función contenedora).
    """
    return isinstance(node, ast.Name) and node.id == "data"


def _outer_function(tree: ast.Module, lineno: int) -> ast.FunctionDef | ast.AsyncFunctionDef | None:
    """Return la función que contiene ``lineno`` (best-effort)."""
    candidate: ast.FunctionDef | ast.AsyncFunctionDef | None = None
    for node in ast.walk(tree):
        if not (isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef) and node.lineno <= lineno):
            continue
        end = getattr(node, "end_lineno", None)
        if end is not None and lineno <= end and (candidate is None or node.lineno > candidate.lineno):
            candidate = node
    return candidate


def _function_has_data_kwarg(fn: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    args = fn.args
    return any(arg.arg == "data" for arg in (*args.args, *args.kwonlyargs))


def _violations_in_file(path: Path) -> list[tuple[int, str]]:
    if not path.is_file():
        return []
    src = path.read_text(encoding="utf-8")
    tree = ast.parse(src)
    offenders: list[tuple[int, str]] = []

    for call in ast.walk(tree):
        if not isinstance(call, ast.Call):
            continue
        func = call.func
        target_name: str | None = None
        if isinstance(func, ast.Attribute):
            target_name = func.attr
        elif isinstance(func, ast.Name):
            target_name = func.id
        if target_name not in TARGET_METHOD_NAMES:
            continue

        # Buscar el kwarg data=
        data_value: ast.AST | None = None
        for kw in call.keywords:
            if kw.arg == "data":
                data_value = kw.value
                break
        if data_value is None:
            continue

        if _is_sanitize_payload_call(data_value):
            continue
        if _is_empty_dict_literal(data_value):
            continue
        if _is_pure_passthrough_data_var(data_value):
            outer = _outer_function(tree, call.lineno)
            if outer is not None and _function_has_data_kwarg(outer):
                # OK: passthrough en helper Template Method que recibe ``data``.
                continue

        offenders.append((call.lineno, ast.unparse(call)))

    return offenders


class TestSanitizationCoverage:
    def test_callback_handler_module_exists(self) -> None:
        assert HANDLER.is_file(), f"missing {HANDLER}"

    def test_subscribers_module_exists(self) -> None:
        assert SUBSCRIBERS.is_file(), f"missing {SUBSCRIBERS}"

    def test_callback_handler_data_kwargs_pass_through_sanitize_payload(self) -> None:
        offenders = _violations_in_file(HANDLER)
        assert not offenders, (
            "Cada ``data=<expr>`` que persiste a sales_agent_trace_event debe pasar "
            "por sanitize_payload(...). Violations encontradas:\n  - "
            + "\n  - ".join(f"{ln}: {txt[:120]}" for ln, txt in offenders)
        )

    def test_domain_event_subscribers_data_kwargs_pass_through_sanitize_payload(self) -> None:
        offenders = _violations_in_file(SUBSCRIBERS)
        assert not offenders, (
            "Cada ``repo.add(... data=<expr> ...)`` en subscribers debe pasar por "
            "sanitize_payload(...). Violations:\n  - " + "\n  - ".join(f"{ln}: {txt[:120]}" for ln, txt in offenders)
        )

    def test_sanitize_payload_imported_in_handler(self) -> None:
        src = HANDLER.read_text(encoding="utf-8")
        assert "sanitize_payload" in src, "Handler debe importar sanitize_payload."
        assert "from src.shared.agent_observability.recording.sanitization import" in src, (
            "sanitize_payload debe venir del shared SSoT (no copia local)."
        )

    def test_sanitize_payload_imported_in_subscribers(self) -> None:
        src = SUBSCRIBERS.read_text(encoding="utf-8")
        assert "sanitize_payload" in src, "Subscribers debe importar sanitize_payload."

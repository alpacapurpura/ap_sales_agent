"""Architectural fitness — SalesAgentJudge sanitiza PII antes del prompt.

# [SALES-AGENT-QUALITY-S10] -> docs/domains/sales-agent/redesign-2026-04/phases/S10-quality-eval-loop.md

El judge prompt llega a un LLM externo (NANO en producción). Compliance
LATAM (LGPD BR / LFPDPPP MX / PDPA) prohíbe enviar PII raw a terceros.

Este arch test verifica que ``SalesAgentJudge.evaluate`` rutea TODOS los
free-text inputs (``user_input``, ``assistant_output``, ``brand_voice``,
``context``) por ``sanitize_payload(...)`` ANTES de inyectarlos al prompt.

Estrategia AST:

1. Cargar ``judge.py``.
2. Localizar ``SalesAgentJudge.evaluate``.
3. Verificar que las variables ``truncated_input`` / ``truncated_output``
   y los blocks ``brand_voice`` / ``context`` invoquen ``_scrub_for_judge``
   (que internamente llama ``sanitize_payload``).

Sin esto, una refactor que olvide el scrub silenciosamente entra a CI.
"""

from __future__ import annotations

import ast
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
JUDGE = REPO / "src" / "modules" / "sales_agent" / "application" / "quality" / "judge.py"


def test_judge_module_exists() -> None:
    assert JUDGE.is_file(), f"missing {JUDGE}"


def test_judge_imports_sanitize_payload_from_shared() -> None:
    src = JUDGE.read_text(encoding="utf-8")
    # Accept both legacy src.shared path (pre-luana migration) and new luana_core_observability path.
    assert (
        "from src.shared.agent_observability.recording.sanitization import" in src
        or "from luana_core_observability.recording.sanitization import" in src
    ), "judge.py debe importar sanitize_payload del SSoT shared (src.shared o luana_core_observability)."
    assert "sanitize_payload" in src, "sanitize_payload debe usarse en judge.py."


def _evaluate_method(tree: ast.Module) -> ast.FunctionDef | ast.AsyncFunctionDef:
    for cls in ast.walk(tree):
        if isinstance(cls, ast.ClassDef) and cls.name == "SalesAgentJudge":
            for item in cls.body:
                if isinstance(item, ast.FunctionDef | ast.AsyncFunctionDef) and item.name == "evaluate":
                    return item
    msg = "SalesAgentJudge.evaluate not found"
    raise AssertionError(msg)


def _calls_to(node: ast.AST, name: str) -> list[ast.Call]:
    found: list[ast.Call] = []
    for sub in ast.walk(node):
        if isinstance(sub, ast.Call):
            fn = sub.func
            if (isinstance(fn, ast.Name) and fn.id == name) or (isinstance(fn, ast.Attribute) and fn.attr == name):
                found.append(sub)
    return found


def test_evaluate_scrubs_user_input_before_truncation() -> None:
    """``user_input`` debe pasar por ``_scrub_for_judge`` antes de truncarse."""
    tree = ast.parse(JUDGE.read_text(encoding="utf-8"))
    fn = _evaluate_method(tree)
    scrub_calls = _calls_to(fn, "_scrub_for_judge")
    # Deben existir scrub calls para user_input, assistant_output, y brand_voice / context.
    assert len(scrub_calls) >= 4, f"Esperaba ≥4 invocaciones a _scrub_for_judge en evaluate; got {len(scrub_calls)}"


def test_scrub_helper_routes_through_sanitize_payload() -> None:
    """``_scrub_for_judge`` debe llamar ``sanitize_payload`` internamente."""
    tree = ast.parse(JUDGE.read_text(encoding="utf-8"))
    scrub_fn: ast.FunctionDef | None = None
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == "_scrub_for_judge":
            scrub_fn = node
            break
    assert scrub_fn is not None, "Falta helper _scrub_for_judge en judge.py."
    assert _calls_to(scrub_fn, "sanitize_payload"), "_scrub_for_judge debe llamar sanitize_payload internamente."

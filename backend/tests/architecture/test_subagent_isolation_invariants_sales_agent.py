"""Architectural fitness — preventive subagent isolation invariants para sales_agent.

Sales_agent NO usa subagents hoy (StateGraph lineal qualifier → product_expert
→ closer → tool_executor; ver §2.3 ``00-vision-and-objectives.md``: "NO
subagents deepagents"). Pero el contrato preventivo del ratchet S6:

1. Si alguien introduce un subagente vía deepagents ``task`` tool, el archivo
   del orchestrator debe consultar ``policy_for`` antes de surface events del
   stream — mismo contrato que copilot post-2026-04-26.
2. ``REGISTERED_SUBAGENTS_RATCHET`` empieza vacío. Cualquier subagente nuevo
   debe sumarse acá + cobertura en un test de aislamiento dedicado.
3. Si el orchestrator consume ``astream_events(version="v2")`` (no lo hace
   hoy), el archivo emisor DEBE consultar ``policy_for(...)`` en el mismo
   módulo — sin esa salvaguarda los events de subagentes leak al historial.

# [SALES-AGENT-CALLBACK-HANDLER-S1] guard del modelo de stream isolation.
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CHAT_FILE = ROOT / "src" / "modules" / "sales_agent" / "application" / "orchestrator" / "chat.py"
GRAPH_FILE = ROOT / "src" / "modules" / "sales_agent" / "application" / "orchestrator" / "graph.py"


REGISTERED_SUBAGENTS_RATCHET: tuple[str, ...] = ()
"""Sales_agent NO registra subagentes deepagents. Lista vacía intencional.

Si en una fase futura se introduce uno (improbable per §2.3 del plan):

1. Agregarlo al registro del orchestrator (mirror del pattern copilot
   ``subagents/__init__.py``).
2. Agregar el nombre acá.
3. Crear un test de aislamiento que verifique que sus events nunca
   leak a ``acc.messages`` ni al text_block del usuario.
"""


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.is_file() else ""


def test_orchestrator_does_not_use_subagent_streaming_without_policy_for() -> None:
    """Si chat.py adopta ``astream_events(version="v2")``, debe consultar
    ``policy_for(...)`` para clasificar events parent/subagent.

    Hoy sales_agent usa ``agent_app.ainvoke`` (one-shot). Cualquier shift a
    streaming requiere el contrato copilot post-2026-04-26 — tokens y
    AIMessages de subagentes NO deben leak al historial del lead.
    """
    src = _read(CHAT_FILE)
    if "astream_events" not in src:
        # No streaming → invariant trivially OK.
        return
    assert "policy_for(" in src, (
        "chat.py introdujo astream_events pero no consume policy_for(...). "
        "Sin clasificación, los events de un subagente futuro leak al "
        "historial. Ver tests/architecture/test_subagent_isolation_invariants.py "
        "(copilot pattern)."
    )


def test_graph_does_not_introduce_implicit_subagents() -> None:
    """``graph.py`` no debe importar deepagents ``create_deep_agent`` ni
    declarar nodes vía ``task`` tool sin sumar a REGISTERED_SUBAGENTS_RATCHET.

    Sales_agent es StateGraph lineal — cualquier intento de envolver
    specialist en un deep agent rompe el playbook de cierre.
    """
    src = _read(GRAPH_FILE)
    assert "from deepagents" not in src, (
        "graph.py NO debe importar deepagents. §2.3 del redesign declara "
        "subagents fuera de scope; el StateGraph lineal es el valor."
    )
    assert "create_deep_agent" not in src, (
        "graph.py NO debe envolver specialists en deep agents. "
        "Specialists son nodos del StateGraph (ver application/agents/sales/nodes.py)."
    )


def test_registered_subagents_ratchet_is_empty() -> None:
    """Por diseño la lista está vacía. Si alguien la pobla sin actualizar
    los tests de aislamiento dedicados, este invariante alerta."""
    if not REGISTERED_SUBAGENTS_RATCHET:
        # OK: sales_agent no tiene subagents.
        return

    # Si se pobló (futuro): cada subagente DEBE tener archivo de test
    # de aislamiento dedicado mirror del pattern copilot.
    coverage_path = ROOT / "tests" / "modules" / "sales_agent" / "test_subagent_stream_isolation.py"
    assert coverage_path.is_file(), (
        f"REGISTERED_SUBAGENTS_RATCHET tiene entries ({REGISTERED_SUBAGENTS_RATCHET}) "
        f"pero falta {coverage_path.relative_to(ROOT)} — necesitás coverage por "
        "subagente (mirror tests/modules/copilot/test_subagent_stream_isolation.py)."
    )
    test_src = coverage_path.read_text(encoding="utf-8")
    missing = [name for name in REGISTERED_SUBAGENTS_RATCHET if name not in test_src]
    assert not missing, f"Subagentes sales sin cobertura en {coverage_path.name}: {missing}."

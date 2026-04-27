"""Architecture fitness: subagent stream isolation invariants.

Bloquea regresiones futuras en el contrato establecido en Layer 0-4 del
fix de duplicación de mensajes (2026-04-26):

1. ``_process_stream_event`` consulta ``policy_for`` para decidir si surface
   un event al user/historial. Sin eso, los events de subagentes leak al
   stream user-facing y al historial persistido.

2. ``_handle_tool_end`` extrae ``ToolMessage`` de ``Command(update={...})``
   — el shape que deepagents usa para devolver el resultado del sub-agente.
   Sin eso, ``tool_call(task)`` queda sin matching ``tool_message`` y
   LangGraph rompe en el siguiente turn al recargar historial.

3. Cada subagente registrado en ``subagents/__init__.py`` tiene cobertura
   de aislamiento en ``tests/modules/copilot/test_subagent_stream_isolation.py``.
   Pattern ratchet: el set crece, no se pone allowlist.
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CHAT_FILE = ROOT / "src" / "modules" / "copilot" / "application" / "orchestrator" / "chat.py"
ISOLATION_TEST_FILE = ROOT / "tests" / "modules" / "copilot" / "test_subagent_stream_isolation.py"
SUBAGENTS_INIT = ROOT / "src" / "modules" / "copilot" / "application" / "orchestrator" / "subagents" / "__init__.py"


def test_process_stream_event_uses_policy_for() -> None:
    """``_process_stream_event`` debe consultar ``policy_for`` antes de decidir.

    Sin esto regresa el bug de duplicación: events de sub-agentes llegan al
    text_block del user (tokens) y a ``acc.messages`` (AIMessage final
    duplicado del que ``deepagents`` ya devuelve como ToolMessage).
    """
    src = CHAT_FILE.read_text(encoding="utf-8")
    assert "policy_for(" in src, (
        "_process_stream_event debe llamar policy_for(event). "
        "Pre-fix: branchear directo por event['event'] dejaba leak de "
        "tokens y AIMessages de sub-agentes al stream user-facing."
    )
    assert "StreamPolicy.EMIT_TO_USER" in src, (
        "Falta el check explícito StreamPolicy.EMIT_TO_USER en "
        "on_chat_model_stream — la política debe gobernar la decisión."
    )
    assert "StreamPolicy.CAPTURE_HISTORY" in src, (
        "Falta el check explícito StreamPolicy.CAPTURE_HISTORY en "
        "on_chat_model_end — sin él se persisten AIMessages del sub-agente."
    )


def test_handle_tool_end_normalises_command_via_helper() -> None:
    """``_handle_tool_end`` debe usar ``_extract_tool_message`` (que sabe
    desempaquetar ``Command(update={"messages": [...]})``).

    Pre-fix el branch chequeaba sólo ``isinstance(ToolMessage|str)`` y
    descartaba silencioso el output del ``task`` tool (siempre Command).
    Resultado: tool_call sin tool_message en el historial → state inconsistente.
    """
    src = CHAT_FILE.read_text(encoding="utf-8")
    assert "_extract_tool_message" in src, (
        "_handle_tool_end debe delegar la normalización del output al helper "
        "_extract_tool_message (ToolMessage | str | Command)."
    )


REGISTERED_SUBAGENTS_RATCHET: tuple[str, ...] = (
    "audit_inspector",
    "url_analyzer",
    "data_query",
)
"""Lista esperada de subagentes registrados.

Crece sólo por adición. Si agregas un subagente nuevo:
1. Agregalo a ``subagents/__init__.py`` (export del SubAgent dict).
2. Agregalo aquí.
3. Agrega cobertura en ``test_subagent_stream_isolation.py`` (mínimo:
   un test que dispare un event ``on_chat_model_end`` con
   ``langgraph_path`` o ``langgraph_checkpoint_ns`` que mencione el
   subagente y assert NO append a ``acc.messages``).
"""


def test_registered_subagents_match_init_module() -> None:
    """Drift detection: si agregan un subagente al __init__ sin actualizar
    el ratchet, este test falla y obliga a documentar."""
    src = SUBAGENTS_INIT.read_text(encoding="utf-8")
    # __init__.py declara los SubAgents importados: AUDIT_INSPECTOR_SUBAGENT,
    # URL_ANALYZER_SUBAGENT, DATA_QUERY_SUBAGENT — todos terminan en _SUBAGENT.
    expected_constants = {f"{name.upper()}_SUBAGENT" for name in REGISTERED_SUBAGENTS_RATCHET}
    found = {c for c in expected_constants if c in src}
    assert found == expected_constants, (
        f"Drift en subagents/__init__.py. Esperado: {sorted(expected_constants)}. "
        f"Falta: {sorted(expected_constants - found)}. "
        "Si agregaste un SubAgent nuevo, sumalo a REGISTERED_SUBAGENTS_RATCHET "
        "y agrega su test de aislamiento."
    )


def test_each_registered_subagent_has_isolation_coverage() -> None:
    """Allowlist ratchet — cada subagente registrado DEBE aparecer en el
    test de aislamiento (nombre como string en el archivo)."""
    test_src = ISOLATION_TEST_FILE.read_text(encoding="utf-8")
    missing = [name for name in REGISTERED_SUBAGENTS_RATCHET if name not in test_src]
    assert not missing, (
        f"Subagentes sin cobertura en {ISOLATION_TEST_FILE.name}: {missing}. "
        "Agregar al menos una assertion que mencione el nombre del subagente "
        "(typically en TestSubagentCoverageInvariant.REGISTERED) o un "
        "fixture de event que lo cite en langgraph_path/checkpoint_ns."
    )

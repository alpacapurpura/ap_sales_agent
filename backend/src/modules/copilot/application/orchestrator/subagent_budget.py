"""Subagent execution budget enforcement.

Defensa genérica contra runaway en delegación a sub-agentes:

- parent que invoca múltiples ``task`` por turn (waste de output tokens
  + duplicación de contexto);
- subagente que loopea internamente (anidación + costo compounding);
- subagente que invoca task-de-task (deepagents soporta nesting,
  pero a este nivel del producto no tiene caso de uso).

Aplica a TODOS los subagentes registrados (``audit_inspector``,
``url_analyzer``, ``data_query``, futuros). El módulo está aislado
para que el wire-up con la library deepagents pueda evolucionar sin
tocar la política.

Layer 4 del fix subagent stream isolation (2026-04-26). El wire-up al
``task`` tool se mantiene fuera de este módulo: la política expone
funciones puras que el orquestador llama en su loop. Esto evita
acoplar el budget al detail interno de deepagents y mantiene el
módulo testeable sin levantar el grafo completo.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SubagentBudget:
    """Caps duros para una ejecución de turno.

    Defaults conservadores. Suben sólo con justificación en PR.
    """

    max_subagents_per_turn: int = 2
    """``task`` calls que el parent puede emitir en un mismo turno."""

    max_subagent_depth: int = 1
    """Niveles de anidación. 1 = sub-agente no puede invocar otro ``task``."""

    max_subagent_iterations: int = 6
    """Tool-loop interno del sub-agente. Evita prompt loops."""


DEFAULT_BUDGET = SubagentBudget()


class SubagentBudgetError(Exception):
    """Levantada cuando el parent o un sub-agente excede su budget.

    El handler en el ``task`` tool wrapper captura la excepción y la
    convierte en ``ToolMessage`` con un mensaje explicativo, así el
    modelo decide cómo seguir (típicamente: pedir disculpas + ofrecer
    una alternativa).
    """


def check_per_turn_calls(
    current_count: int,
    budget: SubagentBudget = DEFAULT_BUDGET,
) -> None:
    """Validar el cap ``max_subagents_per_turn``.

    Llamar ANTES de spawn del sub-agente. ``current_count`` es la
    cantidad actual de ``task`` calls ya iniciados (cero en el primer call).
    """
    if current_count >= budget.max_subagents_per_turn:
        msg = (
            f"Subagent calls per turn exceeded: {current_count} >= "
            f"{budget.max_subagents_per_turn}. Consolida la solicitud en "
            "una sola invocación o continúa con tools del parent."
        )
        raise SubagentBudgetError(msg)


def check_depth(
    current_depth: int,
    budget: SubagentBudget = DEFAULT_BUDGET,
) -> None:
    """Validar el cap ``max_subagent_depth``.

    Un sub-agente que está corriendo dentro de un ``task`` ya tiene
    depth=1. Si ese sub-agente intenta invocar otro ``task``,
    ``current_depth`` sería 1 al invocar y dispararía el cap (1 >= 1).
    """
    if current_depth >= budget.max_subagent_depth:
        msg = (
            f"Subagent nesting depth exceeded: {current_depth} >= "
            f"{budget.max_subagent_depth}. Sub-agentes no pueden invocar "
            "otros sub-agentes en este producto — devuelve un reporte y "
            "deja que el parent decida el siguiente paso."
        )
        raise SubagentBudgetError(msg)


def check_iterations(
    current_iterations: int,
    budget: SubagentBudget = DEFAULT_BUDGET,
) -> None:
    """Validar el cap ``max_subagent_iterations``.

    Defensa contra prompt loops (sub-agente que sigue invocando tools
    sin converger a una respuesta final).
    """
    if current_iterations >= budget.max_subagent_iterations:
        msg = (
            f"Subagent tool-loop iterations exceeded: {current_iterations} "
            f">= {budget.max_subagent_iterations}. Termina con el resumen "
            "parcial que tienes — no sigas invocando tools."
        )
        raise SubagentBudgetError(msg)


__all__ = [
    "DEFAULT_BUDGET",
    "SubagentBudget",
    "SubagentBudgetError",
    "check_depth",
    "check_iterations",
    "check_per_turn_calls",
]

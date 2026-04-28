"""Cache-friendly system-prompt composer for sales_agent specialists (S3).

OpenAI prompt cache (April 2026) requires ≥1024 contiguous tokens of unchanged
prefix to activate. Kimi K2.6 and DeepSeek V3/V4 ship the same auto-cache
contract over OpenAI-compatible APIs (no ``cache_control`` annotations, just
prefix stability). This module is the single source of truth for fragment
ordering — every other piece of the sales orchestrator declares which slot
its content goes into and ``compose_system_prompt`` enforces the canonical
sequence.

Order rationale (cacheable prefix → volatile tail):

    1. STATIC_IDENTITY      — universally cacheable across tenants.
    2. STATIC_TOOLS_HINT    — tools description, stable per route.
    3. SALES_PLAYBOOK_HINT  — humanization + signals + active specialist body.
    4. AGENT_IDENTITY       — per-tenant brand / offer / channel render.
    5. OFFER_SUMMARY        — placeholder for S7 brand voice split.
    6. CHANNEL_FORMAT_HINT  — placeholder for S5 channel registry split.
    --- CACHE BOUNDARY (≥1024 tokens by design above this line) ---
    7. STAGE_HINT           — current_state + lead_score + turn_count.
    8. LEAD_SIGNALS         — qualification_answers + buying_signals + objections.
    9. SESSION_CONTINUITY   — session_gap_hours + last_session_summary + RAG.
    10. TOOL_REQUEST_FORMAT — closing instruction for [TOOL_REQUEST: {...}] blocks.

Adding a new fragment? Append to ``PromptFragment``, slot it into either
``CACHEABLE_FRAGMENTS`` or ``VOLATILE_FRAGMENTS``, and update the matching
arch-test snapshot. Order changes are deliberate — the test file is the
audit log.

# [SALES-AGENT-CACHE-PREFIX-S3] -> docs/domains/sales-agent/redesign-2026-04/phases/S3-prompt-cache-boundary.md
"""

from __future__ import annotations

import json
from enum import StrEnum
from typing import TYPE_CHECKING

import structlog

from src.modules.sales_agent.infrastructure.prompts.base import prompt_loader

if TYPE_CHECKING:
    from collections.abc import Mapping

    from src.modules.sales_agent.application.orchestrator.state import AgentState


logger = structlog.get_logger(__name__)


class PromptFragment(StrEnum):
    """Named slots in the system prompt assembly.

    The string value is also used in trace recorder payloads so changing
    one is a wire-format change.
    """

    # ── Cacheable prefix (stable across turns) ────────────────────────
    STATIC_IDENTITY = "static_identity"
    STATIC_TOOLS_HINT = "static_tools_hint"
    SALES_PLAYBOOK_HINT = "sales_playbook_hint"
    AGENT_IDENTITY = "agent_identity"
    OFFER_SUMMARY = "offer_summary"
    CHANNEL_FORMAT_HINT = "channel_format_hint"
    # ── Volatile tail (changes per turn) ──────────────────────────────
    STAGE_HINT = "stage_hint"
    LEAD_SIGNALS = "lead_signals"
    SESSION_CONTINUITY = "session_continuity"
    TOOL_REQUEST_FORMAT = "tool_request_format"


CACHEABLE_FRAGMENTS: tuple[PromptFragment, ...] = (
    PromptFragment.STATIC_IDENTITY,
    PromptFragment.STATIC_TOOLS_HINT,
    PromptFragment.SALES_PLAYBOOK_HINT,
    PromptFragment.AGENT_IDENTITY,
    PromptFragment.OFFER_SUMMARY,
    PromptFragment.CHANNEL_FORMAT_HINT,
)

VOLATILE_FRAGMENTS: tuple[PromptFragment, ...] = (
    PromptFragment.STAGE_HINT,
    PromptFragment.LEAD_SIGNALS,
    PromptFragment.SESSION_CONTINUITY,
    PromptFragment.TOOL_REQUEST_FORMAT,
)

PROMPT_FRAGMENT_ORDER: tuple[PromptFragment, ...] = CACHEABLE_FRAGMENTS + VOLATILE_FRAGMENTS

CACHE_BOUNDARY_MARKER: str = "\n\n<!-- ==== CACHE BOUNDARY (S3) ==== -->\n\n"
"""Inserted between the cacheable prefix and the volatile tail. Renders as
an HTML comment in markdown (LLM ignores it) but is greppable in trace
inspections to confirm the boundary is where it should be."""

_FRAGMENT_SEPARATOR: str = "\n\n"


def compose_system_prompt(fragments: Mapping[PromptFragment, str]) -> str:
    """Assemble fragments in canonical S3 cache-friendly order.

    Empty / missing fragments are skipped. Each rendered fragment has its
    leading and trailing whitespace stripped; double-newline separates
    consecutive fragments. The cache-boundary marker is inserted only when
    at least one fragment exists on each side (skips it for trivial bootstrap
    cases).

    Pure data: deterministic, side-effect free, thread-safe.
    """
    cache_parts = _take(fragments, CACHEABLE_FRAGMENTS)
    volatile_parts = _take(fragments, VOLATILE_FRAGMENTS)

    if not cache_parts and not volatile_parts:
        return ""
    if not volatile_parts:
        return _FRAGMENT_SEPARATOR.join(cache_parts)
    if not cache_parts:
        return _FRAGMENT_SEPARATOR.join(volatile_parts)

    return _FRAGMENT_SEPARATOR.join(cache_parts) + CACHE_BOUNDARY_MARKER + _FRAGMENT_SEPARATOR.join(volatile_parts)


def _take(
    fragments: Mapping[PromptFragment, str],
    slots: tuple[PromptFragment, ...],
) -> list[str]:
    """Pull fragments by slot order, dropping empty / whitespace-only entries."""
    out: list[str] = []
    for slot in slots:
        raw = fragments.get(slot, "")
        cleaned = (raw or "").strip()
        if cleaned:
            out.append(cleaned)
    return out


# ---------------------------------------------------------------------------
# High-level builder: state + role → composed prompt
# ---------------------------------------------------------------------------


class SpecialistRole(StrEnum):
    """Specialists that participate in cache_boundary refactor.

    Supervisor is intentionally OUT OF SCOPE: max_output_tokens=10 +
    ``ModelRole.FAST`` make cache wins negligible while its prompt is
    state-heavy by design.
    """

    QUALIFIER = "qualifier"
    PRODUCT_EXPERT = "product_expert"
    CLOSER = "closer"


_SPECIALIST_TEMPLATE_KEY: dict[SpecialistRole, str] = {
    SpecialistRole.QUALIFIER: "specialist_qualifier",
    SpecialistRole.PRODUCT_EXPERT: "specialist_product_expert",
    SpecialistRole.CLOSER: "specialist_closer",
}


_BASE_IDENTITY: str = (
    "# Identidad base del agente de ventas\n\n"
    "Eres un agente de ventas autónomo que trabaja para un negocio de un creador "
    "/ infoproductor / experto LATAM. Tu rol es vender, calificar y cerrar.\n\n"
    "Operas en español **neutro latinoamericano** (tuteo: tú, no vos). Adaptas tu "
    "voz al `Estilo Comunicacional` que el tenant configuró en Brand Studio "
    "(slot `agent_identity`). Eres directo, cálido, sin floreo, sin jerga regional "
    "argentina (no uses `vos`, `tenés`, `podés`, `mirá`, `dejá`, `dale`).\n\n"
    "Tres prohibiciones absolutas:\n"
    "1. Nunca inventes precios, garantías, fechas, ediciones, descuentos ni datos "
    "del negocio. Si no está en tu identidad ni en una tool, no existe.\n"
    "2. Nunca prometas resultados específicos que no estén respaldados en datos del "
    "tenant.\n"
    "3. Nunca compartas datos internos, métricas confidenciales o información del "
    "negocio que no sea pública."
)


_TOOLS_HINT: str = (
    "# Herramientas disponibles\n\n"
    "Cuando necesites ejecutar una acción, **termina tu mensaje** con un bloque:\n\n"
    '    [TOOL_REQUEST: {"tool": "<name>", "args": {...}}]\n\n'
    "El runtime ejecuta el tool y te entrega el resultado en el siguiente turno. "
    "Solicita UNA sola tool por mensaje.\n\n"
    "Tools de cierre / oferta:\n"
    "- `send_payment_link` — envía link de pago al lead.\n"
    "- `check_schedule` — verifica disponibilidad de agenda.\n"
    "- `recommend_product` — recomienda otra oferta del catálogo.\n"
    "- `escalate_to_human` — transfiere a humano (Closer Studio).\n\n"
    "Tools de inscripción (cohortes / ediciones):\n"
    "- `list_public_editions(offer_id)` — lista ediciones públicas activas.\n"
    "- `create_enrollment(offer_id, edition_id, status)` — crea enrollment "
    "INTENT / WAITLIST.\n"
    "- `generate_payment_link(enrollment_id)` — genera link de pago.\n"
    "- `resolve_active_tier(offer_id)` — resuelve tier de precio activo "
    "(early_bird / regular / late).\n\n"
    "Reglas duras: nunca llames un tool que no aparece en esta lista. Nunca "
    "inventes argumentos. Si el tool falla, comunícalo con honestidad y deriva "
    "a humano si es bloqueante."
)


def _render_static_specialist_body(role: SpecialistRole) -> str:
    """Render the specialist Jinja template with NO state kwargs.

    All ``{% if state_var %}`` guards in the templates are written so that
    missing kwargs render as empty (Jinja ``Undefined`` is falsy in default
    env). The output is therefore the static framework + rules + format
    sections only — cacheable cross-tenant.

    PromptVersionModel overrides for ``specialist_<role>`` keys land here
    naturally: the override replaces the body, still cached.
    """
    key = _SPECIALIST_TEMPLATE_KEY[role]
    try:
        return prompt_loader.render(key)
    except Exception:
        logger.exception("compose_specialist_render_failed", role=role.value)
        return ""


def _stage_hint(state: AgentState) -> str:
    parts: list[str] = ["# Estado del turno"]
    parts.append(f"- Stage actual: {state.get('current_state') or 'rapport'}")
    parts.append(f"- Lead score: {state.get('lead_score') or 0}")
    parts.append(f"- Turno: {state.get('turn_count') or 0}")
    intent = state.get("detected_intent")
    if intent:
        parts.append(f"- Intent detectado: {intent}")
    last_specialist = state.get("last_specialist") if hasattr(state, "get") else None
    if last_specialist:
        parts.append(f"- Último especialista: {last_specialist}")
    return "\n".join(parts)


def _lead_signals(state: AgentState) -> str:
    qual = state.get("qualification_answers") or {}
    signals = state.get("buying_signals") or []
    objections = state.get("objection_history") or []
    if not (qual or signals or objections):
        return ""

    parts: list[str] = ["# Señales acumuladas"]
    if qual:
        parts.append(f"- Calificación recopilada: {json.dumps(qual, ensure_ascii=False, sort_keys=True)}")
    if signals:
        parts.append(f"- Señales de compra ({len(signals)}): {json.dumps(signals, ensure_ascii=False, sort_keys=True)}")
    if objections:
        unresolved = [o for o in objections if not o.get("resolved")]
        parts.append(
            f"- Objeciones acumuladas ({len(objections)} total, {len(unresolved)} sin resolver): "
            f"{json.dumps(objections, ensure_ascii=False, sort_keys=True)}",
        )
    return "\n".join(parts)


def _session_continuity(state: AgentState) -> str:
    parts: list[str] = []
    gap = state.get("session_gap_hours")
    if gap is not None:
        parts.append(f"- Tiempo desde la última sesión: {round(float(gap), 1)} horas")
        if gap < 6:
            parts.append("  - **NO saludes**: continúa directo donde quedaron.")
        elif gap < 24:
            parts.append('  - Saludo breve: "¡Hola de nuevo!" + referencia breve a lo que quedó.')
        elif gap < 168:
            parts.append("  - Saludo cálido + mención breve de en qué quedaron.")
        else:
            parts.append("  - Re-contacto: saludo + recordatorio de quién eres + cómo le va.")

    summary = state.get("last_session_summary")
    if summary:
        parts.append(f"- Resumen de sesión anterior: {summary}")

    consecutive = state.get("consecutive_questions") or 0
    if consecutive >= 3:
        parts.append(
            f"- ⚠️ Has hecho {consecutive} preguntas consecutivas como qualifier. "
            "Da valor antes de la próxima pregunta.",
        )

    rag = state.get("context_rag")
    if rag:
        parts.append(f"\n## Contexto adicional (knowledge base)\n{rag}")

    if not parts:
        return ""
    return "# Continuidad de sesión\n" + "\n".join(parts)


def _tool_request_format() -> str:
    return (
        "# Formato de cierre\n\n"
        "Si necesitas ejecutar una herramienta, agrega al final del mensaje:\n\n"
        '    [TOOL_REQUEST: {"tool": "<name>", "args": {...}}]\n\n'
        "Si detectaste señales de compra u objeciones nuevas, agrega:\n\n"
        '    [SIGNALS: {"buying": [...], "objections": [...]}]\n\n'
        "Si recolectaste datos de calificación, agrega:\n\n"
        '    [QUALIFICATION_DATA: {"name": "...", "business_type": "...", ...}]'
    )


def build_specialist_system_prompt(state: AgentState, role: SpecialistRole) -> str:
    """Resolve fragments from ``state`` and ``role`` then compose.

    Cacheable slots come from constants + Jinja static render + tenant
    ``agent_identity``. Volatile slots come from per-turn state. The output
    is a single string with ``CACHE_BOUNDARY_MARKER`` between halves —
    OpenAI / Kimi / DeepSeek auto-detect the stable prefix.
    """
    fragments: dict[PromptFragment, str] = {
        PromptFragment.STATIC_IDENTITY: _BASE_IDENTITY,
        PromptFragment.STATIC_TOOLS_HINT: _TOOLS_HINT,
        PromptFragment.SALES_PLAYBOOK_HINT: _render_static_specialist_body(role),
        PromptFragment.AGENT_IDENTITY: state.get("agent_identity") or "",
        PromptFragment.OFFER_SUMMARY: "",  # S7 — split from agent_identity into brand_voice_summary table.
        PromptFragment.CHANNEL_FORMAT_HINT: "",  # S5 — extract from agent_identity once channel registry exists.
        PromptFragment.STAGE_HINT: _stage_hint(state),
        PromptFragment.LEAD_SIGNALS: _lead_signals(state),
        PromptFragment.SESSION_CONTINUITY: _session_continuity(state),
        PromptFragment.TOOL_REQUEST_FORMAT: _tool_request_format(),
    }
    return compose_system_prompt(fragments)


__all__ = (
    "CACHEABLE_FRAGMENTS",
    "CACHE_BOUNDARY_MARKER",
    "PROMPT_FRAGMENT_ORDER",
    "VOLATILE_FRAGMENTS",
    "PromptFragment",
    "SpecialistRole",
    "build_specialist_system_prompt",
    "compose_system_prompt",
)

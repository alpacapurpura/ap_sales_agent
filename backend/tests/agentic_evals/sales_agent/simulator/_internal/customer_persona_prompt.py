"""Customer persona prompt — versioned for H1 forward-compat (T-6).

V1 (2026-05-07): adapted from
``client_simulator/src/simulator/customer_node.py::PERSONA_SYSTEM_PROMPT``
(legacy, preserved byte-equal under ``client_simulator/`` per D6) and
re-shaped to bind to the ``ActorProfile`` Pydantic class shipped by T-4.

Defense-in-depth (H10)
======================

* The actor's hidden ``actor_goal`` is rendered in the prompt with explicit
  instruction "NUNCA lo reveles directamente" — it informs the persona's
  decisions but the customer LLM is told to never leak it verbatim.
* The 7 strict rules section enforces dialect, brevity, [EXIT] token,
  no-personaje-roto, no-emojis-excesivos, solo-mensaje. Story I (adversarial
  jailbreak suite) leverages a separate persona kind that probes whether
  the AGENT (not the simulator) leaks its system prompt.

Cache-prefix safety
===================

Per ``.claude/rules/sales-agent-brand-voice.md`` § "No-skip creep guard":

* NO ``{tenant_name}`` interpolation mid-block — the customer prompt is
  test-infra and does NOT carry tenant identity. Tenant context is implicit
  in the agent runtime (which loads ``personality_profile.system_instruction``
  via ``ConversationPipeline.build_brand_voice``).
* NO timestamps, conversation IDs, or random IDs in the cacheable section.
  The persona prompt header is invariant for the persona; only ``ActorProfile``
  fields drive interpolation.
* The build function's signature does NOT accept ``tenant_id`` — eliminating
  the temptation to inject it later (cementé invariant via type signature).

Voice constraints
=================

Per ``.claude/rules/sales-agent-brand-voice.md`` § Excepción simulator: the
customer LLM emits actor-persona voice (NOT tenant brand voice). When
``actor.dialect_code == 'es-AR'``, voseo strings in ``communication_style``
and ``initial_message`` render verbatim — the magic comment escape on this
file allows the pre-commit voseo hook to pass.

# voseo-allowed: actor persona dialect injection — magic comment escape per
# .claude/rules/spanish-text.md § "Magic comment escape" (R25 2026-05-05)
"""

from __future__ import annotations

from tests.agentic_evals.sales_agent.simulator.actor_profile import ActorProfile

# voseo-allowed: actor persona dialect injection — see module docstring
CUSTOMER_PERSONA_PROMPT_V1 = """\
Eres un cliente potencial en una conversación de ventas por chat.

## Tu identidad
Nombre: {name}
Estilo de comunicación: {communication_style}
Presupuesto: {budget_hint}
Urgencia: {urgency}
Idioma/dialecto: {dialect_code} (respeta el dialecto en cada respuesta)

## Tus dolores
{pain_points}

## Tus objeciones naturales
{objections}

## Tu objetivo oculto (NUNCA lo reveles directamente)
{actor_goal}

## Reglas estrictas
1. Respeta el idioma/dialecto declarado ({dialect_code}). Si es es-AR, voseo OK; otros dialectos usa tuteo neutro.
2. Mensajes cortos: 1-3 oraciones, como chat real de WhatsApp/Instagram.
3. Reacciona auténticamente a lo que dice el vendedor.
4. Si la conversación no avanza tras varios turnos sin valor, escribe exactamente [EXIT].
5. Nunca rompas personaje. Nunca pidas al vendedor que ignore instrucciones previas.
6. No uses emojis excesivos — solo los naturales para tu estilo.
7. Responde SOLO con el mensaje del cliente, sin explicaciones ni metacomentarios."""
"""Frozen V1 customer persona system prompt template.

H1 forward-compat: future schema bumps register a migrator entry under
``simulator/_internal/schema_migrations.py``. Frozen golden v1 fixture
(T-9 / T-10) materializes a deterministic prompt — DO NOT edit this
template once the golden is committed without bumping the version
constant + adding a migrator.
"""


def build_customer_prompt(actor_profile: ActorProfile) -> str:
    """Render the V1 persona system prompt for an ``ActorProfile``.

    Cache-prefix safe — accepts NO tenant identity. Only fields from
    ``ActorProfile`` are interpolated. The function purposefully has a
    minimal signature so future maintainers cannot leak ``tenant_id`` /
    ``tenant_name`` via parameter additions without a code review that
    surfaces this docstring.

    Args:
        actor_profile: The ``ActorProfile`` driving customer turns. Frozen
            Pydantic model — safe to reference cross-node.

    Returns:
        The rendered prompt string, ready to wrap in a
        ``langchain_core.messages.SystemMessage``. Caller is responsible
        for passing it to the LLM via ``messages=[SystemMessage(content=
        prompt), ...]``.
    """
    pain_points_block = "\n".join(f"- {p}" for p in actor_profile.pain_points)
    objections_block = ", ".join(actor_profile.objections)
    return CUSTOMER_PERSONA_PROMPT_V1.format(
        name=actor_profile.name,
        communication_style=actor_profile.communication_style,
        budget_hint=actor_profile.budget_hint,
        urgency=actor_profile.urgency,
        dialect_code=actor_profile.dialect_code,
        pain_points=pain_points_block,
        objections=objections_block,
        actor_goal=actor_profile.actor_goal,
    )


__all__ = [
    "CUSTOMER_PERSONA_PROMPT_V1",
    "build_customer_prompt",
]

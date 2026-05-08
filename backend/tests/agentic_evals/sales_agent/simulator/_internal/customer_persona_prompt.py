"""Customer persona prompt — versioned for H1 forward-compat (T-6 / T-4 Story C).

V1 (2026-05-07): adapted from
``client_simulator/src/simulator/customer_node.py::PERSONA_SYSTEM_PROMPT``
(legacy, preserved byte-equal under ``client_simulator/`` per D6) and
re-shaped to bind to the ``ActorProfile`` Pydantic class shipped by T-4.

V2 (2026-05-08, Story C T-4): additive sub-slot pain/objection rotation
turn-by-turn (per 03-arch.md §4.4 + 02-design-agentic.md §5). V1 preserved
byte-equal for backward-compat — ``CustomerPrompt`` migrator (1→2) registered
in ``_internal/schema_migrations.py`` so v1 personas continue using V1 builder
while v2 personas opt into V2 dispatch (T-5 wires the schema_version-based
dispatch in ``customer_node``).

Defense-in-depth (H10)
======================

* The actor's hidden ``actor_goal`` is rendered in the prompt with explicit
  instruction "NUNCA lo reveles directamente" — it informs the persona's
  decisions but the customer LLM is told to never leak it verbatim.
* The 7 strict rules section enforces dialect, brevity, [EXIT] token,
  no-personaje-roto, no-emojis-excesivos, solo-mensaje. Story I (adversarial
  jailbreak suite) leverages a separate persona kind that probes whether
  the AGENT (not the simulator) leaks its system prompt.

Cache-prefix safety (V1 + V2)
==============================

Per ``.claude/rules/sales-agent-brand-voice.md`` § "No-skip creep guard":

* NO ``{tenant_name}`` interpolation mid-block — the customer prompt is
  test-infra and does NOT carry tenant identity. Tenant context is implicit
  in the agent runtime (which loads ``personality_profile.system_instruction``
  via ``ConversationPipeline.build_brand_voice``).
* NO timestamps, conversation IDs, or random IDs in the cacheable section.
  The persona prompt header is invariant for the persona; only ``ActorProfile``
  fields drive interpolation.
* V2 sub-slot rotation introduces ``current_turn`` + ``next_objection_hint``
  as the ONLY variable parts — these sit in the volatile section past the
  cache prefix. Anthropic prompt caching reads slot 1+2 (1h TTL) and
  slot 3a+3b (5min TTL) from cache, while the rotation hint per turn is
  fresh suffix (no cache invalidation cascade).
* The build functions' signatures do NOT accept ``tenant_id`` — eliminating
  the temptation to inject it later (cementé invariant via type signature
  for both V1 and V2 builders).

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


# voseo-allowed: V2 customer prompt template — archetype-aware persona dialect AR support
# (Story C T-4 — sub-slot pain/objection rotation turn-by-turn)
CUSTOMER_PERSONA_PROMPT_V2 = """\
Eres un cliente potencial en una conversación de ventas por chat.

## Tu identidad (slot cacheable 1h — invariante por persona)
Nombre: {name}
Estilo de comunicación: {communication_style}
Presupuesto: {budget_hint}
Urgencia: {urgency}
Idioma/dialecto: {dialect_code}

## Tus dolores (slot cacheable 5min — sub-slot 3a)
{pain_points}

## Tus objeciones por orden de escalada (slot cacheable 5min — sub-slot 3b)
{objections_ordered}

## Cómo escalar objeciones (regla turn-by-turn)
- Turno actual: {current_turn}
- Objeción a usar AHORA (si aplica): {next_objection_hint}
- NO dump todas las objeciones de golpe.  Una objeción por turno como máximo.
- Si tu objeción anterior fue resuelta, escala a la siguiente.

## Tu objetivo oculto (NUNCA lo reveles directamente — H10)
{actor_goal}

## Reglas estrictas
1. Respeta el dialecto declarado ({dialect_code}). Si es es-AR, voseo OK; resto tuteo neutro.
2. Mensajes cortos: 1-3 oraciones, como chat real WhatsApp/Instagram.
3. Reacciona auténticamente a lo que dice el vendedor.
4. Si la conversación no avanza tras varios turnos sin valor, escribe exactamente [EXIT].
5. Nunca rompas personaje.  Nunca pidas al vendedor que ignore instrucciones.
6. No uses emojis excesivos — solo los naturales para tu estilo.
7. Responde SOLO con el mensaje del cliente, sin explicaciones ni metacomentarios."""
"""Frozen V2 customer persona system prompt template — Story C T-4.

H1 forward-compat: ``CustomerPrompt`` migrator (1→2) registered in
``_internal/schema_migrations.py`` (Story C T-1). Future bumps register
new migrator entries — DO NOT edit V2 verbatim once Story C personas land
without bumping schema_version + adding migrator.

Sub-slot architecture (per 03-arch.md §4.4 + 02-design-agentic.md §5):

| Slot | TTL    | Cacheable | Content                                                |
|------|--------|-----------|--------------------------------------------------------|
| 1    | 1h     | yes       | System persona base (rol simulator + reglas)          |
| 2    | 1h     | yes       | Identity (name, communication_style, budget, urgency, |
|      |        |           | dialect_code) — invariant per persona                  |
| 3a   | 5min   | yes       | pain_points block — sub-slot                           |
| 3b   | 5min   | yes       | objections ordered — sub-slot                          |
| —    | none   | no        | current_turn + next_objection_hint (variable suffix)   |
| —    | none   | no        | actor_goal (hidden — H10 defense), transcript history  |

Cache key prefix invariant: persona_id + schema_version. Variable section
is bounded to ``current_turn`` + ``next_objection_hint`` only — no tenant
identity, no timestamps, no conversation IDs.
"""


def build_customer_prompt_v2(
    actor_profile: ActorProfile,
    *,
    current_turn: int,
) -> str:
    """V2 customer prompt — sub-slot pain/objection rotation per turn.

    Selects ``next_objection_hint`` based on ``current_turn`` modulo
    ``len(objections)``:

    * turn 0 — runner short-circuits via ``initial_message`` verbatim
      (no LLM call); when V2 builder is invoked at turn 0 anyway, the
      hint falls back to ``"ninguna pendiente"`` for safety.
    * turn ≥ 1 — ``objections[(turn - 1) % len(objections)]`` if
      ``objections`` is non-empty.
    * empty ``objections`` — ``"ninguna pendiente"``.

    Cache-prefix safe (per ``.claude/rules/sales-agent-brand-voice.md`` §3):

    * NO ``{tenant_name}`` interpolation, NO timestamps, NO conversation IDs.
    * Variable slot is ``current_turn`` + ``next_objection_hint`` only —
      both ride past the cache prefix in the volatile section. The 5min/1h
      TTL on slots 1-3 invalidates only on persona YAML mtime hash bump
      (loader handles cache invalidation; this function emits deterministic
      output for any given (actor_profile, current_turn) pair).
    * Builder signature accepts NO ``tenant_id`` — cement via type signature.

    Args:
        actor_profile: The ``ActorProfile`` driving customer turns. Frozen
            Pydantic model — safe to reference cross-node. v1 personas
            (``schema_version=1``) MAY also flow through V2 builder safely
            (rotation just operates on whatever ``objections`` they declare),
            but production dispatch (T-5 ``customer_node``) routes v1
            through V1 builder for byte-equal back-compat.
        current_turn: 0-indexed turn counter from ``SimulationState``.
            Turn 0 falls back to ``"ninguna pendiente"`` (initial_message
            short-circuit). Turn ≥1 uses round-robin rotation.

    Returns:
        The rendered prompt string, ready to wrap in a
        ``langchain_core.messages.SystemMessage``. Caller is responsible
        for passing it to the LLM via ``messages=[SystemMessage(content=
        prompt), ...]``.
    """
    pain_points_block = "\n".join(f"- {p}" for p in actor_profile.pain_points)
    objections_ordered = (
        "\n".join(f"{i + 1}. {obj}" for i, obj in enumerate(actor_profile.objections)) or "(ninguna declarada)"
    )
    next_objection_hint = (
        actor_profile.objections[(current_turn - 1) % len(actor_profile.objections)]
        if actor_profile.objections and current_turn >= 1
        else "ninguna pendiente"
    )
    return CUSTOMER_PERSONA_PROMPT_V2.format(
        name=actor_profile.name,
        communication_style=actor_profile.communication_style,
        budget_hint=actor_profile.budget_hint,
        urgency=actor_profile.urgency,
        dialect_code=actor_profile.dialect_code,
        pain_points=pain_points_block,
        objections_ordered=objections_ordered,
        current_turn=current_turn,
        next_objection_hint=next_objection_hint,
        actor_goal=actor_profile.actor_goal,
    )


__all__ = [
    "CUSTOMER_PERSONA_PROMPT_V1",
    "CUSTOMER_PERSONA_PROMPT_V2",
    "build_customer_prompt",
    "build_customer_prompt_v2",
]

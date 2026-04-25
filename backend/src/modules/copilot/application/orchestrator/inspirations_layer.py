"""F4 — Inspirations system-prompt layer.

Renders the "## Inspiraciones cargadas" table the LLM sees between the
brand lighthouse (F3) and the volatile completion snapshot. State-aware
rather than ContextInjector-aware because inspirations live per
*conversation*, and ``ContextInjector.inject_for(target_route, tenant_id)``
intentionally has no conversation handle (the port is wider than this
feature).

Order rationale (matches F3 cacheable prefix invariant):

    [lighthouse — stable per tenant]
    [inspirations — stable while the inspirations set is unchanged]
    [completion snapshot / behavior / guided / studio — volatile]
    [deep-agent suffix — stable boilerplate]

If the inspirations set itself changes (new fetch, FIFO eviction) the
prefix invalidates from this layer onward, but the lighthouse above
still hits the Anthropic prompt cache. We deliberately omit relative
timestamps ("hace 5 min") so the formatted block stays byte-stable
between consecutive turns when the underlying rows haven't changed.

# [COPILOT-INSPIRATION-F4] -> docs/domains/copilot/redesign-2026-04/phases/F4-url-contextual-scratchpad.md
"""

from __future__ import annotations

from uuid import UUID

import structlog

from src.modules.copilot.application.tools.fetch_url import (
    ACTIVE_INSPIRATIONS_CAP,
)

logger = structlog.get_logger()


_HEADER = "## Inspiraciones cargadas"
_HINT = (
    "Tienes el resumen + sub-elementos en `/inspirations/{slug}.md`. "
    "Cuando el usuario diga 'rescatá X de Y', `task('url_analyzer', ...)` "
    "o referenciá el slug directamente."
)


def _render_row(
    *,
    slug: str,
    domain: str,
    why: str,
    score: float,
) -> str:
    """Render a single inspiration row in the system-prompt table."""
    why_clean = (why or "").strip().replace("\n", " ")
    if not why_clean:
        why_clean = "(sin razón explícita)"
    return f"- `{slug}` · {domain} · {why_clean} · relevance {score:.2f}"


def build_inspirations_layer(state: dict) -> str:
    """Return the inspirations table fragment for ``state`` or ``""``.

    Args:
        state: The full :class:`CopilotState` mapping. We need
            ``tenant_id`` (UUID) + ``conversation_id`` (str/UUID) to
            scope the query. Missing either one → empty fragment.

    Returns:
        A short markdown block with the active inspirations, or ``""``
        when there are none / the lookup fails. Caller (the system
        prompt builder) treats ``""`` as "skip".

    Resilience: any DB exception is logged and swallowed — the user's
    chat must never fail just because the inspirations cache is broken.
    """
    tenant_id = state.get("tenant_id")
    conversation_id_raw = state.get("conversation_id")
    if not isinstance(tenant_id, UUID) or not conversation_id_raw:
        return ""

    try:
        conversation_id = (
            conversation_id_raw if isinstance(conversation_id_raw, UUID) else UUID(str(conversation_id_raw))
        )
    except (TypeError, ValueError):
        return ""

    try:
        from src.core.database import SessionLocal
        from src.modules.copilot.infrastructure.repositories.inspiration_repository import (
            CopilotInspirationRepository,
        )

        db = SessionLocal()
        try:
            rows = CopilotInspirationRepository(db).list_active_for_conversation(
                tenant_id=tenant_id,
                conversation_id=conversation_id,
                limit=ACTIVE_INSPIRATIONS_CAP,
            )
        finally:
            db.close()
    except Exception:
        logger.exception(
            "inspirations_layer_load_failed",
            tenant_id=str(tenant_id),
            conversation_id=str(conversation_id),
        )
        return ""

    if not rows:
        return ""

    body = "\n".join(
        _render_row(
            slug=row.slug,
            domain=row.domain,
            why=row.why,
            score=float(row.brand_relevance_score),
        )
        for row in rows
    )
    return f"{_HEADER}\n{body}\n\n{_HINT}\n"


__all__ = ["build_inspirations_layer"]

"""F4 — ``fetch_url`` transversal tool.

Lets the user paste any public URL as inspiration. The tool:

1. Validates + canonicalizes the URL (strips query/fragment, blocks
   private hosts).
2. Enforces a per-conversation rate limit (max 10 inspirations).
3. Fetches HTML via httpx + extracts markdown via trafilatura.
4. Loads the tenant's brand lighthouse to feed the analyzer.
5. Calls the LLM analyzer (FAST tier) → summary, sub-elements,
   ``brand_relevance_score``, slug.
6. UPSERTs a row in ``copilot_inspiration`` (per-conversation key).
7. Trims FIFO so at most 5 active inspirations remain (older ones are
   evicted from the system-prompt fragment but still queryable until
   the cap is hit again — actually they're hard-deleted to keep the
   table small).

Returns ``llm_content`` so the LLM only sees the small preview, never
the raw markdown — context budget protection per F2 design.

# [COPILOT-FETCH-URL-F4] -> docs/domains/copilot/redesign-2026-04/phases/F4-url-contextual-scratchpad.md
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING
from uuid import UUID

import structlog
from langchain_core.tools import tool
from luana_core_copilot.application.tools.url_inspiration_analyzer import (
    InspirationAnalysis,
    analyze,
)
from luana_core_copilot.infrastructure.web.trafilatura_client import (
    FetchUrlError,
    WebExtractResult,
    fetch_extract,
)
from luana_core_platform.core.context import get_conversation_id, get_tenant_id

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

logger = structlog.get_logger()


# Hard caps keep abuse + cost predictable. F4 §7 mandates these values.
MAX_INSPIRATIONS_PER_CONVERSATION = 10
ACTIVE_INSPIRATIONS_CAP = 5


def _err_payload(message: str, **extra: object) -> str:
    """Shape an error payload mirroring the success envelope."""
    return json.dumps(
        {
            "status": "error",
            "message": message,
            "llm_content": message,
            **extra,
        },
        ensure_ascii=False,
    )


def _success_payload(
    *,
    slug: str,
    url: str,
    domain: str,
    summary: str,
    brand_relevance_score: float,
    scratchpad_path: str,
    og_image: str | None,
) -> str:
    """Shape a success payload for the LLM + UI.

    ``llm_content`` is short on purpose so the model gets just enough to
    cite the inspiration in its next turn without re-quoting the page.
    The frontend reads ``ui_action`` to render the ``inspiration_saved``
    card (preview + thumbnail).
    """
    llm_content = (
        f"Guardé {domain} como inspiración (slug={slug}, "
        f"relevance={brand_relevance_score:.2f}). "
        f"Disponible en {scratchpad_path}. Resumen: {summary}"
    )
    return json.dumps(
        {
            "status": "saved",
            "slug": slug,
            "url": url,
            "domain": domain,
            "summary": summary,
            "brand_relevance_score": round(brand_relevance_score, 2),
            "scratchpad_path": scratchpad_path,
            "og_image": og_image,
            "llm_content": llm_content,
            "ui_action": {
                "type": "inspiration_saved",
                "payload": {
                    "slug": slug,
                    "url": url,
                    "domain": domain,
                    "summary": summary,
                    "brand_relevance_score": round(brand_relevance_score, 2),
                    "og_image": og_image,
                    "scratchpad_path": scratchpad_path,
                },
            },
        },
        ensure_ascii=False,
    )


def _open_session() -> Session:
    """Lazy import of ``SessionLocal`` so import-time stays light."""
    from luana_core_platform.core.database import SessionLocal

    return SessionLocal()


async def _load_brand_lighthouse(tenant_id: UUID) -> str | None:
    """Read the brand-lighthouse summary for ``tenant_id`` via provider port.

    Iterates ``discover_providers()`` and asks each one for its
    ``summary_provider``. Brand is the only provider with a summary
    today (F3) but the abstraction keeps F4 free of cross-module
    imports — the ratchet ``copilot → brand`` stays at 22 entries.

    Best-effort: any exception/missing summary returns ``None`` so the
    analyzer falls back to generic criteria.
    """
    try:
        from luana_core_copilot.application.discovery import (
            discover_providers,
        )

        for provider in discover_providers().values():
            sp = provider.summary_provider()
            if sp is None:
                continue
            try:
                summary = await sp.summary(tenant_id=tenant_id)
            except Exception:
                logger.exception(
                    "fetch_url_summary_provider_failed",
                    module=getattr(provider, "module_id", "?"),
                )
                continue
            if summary:
                return str(summary)
    except Exception:
        logger.exception("fetch_url_brand_lighthouse_load_failed")
        return None
    return None


def _scratchpad_path(slug: str) -> str:
    """Canonical scratchpad path the deep-agent subagent writes to."""
    return f"/inspirations/{slug}.md"


def _frontmatter(
    *,
    extract: WebExtractResult,
    why: str,
    analysis: InspirationAnalysis,
) -> str:
    """Render the markdown frontmatter the subagent persists with each file."""
    title = (extract.title or "").replace("\n", " ").strip()
    return (
        "---\n"
        f"url: {extract.url}\n"
        f"domain: {extract.domain}\n"
        f"title: {title}\n"
        f"why: {why}\n"
        f"slug: {analysis.slug}\n"
        f"brand_relevance: {analysis.brand_relevance_score:.2f}\n"
        "---\n\n"
    )


def _scratchpad_body(
    *,
    extract: WebExtractResult,
    why: str,
    analysis: InspirationAnalysis,
) -> str:
    """Compose the full markdown the subagent would persist (preview material)."""
    fm = _frontmatter(extract=extract, why=why, analysis=analysis)
    sub = analysis.sub_elements or {}

    def _block(header: str, items: list) -> str:
        if not items:
            return ""
        bullets = "\n".join(f"- {item}" for item in items)
        return f"\n## {header}\n{bullets}\n"

    sections = (
        _block("Testimonios", sub.get("testimonials", []))
        + _block("CTAs", sub.get("ctas", []))
        + _block("Propuestas de valor", sub.get("value_props", []))
        + _block("Cues visuales", sub.get("visual_cues", []))
    )
    return f"{fm}## Resumen\n{analysis.summary}\n{sections}"


async def _fetch_url_impl(  # noqa: PLR0911 — flat early-return guards stay readable as separate paths
    *,
    url: str,
    why: str,
    db: Session | None = None,
    extract_fn: object = None,
    analyze_fn: object = None,
    lighthouse_fn: object = None,
) -> str:
    """Core implementation — split out so unit tests mock collaborators.

    ``extract_fn`` defaults to :func:`fetch_extract`; tests substitute a
    coroutine returning a ``WebExtractResult``.
    ``analyze_fn`` defaults to :func:`analyze`; tests substitute a
    callable returning an ``InspirationAnalysis``.
    ``lighthouse_fn`` defaults to :func:`_load_brand_lighthouse`; tests
    substitute an async callable returning ``str | None`` so the unit
    test path doesn't hit ``discover_providers`` (which loads every
    provider module — too heavy for in-memory SQLite suites).
    """
    tenant_id = get_tenant_id()
    if tenant_id is None:
        return _err_payload("No hay contexto de tenant. Vuelve a iniciar sesión.")

    conversation_id_str = get_conversation_id()
    if not conversation_id_str:
        return _err_payload("No hay conversación activa para asociar la inspiración.")
    try:
        conversation_id = UUID(conversation_id_str)
    except (TypeError, ValueError):
        return _err_payload("Conversación inválida.")

    extract_callable = extract_fn or fetch_extract
    analyze_callable = analyze_fn or analyze
    lighthouse_callable = lighthouse_fn or _load_brand_lighthouse

    # 1) Fetch + extract (validation lives inside fetch_extract).
    try:
        extract: WebExtractResult = await extract_callable(url)
    except FetchUrlError as exc:
        return _err_payload(str(exc), url=url)
    except Exception as exc:
        logger.exception("fetch_url_unexpected_fetch_error", url=url)
        return _err_payload(f"Error analizando la URL: {exc.__class__.__name__}.")

    # 2) DB: rate-limit, lighthouse, upsert, FIFO trim. We open a session
    # lazily so test injection (``db=...``) bypasses the global engine.
    owns_db = db is None
    if owns_db:
        db = _open_session()
    try:
        from luana_core_copilot.infrastructure.repositories.inspiration_repository import (
            CopilotInspirationRepository,
        )

        repo = CopilotInspirationRepository(db)
        existing = repo.count_for_conversation(
            tenant_id=tenant_id,
            conversation_id=conversation_id,
        )
        if existing >= MAX_INSPIRATIONS_PER_CONVERSATION:
            return _err_payload(
                "Ya tenés el máximo de inspiraciones por conversación. "
                "Eliminá alguna o promové con pin_to_memory las importantes.",
                limit=MAX_INSPIRATIONS_PER_CONVERSATION,
            )

        lighthouse = await lighthouse_callable(tenant_id)

        # 3) LLM analyze — outside the DB lock, but we keep the session
        # open because the LLM call is a few seconds and reopening the
        # session would lose the rate-limit read consistency.
        analysis = analyze_callable(
            url=extract.url,
            why=why,
            brand_lighthouse=lighthouse,
            page_title=extract.title,
            content_md=extract.content_md,
            fallback_domain=extract.domain,
        )

        # 4) Upsert + commit.
        body = _scratchpad_body(extract=extract, why=why, analysis=analysis)
        repo.upsert(
            tenant_id=tenant_id,
            conversation_id=conversation_id,
            slug=analysis.slug,
            url=extract.url,
            why=why,
            domain=extract.domain,
            title=extract.title,
            summary=analysis.summary,
            sub_elements=analysis.sub_elements,
            brand_relevance_score=analysis.brand_relevance_score,
            content_md=body,
            og_image=extract.og_image,
        )

        # 5) FIFO eviction beyond the visible cap. We delete rows beyond
        # the cap so the table doesn't bloat — they're never reachable
        # via the system-prompt fragment anyway.
        repo.delete_oldest_beyond_cap(
            tenant_id=tenant_id,
            conversation_id=conversation_id,
            cap=ACTIVE_INSPIRATIONS_CAP,
        )

        db.commit()
    except Exception:
        logger.exception("fetch_url_persist_failed")
        if owns_db:
            db.rollback()
        return _err_payload("No se pudo guardar la inspiración. Intentalo otra vez.")
    finally:
        if owns_db:
            db.close()

    return _success_payload(
        slug=analysis.slug,
        url=extract.url,
        domain=extract.domain,
        summary=analysis.summary,
        brand_relevance_score=analysis.brand_relevance_score,
        scratchpad_path=_scratchpad_path(analysis.slug),
        og_image=extract.og_image,
    )


@tool
async def fetch_url(url: str, why: str = "") -> str:
    """Analiza una URL pública como inspiración y la guarda en la conversación.

    Cuándo usarla:
    - El usuario pega un link y dice "mirá esto", "esto me gusta",
      "competencia", "referencia", o pregunta si vale la pena copiarlo.
    - El usuario pide "rescatá los testimonios de tal página".

    NO la uses cuando:
    - El usuario quiere extraer datos hacia Brand/Offer (usá ``extract_from_url``).
    - El usuario pide búsquedas de mercado abiertas (usá ``web_research``).

    Args:
        url: URL pública (https). Se valida + se le quita el query string
            por privacidad antes de fetchear.
        why: Razón corta del usuario (opcional). "competencia voz",
            "estructura página", "testimonios fuertes", etc. La razón
            ayuda al análisis a priorizar elementos.

    Returns:
        JSON con ``status="saved"`` + ``slug`` + ``summary`` +
        ``brand_relevance_score`` + ``scratchpad_path``, o
        ``status="error"`` con ``message`` user-friendly.
    """
    return await _fetch_url_impl(url=url, why=why)


__all__ = [
    "ACTIVE_INSPIRATIONS_CAP",
    "MAX_INSPIRATIONS_PER_CONVERSATION",
    "_fetch_url_impl",
    "fetch_url",
]

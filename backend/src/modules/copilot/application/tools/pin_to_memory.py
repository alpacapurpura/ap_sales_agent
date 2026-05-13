"""F4 — ``pin_to_memory`` transversal tool.

Promotes an inspiration captured during the current conversation
(stored in ``copilot_inspiration``) into the per-user persistent
``copilot_pinned_memory`` table so it survives across conversations.

Use case: the user pegó una URL hace 3 turnos, le gustó como referencia,
y quiere que el copilot la "recuerde" cuando arme la próxima oferta o
landing — incluso en una conversación distinta.

Identifica la inspiración por ``slug`` (visible en el system prompt
fragment "Inspiraciones cargadas") en lugar de por path absoluto, así
el LLM no tiene que re-construir el ``/inspirations/<slug>.md`` —
suficientemente frágil que mejor evitarlo.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING
from uuid import UUID

import structlog
from langchain_core.tools import tool
from luana_core_platform.core.context import get_conversation_id, get_tenant_id, get_user_id

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

logger = structlog.get_logger()


def _err(message: str, **extra: object) -> str:
    """Shape an error envelope."""
    return json.dumps(
        {"status": "error", "message": message, "llm_content": message, **extra},
        ensure_ascii=False,
    )


def _ok(*, slug: str, path: str, summary: str) -> str:
    """Shape a success envelope."""
    llm_content = f"Anclé '{slug}' en tu memoria persistente ({path})."
    return json.dumps(
        {
            "status": "pinned",
            "slug": slug,
            "path": path,
            "summary": summary,
            "llm_content": llm_content,
            "ui_action": {
                "type": "memory_pinned",
                "payload": {"slug": slug, "path": path},
            },
        },
        ensure_ascii=False,
    )


def _open_session() -> Session:
    """Lazy import of ``SessionLocal``."""
    from luana_core_platform.core.database import SessionLocal

    return SessionLocal()


def _persistent_path(slug: str) -> str:
    """Canonical path used in ``copilot_pinned_memory.path``."""
    return f"/memories/inspirations/{slug}.md"


async def _pin_to_memory_impl(  # noqa: PLR0911 — early-return guards
    *,
    slug: str,
    db: Session | None = None,
) -> str:
    """Core implementation — split out for unit tests."""
    tenant_id = get_tenant_id()
    if tenant_id is None:
        return _err("No hay contexto de tenant. Vuelve a iniciar sesión.")

    user_id = get_user_id()
    if user_id is None:
        return _err("No hay contexto de usuario para anclar a memoria.")

    conversation_id_str = get_conversation_id()
    if not conversation_id_str:
        return _err("No hay conversación activa.")
    try:
        conversation_id = UUID(conversation_id_str)
    except (TypeError, ValueError):
        return _err("Conversación inválida.")

    if not slug or not slug.strip():
        return _err("Necesito el slug de la inspiración a anclar.")
    slug_clean = slug.strip().lower()

    owns_db = db is None
    if owns_db:
        db = _open_session()
    try:
        from luana_core_copilot.infrastructure.repositories.inspiration_repository import (
            CopilotInspirationRepository,
        )
        from luana_core_copilot.infrastructure.repositories.pinned_memory_repository import (
            CopilotPinnedMemoryRepository,
        )

        insp = CopilotInspirationRepository(db).get_by_slug(
            tenant_id=tenant_id,
            conversation_id=conversation_id,
            slug=slug_clean,
        )
        if insp is None:
            return _err(
                f"No encontré una inspiración con slug '{slug_clean}'. "
                "Mirá la tabla 'Inspiraciones cargadas' en tu contexto.",
                slug=slug_clean,
            )

        path = _persistent_path(slug_clean)
        CopilotPinnedMemoryRepository(db).upsert(
            tenant_id=tenant_id,
            user_id=user_id,
            path=path,
            content=insp.content_md,
            pinned_from_conversation_id=conversation_id,
        )
        db.commit()
        return _ok(slug=slug_clean, path=path, summary=insp.summary)
    except Exception:
        logger.exception("pin_to_memory_persist_failed", slug=slug)
        if owns_db:
            db.rollback()
        return _err("No se pudo anclar la inspiración a memoria. Intentalo otra vez.")
    finally:
        if owns_db:
            db.close()


@tool
async def pin_to_memory(slug: str) -> str:
    """Ancla una inspiración a tu memoria persistente cross-conversación.

    Cuándo usarla:
    - El usuario dice "guardá esta referencia para siempre", "que te
      acuerdes de mujercoraje en futuras ofertas", "pin esto", "fijá
      esta página".
    - Después de un ``fetch_url`` cuando el resultado fue claramente útil
      (relevance ≥ 0.7) y el usuario lo confirma.

    Args:
        slug: Slug de la inspiración (lo ves en la tabla "Inspiraciones
            cargadas" del system prompt). Ej. "mujer-coraje".

    Returns:
        JSON con ``status="pinned"`` y ``path`` persistido, o
        ``status="error"`` con ``message`` user-friendly.
    """
    return await _pin_to_memory_impl(slug=slug)


__all__ = ["_pin_to_memory_impl", "pin_to_memory"]

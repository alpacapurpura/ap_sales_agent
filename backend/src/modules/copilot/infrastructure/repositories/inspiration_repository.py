"""Copilot inspiration repository — F4 URL contextual scratchpad.

CRUD over ``copilot_inspiration`` (per-conversation, cross-turn). Tenant-
scoped on every query. Used by:

- ``fetch_url`` tool to upsert a row when the user pastes a URL.
- The system-prompt builder to list active inspirations as a stable
  fragment between the brand lighthouse and the completion snapshot.
- ``pin_to_memory`` tool to read the row before promoting it to the
  per-user persistent ``copilot_pinned_memory`` table.
"""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

import structlog
from sqlalchemy import delete, func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert

from src.modules.copilot.infrastructure.models.inspiration_model import (
    CopilotInspirationModel,
)

if TYPE_CHECKING:
    from uuid import UUID

    from sqlalchemy.orm import Session

logger = structlog.get_logger()


class CopilotInspirationRepository:
    """Repository for copilot inspirations."""

    def __init__(self, db: Session) -> None:
        """Bind a SQLAlchemy session."""
        self.db = db

    def upsert(
        self,
        *,
        tenant_id: UUID,
        conversation_id: UUID,
        slug: str,
        url: str,
        why: str,
        domain: str,
        title: str | None,
        summary: str,
        sub_elements: dict,
        brand_relevance_score: float,
        content_md: str,
        og_image: str | None,
    ) -> CopilotInspirationModel:
        """Insert or update by ``(conversation_id, slug)``.

        Uses ``index_elements`` (not ``constraint=...``) so SQLite tests
        also accept the ON CONFLICT clause — see F2 learnings gotcha.
        """
        score = Decimal(str(round(float(brand_relevance_score), 2)))
        stmt = (
            pg_insert(CopilotInspirationModel)
            .values(
                tenant_id=tenant_id,
                conversation_id=conversation_id,
                slug=slug,
                url=url,
                why=why,
                domain=domain,
                title=title,
                summary=summary,
                sub_elements=sub_elements,
                brand_relevance_score=score,
                content_md=content_md,
                og_image=og_image,
            )
            .on_conflict_do_update(
                index_elements=["conversation_id", "slug"],
                set_={
                    "url": url,
                    "why": why,
                    "title": title,
                    "summary": summary,
                    "sub_elements": sub_elements,
                    "brand_relevance_score": score,
                    "content_md": content_md,
                    "og_image": og_image,
                },
            )
            .returning(CopilotInspirationModel)
        )
        row = self.db.execute(stmt).scalar_one()
        self.db.flush()
        return row

    def get_by_slug(
        self,
        *,
        tenant_id: UUID,
        conversation_id: UUID,
        slug: str,
    ) -> CopilotInspirationModel | None:
        """Fetch one inspiration by ``(conversation_id, slug)`` for tenant."""
        stmt = select(CopilotInspirationModel).where(
            CopilotInspirationModel.tenant_id == tenant_id,
            CopilotInspirationModel.conversation_id == conversation_id,
            CopilotInspirationModel.slug == slug,
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def list_active_for_conversation(
        self,
        *,
        tenant_id: UUID,
        conversation_id: UUID,
        limit: int = 5,
    ) -> list[CopilotInspirationModel]:
        """List the N newest inspirations for a conversation (FIFO cap N).

        Ordered ``created_at DESC`` so the most-recent inspiration is at
        index 0 — caller renders top-N then trims older ones for display.
        """
        stmt = (
            select(CopilotInspirationModel)
            .where(
                CopilotInspirationModel.tenant_id == tenant_id,
                CopilotInspirationModel.conversation_id == conversation_id,
            )
            .order_by(CopilotInspirationModel.created_at.desc())
            .limit(limit)
        )
        return list(self.db.execute(stmt).scalars().all())

    def count_for_conversation(
        self,
        *,
        tenant_id: UUID,
        conversation_id: UUID,
    ) -> int:
        """Count total inspirations for a conversation (rate-limit gate)."""
        stmt = select(func.count(CopilotInspirationModel.id)).where(
            CopilotInspirationModel.tenant_id == tenant_id,
            CopilotInspirationModel.conversation_id == conversation_id,
        )
        return int(self.db.execute(stmt).scalar_one() or 0)

    def delete_oldest_beyond_cap(
        self,
        *,
        tenant_id: UUID,
        conversation_id: UUID,
        cap: int = 5,
    ) -> int:
        """Trim oldest rows so at most ``cap`` remain. Returns rows removed.

        FIFO eviction strategy: keep newest ``cap`` rows, delete the rest.
        """
        keep_stmt = (
            select(CopilotInspirationModel.id)
            .where(
                CopilotInspirationModel.tenant_id == tenant_id,
                CopilotInspirationModel.conversation_id == conversation_id,
            )
            .order_by(CopilotInspirationModel.created_at.desc())
            .limit(cap)
        )
        keep_ids = list(self.db.execute(keep_stmt).scalars().all())
        if not keep_ids:
            return 0
        stmt = delete(CopilotInspirationModel).where(
            CopilotInspirationModel.tenant_id == tenant_id,
            CopilotInspirationModel.conversation_id == conversation_id,
            CopilotInspirationModel.id.notin_(keep_ids),
        )
        result = self.db.execute(stmt)
        self.db.flush()
        return int(result.rowcount or 0)

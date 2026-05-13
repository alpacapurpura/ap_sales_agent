"""Copilot conversation repository."""

from __future__ import annotations

import base64
import json
from datetime import UTC
from typing import TYPE_CHECKING

import structlog
from luana_core_copilot.infrastructure.models.conversation_model import (
    CopilotConversationModel,
)
from luana_core_platform.domain.datetime_utils import utc_now
from sqlalchemy import func, select, update

if TYPE_CHECKING:
    from datetime import datetime
    from uuid import UUID

    from sqlalchemy.orm import Session

logger = structlog.get_logger()


class ConversationRepository:
    """Repository for conversation persistence."""

    def __init__(self, db: Session) -> None:
        """Initialize conversation repository."""
        self.db = db

    def count_window(
        self,
        *,
        tenant_id: UUID,
        since: datetime,
        until: datetime,
        include_archived: bool = False,
    ) -> int:
        """Count conversations whose ``updated_at`` falls inside the window.

        Tenant-scoped. Excludes ``deleted_at`` rows always; excludes
        ``archived_at`` unless ``include_archived=True``. Used by
        ``ask_tenant_data`` for "cuántas conversaciones tuve esta semana"-class
        questions where the answer is the tenant's own copilot activity.
        """
        conditions = [
            CopilotConversationModel.tenant_id == tenant_id,
            CopilotConversationModel.deleted_at.is_(None),
            CopilotConversationModel.updated_at >= since,
            CopilotConversationModel.updated_at <= until,
        ]
        if not include_archived:
            conditions.append(CopilotConversationModel.archived_at.is_(None))

        stmt = select(func.count(CopilotConversationModel.id)).where(*conditions)
        return int(self.db.execute(stmt).scalar_one() or 0)

    def create(
        self,
        *,
        conversation_id: UUID,
        tenant_id: UUID,
        user_id: UUID,
        title: str | None = None,
    ) -> CopilotConversationModel:
        """Execute create operation."""
        conv = CopilotConversationModel(
            id=conversation_id,
            tenant_id=tenant_id,
            user_id=user_id,
            title=title,
            messages=[],
        )
        self.db.add(conv)
        self.db.flush()
        return conv

    def get_by_id(
        self,
        conversation_id: UUID,
        tenant_id: UUID,
        user_id: UUID | None = None,
    ) -> CopilotConversationModel | None:
        """Return by id, filtered by tenant and optionally by user.

        When user_id is provided, acts as an ownership check — prevents
        cross-user conversation access within the same tenant.
        """
        conditions = [
            CopilotConversationModel.id == conversation_id,
            CopilotConversationModel.tenant_id == tenant_id,
            CopilotConversationModel.deleted_at.is_(None),
        ]
        if user_id is not None:
            conditions.append(CopilotConversationModel.user_id == user_id)

        stmt = select(CopilotConversationModel).where(*conditions)
        return self.db.execute(stmt).scalars().first()

    def get_or_create_by_channel(
        self,
        *,
        tenant_id: UUID,
        user_id: UUID,
        channel_type: str,
        channel_chat_id: str,
    ) -> CopilotConversationModel:
        """Return the live conversation for ``(tenant, user, channel, chat_id)`` or create one.

        PI-5 D-PI5-007: 1 conversation per ``(tenant_id, user_id,
        channel_type, channel_chat_id)`` quadruple — single source of
        truth for non-web channels (Telegram, future WhatsApp, etc.).

        Concurrency strategy: optimistic SELECT-then-INSERT pattern.
            1. SELECT … WHERE all four keys + ``deleted_at IS NULL`` LIMIT 1.
            2. If hit → return.
            3. Else → INSERT new row + flush + commit.

        Q5 PM-resolved (CONTRACT § 16): the UNIQUE constraint on this
        quadruple is **deferred to S5 PR-5** to avoid a fresh migration
        in PR-2's scope. The race window is microseconds — at MVP
        Telegram volume (≤dozens of active tenants) the chance of a
        true duplicate insert is statistically negligible. Index lookup
        performance is already covered by PR-1's
        ``ix_copilot_conversations_tenant_channel`` on
        ``(tenant_id, channel_type, channel_chat_id)``. Once UNIQUE
        lands, this method gains an ``IntegrityError`` retry-once
        branch.

        Tenant-scoped. Excludes ``deleted_at`` rows (treated as missing
        → creates a new row). Cross-tenant isolation is enforced by the
        ``tenant_id`` predicate; cross-user is enforced by the
        ``user_id`` predicate.
        """
        # Step 1 — optimistic SELECT.
        stmt = (
            select(CopilotConversationModel)
            .where(
                CopilotConversationModel.tenant_id == tenant_id,
                CopilotConversationModel.user_id == user_id,
                CopilotConversationModel.channel_type == channel_type,
                CopilotConversationModel.channel_chat_id == channel_chat_id,
                CopilotConversationModel.deleted_at.is_(None),
            )
            .limit(1)
        )
        existing = self.db.execute(stmt).scalars().first()
        if existing is not None:
            return existing

        # Step 2 — INSERT new row. ``id`` is server-default uuid4 on the
        # model; we let SQLAlchemy generate it.
        from uuid import uuid4

        conv = CopilotConversationModel(
            id=uuid4(),
            tenant_id=tenant_id,
            user_id=user_id,
            channel_type=channel_type,
            channel_chat_id=channel_chat_id,
            messages=[],
        )
        self.db.add(conv)
        self.db.flush()
        return conv

    def append_messages(
        self,
        conversation_id: UUID,
        tenant_id: UUID,
        new_messages: list,
        *,
        user_id: UUID | None = None,
    ) -> None:
        """Execute append messages operation.

        When user_id is provided, validates ownership before appending.
        """
        conv = self.get_by_id(conversation_id, tenant_id, user_id)
        if not conv:
            logger.warning(
                "conversation_not_found",
                conversation_id=str(conversation_id),
                tenant_id=str(tenant_id),
            )
            return
        existing = list(conv.messages or [])
        existing.extend(new_messages)
        conv.messages = existing
        self.db.flush()

    def update_title(
        self,
        conversation_id: UUID,
        tenant_id: UUID,
        title: str,
        *,
        user_id: UUID | None = None,
    ) -> None:
        """Update title, validating ownership when user_id is provided."""
        conv = self.get_by_id(conversation_id, tenant_id, user_id)
        if conv:
            conv.title = title
            self.db.flush()

    def list_by_tenant_user(
        self,
        tenant_id: UUID,
        user_id: UUID,
        limit: int = 20,
        offset: int = 0,
    ) -> list[CopilotConversationModel]:
        """List by tenant user."""
        stmt = (
            select(CopilotConversationModel)
            .where(
                CopilotConversationModel.tenant_id == tenant_id,
                CopilotConversationModel.user_id == user_id,
                CopilotConversationModel.deleted_at.is_(None),
            )
            .order_by(CopilotConversationModel.updated_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(self.db.execute(stmt).scalars().all())

    def cleanup_expired_conversations(self) -> int:
        """Soft-delete conversations past their expires_at.

        Returns the number of soft-deleted rows.
        Uses bulk UPDATE for efficiency — no need to load rows into memory.
        """
        now = utc_now()
        stmt = (
            update(CopilotConversationModel)
            .where(
                CopilotConversationModel.expires_at.isnot(None),
                CopilotConversationModel.expires_at <= now,
                CopilotConversationModel.deleted_at.is_(None),
            )
            .values(deleted_at=now)
        )
        result = self.db.execute(stmt)
        return result.rowcount

    # ── Cross-tenant methods (admin) ─────────────────────────────────────

    def list_by_tenant(
        self,
        tenant_id: UUID,
        limit: int = 20,
        offset: int = 0,
    ) -> list[CopilotConversationModel]:
        """List conversations for a tenant (all users)."""
        stmt = (
            select(CopilotConversationModel)
            .where(
                CopilotConversationModel.tenant_id == tenant_id,
                CopilotConversationModel.deleted_at.is_(None),
            )
            .order_by(CopilotConversationModel.updated_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(self.db.execute(stmt).scalars().all())

    def list_all_paginated(
        self,
        tenant_id: UUID | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[CopilotConversationModel]:
        """List conversations, optionally filtered by tenant."""
        stmt = (
            select(CopilotConversationModel)
            .where(CopilotConversationModel.deleted_at.is_(None))
            .order_by(CopilotConversationModel.updated_at.desc())
            .limit(limit)
            .offset(offset)
        )
        if tenant_id:
            stmt = stmt.where(CopilotConversationModel.tenant_id == tenant_id)
        return list(self.db.execute(stmt).scalars().all())

    # ── v2 methods (CONTRACT §3, §4) ─────────────────────────────────────────

    def list_paginated(
        self,
        *,
        tenant_id: UUID,
        user_id: UUID,
        limit: int = 6,
        cursor: str | None = None,
        include_archived: bool = False,
    ) -> dict:
        """Cursor-paginated conversation list for a tenant+user.

        Returns a dict with keys:
        - ``items``: list of CopilotConversationModel
        - ``next_cursor``: opaque base64 string or None
        """
        conditions = [
            CopilotConversationModel.tenant_id == tenant_id,
            CopilotConversationModel.user_id == user_id,
            CopilotConversationModel.deleted_at.is_(None),
        ]
        if not include_archived:
            conditions.append(CopilotConversationModel.archived_at.is_(None))

        # Decode cursor: encodes {"updated_at": iso, "id": uuid_str}
        if cursor:
            try:
                payload = json.loads(base64.b64decode(cursor).decode())
                cursor_updated_at = payload["updated_at"]
                cursor_id = payload["id"]
                from sqlalchemy import String as SAString
                from sqlalchemy import and_, cast, or_

                conditions.append(
                    or_(
                        CopilotConversationModel.updated_at < cursor_updated_at,
                        and_(
                            CopilotConversationModel.updated_at == cursor_updated_at,
                            cast(CopilotConversationModel.id, SAString) < cursor_id,
                        ),
                    )
                )
            except Exception:  # noqa: BLE001 — malformed cursor → ignore, start from top
                pass

        stmt = (
            select(CopilotConversationModel)
            .where(*conditions)
            .order_by(
                CopilotConversationModel.updated_at.desc(),
                CopilotConversationModel.id.desc(),
            )
            .limit(limit + 1)  # fetch one extra to know if more exist
        )
        rows = list(self.db.execute(stmt).scalars().all())

        has_more = len(rows) > limit
        items = rows[:limit]

        next_cursor: str | None = None
        if has_more and items:
            last = items[-1]
            payload = {
                "updated_at": last.updated_at.isoformat() if last.updated_at else "",
                "id": str(last.id),
            }
            next_cursor = base64.b64encode(json.dumps(payload).encode()).decode()

        return {"items": items, "next_cursor": next_cursor}

    def archive(
        self,
        *,
        conversation_id: UUID,
        tenant_id: UUID,
        user_id: UUID,
    ) -> CopilotConversationModel | None:
        """Set archived_at on a conversation (soft archive).

        Returns the updated model or None if not found / wrong tenant.
        """
        conv = self.get_by_id(conversation_id, tenant_id, user_id)
        if not conv:
            return None
        conv.archived_at = utc_now()
        self.db.flush()
        logger.info(
            "conversation_archived",
            conversation_id=str(conversation_id),
            tenant_id=str(tenant_id),
        )
        return conv

    def update_summary(
        self,
        *,
        conversation_id: UUID,
        tenant_id: UUID,
        summary: str,
        total_tokens: int,
    ) -> None:
        """Persist rolling summary + token count; clear dirty flag."""
        now = utc_now()
        stmt = (
            update(CopilotConversationModel)
            .where(
                CopilotConversationModel.id == conversation_id,
                CopilotConversationModel.tenant_id == tenant_id,
                CopilotConversationModel.deleted_at.is_(None),
            )
            .values(
                summary=summary,
                total_tokens=total_tokens,
                summary_updated_at=now,
                summary_dirty_at=None,
            )
        )
        self.db.execute(stmt)

    def increment_message_count(
        self,
        *,
        conversation_id: UUID,
        tenant_id: UUID,
        delta: int = 1,
    ) -> None:
        """Increment message_count by delta for a conversation."""
        stmt = (
            update(CopilotConversationModel)
            .where(
                CopilotConversationModel.id == conversation_id,
                CopilotConversationModel.tenant_id == tenant_id,
                CopilotConversationModel.deleted_at.is_(None),
            )
            .values(message_count=CopilotConversationModel.message_count + delta)
        )
        self.db.execute(stmt)

    def update_metadata(
        self,
        *,
        conversation_id: UUID,
        tenant_id: UUID,
        **kwargs: object,
    ) -> CopilotConversationModel | None:
        """Update arbitrary metadata fields on a conversation.

        Only the fields present in CopilotConversationModel are allowed.
        Returns the updated model or None if not found.
        """
        allowed = {
            "title",
            "last_tier_used",
            "title_auto_generated",
            "summary_dirty_at",
            "plan_state",
            "procedure_state",
            "procedure_id",
        }
        updates = {k: v for k, v in kwargs.items() if k in allowed}
        if not updates:
            return self.get_by_id(conversation_id, tenant_id)

        stmt = (
            update(CopilotConversationModel)
            .where(
                CopilotConversationModel.id == conversation_id,
                CopilotConversationModel.tenant_id == tenant_id,
                CopilotConversationModel.deleted_at.is_(None),
            )
            .values(**updates)
            .returning(CopilotConversationModel)
        )
        result = self.db.execute(stmt).scalars().first()
        return result

    def set_plan_state(
        self,
        *,
        conversation_id: UUID,
        tenant_id: UUID,
        plan_state: dict | None,
    ) -> None:
        """Write plan_state JSONB column."""
        stmt = (
            update(CopilotConversationModel)
            .where(
                CopilotConversationModel.id == conversation_id,
                CopilotConversationModel.tenant_id == tenant_id,
                CopilotConversationModel.deleted_at.is_(None),
            )
            .values(plan_state=plan_state)
        )
        self.db.execute(stmt)

    def update_procedure_state(
        self,
        *,
        conversation_id: UUID,
        tenant_id: UUID,
        procedure_state: dict | None,
    ) -> None:
        """Write procedure_state JSONB column."""
        stmt = (
            update(CopilotConversationModel)
            .where(
                CopilotConversationModel.id == conversation_id,
                CopilotConversationModel.tenant_id == tenant_id,
                CopilotConversationModel.deleted_at.is_(None),
            )
            .values(procedure_state=procedure_state)
        )
        self.db.execute(stmt)

    def update_workflow_state(
        self,
        *,
        conversation_id: UUID,
        tenant_id: UUID,
        workflow_state: dict | None,
    ) -> None:
        """Write workflow_state JSONB column (F6).

        Coexists with ``procedure_state`` during the cutover. Production
        readers use ``get_workflow_state`` with ``fallback_to_procedure=True``
        for conversations that started before F6.
        """
        stmt = (
            update(CopilotConversationModel)
            .where(
                CopilotConversationModel.id == conversation_id,
                CopilotConversationModel.tenant_id == tenant_id,
                CopilotConversationModel.deleted_at.is_(None),
            )
            .values(workflow_state=workflow_state)
        )
        self.db.execute(stmt)

    def get_workflow_state(
        self,
        *,
        conversation_id: UUID,
        tenant_id: UUID,
        fallback_to_procedure: bool = False,
    ) -> dict | None:
        """Return the workflow_state payload (or fallback to procedure_state).

        ``fallback_to_procedure`` covers conversations that started before
        F6: their workflow_state is NULL but the legacy procedure_state still
        carries the pre-F6 guided/procedure overlay. F-pos cutover removes
        the fallback once all live conversations are migrated.
        """
        stmt = select(
            CopilotConversationModel.workflow_state,
            CopilotConversationModel.procedure_state,
        ).where(
            CopilotConversationModel.id == conversation_id,
            CopilotConversationModel.tenant_id == tenant_id,
            CopilotConversationModel.deleted_at.is_(None),
        )
        row = self.db.execute(stmt).first()
        if row is None:
            return None
        workflow_state, procedure_state = row
        if workflow_state is not None:
            return workflow_state
        if fallback_to_procedure:
            return procedure_state
        return None

    def count_all(self, tenant_id: UUID | None = None) -> int:
        """Count conversations, optionally filtered by tenant."""
        from sqlalchemy import func

        stmt = (
            select(func.count())
            .select_from(CopilotConversationModel)
            .where(
                CopilotConversationModel.deleted_at.is_(None),
            )
        )
        if tenant_id:
            stmt = stmt.where(CopilotConversationModel.tenant_id == tenant_id)
        return self.db.execute(stmt).scalar() or 0

    def get_global_stats(self, days: int = 30) -> dict:
        """Global conversation stats for admin dashboard."""
        from datetime import datetime, timedelta

        from sqlalchemy import func

        cutoff = datetime.now(UTC) - timedelta(days=days)

        total = (
            self.db.execute(
                select(func.count())
                .select_from(CopilotConversationModel)
                .where(
                    CopilotConversationModel.created_at >= cutoff,
                    CopilotConversationModel.deleted_at.is_(None),
                ),
            ).scalar()
            or 0
        )

        tenants_with_convs = (
            self.db.execute(
                select(
                    func.count(func.distinct(CopilotConversationModel.tenant_id)),
                ).where(
                    CopilotConversationModel.created_at >= cutoff,
                    CopilotConversationModel.deleted_at.is_(None),
                ),
            ).scalar()
            or 0
        )

        return {
            "total": total,
            "tenants_with_conversations": tenants_with_convs,
        }

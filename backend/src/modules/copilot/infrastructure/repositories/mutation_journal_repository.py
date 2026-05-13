"""MutationJournalRepository — persist and query copilot mutation journal entries."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import structlog
from luana_core_copilot.infrastructure.models.mutation_journal_model import (
    MutationJournalModel,
)
from luana_core_platform.domain.datetime_utils import utc_now
from sqlalchemy import select, update

if TYPE_CHECKING:
    from uuid import UUID

logger = structlog.get_logger()


class MutationJournalRepository:
    """Persist and query mutation journal entries per tenant."""

    def __init__(self, db: Any) -> None:  # noqa: ANN401  # opaque Session/AsyncSession wrapper
        """Initialize repository with a database session."""
        self.db = db

    def insert(
        self,
        *,
        tenant_id: UUID,
        conversation_id: UUID,
        message_id: UUID,
        domain: str,
        entity_id: UUID | None,
        field_path: str,
        old_value: Any | None,  # noqa: ANN401  # JSONB: genuine JSON value (dict/list/str/num/bool/null)
        new_value: Any | None,  # noqa: ANN401  # JSONB: genuine JSON value (dict/list/str/num/bool/null)
    ) -> MutationJournalModel:
        """Insert a new journal entry and return it.

        The caller is responsible for calling db.commit() / db.flush().
        """
        row = MutationJournalModel(
            tenant_id=tenant_id,
            conversation_id=conversation_id,
            message_id=message_id,
            domain=domain,
            entity_id=entity_id,
            field_path=field_path,
            old_value=old_value,
            new_value=new_value,
        )
        self.db.add(row)
        self.db.flush()
        logger.debug(
            "mutation_journal_inserted",
            domain=domain,
            field_path=field_path,
            tenant_id=str(tenant_id),
        )
        return row

    def find_active_by_natural_key(
        self,
        *,
        tenant_id: UUID,
        conversation_id: UUID,
        message_id: UUID,
        field_path: str,
    ) -> MutationJournalModel | None:
        """Return the active (non-reverted) row matching the natural key, or None.

        Natural key for AC5 idempotency = (tenant_id, conversation_id,
        message_id, field_path) WHERE reverted_at IS NULL. Mirrors the
        partial unique index ``ux_copilot_mutation_journal_active_natural_key``.
        """
        stmt = select(MutationJournalModel).where(
            MutationJournalModel.tenant_id == tenant_id,
            MutationJournalModel.conversation_id == conversation_id,
            MutationJournalModel.message_id == message_id,
            MutationJournalModel.field_path == field_path,
            MutationJournalModel.reverted_at.is_(None),
        )
        return self.db.execute(stmt).scalars().first()

    def upsert_idempotent(
        self,
        *,
        tenant_id: UUID,
        conversation_id: UUID,
        message_id: UUID,
        domain: str,
        entity_id: UUID | None,
        field_path: str,
        old_value: Any | None,  # noqa: ANN401  # JSONB: genuine JSON value
        new_value: Any | None,  # noqa: ANN401  # JSONB: genuine JSON value
    ) -> tuple[MutationJournalModel, str]:
        """Insert if no active row exists for the natural key, else return existing.

        Returns ``(row, status)`` where status is ``"applied"`` for new
        inserts and ``"existing"`` when an active row already exists. Used
        by the ``/mutations/apply`` endpoint to absorb duplicate clicks
        without writing a second journal row.
        """
        existing = self.find_active_by_natural_key(
            tenant_id=tenant_id,
            conversation_id=conversation_id,
            message_id=message_id,
            field_path=field_path,
        )
        if existing is not None:
            logger.debug(
                "mutation_journal_idempotent_hit",
                domain=domain,
                field_path=field_path,
                tenant_id=str(tenant_id),
                existing_id=str(existing.id),
            )
            return existing, "existing"

        row = self.insert(
            tenant_id=tenant_id,
            conversation_id=conversation_id,
            message_id=message_id,
            domain=domain,
            entity_id=entity_id,
            field_path=field_path,
            old_value=old_value,
            new_value=new_value,
        )
        return row, "applied"

    def fetch_by_conversation(
        self,
        *,
        tenant_id: UUID,
        conversation_id: UUID,
        include_reverted: bool = False,
        message_id: UUID | None = None,
    ) -> list[MutationJournalModel]:
        """Return journal entries for a conversation.

        Always filters by tenant_id to prevent cross-tenant leaks.
        By default only returns active (non-reverted) entries.
        ``message_id`` narrows to a single proposal — used by the
        ``ProposalCard`` rehydrate path so a card can repaint its
        per-field "applied" state after a refresh.
        """
        conditions = [
            MutationJournalModel.tenant_id == tenant_id,
            MutationJournalModel.conversation_id == conversation_id,
        ]
        if not include_reverted:
            conditions.append(MutationJournalModel.reverted_at.is_(None))
        if message_id is not None:
            conditions.append(MutationJournalModel.message_id == message_id)

        stmt = select(MutationJournalModel).where(*conditions).order_by(MutationJournalModel.applied_at.asc())
        return list(self.db.execute(stmt).scalars().all())

    def mark_reverted(
        self,
        *,
        tenant_id: UUID,
        entry_ids: list[UUID],
    ) -> int:
        """Set reverted_at on the specified journal entries.

        Only affects rows belonging to the given tenant.
        Returns the number of rows updated.
        """
        if not entry_ids:
            return 0

        now = utc_now()
        stmt = (
            update(MutationJournalModel)
            .where(
                MutationJournalModel.tenant_id == tenant_id,
                MutationJournalModel.id.in_(entry_ids),
                MutationJournalModel.reverted_at.is_(None),
            )
            .values(reverted_at=now)
        )
        result = self.db.execute(stmt)
        logger.info(
            "mutation_journal_reverted",
            count=result.rowcount,
            tenant_id=str(tenant_id),
        )
        return result.rowcount

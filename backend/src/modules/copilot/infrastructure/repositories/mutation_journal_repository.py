"""MutationJournalRepository — persist and query copilot mutation journal entries."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import structlog
from sqlalchemy import select, update

from src.modules.copilot.infrastructure.models.mutation_journal_model import (
    MutationJournalModel,
)
from src.shared.domain.datetime_utils import utc_now

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

    def fetch_by_conversation(
        self,
        *,
        tenant_id: UUID,
        conversation_id: UUID,
        include_reverted: bool = False,
    ) -> list[MutationJournalModel]:
        """Return journal entries for a conversation.

        Always filters by tenant_id to prevent cross-tenant leaks.
        By default only returns active (non-reverted) entries.
        """
        conditions = [
            MutationJournalModel.tenant_id == tenant_id,
            MutationJournalModel.conversation_id == conversation_id,
        ]
        if not include_reverted:
            conditions.append(MutationJournalModel.reverted_at.is_(None))

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

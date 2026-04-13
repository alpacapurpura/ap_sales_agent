"""Repository for InterviewSession persistence."""

from datetime import timedelta
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified

from src.modules.copilot.domain.interview_session import (
    InterviewSession,
    InterviewStatus,
)
from src.modules.copilot.infrastructure.models.interview_session_model import (
    InterviewSessionModel,
)
from src.shared.domain.datetime_utils import utc_now


class InterviewSessionRepository:
    """Repository for interview session persistence."""

    def __init__(self, db: Session) -> None:
        """Initialize interview session repository."""
        self.db = db

    def save(self, session: InterviewSession) -> None:
        """Execute save operation."""
        existing = (
            self.db.execute(
                select(InterviewSessionModel).where(
                    InterviewSessionModel.id == session.id,
                    InterviewSessionModel.deleted_at.is_(None),
                ),
            )
            .scalars()
            .first()
        )

        if existing:
            existing.mapa_global = session.mapa_global
            existing.bloque_actual = session.bloque_actual
            existing.bloques_completados = session.bloques_completados
            existing.status = session.status.value
            existing.messages_count = session.messages_count
            existing.entity_id = session.entity_id
            existing.updated_at = utc_now()
            flag_modified(existing, "mapa_global")
            flag_modified(existing, "bloques_completados")
        else:
            model = InterviewSessionModel(
                id=session.id,
                tenant_id=session.tenant_id,
                domain=session.domain,
                config_snapshot=session.config_snapshot,
                conversation_id=session.conversation_id,
                mapa_global=session.mapa_global,
                bloque_actual=session.bloque_actual,
                bloques_completados=session.bloques_completados,
                status=session.status.value,
                messages_count=session.messages_count,
                entity_id=session.entity_id,
            )
            self.db.add(model)

    def get_by_id(self, session_id: UUID, tenant_id: UUID) -> InterviewSession | None:
        """Return by id."""
        model = (
            self.db.execute(
                select(InterviewSessionModel).where(
                    InterviewSessionModel.id == session_id,
                    InterviewSessionModel.tenant_id == tenant_id,
                    InterviewSessionModel.deleted_at.is_(None),
                ),
            )
            .scalars()
            .first()
        )
        return self._to_entity(model) if model else None

    def get_active_by_domain(
        self,
        tenant_id: UUID,
        domain: str,
    ) -> InterviewSession | None:
        """Return active by domain."""
        model = (
            self.db.execute(
                select(InterviewSessionModel).where(
                    InterviewSessionModel.tenant_id == tenant_id,
                    InterviewSessionModel.domain == domain,
                    InterviewSessionModel.status == InterviewStatus.ACTIVE.value,
                    InterviewSessionModel.deleted_at.is_(None),
                ),
            )
            .scalars()
            .first()
        )
        return self._to_entity(model) if model else None

    def expire_stale(
        self,
        tenant_id: UUID,
        max_inactive_days: int = 7,
    ) -> int:
        """Mark ACTIVE/PAUSED sessions as ABANDONED if inactive > max_inactive_days.

        Returns the number of sessions expired.
        """
        cutoff = utc_now() - timedelta(days=max_inactive_days)
        result = self.db.execute(
            update(InterviewSessionModel)
            .where(
                InterviewSessionModel.tenant_id == tenant_id,
                InterviewSessionModel.status.in_(
                    [
                        InterviewStatus.ACTIVE.value,
                        InterviewStatus.PAUSED.value,
                    ]
                ),
                InterviewSessionModel.updated_at < cutoff,
                InterviewSessionModel.deleted_at.is_(None),
            )
            .values(
                status=InterviewStatus.ABANDONED.value,
                updated_at=utc_now(),
            )
        )
        self.db.commit()
        return result.rowcount

    def soft_delete(self, session_id: UUID, tenant_id: UUID) -> None:
        """Execute soft delete operation."""
        model = (
            self.db.execute(
                select(InterviewSessionModel).where(
                    InterviewSessionModel.id == session_id,
                    InterviewSessionModel.tenant_id == tenant_id,
                ),
            )
            .scalars()
            .first()
        )
        if model:
            model.deleted_at = utc_now()

    def _to_entity(self, model: InterviewSessionModel) -> InterviewSession:
        return InterviewSession(
            id_=model.id,
            tenant_id=model.tenant_id,
            domain=model.domain,
            config_snapshot=model.config_snapshot,
            conversation_id=model.conversation_id,
            mapa_global=model.mapa_global,
            bloque_actual=model.bloque_actual,
            bloques_completados=model.bloques_completados,
            status=InterviewStatus(model.status),
            messages_count=model.messages_count,
            entity_id=model.entity_id,
        )

"""Repository for InterviewSession persistence."""

from uuid import UUID

from sqlalchemy import select
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
    def __init__(self, db: Session):
        self.db = db

    def save(self, session: InterviewSession) -> None:
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

    def soft_delete(self, session_id: UUID, tenant_id: UUID) -> None:
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

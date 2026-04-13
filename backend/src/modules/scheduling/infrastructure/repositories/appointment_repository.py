from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.modules.scheduling.domain.appointment import Appointment
from src.modules.scheduling.domain.enums import AppointmentStatus
from src.modules.scheduling.infrastructure.models.appointment_model import (
    AppointmentModel,
)


class AppointmentRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def _to_domain(self, model: AppointmentModel) -> Appointment:
        status = AppointmentStatus.SCHEDULED
        if model.status:
            try:
                status = AppointmentStatus(model.status)
            except ValueError:
                status = AppointmentStatus.SCHEDULED

        return Appointment(
            id=model.id,
            tenant_id=model.tenant_id,
            lead_id=model.lead_id,
            summary=model.summary,
            start_time=model.start_time,
            end_time=model.end_time,
            status=status,
            meeting_link=model.meeting_link,
            external_event_id=model.external_event_id,
            metadata_info=model.metadata_info or {},
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    def get_appointments_by_date_range(
        self,
        start: datetime,
        end: datetime,
        tenant_id: UUID,
    ) -> list[Appointment]:
        stmt = (
            select(AppointmentModel)
            .where(
                AppointmentModel.tenant_id == tenant_id,
                AppointmentModel.start_time >= start,
                AppointmentModel.start_time <= end,
            )
            .order_by(AppointmentModel.start_time.asc())
        )
        models = self.db.execute(stmt).scalars().all()
        return [self._to_domain(m) for m in models]

"""Repository for LaunchEdition CRUD operations."""

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from src.modules.offer.domain.launch_edition import (
    EditionStatus,
    LaunchEdition,
)
from src.modules.offer.domain.offer import PricingStructure
from src.modules.offer.infrastructure.models.launch_edition_model import (
    LaunchEditionModel,
)


class LaunchEditionRepository:
    def __init__(self, db: Session):
        self.db = db

    def _to_domain(self, model: LaunchEditionModel) -> LaunchEdition:
        pricing = None
        if model.pricing_override is not None:
            pricing = [PricingStructure(**p) for p in model.pricing_override]

        return LaunchEdition(
            id=model.id,
            offer_id=model.offer_id,
            tenant_id=model.tenant_id,
            edition_name=model.edition_name,
            edition_number=model.edition_number,
            start_date=model.start_date,
            end_date=model.end_date,
            registration_start=model.registration_start,
            registration_end=model.registration_end,
            timezone=model.timezone or "UTC",
            pricing_override=pricing,
            capacity=model.capacity,
            enrollment_count=model.enrollment_count or 0,
            status=EditionStatus(model.status) if model.status else EditionStatus.DRAFT,
            location_override=model.location_override,
            notes=model.notes,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    def get_next_edition_number(self, offer_id: UUID) -> int:
        stmt = select(
            func.coalesce(func.max(LaunchEditionModel.edition_number), 0)
        ).where(
            LaunchEditionModel.offer_id == offer_id,
        )
        result = self.db.execute(stmt).scalar()
        return (result or 0) + 1

    def create(
        self,
        offer_id: UUID,
        tenant_id: UUID,
        start_date,
        edition_name: str | None = None,
        end_date=None,
        registration_start=None,
        registration_end=None,
        timezone: str = "UTC",
        pricing_override: list[PricingStructure] | None = None,
        capacity: int | None = None,
        location_override: dict | None = None,
        notes: str | None = None,
    ) -> LaunchEdition:
        edition_number = self.get_next_edition_number(offer_id)
        if not edition_name:
            edition_name = f"Edición #{edition_number}"

        pricing_json = None
        if pricing_override is not None:
            pricing_json = [p.model_dump(mode="json") for p in pricing_override]

        model = LaunchEditionModel(
            offer_id=offer_id,
            tenant_id=tenant_id,
            edition_name=edition_name,
            edition_number=edition_number,
            start_date=start_date,
            end_date=end_date,
            registration_start=registration_start,
            registration_end=registration_end,
            timezone=timezone,
            pricing_override=pricing_json,
            capacity=capacity,
            enrollment_count=0,
            status=EditionStatus.DRAFT.value,
            location_override=location_override,
            notes=notes,
        )
        self.db.add(model)
        self.db.flush()
        self.db.refresh(model)
        return self._to_domain(model)

    def get_by_id(self, edition_id: UUID, tenant_id: UUID) -> LaunchEdition | None:
        stmt = select(LaunchEditionModel).where(
            LaunchEditionModel.id == edition_id,
            LaunchEditionModel.tenant_id == tenant_id,
        )
        model = self.db.execute(stmt).scalar_one_or_none()
        return self._to_domain(model) if model else None

    def list_by_offer(self, offer_id: UUID, tenant_id: UUID) -> list[LaunchEdition]:
        stmt = (
            select(LaunchEditionModel)
            .where(
                LaunchEditionModel.offer_id == offer_id,
                LaunchEditionModel.tenant_id == tenant_id,
                LaunchEditionModel.status != EditionStatus.CANCELLED.value,
            )
            .order_by(LaunchEditionModel.start_date.desc())
        )
        models = self.db.execute(stmt).scalars().all()
        return [self._to_domain(m) for m in models]

    def update(self, edition_id: UUID, tenant_id: UUID, data: dict) -> LaunchEdition:
        stmt = select(LaunchEditionModel).where(
            LaunchEditionModel.id == edition_id,
            LaunchEditionModel.tenant_id == tenant_id,
        )
        model = self.db.execute(stmt).scalar_one_or_none()
        if not model:
            msg = f"Edition {edition_id} not found"
            raise ValueError(msg)

        for key, value in data.items():
            if (
                key == "pricing_override"
                and value is not None
                and isinstance(value, list)
                and value
                and hasattr(value[0], "model_dump")
            ):
                value = [p.model_dump(mode="json") for p in value]
            if hasattr(model, key):
                setattr(model, key, value)

        self.db.flush()
        self.db.refresh(model)
        return self._to_domain(model)

    def soft_delete(self, edition_id: UUID, tenant_id: UUID) -> None:
        self.update(edition_id, tenant_id, {"status": EditionStatus.CANCELLED.value})

"""CRM lead metrics repository."""

import uuid

from luana_core_crm.domain.lead import Lead
from luana_core_crm.infrastructure.models.customer_model import (
    CustomerProfileModel as CustomerProfile,
)
from luana_core_crm.infrastructure.models.lead_model import LeadModel
from luana_core_platform.core.base_repository import BaseRepository
from luana_core_platform.core.context import get_tenant_id
from sqlalchemy import desc, func, or_, select
from sqlalchemy.orm import joinedload

# Maps channel name to the LeadModel attribute that stores channel-specific IDs
_CHANNEL_ATTR_MAP: dict[str, str] = {
    "telegram": "telegram_id",
    "whatsapp": "whatsapp_id",
    "instagram": "instagram_id",
    "tiktok": "tiktok_id",
    "api": "api_id",
    "manychat": "api_id",
    "web": "api_id",
}


class LeadRepository(BaseRepository):
    """Repository for lead persistence."""

    @staticmethod
    def _set_channel_id(
        lead_orm: LeadModel,
        channel: str | None,
        channel_user_id: str | None,
    ) -> None:
        """Set the channel-specific ID attribute on a LeadModel instance."""
        if not channel or not channel_user_id:
            return
        attr = _CHANNEL_ATTR_MAP.get(channel)
        if attr:
            setattr(lead_orm, attr, channel_user_id)

    def count_total(self, tenant_id: uuid.UUID) -> int:
        """Cuenta el total de leads activos."""
        return (
            self.db.execute(
                select(func.count(LeadModel.id)).where(
                    LeadModel.tenant_id == tenant_id,
                    LeadModel.is_blacklisted.is_(False),
                ),
            ).scalar()
            or 0
        )

    def count_qualified(self, tenant_id: uuid.UUID) -> int:
        """Cuenta leads calificados (score alto o no fríos)."""
        return (
            self.db.execute(
                select(func.count(LeadModel.id)).where(
                    LeadModel.tenant_id == tenant_id,
                    LeadModel.is_blacklisted.is_(False),
                    or_(LeadModel.fit_score >= 50, LeadModel.temperature != "COLD"),
                ),
            ).scalar()
            or 0
        )

    def get_by_id(self, lead_id: str | uuid.UUID) -> Lead | None:
        """Robustly fetch lead by ID, handling string/UUID conversion."""
        if isinstance(lead_id, str):
            try:
                lead_id = uuid.UUID(lead_id)
            except ValueError:
                return None

        stmt = select(LeadModel).options(joinedload(LeadModel.customer)).where(LeadModel.id == lead_id)
        tenant_id = get_tenant_id()
        if tenant_id:
            stmt = stmt.where(LeadModel.tenant_id == tenant_id)

        lead_orm = self.db.execute(stmt).scalars().first()

        if lead_orm:
            return Lead.model_validate(lead_orm)
        return None

    def get_by_channel_id(self, channel: str, user_id: str) -> Lead | None:
        """Find a lead by their channel-specific ID (Telegram, WhatsApp, etc)."""
        attr = _CHANNEL_ATTR_MAP.get(channel)
        if not attr:
            return None
        channel_filter = getattr(LeadModel, attr) == user_id

        stmt = select(LeadModel).options(joinedload(LeadModel.customer)).where(channel_filter)
        tenant_id = get_tenant_id()
        if tenant_id:
            stmt = stmt.where(LeadModel.tenant_id == tenant_id)

        lead_orm = self.db.execute(stmt).scalars().first()
        if lead_orm:
            return Lead.model_validate(lead_orm)
        return None

    def get_active_lead(self, customer_id: uuid.UUID) -> Lead | None:
        """Obtiene el lead activo (más reciente) para un cliente."""
        stmt = (
            select(LeadModel)
            .where(
                LeadModel.customer_id == customer_id,
                LeadModel.is_blacklisted.is_(False),
            )
            .order_by(desc(LeadModel.created_at))
        )
        tenant_id = get_tenant_id()
        if tenant_id:
            stmt = stmt.where(LeadModel.tenant_id == tenant_id)

        lead_orm = self.db.execute(stmt).scalars().first()

        if lead_orm:
            return Lead.model_validate(lead_orm)
        return None

    def create_lead(
        self,
        full_name: str | None = None,
        channel: str | None = None,
        channel_user_id: str | None = None,
        customer_id: uuid.UUID | None = None,
    ) -> Lead:
        """Create a new Lead from a channel interaction.

        Return existing lead if one exists for this channel_user_id (linking customer if needed).
        Create a Lead linked to the customer_id if provided, otherwise create a new CustomerProfile first.
        """
        # First, check if a lead already exists for this channel ID
        if channel and channel_user_id:
            existing = self.get_by_channel_id(channel, channel_user_id)
            if existing:
                # If customer changed, update the link
                if customer_id and str(existing.customer_id) != str(customer_id):
                    lead_orm = (
                        self.db.execute(
                            select(LeadModel).where(LeadModel.id == existing.id),
                        )
                        .scalars()
                        .first()
                    )
                    if lead_orm:
                        lead_orm.customer_id = customer_id
                        self.db.commit()
                        self.db.refresh(lead_orm)
                        return Lead.model_validate(lead_orm)
                return existing

        if customer_id:
            lead_orm = LeadModel(customer_id=customer_id)

            if channel and channel_user_id:
                self._set_channel_id(lead_orm, channel, channel_user_id)

            self._set_tenant(lead_orm)
            self.db.add(lead_orm)
            self.db.commit()
            self.db.refresh(lead_orm)
            return Lead.model_validate(lead_orm)

        if not full_name:
            msg = "full_name is required when creating a new customer lead"
            raise ValueError(msg)

        # Create Customer Profile first
        customer = CustomerProfile(full_name=full_name)
        self.db.add(customer)
        self.db.flush()  # Get ID

        lead_orm = LeadModel(customer_id=customer.id)

        self._set_channel_id(lead_orm, channel, channel_user_id)

        self._set_tenant(lead_orm)
        # Also set tenant for customer if needed, usually linked
        if hasattr(lead_orm, "tenant_id") and lead_orm.tenant_id:
            customer.tenant_id = lead_orm.tenant_id

        self.db.add(lead_orm)
        self.db.commit()
        self.db.refresh(lead_orm)

        return Lead.model_validate(lead_orm)

    def update_profile(
        self,
        lead_id: str | uuid.UUID,
        psychographics_update: dict,
    ) -> Lead | None:
        """Update profile."""
        # Fetch ORM object to update
        if isinstance(lead_id, str):
            try:
                lead_id = uuid.UUID(lead_id)
            except ValueError:
                return None

        lead_orm = (
            self.db.execute(
                select(LeadModel).options(joinedload(LeadModel.customer)).where(LeadModel.id == lead_id),
            )
            .scalars()
            .first()
        )

        if lead_orm:
            current = dict(lead_orm.profile_data) if lead_orm.profile_data else {}

            # Smart merge for lists
            for k, v in psychographics_update.items():
                if isinstance(v, list) and k in current and isinstance(current[k], list):
                    current[k] = list(set(current[k] + v))
                else:
                    current[k] = v

            lead_orm.profile_data = current

            # Update Customer Profile if relevant fields exist
            if lead_orm.customer:
                if psychographics_update.get("email"):
                    lead_orm.customer.primary_email = psychographics_update["email"]
                if psychographics_update.get("phone"):
                    lead_orm.customer.primary_phone = psychographics_update["phone"]
                if psychographics_update.get("name"):
                    lead_orm.customer.full_name = psychographics_update["name"]
                elif psychographics_update.get("full_name"):
                    lead_orm.customer.full_name = psychographics_update["full_name"]

            self.db.commit()
            self.db.refresh(lead_orm)
            return Lead.model_validate(lead_orm)

        return None

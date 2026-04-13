from uuid import UUID

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from src.modules.crm.domain.lead import Lead, UserProfile
from src.modules.crm.infrastructure.models.lead_model import LeadModel


class LeadRepository:
    def __init__(self, db: Session):
        self.db = db

    def _to_domain(self, model: LeadModel) -> Lead:
        # Convert JSON profile data back to Domain Object
        profile = UserProfile(**(model.profile_data or {}))

        return Lead(
            id=model.id,
            tenant_id=model.tenant_id,
            customer_id=model.customer_id,
            telegram_id=model.telegram_id,
            whatsapp_id=model.whatsapp_id,
            instagram_id=model.instagram_id,
            tiktok_id=model.tiktok_id,
            api_id=model.api_id,
            profile_data=profile,
            fit_score=model.fit_score or 0,
            intent_score=model.intent_score or 0,
            temperature=model.temperature or "COLD",
            is_blacklisted=model.is_blacklisted,
            last_interaction_date=model.last_interaction_date,
            next_scheduled_action=model.next_scheduled_action,
            conversation_summary=model.conversation_summary,
            key_objections_history=model.key_objections_history or [],
            style_profile=model.style_profile,
            custom_system_instruction=model.custom_system_instruction,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    def _to_model(self, lead: Lead) -> LeadModel:
        return LeadModel(
            id=lead.id,
            tenant_id=lead.tenant_id,
            customer_id=lead.customer_id,
            telegram_id=lead.telegram_id,
            whatsapp_id=lead.whatsapp_id,
            instagram_id=lead.instagram_id,
            tiktok_id=lead.tiktok_id,
            api_id=lead.api_id,
            profile_data=lead.profile_data.model_dump(mode="json"),
            fit_score=lead.fit_score,
            intent_score=lead.intent_score,
            temperature=lead.temperature,
            is_blacklisted=lead.is_blacklisted,
            last_interaction_date=lead.last_interaction_date,
            next_scheduled_action=lead.next_scheduled_action,
            conversation_summary=lead.conversation_summary,
            key_objections_history=lead.key_objections_history,
            style_profile=lead.style_profile,
            custom_system_instruction=lead.custom_system_instruction,
        )

    def get_by_id(self, lead_id: UUID) -> Lead | None:
        model = (
            self.db.execute(select(LeadModel).where(LeadModel.id == lead_id))
            .scalars()
            .first()
        )
        if model:
            return self._to_domain(model)
        return None

    def get_by_channel_id(
        self,
        channel: str,
        channel_id: str,
        tenant_id: UUID,
    ) -> Lead | None:
        """
        Generic fetch by channel ID (telegram_id, whatsapp_id, etc.)
        """
        stmt = select(LeadModel).where(LeadModel.tenant_id == tenant_id)

        if channel == "telegram":
            stmt = stmt.where(LeadModel.telegram_id == channel_id)
        elif channel == "whatsapp":
            stmt = stmt.where(LeadModel.whatsapp_id == channel_id)
        elif channel == "instagram":
            stmt = stmt.where(LeadModel.instagram_id == channel_id)
        elif channel == "api":
            stmt = stmt.where(LeadModel.api_id == channel_id)
        else:
            return None

        model = self.db.execute(stmt).scalars().first()
        if model:
            return self._to_domain(model)
        return None

    def get_high_intent_leads(
        self,
        tenant_id: UUID,
        min_score: int = 50,
        limit: int = 20,
    ) -> list[Lead]:
        models = (
            self.db.execute(
                select(LeadModel)
                .where(
                    LeadModel.tenant_id == tenant_id,
                    LeadModel.intent_score >= min_score,
                    LeadModel.is_blacklisted.is_(False),
                )
                .order_by(desc(LeadModel.intent_score))
                .limit(limit),
            )
            .scalars()
            .all()
        )
        return [self._to_domain(m) for m in models]

    def create(self, lead: Lead) -> Lead:
        model = self._to_model(lead)
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return self._to_domain(model)

    def update(self, lead: Lead) -> Lead:
        model = (
            self.db.execute(select(LeadModel).where(LeadModel.id == lead.id))
            .scalars()
            .first()
        )
        if not model:
            msg = "Lead not found"
            raise ValueError(msg)

        # Update fields
        # Note: A smarter merge/update strategy is needed for production to avoid overwriting race conditions
        # For now, explicit field update
        model.profile_data = lead.profile_data.model_dump(mode="json")
        model.fit_score = lead.fit_score
        model.intent_score = lead.intent_score
        model.temperature = lead.temperature
        model.last_interaction_date = lead.last_interaction_date
        model.conversation_summary = lead.conversation_summary
        model.key_objections_history = lead.key_objections_history
        model.style_profile = lead.style_profile
        model.custom_system_instruction = lead.custom_system_instruction

        self.db.commit()
        self.db.refresh(model)
        return self._to_domain(model)

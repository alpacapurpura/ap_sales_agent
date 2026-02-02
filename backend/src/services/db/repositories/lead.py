from typing import Optional
from src.services.db.models.lead import Lead
from .base import BaseRepository
import uuid

class LeadRepository(BaseRepository):
    def get_by_id(self, lead_id: str | uuid.UUID) -> Optional[Lead]:
        """
        Robustly fetch lead by ID, handling string/UUID conversion.
        """
        if isinstance(lead_id, str):
            try:
                lead_id = uuid.UUID(lead_id)
            except ValueError:
                return None
                
        query = self.db.query(Lead).filter(Lead.id == lead_id)
        query = self._apply_tenant_filter(query, Lead)
        return query.first()

    def get_by_channel_id(self, channel: str, user_id: str) -> Optional[Lead]:
        """
        Find a lead by their channel-specific ID (Telegram, WhatsApp, etc).
        """
        query = self.db.query(Lead)
        
        if channel == "telegram":
            query = query.filter(Lead.telegram_id == user_id)
        elif channel == "whatsapp":
            query = query.filter(Lead.whatsapp_id == user_id)
        elif channel == "instagram":
            query = query.filter(Lead.instagram_id == user_id)
        elif channel == "tiktok":
            query = query.filter(Lead.tiktok_id == user_id)
        else:
            return None
            
        # We might want to apply tenant filter here too, but usually 
        # channel IDs are unique globally or we want to find the lead first 
        # and then check tenant if needed. However, given the multi-tenant context,
        # if a lead belongs to a specific tenant, we should respect that context if set.
        # But often webhook comes without tenant context initially.
        # For now, let's trust the unique constraint on channel IDs or apply filter if context exists.
        query = self._apply_tenant_filter(query, Lead)
        
        return query.first()

    def create_lead(self, full_name: str, channel: str, channel_user_id: str) -> Lead:
        """
        Create a new Lead from a channel interaction.
        """
        lead = Lead(full_name=full_name)
        
        if channel == "telegram":
            lead.telegram_id = channel_user_id
        elif channel == "whatsapp":
            lead.whatsapp_id = channel_user_id
        elif channel == "instagram":
            lead.instagram_id = channel_user_id
        elif channel == "tiktok":
            lead.tiktok_id = channel_user_id
        elif channel in ["api", "manychat", "web"]:
            lead.api_id = channel_user_id
            
        self._set_tenant(lead)
        self.db.add(lead)
        self.db.commit()
        self.db.refresh(lead)
        return lead

    def update_profile(self, lead_id, psychographics_update: dict) -> Optional[Lead]:
        lead = self.get_by_id(lead_id)
        if lead:
            current = dict(lead.profile_data) if lead.profile_data else {}
            
            # Smart merge for lists
            for k, v in psychographics_update.items():
                if isinstance(v, list) and k in current and isinstance(current[k], list):
                    current[k] = list(set(current[k] + v))
                else:
                    current[k] = v
                    
            lead.profile_data = current
            
            if "email" in psychographics_update and psychographics_update["email"]:
                lead.email = psychographics_update["email"]
            if "phone" in psychographics_update and psychographics_update["phone"]:
                lead.phone = psychographics_update["phone"]
                
            self.db.commit()
            self.db.refresh(lead)
        return lead

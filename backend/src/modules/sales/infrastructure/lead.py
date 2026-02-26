from typing import Optional
from sqlalchemy.orm import joinedload
from sqlalchemy import desc, func
from src.modules.sales.domain.lead import Lead
from src.modules.sales.infrastructure.models.lead_model import LeadModel
from src.modules.marketing.infrastructure.models.customer import CustomerProfile
from src.shared.infrastructure.db.base import BaseRepository
import uuid

class LeadRepository(BaseRepository):
    def count_total(self, tenant_id: uuid.UUID) -> int:
        """
        Cuenta el total de leads activos.
        """
        return self.db.query(func.count(LeadModel.id)).filter(
            LeadModel.tenant_id == tenant_id,
            LeadModel.is_blacklisted == False
        ).scalar() or 0

    def count_qualified(self, tenant_id: uuid.UUID) -> int:
        """
        Cuenta leads calificados (score alto o no fríos).
        """
        return self.db.query(func.count(LeadModel.id)).filter(
            LeadModel.tenant_id == tenant_id,
            LeadModel.is_blacklisted == False,
            (LeadModel.fit_score >= 50) | (LeadModel.temperature != 'COLD')
        ).scalar() or 0

    def get_by_id(self, lead_id: str | uuid.UUID) -> Optional[Lead]:
        """
        Robustly fetch lead by ID, handling string/UUID conversion.
        """
        if isinstance(lead_id, str):
            try:
                lead_id = uuid.UUID(lead_id)
            except ValueError:
                return None
                
        lead_orm = self.db.query(LeadModel).options(joinedload(LeadModel.customer)).filter(LeadModel.id == lead_id)
        lead_orm = self._apply_tenant_filter(lead_orm, LeadModel).first()
        
        if lead_orm:
            return Lead.model_validate(lead_orm)
        return None

    def get_by_channel_id(self, channel: str, user_id: str) -> Optional[Lead]:
        """
        Find a lead by their channel-specific ID (Telegram, WhatsApp, etc).
        """
        query = self.db.query(LeadModel).options(joinedload(LeadModel.customer))
        
        if channel == "telegram":
            query = query.filter(LeadModel.telegram_id == user_id)
        elif channel == "whatsapp":
            query = query.filter(LeadModel.whatsapp_id == user_id)
        elif channel == "instagram":
            query = query.filter(LeadModel.instagram_id == user_id)
        elif channel == "tiktok":
            query = query.filter(LeadModel.tiktok_id == user_id)
        else:
            return None
            
        # Apply tenant filter if needed
        query = self._apply_tenant_filter(query, LeadModel)
        
        lead_orm = query.first()
        if lead_orm:
            return Lead.model_validate(lead_orm)
        return None

    def get_active_lead(self, customer_id: uuid.UUID) -> Optional[Lead]:
        """
        Obtiene el lead activo (más reciente) para un cliente.
        """
        query = self.db.query(LeadModel).filter(
            LeadModel.customer_id == customer_id,
            LeadModel.is_blacklisted == False
        ).order_by(desc(LeadModel.created_at))
        
        # Aplicar filtro de tenant
        query = self._apply_tenant_filter(query, LeadModel)
        
        lead_orm = query.first()
        
        if lead_orm:
            return Lead.model_validate(lead_orm)
        return None

    def create_lead(self, full_name: Optional[str] = None, channel: Optional[str] = None, channel_user_id: Optional[str] = None, customer_id: Optional[uuid.UUID] = None) -> Lead:
        """
        Create a new Lead from a channel interaction.
        If customer_id is provided, creates a Lead linked to that customer.
        Otherwise creates a new CustomerProfile first.
        """
        
        if customer_id:
             # Link to existing customer
             lead_orm = LeadModel(customer_id=customer_id)
             
             # Set channel ID if provided, otherwise keep them null as requested
             if channel and channel_user_id:
                if channel == "telegram":
                    lead_orm.telegram_id = channel_user_id
                elif channel == "whatsapp":
                    lead_orm.whatsapp_id = channel_user_id
                elif channel == "instagram":
                    lead_orm.instagram_id = channel_user_id
                elif channel == "tiktok":
                    lead_orm.tiktok_id = channel_user_id
                elif channel in ["api", "manychat", "web"]:
                    lead_orm.api_id = channel_user_id
             
             self._set_tenant(lead_orm)
             self.db.add(lead_orm)
             self.db.commit()
             self.db.refresh(lead_orm)
             return Lead.model_validate(lead_orm)

        if not full_name:
             raise ValueError("full_name is required when creating a new customer lead")

        # Create Customer Profile first
        customer = CustomerProfile(
            full_name=full_name
        )
        self.db.add(customer)
        self.db.flush()  # Get ID

        lead_orm = LeadModel(customer_id=customer.id)
        
        if channel == "telegram":
            lead_orm.telegram_id = channel_user_id
        elif channel == "whatsapp":
            lead_orm.whatsapp_id = channel_user_id
        elif channel == "instagram":
            lead_orm.instagram_id = channel_user_id
        elif channel == "tiktok":
            lead_orm.tiktok_id = channel_user_id
        elif channel in ["api", "manychat", "web"]:
            lead_orm.api_id = channel_user_id
            
        self._set_tenant(lead_orm)
        # Also set tenant for customer if needed, usually linked
        if hasattr(lead_orm, 'tenant_id') and lead_orm.tenant_id:
             customer.tenant_id = lead_orm.tenant_id

        self.db.add(lead_orm)
        self.db.commit()
        self.db.refresh(lead_orm)
        
        return Lead.model_validate(lead_orm)

    def update_profile(self, lead_id, psychographics_update: dict) -> Optional[Lead]:
        # Fetch ORM object to update
        if isinstance(lead_id, str):
             try:
                lead_id = uuid.UUID(lead_id)
             except ValueError:
                return None

        lead_orm = self.db.query(LeadModel).options(joinedload(LeadModel.customer)).filter(LeadModel.id == lead_id).first()
        
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
                if "email" in psychographics_update and psychographics_update["email"]:
                    lead_orm.customer.primary_email = psychographics_update["email"]
                if "phone" in psychographics_update and psychographics_update["phone"]:
                    lead_orm.customer.primary_phone = psychographics_update["phone"]
                if "name" in psychographics_update and psychographics_update["name"]:
                    lead_orm.customer.full_name = psychographics_update["name"]
                elif "full_name" in psychographics_update and psychographics_update["full_name"]:
                    lead_orm.customer.full_name = psychographics_update["full_name"]
                
            self.db.commit()
            self.db.refresh(lead_orm)
            return Lead.model_validate(lead_orm)
            
        return None

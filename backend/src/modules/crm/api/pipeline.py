from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session, joinedload
from datetime import datetime, timedelta, timezone
from typing import List, Literal, Optional
from pydantic import BaseModel, Field
from uuid import UUID

from src.core.database import get_db
from src.modules.iam.api.dependencies import get_current_user
from src.modules.iam.domain.user import User

from src.modules.crm.infrastructure.repositories.lead_repository import LeadRepository
from src.modules.crm.infrastructure.models.lead_model import LeadModel

router = APIRouter(tags=["CRM - Pipeline"])

# --- Response Models ---
class PipelineItem(BaseModel):
    id: UUID
    full_name: Optional[str]
    intent_score: int
    temperature: str
    last_interaction: Optional[datetime]
    channel: Optional[str]
    avatar_url: Optional[str] = None

# --- Endpoints ---

@router.get("/pipeline", response_model=List[PipelineItem])
async def get_pipeline(
    min_score: int = 50,
    limit: int = 20,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    repo = LeadRepository(db)
    # TODO: Implement proper get_high_intent_leads with filters
    # For now, we will return all leads for the tenant to unblock the frontend
    # leads = repo.get_high_intent_leads(user.tenant_id, min_score, limit)
    
    # Fallback to simple query until repo method is robust
    leads_orm = db.query(LeadModel).options(
        joinedload(LeadModel.customer)
    ).filter(
        LeadModel.tenant_id == user.tenant_id,
        LeadModel.is_blacklisted == False
    ).limit(limit).all()
    
    # Manual mapping to avoid repository complexity for now
    results = []
    for l in leads_orm:
        # Try to resolve name from Customer Profile (SSOT), then fallback to Lead profile_data
        customer_name = l.customer.full_name if l.customer else None
        
        profile = l.profile_data or {}
        name = customer_name or profile.get('full_name') or profile.get('name') or "Unknown Lead"
        
        results.append(PipelineItem(
            id=l.id,
            full_name=name,
            intent_score=l.intent_score or 0,
            temperature=l.temperature or "COLD",
            last_interaction=l.last_interaction_date,
            channel="Unknown"
        ))
    return results

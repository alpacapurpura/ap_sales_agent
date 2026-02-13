from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import structlog

from src.services.database import get_db
from src.api.dependencies import get_current_user
from src.services.db.models.user import User
from src.services.db.models.lead import Lead

router = APIRouter(prefix="/leads", tags=["leads"])
logger = structlog.get_logger()

@router.get("/search")
async def search_leads(
    q: str = Query(..., min_length=2),
    limit: int = 10,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """
    Search leads by name or email.
    """
    # Simple search on full_name or email
    leads = db.query(Lead).filter(
        Lead.tenant_id == user.tenant_id,
        (Lead.full_name.ilike(f"%{q}%")) | (Lead.email.ilike(f"%{q}%"))
    ).limit(limit).all()
    
    return [
        {
            "id": str(lead.id),
            "full_name": lead.full_name,
            "email": lead.email,
            "phone": lead.phone
        }
        for lead in leads
    ]

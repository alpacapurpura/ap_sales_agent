from typing import Annotated
from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.modules.crm.application.services.lead_service import LeadService
from src.modules.crm.domain.lead import Lead
from src.modules.iam.api.dependencies import get_current_user
from src.modules.iam.domain.user import User

router = APIRouter(tags=["leads"])
logger = structlog.get_logger()


@router.get("/search", response_model=list[Lead])
async def search_leads(
    q: Annotated[str, Query(min_length=2)],
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    limit: int = 10,
):
    """
    Search leads by name or email.
    TODO: Implement search logic in LeadService/Repository.
    For now returning empty list or placeholder.
    """
    return []


@router.get("/{lead_id}", response_model=Lead)
async def get_lead(
    lead_id: str,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    """
    Get a specific lead by ID.
    """
    service = LeadService(db)
    try:
        lead = service.get_lead(UUID(lead_id))
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid UUID format") from None

    if not lead or str(lead.tenant_id) != str(user.tenant_id):
        raise HTTPException(status_code=404, detail="Lead not found")

    return lead

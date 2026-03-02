from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import Dict, Any
from src.core.database import get_db
from src.modules.iam.api.dependencies import get_current_user
from src.modules.iam.domain.user import User
from src.modules.crm.application.services.customer_service import CustomerService
from src.modules.crm.domain.customer import CustomerProfile

router = APIRouter()

@router.post("/identify", response_model=CustomerProfile)
async def identify_customer(
    payload: Dict[str, Any],
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """
    Identify a customer (create or update profile).
    Payload should contain 'traits' and optional 'userId'.
    """
    service = CustomerService(db)
    
    traits = payload.get("traits", {})
    user_id = payload.get("userId")
    
    identities = {}
    if user_id:
        identities["user_id"] = user_id
        
    profile = service.identify(user.tenant_id, traits, identities)
    return profile

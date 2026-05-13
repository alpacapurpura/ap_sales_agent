"""CRM CDP API endpoints."""

from typing import Annotated, Any

from fastapi import APIRouter, Depends
from luana_core_crm.application.services.customer_service import CustomerService
from luana_core_crm.domain.customer import CustomerProfile
from luana_core_iam.api.dependencies import get_current_user
from luana_core_iam.domain.user import User
from luana_core_platform.core.database import get_db
from sqlalchemy.orm import Session

router = APIRouter()


@router.post("/identify")
async def identify_customer(
    payload: dict[str, Any],
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> CustomerProfile:
    """Identify a customer (create or update profile).

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

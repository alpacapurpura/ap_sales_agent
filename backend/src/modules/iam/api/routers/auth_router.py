"""Auth Router API endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends
from luana_core_iam.api.dependencies import get_user_from_token
from luana_core_iam.api.dto.users import TenantSchema
from luana_core_iam.application.services.user_service import UserService
from luana_core_iam.domain.user import User
from luana_core_platform.core.database import get_db
from sqlalchemy.orm import Session

router = APIRouter()


@router.get("/me")
async def get_current_user_profile(user: Annotated[User, Depends(get_user_from_token)]) -> User:
    """Get current user profile based on Clerk Token."""
    return user


@router.get("/me/tenants")
async def get_my_tenants(
    user: Annotated[User, Depends(get_user_from_token)],
    db: Annotated[Session, Depends(get_db)],
) -> list[TenantSchema]:
    """List all tenants the current user belongs to.

    Used for the organization switcher in frontend.
    """
    service = UserService(db)
    return service.get_user_tenants(user.id)

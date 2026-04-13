from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.modules.iam.api.dependencies import get_user_from_token
from src.modules.iam.api.dto.users import TenantSchema
from src.modules.iam.application.services.user_service import UserService
from src.modules.iam.domain.user import User

router = APIRouter()


@router.get("/me", response_model=User)
async def get_current_user_profile(user: User = Depends(get_user_from_token)):
    """
    Get current user profile based on Clerk Token.
    """
    return user


@router.get("/me/tenants", response_model=list[TenantSchema])
async def get_my_tenants(
    user: User = Depends(get_user_from_token),
    db: Session = Depends(get_db),
):
    """
    List all tenants the current user belongs to.
    Used for the organization switcher in frontend.
    """
    service = UserService(db)
    return service.get_user_tenants(user.id)

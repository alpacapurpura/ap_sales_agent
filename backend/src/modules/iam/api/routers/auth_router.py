from fastapi import APIRouter, Depends, HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session
from src.shared.infrastructure.db.database import get_db
from src.modules.iam.application.auth import verify_clerk_token
from src.modules.iam.infrastructure.repositories.user_repository import UserRepository
from src.modules.iam.domain.user import User

router = APIRouter()
security = HTTPBearer()

@router.get("/me", response_model=User)
async def get_current_user_profile(
    credentials: HTTPAuthorizationCredentials = Security(security),
    db: Session = Depends(get_db)
):
    """
    Get current user profile based on Clerk Token.
    """
    payload = verify_clerk_token(credentials)
    clerk_id = payload.get("sub")
    if not clerk_id:
        raise HTTPException(status_code=401, detail="Invalid Token Payload")
    
    repo = UserRepository(db)
    user = repo.get_by_clerk_id(clerk_id)
    
    if not user:
        # Auto-provisioning could happen here if desired, 
        # but for now we return 404 or 403
        raise HTTPException(status_code=404, detail="User not found in system")
        
    return user

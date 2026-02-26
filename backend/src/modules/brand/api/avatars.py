from fastapi import APIRouter, HTTPException, Depends
from typing import List
from sqlalchemy.orm import Session
from src.shared.infrastructure.db.database import get_db
from src.modules.iam.domain.user import User
from src.modules.iam.api.dependencies import get_current_user
from src.modules.brand.api.dto.avatars import AvatarCreate, AvatarResponse
from src.modules.brand.infrastructure.repositories.avatar_repository import AvatarRepository
from src.modules.brand.domain import Avatar
import uuid

router = APIRouter()

@router.get("/", response_model=List[AvatarResponse])
async def list_avatars(
    scope: str = "GLOBAL", 
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    repo = AvatarRepository(db)
    # TODO: Add scope filtering in Repo
    avatars = repo.get_by_tenant(user.tenant_id)
    # Filter by scope in memory for now if not in repo
    return [a for a in avatars if a.scope == scope]

@router.post("/", response_model=AvatarResponse)
async def create_avatar(
    avatar_dto: AvatarCreate, 
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    repo = AvatarRepository(db)
    
    new_avatar = Avatar(
        id=uuid.uuid4(),
        tenant_id=user.tenant_id,
        user_id=user.id,
        name=avatar_dto.name,
        scope=avatar_dto.scope,
        icp_description=avatar_dto.icp_description,
        anti_avatar=avatar_dto.anti_avatar,
        voice_tone_config=avatar_dto.voice_tone_config,
        is_default=False
    )
    
    created = repo.create(new_avatar)
    return created

@router.get("/{avatar_id}", response_model=AvatarResponse)
async def get_avatar(
    avatar_id: str, 
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    repo = AvatarRepository(db)
    avatar = repo.get_by_id(uuid.UUID(avatar_id))
    
    if not avatar or str(avatar.tenant_id) != str(user.tenant_id):
        raise HTTPException(status_code=404, detail="Avatar not found")
    return avatar

# TODO: Implement update and delete in Repo and Router

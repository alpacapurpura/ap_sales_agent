from fastapi import APIRouter, HTTPException, Depends
from typing import List
from sqlalchemy.orm import Session
from src.core.database import get_db
from src.modules.iam.domain.user import User
from src.modules.iam.api.dependencies import get_current_user
from src.modules.brand.api.dto.avatars import AvatarCreate, AvatarResponse, AvatarUpdate
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
    # Scope filtering moved to Repo
    return repo.get_by_tenant(user.tenant_id, scope=scope)

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

@router.patch("/{avatar_id}", response_model=AvatarResponse)
async def update_avatar(
    avatar_id: str,
    avatar_update: AvatarUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    repo = AvatarRepository(db)
    # Verify ownership first
    existing = repo.get_by_id(uuid.UUID(avatar_id))
    if not existing or str(existing.tenant_id) != str(user.tenant_id):
        raise HTTPException(status_code=404, detail="Avatar not found")
    
    # Exclude unset fields from update
    update_data = avatar_update.model_dump(exclude_unset=True)
    updated = repo.update(uuid.UUID(avatar_id), update_data)
    
    if not updated:
         raise HTTPException(status_code=404, detail="Avatar not found")
         
    return updated

@router.delete("/{avatar_id}", status_code=204)
async def delete_avatar(
    avatar_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    repo = AvatarRepository(db)
    # Verify ownership first
    existing = repo.get_by_id(uuid.UUID(avatar_id))
    if not existing or str(existing.tenant_id) != str(user.tenant_id):
        raise HTTPException(status_code=404, detail="Avatar not found")
        
    success = repo.delete(uuid.UUID(avatar_id))
    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete avatar")
    
    return None

@router.post("/{avatar_id}/set-default", response_model=AvatarResponse)
async def set_default_avatar(
    avatar_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    repo = AvatarRepository(db)
    # Verify ownership first
    existing = repo.get_by_id(uuid.UUID(avatar_id))
    if not existing or str(existing.tenant_id) != str(user.tenant_id):
        raise HTTPException(status_code=404, detail="Avatar not found")
    
    if not user.tenant_id:
        raise HTTPException(status_code=400, detail="User has no tenant")
        
    updated = repo.set_global_default(user.tenant_id, uuid.UUID(avatar_id))
    if not updated:
        raise HTTPException(status_code=500, detail="Failed to set default avatar")
        
    return updated

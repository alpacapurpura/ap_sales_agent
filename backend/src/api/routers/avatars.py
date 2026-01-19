from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, ConfigDict
from typing import Optional, Dict, Any, List
import uuid
from src.services.db.repositories.avatar import AvatarRepository
from src.services.database import SessionLocal

router = APIRouter()

def get_avatar_repo():
    db = SessionLocal()
    repo = AvatarRepository(db)
    try:
        yield repo
    finally:
        repo.close()

# Pydantic Models
class AvatarBase(BaseModel):
    name: str
    icp_description: Optional[str] = ""
    anti_avatar: Optional[str] = ""
    voice_tone_config: Optional[Dict[str, Any]] = {}
    scope: Optional[str] = "GLOBAL"

class AvatarCreate(AvatarBase):
    pass

class AvatarUpdate(BaseModel):
    name: Optional[str] = None
    icp_description: Optional[str] = None
    anti_avatar: Optional[str] = None
    voice_tone_config: Optional[Dict[str, Any]] = None
    scope: Optional[str] = None

class AvatarResponse(AvatarBase):
    id: uuid.UUID
    is_default: bool
    created_at: Any # datetime

    model_config = ConfigDict(from_attributes=True)

# Endpoints

@router.get("/", response_model=List[AvatarResponse])
async def list_avatars(scope: str = "GLOBAL", repo: AvatarRepository = Depends(get_avatar_repo)):
    return repo.list_avatars(scope=scope)

@router.post("/", response_model=AvatarResponse)
async def create_avatar(avatar: AvatarCreate, repo: AvatarRepository = Depends(get_avatar_repo)):
    return repo.create_avatar(
        name=avatar.name,
        scope=avatar.scope,
        icp_description=avatar.icp_description,
        anti_avatar=avatar.anti_avatar,
        voice_tone_config=avatar.voice_tone_config
    )

@router.get("/{avatar_id}", response_model=AvatarResponse)
async def get_avatar(avatar_id: str, repo: AvatarRepository = Depends(get_avatar_repo)):
    avatar = repo.get_by_id(avatar_id)
    if not avatar:
        raise HTTPException(status_code=404, detail="Avatar not found")
    return avatar

@router.patch("/{avatar_id}", response_model=AvatarResponse)
async def update_avatar(avatar_id: str, update: AvatarUpdate, repo: AvatarRepository = Depends(get_avatar_repo)):
    updated = repo.update_avatar(avatar_id, update.model_dump(exclude_unset=True))
    if not updated:
        raise HTTPException(status_code=404, detail="Avatar not found")
    return updated

@router.delete("/{avatar_id}")
async def delete_avatar(avatar_id: str, repo: AvatarRepository = Depends(get_avatar_repo)):
    success = repo.delete_avatar(avatar_id)
    if not success:
        raise HTTPException(status_code=404, detail="Avatar not found")
    return {"status": "success"}

@router.post("/{avatar_id}/set-default", response_model=AvatarResponse)
async def set_default_avatar(avatar_id: str, repo: AvatarRepository = Depends(get_avatar_repo)):
    updated = repo.set_default(avatar_id)
    if not updated:
        raise HTTPException(status_code=404, detail="Avatar not found")
    return updated

from fastapi import APIRouter, HTTPException, Depends
from typing import List, Any, Dict
from src.services.db.repositories.user import UserRepository
from src.services.db.repositories.audit import AuditRepository
from src.services.knowledge_service import KnowledgeService
from src.services.database import SessionLocal

router = APIRouter()
kb_service = KnowledgeService()

def get_repos():
    db = SessionLocal()
    user_repo = UserRepository(db)
    audit_repo = AuditRepository(db)
    try:
        yield user_repo, audit_repo
    finally:
        user_repo.close()

@router.post("/sync")
async def sync_knowledge_base():
    try:
        stats = kb_service.sync_from_qdrant()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/audit/users")
async def get_audit_users(limit: int = 20, repos: tuple = Depends(get_repos)):
    """
    Returns recent users for audit.
    """
    user_repo, audit_repo = repos
    results = audit_repo.get_recent_users(limit=limit)
    # Serialize manually
    serialized = []
    for user, last_activity in results:
        serialized.append({
            "user": {
                "id": str(user.id),
                "full_name": user.full_name,
                "telegram_id": user.telegram_id,
                "whatsapp_id": user.whatsapp_id,
                "created_at": user.created_at.isoformat() if user.created_at else None
            },
            "last_activity": last_activity.isoformat() if last_activity else None
        })
    return serialized

@router.get("/audit/users/{user_id}")
async def get_user_details(user_id: str, repos: tuple = Depends(get_repos)):
    """
    Returns full user details including profile_data.
    """
    user_repo, _ = repos
    user = user_repo.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    return {
        "id": str(user.id),
        "full_name": user.full_name,
        "email": user.email,
        "phone": user.phone,
        "telegram_id": user.telegram_id,
        "whatsapp_id": user.whatsapp_id,
        "instagram_id": user.instagram_id,
        "tiktok_id": user.tiktok_id,
        "profile_data": user.profile_data,
        "created_at": user.created_at,
        "updated_at": user.updated_at
    }

@router.delete("/users/{user_id}/history")
async def clear_user_history(user_id: str, repos: tuple = Depends(get_repos)):
    _, audit_repo = repos
    success = audit_repo.clear_user_history(user_id)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to clear history")
    return {"status": "cleared", "user_id": user_id}

@router.get("/audit/users/{user_id}/timeline")
async def get_user_timeline(user_id: str, limit: int = 50, repos: tuple = Depends(get_repos)):
    """
    Returns the unified timeline (messages + traces) for a user.
    """
    _, audit_repo = repos
    timeline = audit_repo.get_full_timeline(user_id, limit=limit)
    return timeline

@router.get("/audit/traces/{trace_id}")
async def get_trace_details(trace_id: str, repos: tuple = Depends(get_repos)):
    """
    Returns full details for a specific trace, including LLM logs.
    """
    _, audit_repo = repos
    details = audit_repo.get_trace_details(trace_id)
    if not details:
        raise HTTPException(status_code=404, detail="Trace not found")
    return details

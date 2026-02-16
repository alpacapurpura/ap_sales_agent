from fastapi import APIRouter, HTTPException, Depends
from src.services.db.repositories.user import UserRepository
from src.services.db.repositories.audit import AuditRepository
from src.services.buffer_service import SmartBufferService
from src.services.database import SessionLocal, get_db
from sqlalchemy.orm import Session
from src.services.db.models.tenant import Tenant
from src.services.db.models.user import User
from src.services.db.models.lead import Lead
from src.api.dependencies import get_current_user
from src.core.domain.schema import TenantPermissionUpdate

router = APIRouter()
buffer_service = SmartBufferService()

def get_repos():
    db = SessionLocal()
    user_repo = UserRepository(db)
    audit_repo = AuditRepository(db)
    try:
        yield user_repo, audit_repo
    finally:
        user_repo.close()

import logging

logger = logging.getLogger(__name__)

@router.get("/audit/leads")
async def get_audit_leads(limit: int = 20, repos: tuple = Depends(get_repos), user: User = Depends(get_current_user)):
    """
    Returns recent leads for audit.
    """
    user_repo, audit_repo = repos
    
    logger.info(f"AUDIT_DEBUG: Fetching audit leads for tenant_id={user.tenant_id}")
    
    try:
        results = audit_repo.get_recent_users(tenant_id=user.tenant_id, limit=limit)
        logger.info(f"AUDIT_DEBUG: Found {len(results)} leads")
    except Exception as e:
        logger.error(f"AUDIT_DEBUG: Error fetching leads: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
        
    # Serialize manually
    serialized = []
    for lead, last_activity in results:
        serialized.append({
            "lead": {
                "id": str(lead.id),
                "full_name": lead.full_name,
                "telegram_id": lead.telegram_id,
                "whatsapp_id": lead.whatsapp_id,
                "created_at": lead.created_at.isoformat() if lead.created_at else None
            },
            "last_activity": last_activity.isoformat() if last_activity else None
        })
    return serialized

@router.get("/audit/leads/{lead_id}")
async def get_lead_details(lead_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """
    Returns full lead details including profile_data.
    """
    # Fetch lead directly from DB ensuring tenant isolation
    target_lead = db.query(Lead).filter(Lead.id == lead_id, Lead.tenant_id == user.tenant_id).first()
    
    if not target_lead:
        raise HTTPException(status_code=404, detail="Lead not found")
        
    return {
        "id": str(target_lead.id),
        "full_name": target_lead.full_name,
        "email": target_lead.email,
        "phone": target_lead.phone,
        "telegram_id": target_lead.telegram_id,
        "whatsapp_id": target_lead.whatsapp_id,
        "instagram_id": target_lead.instagram_id,
        "tiktok_id": target_lead.tiktok_id,
        "profile_data": target_lead.profile_data,
        "created_at": target_lead.created_at,
        "updated_at": target_lead.updated_at
    }

@router.delete("/audit/leads/{lead_id}/history")
async def clear_lead_history(lead_id: str, repos: tuple = Depends(get_repos), user: User = Depends(get_current_user)):
    _, audit_repo = repos
    
    # 1. Clear SQL DB
    success_db = audit_repo.clear_user_history(lead_id, tenant_id=user.tenant_id)
    
    # 2. Clear Redis Cache
    success_cache = buffer_service.clear_user_cache(lead_id)
    
    if not success_db:
        raise HTTPException(status_code=500, detail="Failed to clear history")
    return {"status": "cleared", "lead_id": lead_id, "cache_cleared": success_cache}

@router.get("/audit/leads/{lead_id}/timeline")
async def get_lead_timeline(lead_id: str, limit: int = 50, repos: tuple = Depends(get_repos), user: User = Depends(get_current_user)):
    """
    Returns the unified timeline (messages + traces) for a lead.
    """
    _, audit_repo = repos
    timeline = audit_repo.get_full_timeline(lead_id, tenant_id=user.tenant_id, limit=limit)
    return timeline

@router.get("/audit/traces/{trace_id}")
async def get_trace_details(trace_id: str, repos: tuple = Depends(get_repos), user: User = Depends(get_current_user)):
    """
    Returns full details for a specific trace, including LLM logs.
    """
    _, audit_repo = repos
    details = audit_repo.get_trace_details(trace_id, tenant_id=user.tenant_id)
    if not details:
        raise HTTPException(status_code=404, detail="Trace not found")
    return details

@router.patch("/tenants/{tenant_id}/permissions")
async def update_tenant_permissions(
    tenant_id: str,
    permissions: TenantPermissionUpdate,
    db: Session = Depends(get_db)
):
    """
    Update tenant permissions (Superadmin only).
    """
    # Note: In a real app, verify superadmin role here.
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
        
    tenant.can_use_platform_keys = permissions.can_use_platform_keys
    db.commit()
    db.refresh(tenant)
    return {"status": "updated", "can_use_platform_keys": tenant.can_use_platform_keys}

@router.get("/tenants")
async def get_tenants(limit: int = 50, db: Session = Depends(get_db)):
    """
    List all tenants (Superadmin only).
    """
    tenants = db.query(Tenant).limit(limit).all()
    # Simple serialization
    return [{
        "id": str(t.id),
        "name": t.name,
        "slug": t.slug,
        "can_use_platform_keys": t.can_use_platform_keys,
        "openai_api_key_set": bool(t.openai_api_key),
        "gemini_api_key_set": bool(t.gemini_api_key)
    } for t in tenants]



from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from src.api.dependencies import get_current_user
from src.services.database import get_db
from src.services.db.models.user import User
from src.services.db.models.tenant import Tenant
from src.core.domain.schema import TenantSettingsUpdate, AISettings, GeneralSettings, GeneralSettingsUpdate, WebhookSettings, SystemUserProfile, TenantProfile
from src.core.domain.brand_schema import BrandSettings
from src.config import settings as app_settings
import secrets
import string

router = APIRouter()

def generate_secret_key(length=32):
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for i in range(length))

@router.get("/general", response_model=GeneralSettings)
async def get_general_settings(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get current General configuration for the user's tenant.
    """
    if not current_user.tenant_id:
        raise HTTPException(status_code=400, detail="User is not associated with a tenant")
    
    tenant = db.query(Tenant).filter(Tenant.id == current_user.tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
        
    config = tenant.config_json or {}
    return GeneralSettings(
        default_currency=config.get("default_currency", "USD"),
        timezone=config.get("timezone", "UTC")
    )

@router.patch("/general", response_model=GeneralSettings)
async def update_general_settings(
    settings: GeneralSettingsUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update General configuration for the user's tenant.
    """
    if not current_user.tenant_id:
        raise HTTPException(status_code=400, detail="User is not associated with a tenant")
        
    tenant = db.query(Tenant).filter(Tenant.id == current_user.tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    # Update config_json
    current_config = dict(tenant.config_json) if tenant.config_json else {}
    current_config["default_currency"] = settings.default_currency
    current_config["timezone"] = settings.timezone
    
    # Reassign to trigger SQLAlchemy detection (if using MutableDict it's auto, but safer this way)
    tenant.config_json = current_config
        
    db.commit()
    db.refresh(tenant)
    
    return GeneralSettings(
        default_currency=tenant.config_json.get("default_currency", "USD"),
        timezone=tenant.config_json.get("timezone", "UTC")
    )

@router.get("/ai", response_model=AISettings)
async def get_ai_settings(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get current AI configuration for the user's tenant.
    """
    if not current_user.tenant_id:
        raise HTTPException(status_code=400, detail="User is not associated with a tenant")
    
    tenant = db.query(Tenant).filter(Tenant.id == current_user.tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
        
    return AISettings(
        openai_api_key=tenant.openai_api_key,
        gemini_api_key=tenant.gemini_api_key,
        can_use_platform_keys=tenant.can_use_platform_keys or False
    )

@router.get("/profile", response_model=SystemUserProfile)
async def get_user_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get current user profile and tenant info.
    """
    tenant_profile = None
    if current_user.tenant_id:
        tenant = db.query(Tenant).filter(Tenant.id == current_user.tenant_id).first()
        if tenant:
            config = tenant.config_json or {}
            tenant_profile = TenantProfile(
                id=str(tenant.id),
                name=tenant.name,
                slug=tenant.slug,
                timezone=config.get("timezone", "UTC")
            )
            
    return SystemUserProfile(
        id=str(current_user.id),
        full_name=current_user.full_name,
        email=current_user.email,
        tenant=tenant_profile
    )

@router.get("/webhook", response_model=WebhookSettings)
async def get_webhook_settings(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get Webhook configuration for the user's tenant.
    """
    if not current_user.tenant_id:
        raise HTTPException(status_code=400, detail="User is not associated with a tenant")
    
    tenant = db.query(Tenant).filter(Tenant.id == current_user.tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    # Construct URL
    # Use API_DOMAIN if configured, otherwise fall back to localhost for dev
    domain = app_settings.API_DOMAIN or "localhost:8000"
    protocol = "https" if app_settings.API_DOMAIN else "http"
    webhook_url = f"{protocol}://{domain}/api/v1/webhook/chat"
    
    return WebhookSettings(
        webhook_url=webhook_url,
        webhook_secret=tenant.webhook_secret
    )

@router.post("/webhook/regenerate", response_model=WebhookSettings)
async def regenerate_webhook_secret(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Regenerate Webhook Secret for the user's tenant.
    """
    if not current_user.tenant_id:
        raise HTTPException(status_code=400, detail="User is not associated with a tenant")
        
    tenant = db.query(Tenant).filter(Tenant.id == current_user.tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
        
    # Generate new secret (n8n style)
    new_secret = f"sk_live_{generate_secret_key()}"
    tenant.webhook_secret = new_secret
    
    db.commit()
    db.refresh(tenant)
    
    domain = app_settings.API_DOMAIN or "localhost:8000"
    protocol = "https" if app_settings.API_DOMAIN else "http"
    webhook_url = f"{protocol}://{domain}/api/v1/webhook/chat"
    
    return WebhookSettings(
        webhook_url=webhook_url,
        webhook_secret=tenant.webhook_secret
    )

@router.patch("/ai", response_model=AISettings)
async def update_ai_settings(
    settings: TenantSettingsUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update AI API Keys for the user's tenant.
    """
    if not current_user.tenant_id:
        raise HTTPException(status_code=400, detail="User is not associated with a tenant")
        
    tenant = db.query(Tenant).filter(Tenant.id == current_user.tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    if settings.openai_api_key is not None:
        # Allow clearing the key by sending empty string? Or just update if provided.
        # If user sends "", we might want to set to None or ""
        tenant.openai_api_key = settings.openai_api_key
        
    if settings.gemini_api_key is not None:
        tenant.gemini_api_key = settings.gemini_api_key
        
    db.commit()
    db.refresh(tenant)
    
    return AISettings(
        openai_api_key=tenant.openai_api_key,
        gemini_api_key=tenant.gemini_api_key,
        can_use_platform_keys=tenant.can_use_platform_keys or False
    )

@router.get("/brand", response_model=BrandSettings)
async def get_brand_settings(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get Global Brand Settings for the user's tenant.
    """
    if not current_user.tenant_id:
        raise HTTPException(status_code=400, detail="User is not associated with a tenant")
    
    tenant = db.query(Tenant).filter(Tenant.id == current_user.tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
        
    config = tenant.config_json or {}
    brand_data = config.get("brand_settings", {})
    
    # Validation/Defaulting handled by Pydantic
    return BrandSettings(**brand_data)

@router.patch("/brand", response_model=BrandSettings)
async def update_brand_settings(
    settings: BrandSettings,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update Global Brand Settings for the user's tenant.
    """
    if not current_user.tenant_id:
        raise HTTPException(status_code=400, detail="User is not associated with a tenant")
        
    tenant = db.query(Tenant).filter(Tenant.id == current_user.tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    # Update config_json
    current_config = dict(tenant.config_json) if tenant.config_json else {}
    current_config["brand_settings"] = settings.model_dump()
    
    tenant.config_json = current_config
        
    db.commit()
    db.refresh(tenant)
    
    return BrandSettings(**tenant.config_json.get("brand_settings", {}))

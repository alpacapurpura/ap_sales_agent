from typing import Optional, Dict, Any
from datetime import datetime
from uuid import UUID
from src.shared.domain.base_entity import BaseEntity

class Tenant(BaseEntity):
    id: UUID
    name: str
    slug: str
    clerk_org_id: Optional[str] = None
    config_json: Dict[str, Any] = {}
    openai_api_key: Optional[str] = None
    gemini_api_key: Optional[str] = None
    webhook_secret: Optional[str] = None
    can_use_platform_keys: bool = False
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class AISettings(BaseEntity):
    """
    Configuration for AI API Keys (Tenant level).
    """
    openai_api_key: Optional[str] = None
    gemini_api_key: Optional[str] = None
    can_use_platform_keys: bool = False

class TenantSettingsUpdate(BaseEntity):
    """
    Request model for updating Tenant AI settings.
    """
    openai_api_key: Optional[str] = None
    gemini_api_key: Optional[str] = None

class GeneralSettings(BaseEntity):
    """
    General Tenant Configuration (e.g. currency, timezone).
    """
    default_currency: str = "USD"
    timezone: str = "UTC"

class GeneralSettingsUpdate(BaseEntity):
    """
    Request model for updating General Tenant settings.
    """
    default_currency: Optional[str] = None
    timezone: Optional[str] = None

class WebhookSettings(BaseEntity):
    """
    Webhook Configuration.
    """
    webhook_url: str
    webhook_secret: Optional[str] = None

class TenantProfile(BaseEntity):
    """
    Public Tenant Profile.
    """
    id: str
    name: str
    slug: str
    timezone: str = "UTC"

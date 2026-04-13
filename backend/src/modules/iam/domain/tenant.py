"""Tenant domain definitions."""

from datetime import datetime
from typing import Any
from uuid import UUID

from src.shared.domain.base_entity import BaseEntity


class Tenant(BaseEntity):
    """Represent tenant."""

    id: UUID
    name: str
    slug: str
    config_json: dict[str, Any] = {}
    openai_api_key: str | None = None
    gemini_api_key: str | None = None
    webhook_secret: str | None = None
    can_use_platform_keys: bool = False
    is_active: bool = True
    created_at: datetime | None = None
    updated_at: datetime | None = None


class AISettings(BaseEntity):
    """Configuration for AI API Keys (Tenant level)."""

    openai_api_key: str | None = None
    gemini_api_key: str | None = None
    can_use_platform_keys: bool = False


class TenantSettingsUpdate(BaseEntity):
    """Request model for updating Tenant AI settings."""

    openai_api_key: str | None = None
    gemini_api_key: str | None = None


class GeneralSettings(BaseEntity):
    """General Tenant Configuration (e.g. currency, timezone)."""

    default_currency: str = "USD"
    timezone: str = "UTC"


class GeneralSettingsUpdate(BaseEntity):
    """Request model for updating General Tenant settings."""

    default_currency: str | None = None
    timezone: str | None = None


class WebhookSettings(BaseEntity):
    """Webhook Configuration."""

    webhook_url: str
    webhook_secret: str | None = None


class TenantProfile(BaseEntity):
    """Public Tenant Profile."""

    id: str
    name: str
    slug: str
    timezone: str | None = "UTC"

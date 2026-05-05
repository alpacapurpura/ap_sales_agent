"""Tenant domain definitions.

T-6a (PI-12 S1 — sales-agent-litellm-canonicalization, Phase 1
expand-contract): the per-tenant API key columns
``openai_api_key``, ``deepseek_api_key``, ``kimi_api_key``,
``dashscope_api_key`` are deprecated. Pydantic ``Field(deprecated=True,
exclude=True)`` removes them from ``model_dump`` output (so FastAPI's
serializer drops them from the wire response) and emits a
``DeprecationWarning`` when accessed.

``gemini_api_key`` remains active (out of scope per architect §2.4 Q4
ratification — still consumed by landing extractors that bypass the
LiteLLM Proxy).

T-6c will physically ``DROP COLUMN`` and remove these Pydantic fields
entirely; until then the fields exist for SQLAlchemy ORM mapping
compatibility but are invisible to API consumers.
"""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import Field

from src.shared.domain.base_entity import BaseEntity


class Tenant(BaseEntity):
    """Represent tenant.

    Deprecated fields below are retained at the Pydantic-model level so
    SQLAlchemy ``model_validate`` from a TenantModel row still succeeds
    (the DB columns still exist until T-6c). ``exclude=True`` ensures
    they never propagate into ``model_dump`` output.
    """

    id: UUID
    name: str
    slug: str
    config_json: dict[str, Any] = {}
    openai_api_key: str | None = Field(default=None, deprecated=True, exclude=True)
    gemini_api_key: str | None = None
    deepseek_api_key: str | None = Field(default=None, deprecated=True, exclude=True)
    kimi_api_key: str | None = Field(default=None, deprecated=True, exclude=True)
    dashscope_api_key: str | None = Field(default=None, deprecated=True, exclude=True)
    webhook_secret: str | None = None
    can_use_platform_keys: bool = False
    is_active: bool = True
    created_at: datetime | None = None
    updated_at: datetime | None = None


class AISettings(BaseEntity):
    """Configuration for AI API Keys (Tenant level).

    Response model used by ``GET/PATCH /settings/ai``. Deprecated fields
    are excluded from serialized output (FastAPI uses ``model_dump`` to
    render the JSON response, so the deprecated keys never reach the
    wire after T-6a).
    """

    openai_api_key: str | None = Field(default=None, deprecated=True, exclude=True)
    gemini_api_key: str | None = None
    deepseek_api_key: str | None = Field(default=None, deprecated=True, exclude=True)
    kimi_api_key: str | None = Field(default=None, deprecated=True, exclude=True)
    dashscope_api_key: str | None = Field(default=None, deprecated=True, exclude=True)
    can_use_platform_keys: bool = False


class TenantSettingsUpdate(BaseEntity):
    """Request model for updating Tenant AI settings.

    Deprecated fields are excluded from serialization. The settings
    router's PATCH endpoint also no-ops on deprecated cols (T-6a removes
    the assignment statements) so even a client that bypasses Pydantic
    by sending raw JSON cannot persist the deprecated keys.
    """

    openai_api_key: str | None = Field(default=None, deprecated=True, exclude=True)
    gemini_api_key: str | None = None
    deepseek_api_key: str | None = Field(default=None, deprecated=True, exclude=True)
    kimi_api_key: str | None = Field(default=None, deprecated=True, exclude=True)
    dashscope_api_key: str | None = Field(default=None, deprecated=True, exclude=True)


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

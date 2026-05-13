"""Tenant domain definitions.

T-6c (PI-12 S1 — sales-agent-litellm-canonicalization, Phase 3
expand-contract): the 4 deprecated per-tenant API key fields
(``openai_api_key``, ``deepseek_api_key``, ``kimi_api_key``,
``dashscope_api_key``) have been physically removed from the Pydantic
models. They were marked ``deprecated=True, exclude=True`` in T-6a
(Phase 1) so the wire-response payload already excluded them; T-6c
removes the field declarations entirely now that the underlying DB
columns have also been dropped (alembic
``124_drop_tenant_provider_api_keys``).

``gemini_api_key`` remains active (out of scope per architect
03-arch-be.md §2.4 Q4 ratification — still consumed by landing
extractors that bypass the LiteLLM Proxy).

Old clients sending the deprecated keys via raw JSON will have those
keys silently ignored by Pydantic v2 (default ``extra='ignore'``),
preserving backward compatibility.
"""

from datetime import datetime
from typing import Any
from uuid import UUID

from luana_core_platform.domain.base_entity import BaseEntity


class Tenant(BaseEntity):
    """Represent tenant aggregate root.

    The 4 deprecated provider API key fields were removed in T-6c
    after the underlying DB columns were dropped by alembic
    ``124_drop_tenant_provider_api_keys``. ``gemini_api_key`` is
    retained per architect §2.4.
    """

    id: UUID
    name: str
    slug: str
    config_json: dict[str, Any] = {}
    gemini_api_key: str | None = None
    webhook_secret: str | None = None
    can_use_platform_keys: bool = False
    is_active: bool = True
    created_at: datetime | None = None
    updated_at: datetime | None = None


class AISettings(BaseEntity):
    """Configuration for AI API Keys (Tenant level).

    Response model used by ``GET/PATCH /settings/ai``. Only the
    ``gemini_api_key`` field remains; the 4 deprecated keys were
    removed in T-6c (Phase 3 expand-contract physical removal).
    """

    gemini_api_key: str | None = None
    can_use_platform_keys: bool = False


class TenantSettingsUpdate(BaseEntity):
    """Request model for updating Tenant AI settings.

    Old clients sending the 4 deprecated keys via raw JSON will have
    those keys silently ignored by Pydantic v2 (default
    ``extra='ignore'``). Only ``gemini_api_key`` is writable.
    """

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

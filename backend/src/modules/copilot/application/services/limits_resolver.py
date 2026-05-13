"""CopilotLimitsResolver — resolves effective limits: per-tenant override > env default.

PI-2 S1 PR-1: voice/media hardening.
"""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

import structlog
from luana_core_platform.core.config import settings

logger = structlog.get_logger(__name__)


@dataclass(frozen=True)
class EffectiveLimits:
    """Resolved (effective) limits for a tenant.

    Internal domain object — NOT the Pydantic DTO.
    voice_rpm and media_max_bytes are always populated
    (override OR env default).
    """

    tenant_id: UUID
    voice_rpm: int
    voice_window_seconds: int
    media_max_bytes: int
    voice_rpm_is_override: bool
    media_max_bytes_is_override: bool


class CopilotLimitsResolver:
    """Resolves effective copilot limits for a tenant.

    Rule: per-tenant DB override > env default.
    Redis cache: not applied in PR-1 (< 5ms overhead per call; optimize later if needed).
    """

    def __init__(self, repo: object) -> None:
        """Initialize with any repo implementing get_by_tenant (async or sync).

        Type is `object` to support both AsyncCopilotTenantLimitsRepository
        and SyncCopilotTenantLimitsRepository without a common ABC that imports async.
        """
        self._repo = repo

    async def get_effective(self, tenant_id: UUID) -> EffectiveLimits:
        """Resolve effective limits — async path (FastAPI endpoints)."""
        override = None
        try:
            override = await self._repo.get_by_tenant(tenant_id)  # type: ignore[attr-defined]
        except Exception:
            logger.exception(
                "copilot_limits_resolver_db_error",
                tenant_id=str(tenant_id),
            )
            # Graceful degradation: fall back to env defaults on DB error

        voice_rpm = (
            override.voice_rpm_override
            if override and override.voice_rpm_override is not None
            else settings.COPILOT_VOICE_RATE_LIMIT_PER_MIN
        )
        media_max_bytes = (
            override.media_max_bytes_override
            if override and override.media_max_bytes_override is not None
            else settings.COPILOT_MEDIA_MAX_BYTES
        )

        return EffectiveLimits(
            tenant_id=tenant_id,
            voice_rpm=voice_rpm,
            voice_window_seconds=60,
            media_max_bytes=media_max_bytes,
            voice_rpm_is_override=bool(override and override.voice_rpm_override is not None),
            media_max_bytes_is_override=bool(override and override.media_max_bytes_override is not None),
        )

    def get_effective_sync(self, tenant_id: UUID) -> EffectiveLimits:
        """Resolve effective limits — sync path (Streamlit admin)."""
        override = None
        try:
            override = self._repo.get_by_tenant(tenant_id)  # type: ignore[attr-defined]
        except Exception:
            logger.exception(
                "copilot_limits_resolver_db_error_sync",
                tenant_id=str(tenant_id),
            )

        voice_rpm = (
            override.voice_rpm_override
            if override and override.voice_rpm_override is not None
            else settings.COPILOT_VOICE_RATE_LIMIT_PER_MIN
        )
        media_max_bytes = (
            override.media_max_bytes_override
            if override and override.media_max_bytes_override is not None
            else settings.COPILOT_MEDIA_MAX_BYTES
        )

        return EffectiveLimits(
            tenant_id=tenant_id,
            voice_rpm=voice_rpm,
            voice_window_seconds=60,
            media_max_bytes=media_max_bytes,
            voice_rpm_is_override=bool(override and override.voice_rpm_override is not None),
            media_max_bytes_is_override=bool(override and override.media_max_bytes_override is not None),
        )

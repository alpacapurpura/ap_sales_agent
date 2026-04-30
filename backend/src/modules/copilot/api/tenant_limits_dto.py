"""DTOs for per-tenant copilot limit overrides.

Admin-only surface — not exposed to tenant-facing copilot UI.
PII: none (UUIDs + ints + datetimes only).
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

_ONE_MIB = 1 * 1024 * 1024  # 1 MiB in bytes
_HUNDRED_MIB = 100 * 1024 * 1024  # 100 MiB in bytes (Q4 cap — SaaS standard)


class CopilotTenantLimitsResponse(BaseModel):
    """Response — current per-tenant overrides. Optional fields = no override set."""

    model_config = ConfigDict(from_attributes=True)

    tenant_id: UUID
    voice_rpm_override: int | None = Field(
        None,
        ge=1,
        le=1000,
        description="Override de requests/min para voice upload+transcribe. None = usa env default.",
    )
    media_max_bytes_override: int | None = Field(
        None,
        ge=_ONE_MIB,
        le=_HUNDRED_MIB,
        description="Override de tamaño máximo en bytes para uploads. None = usa env default.",
    )
    updated_at: datetime
    updated_by_user_id: UUID | None = None


class CopilotTenantLimitsUpsertRequest(BaseModel):
    """Upsert request — None in a field clears the override (reverts to env default)."""

    model_config = ConfigDict(from_attributes=True)

    voice_rpm_override: int | None = Field(
        None,
        ge=1,
        le=1000,
        description="Override RPM voice. None limpia el override.",
    )
    media_max_bytes_override: int | None = Field(
        None,
        ge=_ONE_MIB,
        le=_HUNDRED_MIB,
        description="Override bytes media. None limpia el override.",
    )


class EffectiveLimitsResponse(BaseModel):
    """Read-only response — effective limits (override OR env default).

    Consumed by internal voice/media endpoints via service dependency.
    Not admin-facing — internal DTO for endpoint-level inspection.
    """

    model_config = ConfigDict(from_attributes=True)

    tenant_id: UUID
    voice_rpm: int = Field(description="Requests/min efectivos para voice upload.")
    voice_window_seconds: int = Field(default=60, description="Ventana sliding window en segundos.")
    media_max_bytes: int = Field(description="Tamaño máximo efectivo en bytes para uploads.")
    voice_rpm_is_override: bool = Field(description="True si proviene de override DB; False si es env default.")
    media_max_bytes_is_override: bool = Field(description="True si proviene de override DB; False si es env default.")

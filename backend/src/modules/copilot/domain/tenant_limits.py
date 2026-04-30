"""Per-tenant overrides for copilot rate limits and media size caps.

Domain entity — pure Python, zero framework dependencies.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

# ── Invariant constants ────────────────────────────────────────────────────────

_VOICE_RPM_MIN: int = 1
_VOICE_RPM_MAX: int = 1000  # anti-typo cap; storm-protects Whisper quota
_MEDIA_BYTES_MIN: int = 1 * 1024 * 1024  # 1 MiB
_MEDIA_BYTES_MAX: int = 100 * 1024 * 1024  # 100 MiB (SaaS standard for microempresarios)


@dataclass(frozen=True)
class CopilotTenantLimits:
    """Aggregate root: tenant-scoped overrides for copilot voice and media limits.

    Invariants (enforced in __post_init__):
    - tenant_id mandatory (1:1 con Tenant; row optional — None overrides = use env defaults).
    - voice_rpm_override in [1, 1000] or None (sentinel = no override).
    - media_max_bytes_override in [1 MiB, 100 MiB] or None (sentinel = no override).
    - deleted_at None while alive (soft-delete only).
    """

    tenant_id: UUID
    voice_rpm_override: int | None
    media_max_bytes_override: int | None
    updated_at: datetime
    updated_by_user_id: UUID | None
    deleted_at: datetime | None

    def __post_init__(self) -> None:
        """Enforce domain invariants on construction."""
        if self.tenant_id is None:
            msg = "tenant_id is required"
            raise ValueError(msg)

        if self.voice_rpm_override is not None:
            if not isinstance(self.voice_rpm_override, int) or isinstance(self.voice_rpm_override, bool):
                msg = "voice_rpm_override must be int or None"
                raise TypeError(msg)
            if self.voice_rpm_override < _VOICE_RPM_MIN:
                msg = f"voice_rpm_override must be >= {_VOICE_RPM_MIN}, got {self.voice_rpm_override}"
                raise ValueError(msg)
            if self.voice_rpm_override > _VOICE_RPM_MAX:
                msg = f"voice_rpm_override must be <= {_VOICE_RPM_MAX}, got {self.voice_rpm_override}"
                raise ValueError(msg)

        if self.media_max_bytes_override is not None:
            if not isinstance(self.media_max_bytes_override, int) or isinstance(self.media_max_bytes_override, bool):
                msg = "media_max_bytes_override must be int or None"
                raise TypeError(msg)
            if self.media_max_bytes_override < _MEDIA_BYTES_MIN:
                msg = (
                    f"media_max_bytes_override must be >= {_MEDIA_BYTES_MIN} bytes (1 MiB), "
                    f"got {self.media_max_bytes_override}"
                )
                raise ValueError(msg)
            if self.media_max_bytes_override > _MEDIA_BYTES_MAX:
                msg = (
                    f"media_max_bytes_override must be <= {_MEDIA_BYTES_MAX} bytes (100 MiB), "
                    f"got {self.media_max_bytes_override}"
                )
                raise ValueError(msg)

    @property
    def is_alive(self) -> bool:
        """True if the override row is active (not soft-deleted)."""
        return self.deleted_at is None

"""Domain invariants for CopilotTenantLimits.

TDD RED phase: tests run before domain entity exists.
"""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

import pytest

from luana_core_copilot.domain.tenant_limits import CopilotTenantLimits


class TestCopilotTenantLimitsInvariants:
    """Verifica invariantes del domain entity CopilotTenantLimits."""

    def _make(self, **kwargs: object) -> CopilotTenantLimits:
        defaults = {
            "tenant_id": uuid4(),
            "voice_rpm_override": None,
            "media_max_bytes_override": None,
            "updated_at": datetime.now(timezone.utc),
            "updated_by_user_id": None,
            "deleted_at": None,
        }
        defaults.update(kwargs)
        return CopilotTenantLimits(**defaults)  # type: ignore[arg-type]

    def test_sentinel_none_fields_allowed(self) -> None:
        """None en ambos campos override es valido (usa env defaults)."""
        limits = self._make(voice_rpm_override=None, media_max_bytes_override=None)
        assert limits.voice_rpm_override is None
        assert limits.media_max_bytes_override is None

    def test_valid_voice_rpm_override(self) -> None:
        """voice_rpm_override valido en [1, 1000]."""
        limits = self._make(voice_rpm_override=20)
        assert limits.voice_rpm_override == 20

    def test_valid_media_max_bytes_override(self) -> None:
        """media_max_bytes_override valido en [1MiB, 100MiB]."""
        fifty_mb = 50 * 1024 * 1024
        limits = self._make(media_max_bytes_override=fifty_mb)
        assert limits.media_max_bytes_override == fifty_mb

    def test_voice_rpm_zero_raises(self) -> None:
        """voice_rpm_override = 0 viola la invariante (debe ser > 0)."""
        with pytest.raises((ValueError, TypeError)):
            self._make(voice_rpm_override=0)

    def test_voice_rpm_negative_raises(self) -> None:
        """voice_rpm_override negativo viola la invariante."""
        with pytest.raises((ValueError, TypeError)):
            self._make(voice_rpm_override=-5)

    def test_voice_rpm_over_cap_raises(self) -> None:
        """voice_rpm_override > 1000 viola cap anti-typo."""
        with pytest.raises((ValueError, TypeError)):
            self._make(voice_rpm_override=1001)

    def test_media_bytes_zero_raises(self) -> None:
        """media_max_bytes_override = 0 viola invariante."""
        with pytest.raises((ValueError, TypeError)):
            self._make(media_max_bytes_override=0)

    def test_media_bytes_over_100mib_raises(self) -> None:
        """media_max_bytes_override > 100 MiB viola cap."""
        over_cap = 101 * 1024 * 1024
        with pytest.raises((ValueError, TypeError)):
            self._make(media_max_bytes_override=over_cap)

    def test_tenant_id_required(self) -> None:
        """tenant_id es REQUIRED — no puede ser None."""
        with pytest.raises((ValueError, TypeError)):
            self._make(tenant_id=None)

    def test_frozen_dataclass_immutable(self) -> None:
        """CopilotTenantLimits es frozen — no permite mutación."""
        limits = self._make(voice_rpm_override=10)
        with pytest.raises((AttributeError, TypeError)):
            limits.voice_rpm_override = 20  # type: ignore[misc]

    def test_deleted_at_nullable(self) -> None:
        """deleted_at puede ser None (entidad viva) o datetime (soft-deleted)."""
        alive = self._make(deleted_at=None)
        assert alive.deleted_at is None

        deleted = self._make(deleted_at=datetime.now(timezone.utc))
        assert deleted.deleted_at is not None

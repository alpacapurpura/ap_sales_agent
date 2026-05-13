"""Unit tests — IdempotencyKey value object."""

from __future__ import annotations

import pytest

from luana_core_idempotency.domain.key import IdempotencyKey


class TestIdempotencyKey:
    """IdempotencyKey invariants."""

    def test_storage_key_format(self):
        """storage_key must follow idem:{namespace}:{key} format."""
        key = IdempotencyKey(namespace="webhook:manychat", key="sig-abc123")
        assert key.storage_key == "idem:webhook:manychat:sig-abc123"

    def test_equality_by_value(self):
        """Two keys with same fields are equal (frozen dataclass)."""
        k1 = IdempotencyKey(namespace="webhook:meta", key="event-id-123")
        k2 = IdempotencyKey(namespace="webhook:meta", key="event-id-123")
        assert k1 == k2

    def test_inequality_different_namespace(self):
        """Different namespace produces different key."""
        k1 = IdempotencyKey(namespace="webhook:manychat", key="abc")
        k2 = IdempotencyKey(namespace="webhook:meta", key="abc")
        assert k1 != k2

    def test_hashable(self):
        """IdempotencyKey must be hashable (for use in sets/dicts)."""
        k1 = IdempotencyKey(namespace="webhook:manychat", key="abc")
        k2 = IdempotencyKey(namespace="webhook:meta", key="xyz")
        key_set = {k1, k2}
        assert len(key_set) == 2

    def test_default_ttl_is_24h(self):
        """Default TTL is 86400 seconds (24h)."""
        key = IdempotencyKey(namespace="webhook:manychat", key="abc")
        assert key.ttl_seconds == 86400

    def test_custom_ttl(self):
        """Custom TTL is preserved."""
        key = IdempotencyKey(namespace="webhook:manychat", key="abc", ttl_seconds=3600)
        assert key.ttl_seconds == 3600

    def test_empty_namespace_raises(self):
        """Empty namespace raises ValueError."""
        with pytest.raises(ValueError, match="namespace is required"):
            IdempotencyKey(namespace="", key="abc")

    def test_empty_key_raises(self):
        """Empty key raises ValueError."""
        with pytest.raises(ValueError, match="key is required"):
            IdempotencyKey(namespace="webhook:meta", key="")

    def test_zero_ttl_raises(self):
        """ttl_seconds=0 raises ValueError."""
        with pytest.raises(ValueError, match="ttl_seconds must be > 0"):
            IdempotencyKey(namespace="webhook:meta", key="abc", ttl_seconds=0)

    def test_negative_ttl_raises(self):
        """Negative TTL raises ValueError."""
        with pytest.raises(ValueError, match="ttl_seconds must be > 0"):
            IdempotencyKey(namespace="webhook:meta", key="abc", ttl_seconds=-1)

    def test_namespace_with_colons_allowed(self):
        """Namespace with colons is valid — supports sub-namespacing like webhook:manychat."""
        key = IdempotencyKey(namespace="copilot:extract_card", key="nav:job123:section_slug")
        assert key.storage_key == "idem:copilot:extract_card:nav:job123:section_slug"

    def test_frozen_immutable(self):
        """Frozen dataclass — mutation raises FrozenInstanceError."""
        from dataclasses import FrozenInstanceError

        key = IdempotencyKey(namespace="webhook:meta", key="abc")
        with pytest.raises(FrozenInstanceError):
            key.namespace = "changed"  # type: ignore[misc]

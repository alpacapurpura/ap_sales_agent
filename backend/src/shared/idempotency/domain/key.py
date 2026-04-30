"""IdempotencyKey — immutable value object for Redis-backed deduplication."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class IdempotencyKey:
    """Value Object — key for idempotency deduplication via Redis.

    Format in Redis: ``idem:{namespace}:{key}``

    Example:
        ``IdempotencyKey(namespace="webhook:manychat", key="sig-abc123")``
        → Redis key: ``idem:webhook:manychat:sig-abc123``
    """

    namespace: str
    """Namespace for the key group. Must not contain ':'.
    Examples: ``webhook:manychat``, ``webhook:meta``, ``tool:create_payment_link``.
    """

    key: str
    """Natural key within the namespace. Typically a provider-issued ID or
    a deterministic hash of request parameters."""

    ttl_seconds: int = 86400
    """TTL in seconds. Default 24h. Override per use-case."""

    @property
    def storage_key(self) -> str:
        """Redis storage key: ``idem:{namespace}:{key}``."""
        return f"idem:{self.namespace}:{self.key}"

    def __post_init__(self) -> None:
        """Validate value object invariants."""
        if not self.namespace:
            msg = "namespace is required"
            raise ValueError(msg)
        if not self.key:
            msg = "key is required"
            raise ValueError(msg)
        if self.ttl_seconds <= 0:
            msg = "ttl_seconds must be > 0"
            raise ValueError(msg)

"""Circuit breaker error hierarchy.

PR-5 PI-1 S2.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from uuid import UUID


class CircuitBreakerOpenError(Exception):
    """Raised when the circuit breaker short-circuits before executing fn.

    Caller (worker) catches this, marks task failed with error_code='circuit_open',
    and does NOT trigger ARQ retry (waits for next scheduler_tick).
    """

    def __init__(self, channel: str, tenant_id: UUID, retry_after_seconds: float) -> None:
        """Initialize with context for audit log and worker decision."""
        super().__init__(f"circuit open for {channel!r} tenant={tenant_id} retry_after={retry_after_seconds:.0f}s")
        self.channel = channel
        self.tenant_id = tenant_id
        self.retry_after_seconds = retry_after_seconds

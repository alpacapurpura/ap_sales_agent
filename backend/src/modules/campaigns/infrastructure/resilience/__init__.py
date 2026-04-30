"""Campaign infrastructure resilience primitives.

Exports:
    CircuitBreaker — asyncio Redis-backed per-(channel, tenant_id) breaker.
    CircuitBreakerConfig — tunable configuration.
    CircuitState — state enum.
    CircuitBreakerOpenError — raised on OPEN state (callers catch + mark task failed).
"""

from src.modules.campaigns.infrastructure.resilience.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitState,
)
from src.modules.campaigns.infrastructure.resilience.errors import CircuitBreakerOpenError

__all__ = [
    "CircuitBreaker",
    "CircuitBreakerConfig",
    "CircuitBreakerOpenError",
    "CircuitState",
]

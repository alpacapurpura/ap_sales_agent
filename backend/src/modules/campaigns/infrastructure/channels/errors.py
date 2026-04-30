"""Channel-layer error hierarchy.

Separates provider-side transient errors (counted by CB) from tenant-gate
errors (compliance/rate-limit — never counted by CB) so the worker can make
the correct retry / skip / reschedule decision without isinstance gymnastics.

PR-5 PI-1 S2 — tessl__graceful-degradation: every error class drives a
distinct resilience action.
"""

from __future__ import annotations


class ChannelError(Exception):
    """Base for all channel-layer errors."""

    error_code: str = "unknown"


class ChannelRetryableError(ChannelError):
    """Transient provider error (5xx, network timeout, connection reset).

    Circuit breaker COUNTS this failure.
    Worker re-raises to ARQ for exponential backoff retry.
    """

    error_code = "retryable"


class ChannelRateLimitedError(ChannelRetryableError):
    """HTTP 429 from the provider (Telegram / WhatsApp).

    Circuit breaker COUNTS this failure.
    Worker re-raises; ARQ honors ``retry_after_seconds`` when present.
    """

    error_code = "rate_limited"

    def __init__(self, message: str, *, retry_after_seconds: float | None = None) -> None:
        """Initialize with optional retry delay hint from the provider."""
        super().__init__(message)
        self.retry_after_seconds = retry_after_seconds


class ChannelFatalError(ChannelError):
    """Non-transient provider error (4xx except 429, invalid recipient, user-blocked).

    Circuit breaker does NOT count this.
    Worker marks task FAILED — no retry.
    """

    error_code = "fatal"


class ChannelComplianceBlocked(ChannelFatalError):  # noqa: N818 — intentional non-Error suffix
    """Blocked by ComplianceService before send.

    Circuit breaker does NOT count this (tenant gate, not provider issue).
    Worker marks task SKIPPED — no retry (opt-out is permanent).
    """

    error_code = "compliance_blocked"


class ChannelTenantRateExceeded(ChannelRetryableError):  # noqa: N818 — intentional non-Error suffix
    """OutboundRateLimiter denied — tenant daily cap reached.

    Circuit breaker does NOT count this (tenant gate, not provider issue).
    Worker reschedules task (pending + scheduled_at += delay); no CB hit.
    """

    error_code = "tenant_rate_exceeded"

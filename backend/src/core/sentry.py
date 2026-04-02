"""Shared Sentry initialisation for all backend services (api, worker, scheduler)."""

import sentry_sdk

from src.core.config import settings


_SENSITIVE_KEYS = frozenset(
    {
        "access_token",
        "refresh_token",
        "api_key",
        "page_access_token",
        "client_secret",
        "authorization",
    }
)


def _redact_event(event: dict[str, object], hint: dict[str, object]) -> dict[str, object]:  # noqa: ARG001 — required by sentry_sdk before_send signature
    """Strip sensitive keys from Sentry event extras/data."""
    def _scrub(obj: object) -> object:
        if isinstance(obj, dict):
            return {
                k: "[Filtered]" if k.lower() in _SENSITIVE_KEYS else _scrub(v)
                for k, v in obj.items()
            }
        if isinstance(obj, list):
            return [_scrub(i) for i in obj]
        return obj

    event = _scrub(event)
    # Scrub request headers
    try:
        headers = event["request"]["headers"]
        if "Authorization" in headers:
            headers["Authorization"] = "[Filtered]"
    except (KeyError, TypeError):
        pass
    return event


_EXCLUDED_PATHS = frozenset({"/health", "/metrics"})
_LOW_SAMPLE_PATH_PREFIXES = ("/api/v1/connections/webhook", "/api/v1/iam/webhooks", "/api/v1/connections/shopify/compliance")


def _traces_sampler(sampling_context: dict[str, object]) -> float:
    """Dynamic sampling: exclude health checks, reduce webhook noise."""
    wsgi_env = sampling_context.get("wsgi_environ") or {}
    asgi_scope = sampling_context.get("asgi_scope") or {}
    path = (
        wsgi_env.get("PATH_INFO")
        or asgi_scope.get("path")
        or ""
    )
    if path in _EXCLUDED_PATHS:
        return 0.0
    if path.startswith(_LOW_SAMPLE_PATH_PREFIXES):
        return 0.01
    return settings.SENTRY_TRACES_SAMPLE_RATE


def init_sentry(service_name: str) -> None:
    """Initialise Sentry SDK for the given service.

    service_name: "api" | "worker" | "scheduler"
    Workers use SENTRY_WORKER_DSN when set, else fall back to SENTRY_DSN.
    No-op if no DSN is configured.
    """
    import logging

    dsn = settings.SENTRY_DSN
    if service_name in ("worker", "scheduler") and settings.SENTRY_WORKER_DSN:
        dsn = settings.SENTRY_WORKER_DSN
    if not dsn:
        return

    from sentry_sdk.integrations import Integration
    from sentry_sdk.integrations.logging import LoggingIntegration

    logging_integration = LoggingIntegration(
        level=logging.WARNING,       # WARNING+ → Sentry breadcrumbs
        event_level=logging.ERROR,   # ERROR+ → Sentry events
    )
    integrations: list[Integration] = [logging_integration]

    if service_name == "api":
        from sentry_sdk.integrations.fastapi import FastApiIntegration
        from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
        from sentry_sdk.integrations.httpx import HttpxIntegration

        integrations += [FastApiIntegration(), SqlalchemyIntegration(), HttpxIntegration()]

    elif service_name in ("worker", "scheduler"):
        from sentry_sdk.integrations.arq import ArqIntegration
        from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
        from sentry_sdk.integrations.httpx import HttpxIntegration

        integrations += [ArqIntegration(), SqlalchemyIntegration(), HttpxIntegration()]

    sentry_sdk.init(
        dsn=dsn,
        environment=settings.ENVIRONMENT,
        release=f"nicolify-backend@{settings.SENTRY_RELEASE}",
        server_name=f"nicolify-{service_name}",
        enable_tracing=True,
        traces_sampler=_traces_sampler,
        profiles_sample_rate=settings.SENTRY_PROFILES_SAMPLE_RATE,
        send_default_pii=False,
        integrations=integrations,
        before_send=_redact_event,
    )

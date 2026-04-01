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


def init_sentry(service_name: str) -> None:
    """Initialise Sentry SDK for the given service.

    service_name: "api" | "worker" | "scheduler"
    No-op if SENTRY_DSN is not configured.
    """
    if not settings.SENTRY_DSN:
        return

    from sentry_sdk.integrations import Integration
    integrations: list[Integration] = []

    if service_name == "api":
        from sentry_sdk.integrations.fastapi import FastApiIntegration
        from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
        from sentry_sdk.integrations.httpx import HttpxIntegration

        integrations = [FastApiIntegration(), SqlalchemyIntegration(), HttpxIntegration()]

    elif service_name in ("worker", "scheduler"):
        from sentry_sdk.integrations.arq import ArqIntegration
        from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
        from sentry_sdk.integrations.httpx import HttpxIntegration

        integrations = [ArqIntegration(), SqlalchemyIntegration(), HttpxIntegration()]

    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        environment=settings.ENVIRONMENT,
        traces_sample_rate=settings.SENTRY_TRACES_SAMPLE_RATE,
        send_default_pii=False,
        integrations=integrations,
        before_send=_redact_event,
    )

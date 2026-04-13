"""
Google Workspace Unified OAuth Router.

Handles a single OAuth flow that grants access to all Google services
(Gmail, Calendar, Analytics, YouTube) at once. The code is exchanged
ONCE and the resulting credentials are distributed to each service.
"""

import json
import os
from typing import Annotated, Any

import sentry_sdk
import structlog
from fastapi import APIRouter, Body, Depends, HTTPException
from google.auth.exceptions import RefreshError
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from pydantic import BaseModel
from sqlalchemy.orm import Session

from src.core.config import settings
from src.core.database import get_db
from src.modules.connections.api.dto.common import (
    ToggleServiceResponse,
    WorkspaceStatusResponse,
)
from src.modules.connections.domain.enums import ChannelType
from src.modules.connections.infrastructure.channels.youtube import YoutubeAdapter
from src.modules.connections.infrastructure.repositories import (
    ChannelConnectionRepository,
)
from src.modules.iam.api.dependencies import get_current_user
from src.modules.iam.domain.user import User

# Allow OAuth scope changes (e.g. if user granted extra scopes previously)
os.environ["OAUTHLIB_RELAX_TOKEN_SCOPE"] = "1"

router = APIRouter(tags=["google-workspace"])
logger = structlog.get_logger()


class ConnectionTestResponse(BaseModel):
    status: str
    message: str
    details: dict[str, Any] | None = None


# Combined scopes for all supported Google services
WORKSPACE_SCOPES = [
    # Gmail
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.readonly",
    # Calendar
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/calendar.events",
    # Analytics
    "https://www.googleapis.com/auth/analytics.readonly",
    # YouTube Data
    "https://www.googleapis.com/auth/youtube.readonly",
    # YouTube Analytics (watch time, demographics, traffic sources, revenue)
    "https://www.googleapis.com/auth/yt-analytics.readonly",
    "https://www.googleapis.com/auth/yt-analytics-monetary.readonly",
    # Search Console
    "https://www.googleapis.com/auth/webmasters.readonly",
]

# Maps service slug -> ChannelType
SERVICE_MAP: dict[str, ChannelType] = {
    "gmail": ChannelType.GMAIL,
    "calendar": ChannelType.GOOGLE_CALENDAR,
    "analytics": ChannelType.GOOGLE_ANALYTICS,
    "youtube": ChannelType.YOUTUBE,
    "youtube_analytics": ChannelType.YOUTUBE_ANALYTICS,
}


def _get_repo(db: Session = Depends(get_db)) -> ChannelConnectionRepository:
    return ChannelConnectionRepository(db)


def _get_client_config() -> dict:
    return {
        "web": {
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
        },
    }


@router.get("/auth-url")
async def get_auth_url(
    user: Annotated[User, Depends(get_current_user)],
):
    """Returns a Google OAuth URL requesting ALL workspace scopes at once."""
    flow = Flow.from_client_config(
        _get_client_config(),
        scopes=WORKSPACE_SCOPES,
        autogenerate_code_verifier=False,
    )
    flow.redirect_uri = settings.GOOGLE_REDIRECT_URI

    authorization_url, state = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",  # Force consent to always get a refresh_token
    )
    return {"url": authorization_url, "state": state}


@router.post("/callback")
async def oauth_callback(
    code: Annotated[str, Body(embed=True)],
    user: Annotated[User, Depends(get_current_user)],
    repo: Annotated[ChannelConnectionRepository, Depends(_get_repo)],
):
    """
    Exchanges the authorization code ONCE and stores the resulting credentials
    for all 4 Google services (Gmail, Calendar, Analytics, YouTube).
    """
    # Exchange code for credentials
    flow = Flow.from_client_config(
        _get_client_config(),
        scopes=WORKSPACE_SCOPES,
        autogenerate_code_verifier=False,
    )
    flow.redirect_uri = settings.GOOGLE_REDIRECT_URI

    try:
        flow.fetch_token(code=code)
        creds = flow.credentials
        creds_data = json.loads(creds.to_json())
    except Exception as e:
        logger.exception("google_workspace_oauth_exchange_failed", error=str(e))
        raise HTTPException(
            status_code=400,
            detail="Error de autenticación con Google. Intenta de nuevo.",
        ) from e

    # Get user profile to obtain email address
    try:
        gmail_creds = Credentials.from_authorized_user_info(creds_data)
        gmail_service = build("gmail", "v1", credentials=gmail_creds)
        profile = gmail_service.users().getProfile(userId="me").execute()
        email = profile.get("emailAddress", "")
    except Exception as e:  # noqa: BLE001 — API error boundary
        logger.warning("google_workspace_profile_fetch_failed", error=str(e))
        email = ""

    # Store the SAME credentials for all 5 services
    for service_slug, channel_type in SERVICE_MAP.items():
        service_config: dict = {}
        if service_slug in {"gmail", "calendar"}:
            service_config = {"email": email}

        repo.upsert(
            tenant_id=user.tenant_id,
            channel_type=channel_type,
            credentials=creds_data,
            config=service_config,
        )

    # YouTube auto-discovery: fetch channel info and enrich config
    youtube_channel = None
    try:
        yt_adapter = YoutubeAdapter(
            client_config={
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
            },
            credentials_data=creds_data.copy(),
        )
        channel_info = yt_adapter.get_channel_info()
        if channel_info and channel_info.get("id"):
            youtube_channel = {
                "channel_id": channel_info["id"],
                "channel_title": channel_info.get("title"),
                "customUrl": channel_info.get("customUrl"),
                "statistics": channel_info.get("statistics"),
            }

            # Update YOUTUBE connection config
            yt_conn = repo.get_by_tenant_and_type(user.tenant_id, ChannelType.YOUTUBE)
            if yt_conn:
                repo.update_config(yt_conn, youtube_channel)

            # Update YOUTUBE_ANALYTICS connection config with same channel data
            yta_conn = repo.get_by_tenant_and_type(
                user.tenant_id,
                ChannelType.YOUTUBE_ANALYTICS,
            )
            if yta_conn:
                repo.update_config(yta_conn, youtube_channel)

            logger.info(
                "google_workspace_youtube_discovered",
                tenant_id=str(user.tenant_id),
                channel_id=channel_info["id"],
                channel_title=channel_info.get("title"),
            )
    except Exception as e:  # noqa: BLE001 — API error boundary
        logger.warning(
            "google_workspace_youtube_discovery_failed",
            tenant_id=str(user.tenant_id),
            error=str(e),
        )

    logger.info(
        "google_workspace_connected",
        tenant_id=str(user.tenant_id),
        email=email,
    )
    return {"status": "connected", "email": email, "youtube_channel": youtube_channel}


@router.get("/status", response_model=WorkspaceStatusResponse)
async def get_status(
    user: Annotated[User, Depends(get_current_user)],
    repo: Annotated[ChannelConnectionRepository, Depends(_get_repo)],
):
    """Returns the connection status for all 4 Google services."""
    services: dict[str, dict] = {}
    any_connected = False

    for service_slug, channel_type in SERVICE_MAP.items():
        connection = repo.get_by_tenant_and_type(user.tenant_id, channel_type)
        is_active = bool(connection and connection.is_active)
        has_credentials = bool(connection and connection.credentials)

        services[service_slug] = {
            "is_active": is_active,
            "has_credentials": has_credentials,
        }
        if has_credentials:
            any_connected = True

    # Get email from gmail or calendar connection (whichever exists)
    email = None
    for slug in ("gmail", "calendar"):
        conn = repo.get_by_tenant_and_type(user.tenant_id, SERVICE_MAP[slug])
        if conn and conn.config:
            email = conn.config.get("email")
            if email:
                break

    return {
        "is_connected": any_connected,
        "email": email,
        "services": services,
    }


@router.patch("/services/{service}", response_model=ToggleServiceResponse)
async def toggle_service(
    service: str,
    is_active: Annotated[bool, Body(embed=True)],
    user: Annotated[User, Depends(get_current_user)],
    repo: Annotated[ChannelConnectionRepository, Depends(_get_repo)],
):
    """Activates or deactivates a specific Google service without revoking OAuth."""
    if service not in SERVICE_MAP:
        raise HTTPException(status_code=400, detail=f"Servicio desconocido: {service}")

    channel_type = SERVICE_MAP[service]
    connection = repo.get_by_tenant_and_type(user.tenant_id, channel_type)

    if not connection:
        raise HTTPException(
            status_code=404,
            detail="No hay credenciales de Google. Conecta tu cuenta primero.",
        )

    if is_active:
        repo.activate(connection)
    else:
        repo.deactivate(connection)

    return {"status": "updated", "service": service, "is_active": is_active}


@router.delete("/")
async def disconnect_all(
    user: Annotated[User, Depends(get_current_user)],
    repo: Annotated[ChannelConnectionRepository, Depends(_get_repo)],
):
    """Soft-deletes all Google service connections for this tenant."""
    deactivated = []
    for service_slug, channel_type in SERVICE_MAP.items():
        connection = repo.get_by_tenant_and_type(user.tenant_id, channel_type)
        if connection and connection.credentials:
            repo.revoke(connection)
            deactivated.append(service_slug)

    return {"status": "disconnected", "services": deactivated}


# ── Service-specific test helpers ────────────────────────────────────────────


def _test_gmail(creds_data: dict) -> dict:
    """Test Gmail: fetch user profile."""
    creds = Credentials.from_authorized_user_info(creds_data)
    service = build("gmail", "v1", credentials=creds)
    profile = service.users().getProfile(userId="me").execute()
    return {
        "email": profile.get("emailAddress"),
        "messages_total": profile.get("messagesTotal"),
        "threads_total": profile.get("threadsTotal"),
    }


def _test_calendar(creds_data: dict) -> dict:
    """Test Calendar: list calendars to verify access."""
    creds = Credentials.from_authorized_user_info(creds_data)
    service = build("calendar", "v3", credentials=creds)
    result = service.calendarList().list(maxResults=5).execute()
    calendars = result.get("items", [])
    return {
        "calendars_found": len(calendars),
        "calendars": [
            {
                "id": c.get("id"),
                "summary": c.get("summary"),
                "primary": c.get("primary", False),
            }
            for c in calendars[:5]
        ],
    }


def _test_analytics(creds_data: dict) -> dict:
    """Test Analytics: fetch account summaries."""
    creds = Credentials.from_authorized_user_info(creds_data)
    service = build("analyticsadmin", "v1beta", credentials=creds)
    response = service.accountSummaries().list().execute()
    summaries = response.get("accountSummaries", [])
    return {
        "accounts_found": len(summaries),
        "accounts": [
            {
                "name": s.get("displayName"),
                "properties": len(s.get("propertySummaries", [])),
            }
            for s in summaries[:5]
        ],
    }


def _test_youtube(creds_data: dict) -> dict:
    """Test YouTube: fetch channel info."""
    creds_copy = creds_data.copy()
    if "client_id" not in creds_copy:
        creds_copy["client_id"] = settings.GOOGLE_CLIENT_ID
    if "client_secret" not in creds_copy:
        creds_copy["client_secret"] = settings.GOOGLE_CLIENT_SECRET
    creds = Credentials.from_authorized_user_info(creds_copy)
    service = build("youtube", "v3", credentials=creds)
    response = service.channels().list(mine=True, part="snippet,statistics").execute()
    items = response.get("items", [])
    if not items:
        return {"channel": None, "note": "No se encontró un canal de YouTube asociado"}
    ch = items[0]
    return {
        "channel_id": ch.get("id"),
        "title": ch.get("snippet", {}).get("title"),
        "subscribers": ch.get("statistics", {}).get("subscriberCount"),
        "videos": ch.get("statistics", {}).get("videoCount"),
    }


# Maps service slug -> test function
_SERVICE_TESTS: dict[str, callable] = {
    "gmail": _test_gmail,
    "calendar": _test_calendar,
    "analytics": _test_analytics,
    "youtube": _test_youtube,
}


def _run_service_test(
    test_fn: callable,
    creds_data: dict,
    service_slug: str,
    tenant_id: Any,
) -> dict:
    """Execute a single service test and return a result dict.

    Returns a dict with 'status' and context. Adds '_auth_error': True
    on auth-related failures (stripped before sending to client).
    """
    try:
        data = test_fn(creds_data)
    except RefreshError as exc:
        logger.warning(
            "google_workspace_test_refresh_error",
            tenant_id=str(tenant_id),
            service=service_slug,
            error=str(exc),
        )
        return {
            "status": "error",
            "_auth_error": True,
            "error": "Token expirado o revocado. Reconecta tu cuenta de Google.",
            "detail": str(exc),
        }
    except HttpError as exc:
        error_reason = str(exc)
        if exc.resp.status >= 500:
            with sentry_sdk.push_scope() as scope:
                scope.set_tag("tenant_id", str(tenant_id))
                scope.set_tag("provider", "google_workspace")
                scope.set_tag("service", service_slug)
                scope.set_tag("failure_type", "google_api_5xx")
                sentry_sdk.capture_exception(exc)
        logger.exception(
            "google_workspace_test_http_error",
            tenant_id=str(tenant_id),
            service=service_slug,
            status_code=exc.resp.status,
            error=error_reason,
        )
        return {
            "status": "error",
            "error": f"Error de API de Google: {exc.resp.status}",
            "detail": error_reason,
        }
    except Exception as exc:
        with sentry_sdk.push_scope() as scope:
            scope.set_tag("tenant_id", str(tenant_id))
            scope.set_tag("provider", "google_workspace")
            scope.set_tag("service", service_slug)
            scope.set_tag("failure_type", "unexpected")
            sentry_sdk.capture_exception(exc)
        logger.exception(
            "google_workspace_test_unexpected_error",
            tenant_id=str(tenant_id),
            service=service_slug,
            error=str(exc),
        )
        return {
            "status": "error",
            "error": f"Error inesperado: {type(exc).__name__}",
            "detail": str(exc),
        }

    else:
        return {"status": "ok", "data": data}


@router.post("/test", response_model=ConnectionTestResponse)
async def test_connection(
    user: Annotated[User, Depends(get_current_user)],
    repo: Annotated[ChannelConnectionRepository, Depends(_get_repo)],
):
    """
    Tests the Google Workspace connection by probing each active service.
    Returns per-service results or the exact failure reason.
    Reports programming/infrastructure errors to Sentry.
    """
    # Find any connection with credentials (they all share the same OAuth token)
    creds_data = None
    for channel_type in SERVICE_MAP.values():
        conn = repo.get_by_tenant_and_type(user.tenant_id, channel_type)
        if conn and conn.credentials:
            creds_data = conn.credentials
            break

    if not creds_data:
        raise HTTPException(
            status_code=404,
            detail="No hay credenciales de Google Workspace. Conecta tu cuenta primero.",
        )

    results: dict[str, dict] = {}
    any_success = False
    has_auth_error = False

    for service_slug, test_fn in _SERVICE_TESTS.items():
        # Only test services that have active connections
        channel_type = SERVICE_MAP.get(service_slug)
        if not channel_type:
            continue
        conn = repo.get_by_tenant_and_type(user.tenant_id, channel_type)
        if not conn or not conn.is_active:
            results[service_slug] = {
                "status": "skipped",
                "reason": "Servicio desactivado",
            }
            continue

        result = _run_service_test(test_fn, creds_data, service_slug, user.tenant_id)
        results[service_slug] = result
        if result["status"] == "ok":
            any_success = True
        elif result.get("_auth_error"):
            has_auth_error = True

    if has_auth_error:
        return ConnectionTestResponse(
            status="auth_error",
            message="Las credenciales de Google han expirado o fueron revocadas. Reconecta tu cuenta.",
            details=results,
        )

    if any_success:
        failed = [s for s, r in results.items() if r.get("status") == "error"]
        if failed:
            return ConnectionTestResponse(
                status="partial",
                message=f"Conexión parcial. Servicios con error: {', '.join(failed)}.",
                details=results,
            )
        return ConnectionTestResponse(
            status="active",
            message="Todos los servicios de Google están funcionando correctamente.",
            details=results,
        )

    return ConnectionTestResponse(
        status="error",
        message="No se pudo conectar con ningún servicio de Google.",
        details=results,
    )

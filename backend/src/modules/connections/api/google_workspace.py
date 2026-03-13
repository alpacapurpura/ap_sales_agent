"""
Google Workspace Unified OAuth Router.

Handles a single OAuth flow that grants access to all Google services
(Gmail, Calendar, Analytics, YouTube) at once. The code is exchanged
ONCE and the resulting credentials are distributed to each service.
"""
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
import json
import os
import structlog

from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from src.core.config import settings
from src.core.database import get_db
from src.modules.iam.api.dependencies import get_current_user
from src.modules.iam.domain.user import User
from src.modules.connections.domain.enums import ChannelType
from src.modules.connections.infrastructure.repositories import ChannelConnectionRepository

# Allow OAuth scope changes (e.g. if user granted extra scopes previously)
os.environ["OAUTHLIB_RELAX_TOKEN_SCOPE"] = "1"

router = APIRouter(tags=["google-workspace"])
logger = structlog.get_logger()

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
        }
    }


@router.get("/auth-url")
async def get_auth_url(
    user: User = Depends(get_current_user),
):
    """Returns a Google OAuth URL requesting ALL workspace scopes at once."""
    flow = Flow.from_client_config(_get_client_config(), scopes=WORKSPACE_SCOPES)
    flow.redirect_uri = settings.GOOGLE_REDIRECT_URI

    authorization_url, state = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",  # Force consent to always get a refresh_token
    )
    return {"url": authorization_url, "state": state}


@router.post("/callback")
async def oauth_callback(
    code: str = Body(..., embed=True),
    user: User = Depends(get_current_user),
    repo: ChannelConnectionRepository = Depends(_get_repo),
):
    """
    Exchanges the authorization code ONCE and stores the resulting credentials
    for all 4 Google services (Gmail, Calendar, Analytics, YouTube).
    """
    # Exchange code for credentials
    flow = Flow.from_client_config(_get_client_config(), scopes=WORKSPACE_SCOPES)
    flow.redirect_uri = settings.GOOGLE_REDIRECT_URI

    try:
        flow.fetch_token(code=code)
        creds = flow.credentials
        creds_data = json.loads(creds.to_json())
    except Exception as e:
        logger.error("google_workspace_oauth_exchange_failed", error=str(e))
        raise HTTPException(status_code=400, detail="Error de autenticación con Google. Intenta de nuevo.")

    # Get user profile to obtain email address
    try:
        gmail_creds = Credentials.from_authorized_user_info(creds_data)
        gmail_service = build("gmail", "v1", credentials=gmail_creds)
        profile = gmail_service.users().getProfile(userId="me").execute()
        email = profile.get("emailAddress", "")
    except Exception as e:
        logger.warning("google_workspace_profile_fetch_failed", error=str(e))
        email = ""

    # Store the SAME credentials for all 4 services
    for service_slug, channel_type in SERVICE_MAP.items():
        service_config: dict = {}
        if service_slug == "gmail":
            service_config = {"email": email}
        elif service_slug == "calendar":
            service_config = {"email": email}

        repo.upsert(
            tenant_id=user.tenant_id,
            channel_type=channel_type,
            credentials=creds_data,
            config=service_config,
        )

    logger.info("google_workspace_connected", tenant_id=str(user.tenant_id), email=email)
    return {"status": "connected", "email": email}


@router.get("/status")
async def get_status(
    user: User = Depends(get_current_user),
    repo: ChannelConnectionRepository = Depends(_get_repo),
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


@router.patch("/services/{service}")
async def toggle_service(
    service: str,
    is_active: bool = Body(..., embed=True),
    user: User = Depends(get_current_user),
    repo: ChannelConnectionRepository = Depends(_get_repo),
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
    user: User = Depends(get_current_user),
    repo: ChannelConnectionRepository = Depends(_get_repo),
):
    """Soft-deletes all Google service connections for this tenant."""
    deactivated = []
    for service_slug, channel_type in SERVICE_MAP.items():
        connection = repo.get_by_tenant_and_type(user.tenant_id, channel_type)
        if connection and connection.is_active:
            repo.deactivate(connection)
            deactivated.append(service_slug)

    return {"status": "disconnected", "services": deactivated}

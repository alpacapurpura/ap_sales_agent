import asyncio

import structlog
from fastapi import APIRouter, Body, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.modules.connections.api.dto.google_analytics import (
    GA4PropertySummary,
    GoogleAnalyticsCallbackResponse,
    GoogleAnalyticsStatusResponse,
    PropertySelectRequest,
    PropertySelectResponse,
    SelectedProperty,
)
from src.modules.connections.domain.enums import ChannelType
from src.modules.connections.infrastructure.channels.google_analytics import (
    GoogleAnalyticsAdapter,
)
from src.modules.connections.infrastructure.models import ChannelConnectionModel
from src.modules.connections.infrastructure.repositories import (
    ChannelConnectionRepository,
)
from src.modules.iam.api.dependencies import get_current_user
from src.modules.iam.domain.user import User

router = APIRouter(tags=["google_analytics"])
logger = structlog.get_logger()


class GoogleAnalyticsConfig(BaseModel):
    client_id: str
    client_secret: str


def _get_repo(db: Session = Depends(get_db)) -> ChannelConnectionRepository:
    return ChannelConnectionRepository(db)


def _build_adapter(
    connection: ChannelConnectionModel, with_creds: bool = False
) -> GoogleAnalyticsAdapter:
    """Build a GoogleAnalyticsAdapter from a connection model."""
    client_config = {
        "client_id": connection.credentials.get("client_id"),
        "client_secret": connection.credentials.get("client_secret"),
    }
    creds = dict(connection.credentials) if with_creds else None
    return GoogleAnalyticsAdapter(client_config=client_config, credentials_data=creds)


@router.put("/config")
async def save_config(
    config: GoogleAnalyticsConfig,
    user: User = Depends(get_current_user),
    repo: ChannelConnectionRepository = Depends(_get_repo),
):
    """Save Google Analytics client configuration (client_id, client_secret)."""
    connection = repo.get_by_tenant_and_type(
        user.tenant_id, ChannelType.GOOGLE_ANALYTICS
    )

    creds_update = {
        "client_id": config.client_id,
        "client_secret": config.client_secret,
    }

    if connection:
        existing_creds = dict(connection.credentials) if connection.credentials else {}
        existing_creds.update(creds_update)
        repo.update_credentials(connection, existing_creds)
    else:
        connection = ChannelConnectionModel(
            tenant_id=user.tenant_id,
            channel_type=ChannelType.GOOGLE_ANALYTICS.value,
            credentials=creds_update,
            config={},
            is_active=False,
        )
        repo.db.add(connection)
        repo.db.commit()

    return {"status": "config_saved"}


@router.get("/auth-url")
async def get_auth_url(
    redirect_uri: str | None = None,
    user: User = Depends(get_current_user),
    repo: ChannelConnectionRepository = Depends(_get_repo),
):
    connection = repo.get_by_tenant_and_type(
        user.tenant_id, ChannelType.GOOGLE_ANALYTICS
    )

    if (
        not connection
        or not connection.credentials
        or "client_id" not in connection.credentials
        or "client_secret" not in connection.credentials
    ):
        raise HTTPException(
            status_code=400,
            detail="Configuracion de cliente no encontrada. Configure client_id y client_secret primero.",
        )

    adapter = _build_adapter(connection)
    url, state = adapter.get_authorization_url(redirect_uri)
    return {"url": url, "state": state}


@router.post("/callback", response_model=GoogleAnalyticsCallbackResponse)
async def oauth_callback(
    code: str = Body(..., embed=True),
    redirect_uri: str | None = Body(None, embed=True),
    user: User = Depends(get_current_user),
    repo: ChannelConnectionRepository = Depends(_get_repo),
):
    connection = repo.get_by_tenant_and_type(
        user.tenant_id, ChannelType.GOOGLE_ANALYTICS
    )

    if (
        not connection
        or not connection.credentials
        or "client_id" not in connection.credentials
        or "client_secret" not in connection.credentials
    ):
        raise HTTPException(
            status_code=400, detail="Configuracion de cliente no encontrada."
        )

    # Exchange code for tokens
    try:
        adapter = _build_adapter(connection)
        token_data = await asyncio.to_thread(adapter.exchange_code, code, redirect_uri)
    except Exception as e:
        logger.error("google_analytics_oauth_exchange_failed", error=str(e))
        raise HTTPException(status_code=400, detail="Error de autenticacion con Google")

    # Save credentials FIRST (don't block on Admin API)
    full_creds = dict(connection.credentials)
    full_creds.update(token_data)
    connection.credentials = full_creds
    connection.is_active = True
    repo.db.commit()

    # Try to fetch properties (graceful fallback)
    properties: list[GA4PropertySummary] = []
    try:
        adapter = _build_adapter(connection, with_creds=True)
        flat = await asyncio.to_thread(adapter.get_flat_properties)
        properties = [GA4PropertySummary(**p) for p in flat]

        # Update config with account count
        repo.update_config(connection, {"account_count": len(flat)})
    except Exception as e:
        logger.warning(
            "google_analytics_properties_fetch_failed",
            error=str(e),
            tenant_id=str(user.tenant_id),
        )

    return GoogleAnalyticsCallbackResponse(status="connected", properties=properties)


@router.get("/status", response_model=GoogleAnalyticsStatusResponse)
async def get_status(
    user: User = Depends(get_current_user),
    repo: ChannelConnectionRepository = Depends(_get_repo),
):
    connection = repo.get_by_tenant_and_type(
        user.tenant_id, ChannelType.GOOGLE_ANALYTICS
    )

    if not connection:
        return GoogleAnalyticsStatusResponse(is_connected=False, is_configured=False)

    has_client_id = bool(
        connection.credentials and connection.credentials.get("client_id")
    )
    is_connected = bool(
        connection.is_active
        and connection.credentials
        and connection.credentials.get("refresh_token")
    )

    # Read selected property from config (fast, no API call)
    selected = None
    config = connection.config or {}
    if config.get("property_id"):
        selected = SelectedProperty(
            property_id=config["property_id"],
            display_name=config.get("property_display_name", config["property_id"]),
        )

    return GoogleAnalyticsStatusResponse(
        is_connected=is_connected,
        is_configured=has_client_id,
        selected_property=selected,
    )


@router.get("/properties", response_model=list[GA4PropertySummary])
async def get_properties(
    user: User = Depends(get_current_user),
    repo: ChannelConnectionRepository = Depends(_get_repo),
):
    connection = repo.get_active(user.tenant_id, ChannelType.GOOGLE_ANALYTICS)

    if not connection or not connection.credentials:
        raise HTTPException(status_code=400, detail="Google Analytics no conectado")

    try:
        adapter = _build_adapter(connection, with_creds=True)
        flat = await asyncio.to_thread(adapter.get_flat_properties)
        return [GA4PropertySummary(**p) for p in flat]
    except Exception as e:
        logger.error("google_analytics_properties_failed", error=str(e))
        raise HTTPException(
            status_code=500, detail="Error al obtener propiedades de Google Analytics"
        )


@router.put("/properties/select", response_model=PropertySelectResponse)
async def select_property(
    body: PropertySelectRequest,
    user: User = Depends(get_current_user),
    repo: ChannelConnectionRepository = Depends(_get_repo),
):
    connection = repo.get_active(user.tenant_id, ChannelType.GOOGLE_ANALYTICS)

    if not connection or not connection.credentials:
        raise HTTPException(status_code=400, detail="Google Analytics no conectado")

    # Try to validate + get display_name from Admin API
    display_name = body.property_id
    try:
        adapter = _build_adapter(connection, with_creds=True)
        flat = await asyncio.to_thread(adapter.get_flat_properties)
        match = next((p for p in flat if p["property_id"] == body.property_id), None)
        if match:
            display_name = match["display_name"]
    except Exception as e:
        logger.warning("property_validation_skipped", error=str(e))
        # Allow saving anyway (manual input fallback)

    # Save property_id in credentials (for ETL provider)
    creds = dict(connection.credentials)
    creds["property_id"] = body.property_id
    repo.update_credentials(connection, creds)

    # Save display info in config (for UI, no decryption needed)
    repo.update_config(
        connection,
        {
            "property_id": body.property_id,
            "property_display_name": display_name,
        },
    )

    logger.info(
        "ga4_property_selected",
        tenant_id=str(user.tenant_id),
        property_id=body.property_id,
    )

    return PropertySelectResponse(
        status="ok",
        property_id=body.property_id,
        display_name=display_name,
    )


@router.delete("/disconnect")
async def disconnect(
    user: User = Depends(get_current_user),
    repo: ChannelConnectionRepository = Depends(_get_repo),
):
    connection = repo.get_by_tenant_and_type(
        user.tenant_id, ChannelType.GOOGLE_ANALYTICS
    )
    if connection:
        repo.deactivate(connection)
    return {"status": "disconnected"}


@router.post("/test")
async def test_connection(
    user: User = Depends(get_current_user),
    repo: ChannelConnectionRepository = Depends(_get_repo),
):
    connection = repo.get_active(user.tenant_id, ChannelType.GOOGLE_ANALYTICS)

    if not connection or not connection.credentials:
        raise HTTPException(status_code=400, detail="Google Analytics no conectado")

    try:
        adapter = _build_adapter(connection, with_creds=True)
        summaries = await asyncio.to_thread(adapter.get_account_summaries)
        return {"status": "ok", "message": "Conexion exitosa", "data": summaries}
    except Exception as e:
        logger.error("google_analytics_test_failed", error=str(e))
        return {"status": "error", "message": str(e)}

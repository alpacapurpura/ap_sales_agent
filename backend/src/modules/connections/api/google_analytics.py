import asyncio

from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel
import structlog

from src.core.database import get_db
from src.modules.iam.api.dependencies import get_current_user
from src.modules.iam.domain.user import User
from src.modules.connections.domain.enums import ChannelType
from src.modules.connections.infrastructure.repositories import ChannelConnectionRepository
from src.modules.connections.infrastructure.models import ChannelConnectionModel
from src.modules.connections.infrastructure.channels.google_analytics import GoogleAnalyticsAdapter
from src.modules.connections.api.dto.google_analytics import GoogleAnalyticsStatusResponse

router = APIRouter(tags=["google_analytics"])
logger = structlog.get_logger()


class GoogleAnalyticsConfig(BaseModel):
    client_id: str
    client_secret: str


def _get_repo(db: Session = Depends(get_db)) -> ChannelConnectionRepository:
    return ChannelConnectionRepository(db)


@router.put("/config")
async def save_config(
    config: GoogleAnalyticsConfig,
    user: User = Depends(get_current_user),
    repo: ChannelConnectionRepository = Depends(_get_repo),
):
    """Save Google Analytics client configuration (client_id, client_secret)."""
    connection = repo.get_by_tenant_and_type(user.tenant_id, ChannelType.GOOGLE_ANALYTICS)

    creds_update = {"client_id": config.client_id, "client_secret": config.client_secret}

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
    redirect_uri: Optional[str] = None,
    user: User = Depends(get_current_user),
    repo: ChannelConnectionRepository = Depends(_get_repo),
):
    connection = repo.get_by_tenant_and_type(user.tenant_id, ChannelType.GOOGLE_ANALYTICS)

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

    client_config = {
        "client_id": connection.credentials["client_id"],
        "client_secret": connection.credentials["client_secret"],
    }

    adapter = GoogleAnalyticsAdapter(client_config=client_config)
    url, state = adapter.get_authorization_url(redirect_uri)
    return {"url": url, "state": state}


@router.post("/callback")
async def oauth_callback(
    code: str = Body(..., embed=True),
    redirect_uri: Optional[str] = Body(None, embed=True),
    user: User = Depends(get_current_user),
    repo: ChannelConnectionRepository = Depends(_get_repo),
):
    connection = repo.get_by_tenant_and_type(user.tenant_id, ChannelType.GOOGLE_ANALYTICS)

    if (
        not connection
        or not connection.credentials
        or "client_id" not in connection.credentials
        or "client_secret" not in connection.credentials
    ):
        raise HTTPException(status_code=400, detail="Configuracion de cliente no encontrada.")

    client_config = {
        "client_id": connection.credentials["client_id"],
        "client_secret": connection.credentials["client_secret"],
    }

    try:
        adapter = GoogleAnalyticsAdapter(client_config=client_config)
        token_data = await asyncio.to_thread(adapter.exchange_code, code, redirect_uri)
    except Exception as e:
        logger.error("google_analytics_oauth_exchange_failed", error=str(e))
        raise HTTPException(status_code=400, detail="Error de autenticacion con Google")

    full_creds = dict(connection.credentials)
    full_creds.update(token_data)

    try:
        adapter = GoogleAnalyticsAdapter(client_config=client_config, credentials_data=full_creds)
        summaries = await asyncio.to_thread(adapter.get_account_summaries)
    except Exception as e:
        logger.error("failed_to_get_google_analytics_summaries", error=str(e))
        raise HTTPException(
            status_code=400,
            detail="No se pudo obtener informacion de Google Analytics. Verifica los permisos.",
        )

    connection.credentials = full_creds
    connection.config = {"account_count": len(summaries)}
    connection.is_active = True
    repo.db.commit()

    return {"status": "connected", "account_count": len(summaries)}


@router.get("/status", response_model=GoogleAnalyticsStatusResponse)
async def get_status(
    user: User = Depends(get_current_user),
    repo: ChannelConnectionRepository = Depends(_get_repo),
):
    connection = repo.get_active(user.tenant_id, ChannelType.GOOGLE_ANALYTICS)

    if not connection:
        return GoogleAnalyticsStatusResponse(is_connected=False)

    return GoogleAnalyticsStatusResponse(is_connected=True, account_summary=[])


@router.delete("/disconnect")
async def disconnect(
    user: User = Depends(get_current_user),
    repo: ChannelConnectionRepository = Depends(_get_repo),
):
    connection = repo.get_by_tenant_and_type(user.tenant_id, ChannelType.GOOGLE_ANALYTICS)
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

    client_config = {
        "client_id": connection.credentials.get("client_id"),
        "client_secret": connection.credentials.get("client_secret"),
    }

    if not client_config["client_id"] or not client_config["client_secret"]:
        raise HTTPException(status_code=400, detail="Configuracion incompleta")

    try:
        adapter = GoogleAnalyticsAdapter(client_config=client_config, credentials_data=connection.credentials)
        summaries = await asyncio.to_thread(adapter.get_account_summaries)
        return {"status": "ok", "message": "Conexion exitosa", "data": summaries}
    except Exception as e:
        logger.error("google_analytics_test_failed", error=str(e))
        return {"status": "error", "message": str(e)}


@router.get("/properties")
async def get_properties(
    user: User = Depends(get_current_user),
    repo: ChannelConnectionRepository = Depends(_get_repo),
):
    connection = repo.get_active(user.tenant_id, ChannelType.GOOGLE_ANALYTICS)

    if not connection or not connection.credentials:
        raise HTTPException(status_code=400, detail="Google Analytics no conectado")

    client_config = {
        "client_id": connection.credentials.get("client_id"),
        "client_secret": connection.credentials.get("client_secret"),
    }

    if not client_config["client_id"] or not client_config["client_secret"]:
        raise HTTPException(status_code=400, detail="Configuracion incompleta")

    try:
        adapter = GoogleAnalyticsAdapter(client_config=client_config, credentials_data=connection.credentials)
        summaries = await asyncio.to_thread(adapter.get_account_summaries)
        return summaries
    except Exception as e:
        logger.error("google_analytics_properties_failed", error=str(e))
        raise HTTPException(status_code=500, detail="Error al obtener propiedades")

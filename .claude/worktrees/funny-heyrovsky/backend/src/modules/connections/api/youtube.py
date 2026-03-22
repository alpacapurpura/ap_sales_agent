from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified
from typing import Optional, Dict, Any
import structlog

from src.core.database import get_db
from src.modules.iam.api.dependencies import get_current_user
from src.modules.iam.domain.user import User
from src.modules.iam.infrastructure.models.tenant_model import TenantModel
from src.modules.connections.domain.enums import ChannelType
from src.modules.connections.infrastructure.repositories import ChannelConnectionRepository
from src.modules.connections.infrastructure.channels.youtube import YoutubeAdapter
from src.modules.connections.api.dto.youtube import YoutubeStatusResponse

router = APIRouter(tags=["youtube"])
logger = structlog.get_logger()


def _get_repo(db: Session = Depends(get_db)) -> ChannelConnectionRepository:
    return ChannelConnectionRepository(db)


def _get_youtube_config(db: Session, tenant_id: Any) -> Dict[str, str]:
    """Retrieve YouTube App configuration from Tenant config."""
    from sqlalchemy import select

    stmt = select(TenantModel).where(TenantModel.id == tenant_id)
    tenant = db.execute(stmt).scalars().first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant no encontrado")

    config = tenant.config_json or {}
    youtube_config = config.get("integrations", {}).get("youtube", {})

    client_id = youtube_config.get("client_id")
    client_secret = youtube_config.get("client_secret")

    if not client_id or not client_secret:
        raise HTTPException(
            status_code=400,
            detail="YouTube no esta configurado. Por favor ingresa el Client ID y Secret en la configuracion.",
        )

    return {"client_id": client_id, "client_secret": client_secret}


@router.put("/config")
async def update_config(
    client_id: str = Body(..., embed=True),
    client_secret: str = Body(..., embed=True),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    from sqlalchemy import select

    stmt = select(TenantModel).where(TenantModel.id == user.tenant_id)
    tenant = db.execute(stmt).scalars().first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant no encontrado")

    config = dict(tenant.config_json or {})
    if "integrations" not in config:
        config["integrations"] = {}

    config["integrations"]["youtube"] = {
        "client_id": client_id,
        "client_secret": client_secret,
    }

    tenant.config_json = config
    flag_modified(tenant, "config_json")
    db.add(tenant)
    db.commit()

    return {"status": "updated", "message": "Configuracion de YouTube guardada correctamente"}


@router.get("/auth-url")
async def get_auth_url(
    redirect_uri: Optional[str] = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    client_config = _get_youtube_config(db, user.tenant_id)
    adapter = YoutubeAdapter(client_config=client_config)
    url, state = adapter.get_authorization_url(redirect_uri)
    return {"url": url, "state": state}


@router.post("/callback")
async def oauth_callback(
    code: str = Body(..., embed=True),
    redirect_uri: Optional[str] = Body(None, embed=True),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    repo: ChannelConnectionRepository = Depends(_get_repo),
):
    client_config = _get_youtube_config(db, user.tenant_id)
    adapter = YoutubeAdapter(client_config=client_config)

    try:
        creds_data = adapter.exchange_code(code, redirect_uri)
    except Exception as e:
        logger.error("youtube_oauth_exchange_failed", error=str(e))
        raise HTTPException(status_code=400, detail=f"Error de autenticacion con Google: {str(e)}")

    try:
        authenticated_adapter = YoutubeAdapter(client_config=client_config, credentials_data=creds_data)
        channel_info = authenticated_adapter.get_channel_info()
        channel_id = channel_info.get("id")
        if not channel_id:
            raise ValueError("No YouTube channel found for this account")
    except Exception as e:
        logger.error("failed_to_get_youtube_channel", error=str(e))
        raise HTTPException(
            status_code=400,
            detail="No se pudo obtener el canal de YouTube. Verifica que tengas un canal creado.",
        )

    config_data = {
        "channel_id": channel_id,
        "channel_title": channel_info.get("title"),
        "customUrl": channel_info.get("customUrl"),
        "thumbnails": channel_info.get("thumbnails"),
        "statistics": channel_info.get("statistics"),
    }

    repo.upsert(
        tenant_id=user.tenant_id,
        channel_type=ChannelType.YOUTUBE,
        credentials=creds_data,
        config=config_data,
    )

    return {"status": "connected", "channel": config_data}


@router.get("/status", response_model=YoutubeStatusResponse)
async def get_status(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    repo: ChannelConnectionRepository = Depends(_get_repo),
):
    try:
        _get_youtube_config(db, user.tenant_id)
        is_configured = True
    except HTTPException:
        is_configured = False

    connection = repo.get_active(user.tenant_id, ChannelType.YOUTUBE)

    if not connection:
        return YoutubeStatusResponse(is_connected=False, is_configured=is_configured)

    config = connection.config or {}
    return YoutubeStatusResponse(
        is_connected=True,
        is_configured=is_configured,
        channel_id=config.get("channel_id"),
        channel_title=config.get("channel_title"),
        channel_data=config,
    )


@router.delete("/disconnect")
async def disconnect(
    user: User = Depends(get_current_user),
    repo: ChannelConnectionRepository = Depends(_get_repo),
):
    connection = repo.get_by_tenant_and_type(user.tenant_id, ChannelType.YOUTUBE)
    if connection:
        repo.deactivate(connection)
    return {"status": "disconnected"}


@router.post("/test")
async def test_connection(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    repo: ChannelConnectionRepository = Depends(_get_repo),
):
    connection = repo.get_active(user.tenant_id, ChannelType.YOUTUBE)

    if not connection or not connection.credentials:
        raise HTTPException(status_code=400, detail="YouTube no conectado")

    client_config = _get_youtube_config(db, user.tenant_id)

    try:
        adapter = YoutubeAdapter(client_config=client_config, credentials_data=connection.credentials)
        channel_info = adapter.get_channel_info()
        return {"status": "ok", "message": "Conexion exitosa", "data": channel_info}
    except Exception as e:
        logger.error("youtube_test_failed", error=str(e))
        return {"status": "error", "message": str(e)}

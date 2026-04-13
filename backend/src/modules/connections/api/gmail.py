import structlog
from fastapi import APIRouter, Body, Depends, HTTPException
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.modules.connections.api.dto.common import ConnectionTestResponse
from src.modules.connections.api.dto.gmail import GmailStatusResponse
from src.modules.connections.domain.enums import ChannelType
from src.modules.connections.infrastructure.channels.gmail import GmailAdapter
from src.modules.connections.infrastructure.repositories import (
    ChannelConnectionRepository,
)
from src.modules.iam.api.dependencies import get_current_user
from src.modules.iam.domain.user import User

router = APIRouter(tags=["gmail"])
logger = structlog.get_logger()


def _get_repo(db: Session = Depends(get_db)) -> ChannelConnectionRepository:
    return ChannelConnectionRepository(db)


@router.get("/auth-url")
async def get_auth_url(
    redirect_uri: str | None = None,
    user: User = Depends(get_current_user),
):
    url, state = GmailAdapter.get_authorization_url(redirect_uri)
    return {"url": url, "state": state}


@router.post("/callback")
async def oauth_callback(
    code: str = Body(..., embed=True),
    redirect_uri: str | None = Body(None, embed=True),
    user: User = Depends(get_current_user),
    repo: ChannelConnectionRepository = Depends(_get_repo),
):
    try:
        creds_data = GmailAdapter.exchange_code(code, redirect_uri)
    except Exception as e:
        logger.error("gmail_oauth_exchange_failed", error=str(e))
        raise HTTPException(
            status_code=400,
            detail="Error de autenticacion con Google",
        ) from e

    try:
        adapter = GmailAdapter(creds_data)
        profile = adapter.get_profile()
        email = profile.get("emailAddress")
        if not email:
            msg = "Email address not found in profile"
            raise ValueError(msg)
    except Exception as e:
        logger.error("failed_to_get_gmail_profile", error=str(e))
        raise HTTPException(
            status_code=400,
            detail="No se pudo obtener el perfil de Gmail. Verifica los permisos.",
        ) from e

    repo.upsert(
        tenant_id=user.tenant_id,
        channel_type=ChannelType.GMAIL,
        credentials=creds_data,
        config={"email": email},
    )
    return {"status": "connected", "email": email}


@router.get("/status", response_model=GmailStatusResponse)
async def get_status(
    user: User = Depends(get_current_user),
    repo: ChannelConnectionRepository = Depends(_get_repo),
):
    connection = repo.get_active(user.tenant_id, ChannelType.GMAIL)

    if not connection:
        return GmailStatusResponse(is_connected=False)

    return GmailStatusResponse(
        is_connected=True,
        email=connection.config.get("email"),
    )


@router.delete("/disconnect")
async def disconnect(
    user: User = Depends(get_current_user),
    repo: ChannelConnectionRepository = Depends(_get_repo),
):
    connection = repo.get_by_tenant_and_type(user.tenant_id, ChannelType.GMAIL)
    if connection:
        repo.deactivate(connection)
    return {"status": "disconnected"}


@router.post("/test", response_model=ConnectionTestResponse)
async def test_connection(
    user: User = Depends(get_current_user),
    repo: ChannelConnectionRepository = Depends(_get_repo),
):
    connection = repo.get_active(user.tenant_id, ChannelType.GMAIL)

    if not connection or not connection.credentials:
        raise HTTPException(status_code=400, detail="Gmail no conectado")

    try:
        adapter = GmailAdapter(connection.credentials)
        profile = adapter.get_profile()
        return {"status": "ok", "message": "Conexion exitosa", "data": profile}
    except Exception as e:
        logger.error("gmail_test_failed", error=str(e))
        return {"status": "error", "message": str(e)}

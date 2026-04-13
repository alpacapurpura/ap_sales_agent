from typing import Annotated, Any

import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.modules.connections.domain.enums import ChannelType
from src.modules.connections.infrastructure.marketing_connectors.manychat import (
    ManyChatConnector,
)
from src.modules.connections.infrastructure.repositories import (
    ChannelConnectionRepository,
)
from src.modules.iam.api.dependencies import get_current_user
from src.modules.iam.domain.user import User

logger = structlog.get_logger()
router = APIRouter()


class ManyChatConnectRequest(BaseModel):
    api_key: str


class ManyChatStatusResponse(BaseModel):
    is_connected: bool
    account_info: dict[str, Any] | None = None


class ConnectionResponse(BaseModel):
    status: str
    message: str
    details: dict[str, Any] | None = None


def _get_repo(db: Session = Depends(get_db)) -> ChannelConnectionRepository:
    return ChannelConnectionRepository(db)


@router.get("/status", response_model=ManyChatStatusResponse)
async def get_manychat_status(
    user: Annotated[User, Depends(get_current_user)],
    repo: Annotated[ChannelConnectionRepository, Depends(_get_repo)],
):
    connection = repo.get_active(user.tenant_id, ChannelType.MANYCHAT)

    if not connection:
        return ManyChatStatusResponse(is_connected=False)

    return ManyChatStatusResponse(
        is_connected=True,
        account_info=connection.config.get("account_info"),
    )


@router.post("/connect", response_model=ConnectionResponse)
async def connect_manychat(
    request: ManyChatConnectRequest,
    user: Annotated[User, Depends(get_current_user)],
    repo: Annotated[ChannelConnectionRepository, Depends(_get_repo)],
):
    is_valid, result = await ManyChatConnector.verify_connection(
        api_key=request.api_key,
    )

    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to connect to ManyChat: {result.get('error')}",
        )

    repo.upsert(
        tenant_id=user.tenant_id,
        channel_type=ChannelType.MANYCHAT,
        credentials={"api_key": request.api_key},
        config={"account_info": result},
    )

    return ConnectionResponse(
        status="connected",
        message="ManyChat connected successfully",
        details=result,
    )


@router.post("/disconnect", response_model=ConnectionResponse)
async def disconnect_manychat(
    user: Annotated[User, Depends(get_current_user)],
    repo: Annotated[ChannelConnectionRepository, Depends(_get_repo)],
):
    connection = repo.get_by_tenant_and_type(user.tenant_id, ChannelType.MANYCHAT)

    if not connection:
        raise HTTPException(status_code=404, detail="No ManyChat connection found")

    repo.deactivate(connection)

    return ConnectionResponse(
        status="disconnected",
        message="ManyChat disconnected successfully",
    )


@router.post("/test", response_model=ConnectionResponse)
async def test_manychat_connection(
    user: Annotated[User, Depends(get_current_user)],
    repo: Annotated[ChannelConnectionRepository, Depends(_get_repo)],
):
    connection = repo.get_active(user.tenant_id, ChannelType.MANYCHAT)

    if not connection:
        raise HTTPException(
            status_code=404,
            detail="No active ManyChat connection found",
        )

    api_key = connection.credentials.get("api_key")
    if not api_key:
        raise HTTPException(status_code=400, detail="Incomplete connection data")

    is_valid, result = await ManyChatConnector.verify_connection(api_key=api_key)

    if is_valid:
        repo.update_config(connection, {"account_info": result})
        return ConnectionResponse(
            status="active",
            message="Connection is valid",
            details=result,
        )

    return ConnectionResponse(
        status="error",
        message="Connection test failed",
        details=result,
    )

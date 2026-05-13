"""Mailerlite API endpoints."""

from typing import Annotated, Any

import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from luana_core_connections.domain.enums import ChannelType
from luana_core_connections.infrastructure.marketing_connectors.mailerlite import (
    MailerliteConnector,
)
from luana_core_connections.infrastructure.repositories import (
    ChannelConnectionRepository,
)
from luana_core_iam.api.dependencies import get_current_user
from luana_core_iam.domain.user import User
from luana_core_platform.core.database import get_db
from pydantic import BaseModel
from sqlalchemy.orm import Session

logger = structlog.get_logger()
router = APIRouter()


class MailerliteConnectRequest(BaseModel):
    """Mailerlite Connect Request DTO."""

    api_key: str


class MailerliteStatusResponse(BaseModel):
    """Mailerlite Status Response DTO."""

    is_connected: bool
    account_info: dict[str, Any] | None = None


class ConnectionResponse(BaseModel):
    """Connection Response DTO."""

    status: str
    message: str
    details: dict[str, Any] | None = None


def _get_repo(db: Session = Depends(get_db)) -> ChannelConnectionRepository:
    return ChannelConnectionRepository(db)


@router.get("/status")
async def get_mailerlite_status(
    user: Annotated[User, Depends(get_current_user)],
    repo: Annotated[ChannelConnectionRepository, Depends(_get_repo)],
) -> MailerliteStatusResponse:
    """Retrieve mailerlite status."""
    connection = repo.get_active(user.tenant_id, ChannelType.MAILERLITE)

    if not connection:
        return MailerliteStatusResponse(is_connected=False)

    return MailerliteStatusResponse(
        is_connected=True,
        account_info=connection.config.get("account_info"),
    )


@router.post("/connect")
async def connect_mailerlite(
    request: MailerliteConnectRequest,
    user: Annotated[User, Depends(get_current_user)],
    repo: Annotated[ChannelConnectionRepository, Depends(_get_repo)],
) -> ConnectionResponse:
    """Connect mailerlite."""
    is_valid, result = await MailerliteConnector.verify_connection(
        api_key=request.api_key,
    )

    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to connect to MailerLite: {result.get('error')}",
        )

    repo.upsert(
        tenant_id=user.tenant_id,
        channel_type=ChannelType.MAILERLITE,
        credentials={"api_key": request.api_key},
        config={"account_info": result},
    )

    return ConnectionResponse(
        status="connected",
        message="MailerLite connected successfully",
        details=result,
    )


@router.post("/disconnect")
async def disconnect_mailerlite(
    user: Annotated[User, Depends(get_current_user)],
    repo: Annotated[ChannelConnectionRepository, Depends(_get_repo)],
) -> ConnectionResponse:
    """Disconnect mailerlite."""
    connection = repo.get_by_tenant_and_type(user.tenant_id, ChannelType.MAILERLITE)

    if not connection:
        raise HTTPException(status_code=404, detail="No MailerLite connection found")

    repo.deactivate(connection)

    return ConnectionResponse(
        status="disconnected",
        message="MailerLite disconnected successfully",
    )


@router.post("/test")
async def test_mailerlite_connection(
    user: Annotated[User, Depends(get_current_user)],
    repo: Annotated[ChannelConnectionRepository, Depends(_get_repo)],
) -> ConnectionResponse:
    """Test mailerlite connection."""
    connection = repo.get_active(user.tenant_id, ChannelType.MAILERLITE)

    if not connection:
        raise HTTPException(
            status_code=404,
            detail="No active MailerLite connection found",
        )

    api_key = connection.credentials.get("api_key")
    if not api_key:
        raise HTTPException(status_code=400, detail="Incomplete connection data")

    is_valid, result = await MailerliteConnector.verify_connection(api_key=api_key)

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

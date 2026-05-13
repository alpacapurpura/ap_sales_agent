"""Telegram API endpoints."""

from typing import Annotated

import structlog
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from luana_core_connections.api.dependencies import get_message_handler
from luana_core_connections.api.dto.common import (
    ConnectionTestResponse,
    TelegramConnectResponse,
)
from luana_core_connections.api.dto.telegram import (
    ChannelStatusResponse,
    TelegramConnectRequest,
)
from luana_core_connections.infrastructure.channels.telegram_service import (
    TelegramService,
)
from luana_core_iam.api.dependencies import get_current_user
from luana_core_iam.domain.user import User
from luana_core_platform.core.database import get_db
from sqlalchemy.orm import Session

router = APIRouter(tags=["Telegram"])
logger = structlog.get_logger()

# --- Webhooks ---


@router.post("/webhooks/telegram")
async def telegram_webhook_legacy(
    request: Request,
    background_tasks: BackgroundTasks,
    handler: Annotated[object, Depends(get_message_handler)],
) -> dict[str, str]:
    """Legacy Global Webhook. Uses settings.TELEGRAM_BOT_TOKEN."""
    payload = await request.json()
    await handler.handle_telegram_webhook(payload, background_tasks)
    return {"status": "ok"}


@router.post("/webhooks/telegram/{tenant_id}")
async def telegram_webhook_tenant(
    tenant_id: str,
    request: Request,
    background_tasks: BackgroundTasks,
    db: Annotated[Session, Depends(get_db)],
    handler: Annotated[object, Depends(get_message_handler)],
) -> dict[str, str]:
    """Multi-Tenant Webhook. Resolves bot token from Tenant configuration."""
    payload = await request.json()
    await handler.handle_telegram_webhook(
        payload,
        background_tasks,
        tenant_id=tenant_id,
        db=db,
    )
    return {"status": "ok"}


# --- Endpoints ---


@router.get("/status")
async def get_telegram_status(
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> ChannelStatusResponse:
    """Get current Telegram connection status for the tenant."""
    service = TelegramService(db)
    status_data = service.get_status(user.tenant_id)

    if not status_data.get("is_connected"):
        return ChannelStatusResponse(is_connected=False)

    return ChannelStatusResponse(**status_data)


@router.post("/connect")
async def connect_telegram(
    payload: TelegramConnectRequest,
    background_tasks: BackgroundTasks,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> TelegramConnectResponse:
    """Connect a Telegram Bot to the tenant.

    Validates token, sets webhook, and saves to DB.
    """
    service = TelegramService(db)
    try:
        result = await service.connect(user.tenant_id, payload.token)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e)) from e
    except Exception as e:
        logger.exception("telegram_connect_error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e)) from e

    else:
        return result


@router.post("/test", response_model=ConnectionTestResponse)
async def test_telegram_connection(
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> ConnectionTestResponse | dict[str, str]:
    """Test the current Telegram connection."""
    service = TelegramService(db)
    try:
        return await service.test_connection(user.tenant_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
    except Exception as e:  # noqa: BLE001 — API error boundary
        return {"status": "error", "message": f"Error inesperado: {e!s}"}


@router.delete("/disconnect")
async def disconnect_telegram(
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> dict[str, str]:
    """Disconnect Telegram: Delete Webhook and deactivate in DB."""
    service = TelegramService(db)
    try:
        return await service.disconnect(user.tenant_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except Exception as e:
        logger.exception("telegram_disconnect_error", error=str(e))
        raise HTTPException(
            status_code=500,
            detail="Error al desconectar Telegram.",
        ) from e

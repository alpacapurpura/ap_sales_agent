from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Request
from sqlalchemy.orm import Session
import structlog

from src.core.database import get_db
from src.modules.iam.api.dependencies import get_current_user
from src.modules.iam.domain.user import User
from src.modules.sales_agent.application.orchestrator.chat import ChatOrchestrator
from src.modules.sales_agent.api.dto.telegram import TelegramConnectRequest, ChannelStatusResponse
from src.modules.connections.infrastructure.channels.telegram_service import TelegramService

router = APIRouter(tags=["Telegram"])
logger = structlog.get_logger()
orchestrator = ChatOrchestrator()

# --- Webhooks ---

@router.post("/webhooks/telegram")
async def telegram_webhook_legacy(request: Request, background_tasks: BackgroundTasks):
    """
    Legacy Global Webhook. Uses settings.TELEGRAM_BOT_TOKEN.
    """
    payload = await request.json()
    await orchestrator.handle_telegram_webhook(payload, background_tasks)
    return {"status": "ok"}

@router.post("/webhooks/telegram/{tenant_id}")
async def telegram_webhook_tenant(
    tenant_id: str, 
    request: Request, 
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Multi-Tenant Webhook. Resolves bot token from Tenant configuration.
    """
    payload = await request.json()
    await orchestrator.handle_telegram_webhook(payload, background_tasks, tenant_id=tenant_id, db=db)
    return {"status": "ok"}

# --- Endpoints ---

@router.get("/status", response_model=ChannelStatusResponse)
async def get_telegram_status(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """
    Get current Telegram connection status for the tenant.
    """
    service = TelegramService(db)
    status_data = service.get_status(user.tenant_id)
    
    if not status_data.get("is_connected"):
        return ChannelStatusResponse(is_connected=False)
        
    return ChannelStatusResponse(**status_data)

@router.post("/connect")
async def connect_telegram(
    payload: TelegramConnectRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """
    Connect a Telegram Bot to the tenant.
    Validates token, sets webhook, and saves to DB.
    """
    service = TelegramService(db)
    try:
        result = await service.connect(user.tenant_id, payload.token)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.error("telegram_connect_error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/test")
async def test_telegram_connection(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """
    Test the current Telegram connection.
    """
    service = TelegramService(db)
    try:
        return await service.test_connection(user.tenant_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        return {"status": "error", "message": f"Error inesperado: {str(e)}"}

@router.delete("/disconnect")
async def disconnect_telegram(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """
    Disconnect Telegram: Delete Webhook and deactivate in DB.
    """
    service = TelegramService(db)
    try:
        return await service.disconnect(user.tenant_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error("telegram_disconnect_error", error=str(e))
        raise HTTPException(status_code=500, detail="Error al desconectar Telegram.")

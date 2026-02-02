from fastapi import APIRouter, Request, HTTPException, Query, BackgroundTasks, Depends
from sqlalchemy.orm import Session
from src.config import settings
from src.services.chat_orchestrator import ChatOrchestrator
from src.services.database import get_db
import structlog

router = APIRouter()
logger = structlog.get_logger()

# Orchestrator instance
orchestrator = ChatOrchestrator()

# --- Telegram Routes ---

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

# --- WhatsApp Routes ---

@router.get("/webhooks/whatsapp")
async def verify_whatsapp_webhook(
    mode: str = Query(alias="hub.mode"),
    token: str = Query(alias="hub.verify_token"),
    challenge: str = Query(alias="hub.challenge")
):
    if mode == "subscribe" and token == settings.WHATSAPP_VERIFY_TOKEN:
        return int(challenge)
    raise HTTPException(status_code=403, detail="Verification failed")

@router.post("/webhooks/whatsapp")
async def whatsapp_webhook(request: Request, background_tasks: BackgroundTasks):
    payload = await request.json()
    await orchestrator.handle_whatsapp_webhook(payload, background_tasks)
    return {"status": "received"}

from fastapi import APIRouter, Request, HTTPException, Query, BackgroundTasks
from src.config import settings
from src.services.chat_orchestrator import ChatOrchestrator
import structlog

router = APIRouter()
logger = structlog.get_logger()

# Orchestrator instance
orchestrator = ChatOrchestrator()

# --- Telegram Routes ---

@router.post("/webhooks/telegram")
async def telegram_webhook(request: Request, background_tasks: BackgroundTasks):
    payload = await request.json()
    await orchestrator.handle_telegram_webhook(payload, background_tasks)
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

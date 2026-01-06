from fastapi import APIRouter, Request, HTTPException, Query, BackgroundTasks
from src.config import settings
from src.core.agent import agent_app
from src.channels.telegram import TelegramChannel
from src.channels.whatsapp import WhatsAppChannel
from src.core.schema import IncomingMessage, OutgoingMessage
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

# Instancia única de canales (podría inyectarse como dependencia)
telegram_channel = TelegramChannel()
whatsapp_channel = WhatsAppChannel()

async def process_message(channel_adapter, payload: dict):
    """
    Función orquestadora agnóstica del canal.
    1. Normaliza
    2. Invoca Agente
    3. Envía Respuesta
    """
    try:
        # 1. Normalizar
        incoming = channel_adapter.normalize_payload(payload)
        if not incoming:
            logger.info("Payload ignored (not a valid text message)")
            return

        # 2. Invocar Agente (LangGraph)
        # El estado inicial ahora usa el modelo unificado
        initial_state = {
            "user_id": incoming.user_id,
            "messages": [incoming.text],
            "current_state": None, 
            "user_profile": incoming.metadata, # Pasamos metadatos del canal al perfil
            "last_intent": None,
            "financial_flag": False,
            "session_active": True
        }
        
        result = await agent_app.ainvoke(initial_state)
        
        # 3. Extraer Respuesta
        last_msg = result["messages"][-1]
        
        # Handle Dict vs String (backward compatibility)
        if isinstance(last_msg, dict):
            bot_text = last_msg.get("content", "")
        else:
            bot_text = str(last_msg)
        
        outgoing = OutgoingMessage(
            user_id=incoming.user_id,
            text=bot_text
        )
        
        # 4. Enviar
        await channel_adapter.send_message(outgoing)
        
    except Exception as e:
        logger.error(f"Error processing message: {e}", exc_info=True)

# --- Telegram Routes ---

@router.post("/webhooks/telegram")
async def telegram_webhook(request: Request, background_tasks: BackgroundTasks):
    """
    Recibe actualizaciones de Telegram.
    """
    payload = await request.json()
    # Procesar en background para responder rápido 200 OK a Telegram
    background_tasks.add_task(process_message, telegram_channel, payload)
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
    background_tasks.add_task(process_message, whatsapp_channel, payload)
    return {"status": "received"}

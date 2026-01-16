from fastapi import APIRouter, Request, HTTPException, Query, BackgroundTasks
from src.config import settings
from src.core.agent import agent_app
from src.channels.telegram import TelegramChannel
from src.channels.whatsapp import WhatsAppChannel
from src.core.schema import IncomingMessage, OutgoingMessage, FunnelStage
from src.services.repository import Repository
import logging
import structlog

router = APIRouter()
logger = structlog.get_logger()

# Instancia única de canales (podría inyectarse como dependencia)
telegram_channel = TelegramChannel()
whatsapp_channel = WhatsAppChannel()

from datetime import datetime, timedelta, timezone

async def process_message(channel_adapter, payload: dict):
    """
    Función orquestadora agnóstica del canal.
    1. Normaliza
    2. Persistencia (Log User)
    3. Invoca Agente
    4. Persistencia (Log Bot)
    5. Envía Respuesta
    """
    repo = Repository()
    try:
        # 1. Normalizar
        incoming = channel_adapter.normalize_payload(payload)
        if not incoming:
            logger.info("Payload ignored (not a valid text message)")
            return

        # 2. Persistencia: Asegurar usuario y loguear mensaje entrante
        channel_type = incoming.channel_type
        user_id_str = incoming.user_id # Telegram/WA ID
        
        user = repo.get_user_by_channel_id(channel_type, user_id_str)
        if not user:
            # Create user with basic info from metadata
            full_name = f"{incoming.metadata.get('first_name', '')} {incoming.metadata.get('last_name', '')}".strip()
            user = repo.create_user(
                full_name=full_name or "Unknown",
                channel=channel_type,
                channel_user_id=user_id_str
            )
        
        # Determine Session State (Before logging new message)
        last_msg = repo.get_last_message(user.id)
        session_active = True
        last_intent = None
        
        if last_msg:
            # Check 6-hour window
            time_diff = datetime.now(timezone.utc) - last_msg.created_at
            if time_diff > timedelta(hours=6):
                session_active = False
            
            # Extract last intent from metadata
            if last_msg.metadata_log and isinstance(last_msg.metadata_log, dict):
                last_intent = last_msg.metadata_log.get("intent")

        # Log User Message (Now safe to log)
        repo.log_message(
            user_id=user.id,
            role="user",
            content=incoming.text,
            channel=channel_type
        )

        # 3. Prepare Initial State with History Recovery
        
        # Get active product context (Smart Launch Logic)
        active_product, launch_stage = repo.get_current_launch_product()
        active_enrollment = None
        
        if active_product:
            active_enrollment = repo.get_enrollment(user.id, active_product.id)

        # FETCH HISTORY FROM POSTGRES (Single Source of Truth)
        # We fetch last 10 messages (including the one we just logged)
        history = repo.get_chat_history(user.id, limit=10)

        # 3. Prepare Initial State (Delegated to Factory)
        from src.core.state import create_initial_state
        
        initial_state = create_initial_state(
            user_id=str(user.id), # Pass Internal UUID (Single Source of Truth for Core)
            history=history,
            user_profile={**(user.profile_data if user and user.profile_data else {}), **incoming.metadata},
            session_active=session_active,
            active_enrollment=active_enrollment,
            active_product=active_product,
            last_intent=last_intent
        )
        
        # Override launch_stage if detected from repository logic
        if launch_stage:
            initial_state["launch_stage"] = launch_stage
        
        # Invoke Agent
        result = await agent_app.ainvoke(initial_state)
        
        # --- Post-Processing Persistence (Refactored) ---
        try:
            if active_product:
                repo.persist_agent_state(user.id, result, active_product.id)
                
        except Exception as e_pers:
            logger.error(f"Error in persistence post-processing: {e_pers}")

        # 4. Extraer Respuesta
        last_msg = result["messages"][-1]
        
        if isinstance(last_msg, dict):
            bot_text = last_msg.get("content", "")
        else:
            bot_text = str(last_msg)
        
        # Log Assistant Message
        repo.log_message(
            user_id=user.id,
            role="assistant",
            content=bot_text,
            channel=channel_type
        )
        
        outgoing = OutgoingMessage(
            user_id=incoming.user_id,
            text=bot_text
        )
        
        # 5. Enviar
        send_result = await channel_adapter.send_message(outgoing)
        if send_result and isinstance(send_result, dict) and "error" in send_result:
             logger.error(f"Channel adapter reported error sending message: {send_result}")
        
    except Exception as e:
        logger.error(f"Error processing message: {e}", exc_info=True)
        # Fallback: Send technical error message to user
        try:
            if 'incoming' in locals() and incoming and incoming.user_id:
                 error_msg = OutgoingMessage(
                     user_id=incoming.user_id,
                     text="⚠️ Lo siento, ocurrió un error técnico interno. Por favor intenta de nuevo en unos minutos."
                 )
                 await channel_adapter.send_message(error_msg)
        except Exception as e_fallback:
             logger.error(f"Could not send fallback error message: {e_fallback}")

    finally:
        repo.close()

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

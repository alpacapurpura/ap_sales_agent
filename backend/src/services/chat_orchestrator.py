import structlog
import asyncio
import time
from datetime import datetime, timedelta, timezone
from uuid import UUID
from fastapi import BackgroundTasks
from sqlalchemy.orm import Session

from src.core.agents.orchestrator.graph import agent_app
from src.core.domain.schema import IncomingMessage, OutgoingMessage
from src.services.db.repositories.lead import LeadRepository
from src.services.db.repositories.audit import AuditRepository
from src.services.db.repositories.business import BusinessRepository
from src.services.database import SessionLocal
from src.services.buffer_service import SmartBufferService
from src.services.output_manager import OutputManager
from src.core.semantic import check_is_complete
from src.core.agents.orchestrator.state import create_initial_state
from src.channels.telegram import TelegramChannel
from src.channels.whatsapp import WhatsAppChannel
from src.core.context import set_tenant_id
from src.services.db.models.channel_connection import ChannelConnection, ChannelType

logger = structlog.get_logger()

class ChatOrchestrator:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ChatOrchestrator, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        # Legacy/Global channels (fallback)
        self.whatsapp_channel = WhatsAppChannel()
        self.buffer_service = SmartBufferService()
        self._initialized = True

    async def handle_telegram_webhook(self, payload: dict, background_tasks: BackgroundTasks, tenant_id: str = None, db: Session = None):
        """
        Handles Telegram Webhook with Multi-Tenant support.
        """
        token = None
        if tenant_id and db:
            try:
                # Resolve tenant connection
                conn = db.query(ChannelConnection).filter(
                    ChannelConnection.tenant_id == UUID(tenant_id),
                    ChannelConnection.channel_type == ChannelType.TELEGRAM,
                    ChannelConnection.is_active == True
                ).first()
                
                if conn and conn.credentials:
                    token = conn.credentials.get("token")
            except Exception as e:
                logger.error("error_resolving_telegram_connection", error=str(e), tenant_id=tenant_id)

        # Instantiate adapter (with specific token or fallback to global env)
        adapter = TelegramChannel(token=token)
        await self._handle_incoming_webhook(adapter, payload, background_tasks, tenant_id)

    async def handle_whatsapp_webhook(self, payload: dict, background_tasks: BackgroundTasks):
        # TODO: Add multi-tenant support for WhatsApp later
        await self._handle_incoming_webhook(self.whatsapp_channel, payload, background_tasks)

    async def _handle_incoming_webhook(self, channel_adapter, payload: dict, background_tasks: BackgroundTasks, tenant_id: str = None):
        incoming = channel_adapter.normalize_payload(payload)
        if not incoming:
            return

        # Composite key for buffer to prevent collisions between tenants
        # If tenant_id is present, we store as "tenant_id:user_id"
        # We also inject tenant info into metadata for later recovery
        buffer_key = incoming.user_id
        if tenant_id:
            buffer_key = f"{tenant_id}:{incoming.user_id}"
            incoming.metadata["tenant_id"] = str(tenant_id)
            incoming.metadata["real_user_id"] = incoming.user_id

        # Add to buffer
        self.buffer_service.add_message(
            buffer_key, 
            incoming.text, 
            incoming.channel_type, 
            incoming.metadata
        )
        
        # Launch Smart Debounce Task
        background_tasks.add_task(self.smart_debounce_task, buffer_key, channel_adapter)

    async def smart_debounce_task(self, buffer_key: str, channel_adapter):
        """
        Orchestrates the Dynamic Debounce logic.
        """
        try:
            # 1. Initial Buffer (Wait for fast interruptions)
            await asyncio.sleep(0.5)

            # 2. Check if new message arrived (Reset Logic)
            last_ts = self.buffer_service.get_last_timestamp(buffer_key)
            if time.time() - last_ts < 0.4: # Tolerance
                # New message arrived recently, abort this task (let the new one handle it)
                return

            # Recover Metadata to get real user_id (for typing status)
            meta = self.buffer_service.get_metadata(buffer_key)
            real_user_id = meta.get("real_user_id", buffer_key)
            tenant_id = meta.get("tenant_id")

            # 3. Typing Indicator
            await channel_adapter.set_typing_status(real_user_id)

            # 4. Semantic Check (LLM)
            # Peek buffer to check completeness
            messages = self.buffer_service.peek_buffer(buffer_key)
            if not messages:
                return
                
            full_text = " ".join(messages)
            
            # Only check semantic if it's substantial enough
            is_complete = False
            if len(full_text) > 5:
                is_complete = await check_is_complete(full_text)
            
            # 5. Dynamic Wait
            if is_complete:
                # Short wait (already waited 0.5s, wait 2.0s more = 2.5s total)
                wait_time = 4.0
            else:
                # Long wait (wait 4.0s more = 4.5s total)
                wait_time = 6.0
                
            await asyncio.sleep(wait_time)

            # 6. Final Reset Check & Lock
            # If a new message came during the semantic wait, we abort.
            last_ts = self.buffer_service.get_last_timestamp(buffer_key)
            # Using a small buffer for timing discrepancies
            if time.time() - last_ts < (wait_time + 0.3): 
                return

            # Try Acquire Lock
            if not self.buffer_service.acquire_lock(buffer_key):
                return # Already being processed

            try:
                # 7. Process
                msgs = self.buffer_service.get_and_clear_buffer(buffer_key)
                if not msgs:
                    return
                    
                final_text = " ".join(msgs)
                # Re-fetch metadata just in case
                meta = self.buffer_service.get_metadata(buffer_key)
                channel_type = self.buffer_service.get_channel_type(buffer_key) or "unknown"
                
                # Reconstruct IncomingMessage with REAL user_id
                incoming = IncomingMessage(
                    user_id=real_user_id,
                    text=final_text,
                    channel_type=channel_type,
                    metadata=meta
                )
                
                await self.process_chat_flow(channel_adapter, incoming, tenant_id)
                
            finally:
                self.buffer_service.release_lock(buffer_key)
                # Cleanup cache for this user/key
                # self.buffer_service.clear_user_cache(buffer_key) # Optional, but good for hygiene
                
        except Exception as e:
            logger.error(f"Error in smart debounce task: {e}", exc_info=True)

    async def process_chat_flow(self, channel_adapter, incoming: IncomingMessage, tenant_id: str = None):
        """
        Core Logic: Ejecuta el agente con un mensaje YA CONSTRUIDO (y debounced).
        """
        # Set Tenant Context
        if tenant_id:
            try:
                set_tenant_id(UUID(tenant_id))
            except Exception:
                logger.error(f"Invalid tenant_id format: {tenant_id}")
        
        # 0. Reforzar indicador de "Escribiendo..." ahora que empezamos a procesar de verdad
        try:
            await channel_adapter.set_typing_status(incoming.user_id)
        except Exception as e:
            logger.warning(f"Could not set typing status in flow: {e}")

        db = SessionLocal()
        lead_repo = LeadRepository(db)
        audit_repo = AuditRepository(db)
        biz_repo = BusinessRepository(db)
        
        try:
            # 2. Persistencia: Asegurar usuario y loguear mensaje entrante
            channel_type = incoming.channel_type
            user_id_str = incoming.user_id 
            
            user = lead_repo.get_by_channel_id(channel_type, user_id_str)
            if not user:
                full_name = f"{incoming.metadata.get('first_name', '')} {incoming.metadata.get('last_name', '')}".strip()
                user = lead_repo.create_lead(
                    full_name=full_name or "Unknown",
                    channel=channel_type,
                    channel_user_id=user_id_str
                )
            
            # Determine Session State
            last_msg = audit_repo.get_last_message(user.id)
            session_active = True
            last_intent = None
            
            if last_msg:
                time_diff = datetime.now(timezone.utc) - last_msg.created_at
                if time_diff > timedelta(hours=6):
                    session_active = False
                
                if last_msg.metadata_log and isinstance(last_msg.metadata_log, dict):
                    last_intent = last_msg.metadata_log.get("intent")

            # Log User Message
            audit_repo.log_message(
                user_id=user.id,
                role="user",
                content=incoming.text,
                channel=channel_type
            )

            # 3. Prepare Initial State
            active_product, launch_stage = biz_repo.get_current_launch_product()
            active_enrollment = None
            
            if active_product:
                active_enrollment = biz_repo.get_enrollment(user.id, active_product.id)

            history = audit_repo.get_chat_history(user.id, limit=10)

            # Prepare Profile + Style Data
            base_profile = user.profile_data if user and user.profile_data else {}
            
            # Inject Onboarding Style Data
            if getattr(user, "custom_system_instruction", None):
                base_profile["custom_instruction"] = user.custom_system_instruction
            if getattr(user, "style_profile", None):
                base_profile["style_profile"] = user.style_profile

            initial_state = create_initial_state(
                user_id=str(user.id),
                history=history,
                user_profile={**base_profile, **incoming.metadata},
                session_active=session_active,
                active_enrollment=active_enrollment,
                active_product=active_product,
                last_intent=last_intent
            )
            
            if launch_stage:
                initial_state["launch_stage"] = launch_stage
            
            # Invoke Agent
            result = await agent_app.ainvoke(initial_state)
            
            # 4. Extract Response
            last_msg = result["messages"][-1]
            bot_text = last_msg.get("content", "") if isinstance(last_msg, dict) else str(last_msg)
            
            # Log Assistant Message
            audit_repo.log_message(
                user_id=user.id,
                role="assistant",
                content=bot_text,
                channel=channel_type
            )
            
            # 5. Send using OutputManager (Chunks + Human Typing)
            await OutputManager.process_response(incoming.user_id, bot_text, channel_adapter)
            
        except Exception as e:
            logger.error(f"Error processing message: {e}", exc_info=True)
            try:
                if 'incoming' in locals() and incoming and incoming.user_id:
                     error_msg = OutgoingMessage(
                         user_id=incoming.user_id,
                         text="⚠️ Lo siento, ocurrió un error técnico interno."
                     )
                     await channel_adapter.send_message(error_msg)
            except Exception as e_fallback:
                 logger.error(f"Could not send fallback error message: {e_fallback}")

        finally:
            lead_repo.close()
            audit_repo.close()
            biz_repo.close()

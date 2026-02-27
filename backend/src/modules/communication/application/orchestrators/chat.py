import structlog
import asyncio
import time
import uuid
from datetime import datetime, timedelta, timezone
from uuid import UUID
from fastapi import BackgroundTasks
from sqlalchemy.orm import Session

from src.shared.application.orchestrator.graph import agent_app
from src.modules.communication.domain.message_models import IncomingMessage, OutgoingMessage
from src.modules.sales.infrastructure.lead import LeadRepository
from src.modules.marketing.application.services.identity_service import IdentityService
from src.modules.marketing.infrastructure.repositories.customer_repository import CustomerRepository
from src.modules.marketing.domain.enums import IdentityType
from src.shared.infrastructure.monitoring.audit_repository import AuditRepository
from src.shared.infrastructure.db.repositories.business_repository import BusinessRepository
from src.shared.infrastructure.db.database import SessionLocal
from src.shared.infrastructure.external.buffer_service import SmartBufferService
from src.shared.infrastructure.external.output_manager import OutputManager
from src.shared.core.semantic import check_is_complete
from src.shared.application.orchestrator.state import create_initial_state
from src.modules.integration.infrastructure.channels.telegram import TelegramChannel
from src.shared.utils.context import set_tenant_id
from src.modules.communication.domain.channel import ChannelConnection
from src.modules.communication.domain.enums import ChannelType
from src.modules.iam.domain.tenant import Tenant

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
        # self.whatsapp_channel = WhatsAppChannel() # Removed: WhatsAppChannel requires tenant_id
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
                    ChannelConnection.is_active.is_(True)
                ).first()
                
                if conn and conn.credentials:
                    token = conn.credentials.get("token")
            except Exception as e:
                logger.error("error_resolving_telegram_connection", error=str(e), tenant_id=tenant_id)

        # Instantiate adapter (with specific token or fallback to global env)
        adapter = TelegramChannel(token=token)
        await self._handle_incoming_webhook(adapter, payload, background_tasks, tenant_id)

    async def handle_whatsapp_webhook(self, payload: dict, background_tasks: BackgroundTasks):
        # WhatsApp logic is now handled via direct router-to-service calls or unified webhook handler.
        # This method is kept for backward compatibility but should be deprecated.
        pass

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
        tenant_config = {}
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
        customer_repo = CustomerRepository(db)
        identity_service = IdentityService(customer_repo)
        audit_repo = AuditRepository(db)
        biz_repo = BusinessRepository(db)
        
        try:
            # 1. Fetch Tenant Config if tenant_id is present
            tenant_uuid = None
            if tenant_id:
                try:
                    tenant_uuid = UUID(tenant_id)
                    tenant_obj = db.query(Tenant).filter(Tenant.id == tenant_uuid).first()
                    if tenant_obj:
                        tenant_config = tenant_obj.config_json or {}
                except Exception as e:
                    logger.error(f"Error fetching tenant config: {e}")

            # 2. Persistencia: Asegurar usuario y loguear mensaje entrante
            channel_type = incoming.channel_type
            user_id_str = incoming.user_id 
            
            # Map channel to IdentityType
            try:
                identity_type = IdentityType(channel_type)
            except ValueError:
                identity_type = IdentityType.EXTERNAL_ID

            # Prepare Profile Data
            profile_data = {
                "first_name": incoming.metadata.get("first_name"),
                "last_name": incoming.metadata.get("last_name"),
                "traits": incoming.metadata
            }

            # Get or Create Customer
            customer = identity_service.get_or_create_customer(
                tenant_id=tenant_uuid,
                identity_type=identity_type,
                identity_value=user_id_str,
                profile_data=profile_data
            )

            # Update Customer Profile Traits if needed (Metadata Update)
            if incoming.metadata:
                needs_update = False
                # Ensure traits is a dict
                current_traits = dict(customer.traits) if customer.traits else {}
                
                for k, v in incoming.metadata.items():
                    # Update if new or different
                    if k not in current_traits or current_traits[k] != v:
                        current_traits[k] = v
                        needs_update = True
                
                if needs_update:
                    customer.traits = current_traits
                    # Also update basic fields if provided
                    if "first_name" in incoming.metadata:
                        customer.full_name = f"{incoming.metadata.get('first_name', '')} {incoming.metadata.get('last_name', '')}".strip()
                    
                    db.add(customer)
                    db.commit()
                    db.refresh(customer)

            # Get or Create Active Lead linked to Customer
            user = lead_repo.get_active_lead(customer.id)
            if not user:
                user = lead_repo.create_lead(
                    customer_id=customer.id,
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
                tenant_id=str(tenant_id) if tenant_id else str(uuid.uuid4()), # Fallback if None, though should be handled
                tenant_config=tenant_config,
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

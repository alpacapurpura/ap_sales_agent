import structlog
import asyncio
import time
import uuid
from datetime import datetime, timedelta, timezone
from uuid import UUID
from fastapi import BackgroundTasks
from sqlalchemy.orm import Session

from src.modules.sales_agent.application.orchestrator.graph import agent_app
from src.shared.domain.messages import IncomingMessage, OutgoingMessage
from src.modules.crm.infrastructure.repositories.lead_metrics_repository import LeadRepository
from src.modules.crm.application.services.identity_service import IdentityService
from src.modules.crm.infrastructure.repositories.customer_repository import CustomerRepository
from src.modules.crm.domain.enums import IdentityType
from src.modules.sales_agent.infrastructure.memory.audit_repository import AuditRepository
from src.modules.sales_agent.infrastructure.db.repositories.business_repository import BusinessRepository
from src.core.database import SessionLocal
from src.modules.sales_agent.infrastructure.external.buffer_service import SmartBufferService
from src.modules.sales_agent.infrastructure.external.output_manager import OutputManager
from src.modules.sales_agent.infrastructure.prompts.semantic import check_is_complete
from src.modules.sales_agent.application.orchestrator.state import create_initial_state
from src.modules.sales_agent.infrastructure.repositories.state_repository import StateRepository
from src.modules.sales_agent.application.services.knowledge_builder import TenantKnowledgeBuilder
from src.modules.sales_agent.application.services.semantic_router import SemanticRouter
from src.modules.sales_agent.domain.tuning import SESSION_TIMEOUT_HOURS, MESSAGE_HISTORY_LIMIT
from src.modules.connections.infrastructure.channels.telegram import TelegramChannel
from src.core.context import set_tenant_id
from src.modules.connections.infrastructure.models.channel_connection_model import ChannelConnectionModel
from src.modules.connections.domain.enums import ChannelType
from src.modules.iam.infrastructure.models.tenant_model import TenantModel
from src.modules.crm.domain.events import LeadCapturedEvent, CHANNEL_TYPE_TO_CAPTURE_SLUG
from src.shared.domain.events import EventBus

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
                conn = db.query(ChannelConnectionModel).filter(
                    ChannelConnectionModel.tenant_id == UUID(tenant_id),
                    ChannelConnectionModel.channel_type == ChannelType.TELEGRAM.value,
                    ChannelConnectionModel.is_active.is_(True)
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

            # 3.5. Fetch tenant object for LLM service resolution
            tenant_obj = None
            if tenant_id:
                db_tmp = None
                try:
                    db_tmp = SessionLocal()
                    tenant_obj = db_tmp.query(TenantModel).filter(TenantModel.id == UUID(tenant_id)).first()
                except Exception as e:
                    logger.warning(f"Could not fetch tenant for semantic check: {e}")
                finally:
                    if db_tmp:
                        db_tmp.close()

            # 4. Semantic Check (LLM)
            # Peek buffer to check completeness
            messages = self.buffer_service.peek_buffer(buffer_key)
            if not messages:
                return

            full_text = " ".join(messages)

            # Only check semantic if it's substantial enough
            is_complete = False
            if len(full_text) > 5:
                is_complete = await check_is_complete(full_text, tenant=tenant_obj)
            
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
                    tenant_obj = db.query(TenantModel).filter(TenantModel.id == tenant_uuid).first()
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

            # Get or Create Customer (with lead_source for capture tracking)
            capture_slug = CHANNEL_TYPE_TO_CAPTURE_SLUG.get(channel_type, channel_type)
            customer, was_created = identity_service.get_or_create_customer(
                tenant_id=tenant_uuid,
                identity_type=identity_type,
                identity_value=user_id_str,
                profile_data=profile_data,
                lead_source=capture_slug,
                lead_source_detail=channel_type,
            )

            # Enrich Instagram profiles with name/username/pic from User Profile API
            if channel_type == "instagram" and tenant_uuid:
                if was_created or not (customer.traits or {}).get("instagram_username"):
                    try:
                        from src.modules.crm.application.services.ig_profile_enricher import InstagramProfileEnricher
                        from src.modules.connections.application.services.connection_port_impl import ConnectionPortImpl

                        connection_port = ConnectionPortImpl(db)
                        creds = await connection_port.get_credentials(tenant_uuid, "meta")
                        enricher = InstagramProfileEnricher(db)
                        await enricher.enrich(
                            tenant_id=tenant_uuid,
                            igsid=user_id_str,
                            customer_profile_id=customer.id,
                            access_token=creds.credentials.get("access_token", ""),
                        )
                    except Exception:
                        logger.warning("ig_profile_enrichment_failed", exc_info=True)

            # Track message_received journey event for capture conversation metrics
            if tenant_uuid:
                try:
                    from src.modules.crm.infrastructure.repositories.customer_repository import JourneyEventRepository
                    journey_repo = JourneyEventRepository(db)
                    event_props = {
                        "channel_slug": capture_slug,
                        "channel_type": channel_type,
                        "message_direction": "inbound",
                    }
                    # Propagate message_id for dedup (IG DM sync + webhook overlap)
                    mid = incoming.metadata.get("message_id")
                    if mid:
                        event_props["message_id"] = mid
                    journey_repo.track_event(
                        profile_id=customer.id,
                        tenant_id=tenant_uuid,
                        event_name="message_received",
                        event_type="track",
                        properties=event_props,
                    )
                except Exception:
                    logger.warning("failed_to_track_message_received", exc_info=True)

            # Emit LeadCapturedEvent only for NEW profiles (not returning visitors)
            if was_created and tenant_uuid:
                EventBus.publish(
                    LeadCapturedEvent.create(
                        tenant_id=tenant_uuid,
                        profile_id=customer.id,
                        channel_slug=capture_slug,
                        extracted_field="external_id",
                        source_channel_type=channel_type,
                    ),
                    session=db,
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
                    from src.modules.crm.infrastructure.models.customer_model import CustomerProfileModel
                    profile_model = db.query(CustomerProfileModel).filter(
                        CustomerProfileModel.id == customer.id
                    ).first()
                    if profile_model:
                        profile_model.traits = current_traits
                        if "first_name" in incoming.metadata:
                            profile_model.full_name = f"{incoming.metadata.get('first_name', '')} {incoming.metadata.get('last_name', '')}".strip()
                        db.commit()

            # Get or Create Active Lead linked to Customer
            user = lead_repo.get_active_lead(customer.id)
            if not user:
                user = lead_repo.create_lead(
                    customer_id=customer.id,
                    channel=channel_type,
                    channel_user_id=user_id_str
                )

            # Log User Message FIRST (before checkpoint) so audit trail
            # is preserved even if downstream steps fail
            audit_repo.log_message(
                user_id=user.id,
                role="user",
                content=incoming.text,
                channel=channel_type,
                tenant_id=tenant_uuid
            )

            # Load existing state checkpoint (if any)
            state_repo = StateRepository(db)
            checkpoint = None
            try:
                checkpoint = state_repo.get_active_checkpoint(tenant_uuid, user.id) if tenant_uuid else None
            except Exception as e:
                logger.warning("checkpoint_load_failed", error=str(e))
                try:
                    db.rollback()
                except Exception:
                    pass

            # ── Closer Studio: handler_mode check ──
            # If handler_mode is "human", the owner is in control.
            # Store the message, increment unread, but do NOT run the AI graph.
            if checkpoint and checkpoint.handler_mode == "human":
                logger.info(
                    "handler_mode_human_skip",
                    lead_id=str(user.id),
                    tenant_id=tenant_id,
                )
                checkpoint.unread_count = (checkpoint.unread_count or 0) + 1
                checkpoint.last_human_message_at = datetime.now(timezone.utc)
                db.commit()

                # Emit WS event so Closer Studio UI gets the new message in real-time
                try:
                    from src.modules.sales_agent.infrastructure.ws_manager import ws_manager
                    asyncio.ensure_future(ws_manager.emit(str(tenant_uuid), {
                        "type": "new_message",
                        "lead_id": str(user.id),
                        "role": "user",
                        "content": incoming.text[:200],
                        "handler_mode": "human",
                    }))
                except Exception:
                    pass  # WS is best-effort
                return

            # Determine Session State
            last_msg = audit_repo.get_last_message(user.id)
            session_active = True
            last_intent = None

            if last_msg and last_msg.created_at:
                msg_time = last_msg.created_at
                if msg_time.tzinfo is None:
                    msg_time = msg_time.replace(tzinfo=timezone.utc)
                time_diff = datetime.now(timezone.utc) - msg_time
                if time_diff > timedelta(hours=SESSION_TIMEOUT_HOURS):
                    session_active = False

                if last_msg.metadata_log and isinstance(last_msg.metadata_log, dict):
                    last_intent = last_msg.metadata_log.get("intent")

            # 2.5 Build Agent Identity (AKS)
            agent_identity = None
            if tenant_uuid:
                try:
                    knowledge_builder = TenantKnowledgeBuilder(db)
                    agent_identity = knowledge_builder.build_identity(tenant_uuid)
                except Exception as e:
                    logger.warning(f"Could not build agent identity: {e}")
                    # Rollback to clear any failed transaction state on shared db session
                    try:
                        db.rollback()
                    except Exception:
                        pass

            # 3. Prepare Initial State
            active_product, launch_stage = biz_repo.get_current_launch_product()
            active_enrollment = None

            # Convert ORM product to dict for serialization
            active_product_dict = None
            if active_product:
                active_enrollment = biz_repo.get_enrollment(user.id, active_product.id)
                active_product_dict = {
                    "id": str(active_product.id),
                    "name": getattr(active_product, "name", None),
                    "status": getattr(active_product, "status", None),
                    "price": getattr(active_product, "price", None),
                }

            # Convert ORM history to dicts
            raw_history = audit_repo.get_chat_history(user.id, limit=MESSAGE_HISTORY_LIMIT)
            history = [
                {"role": msg.role, "content": msg.content}
                for msg in raw_history if msg.content
            ]

            # Prepare Profile + Style Data (ensure dict, not Pydantic model)
            if user and user.profile_data:
                base_profile = user.profile_data.model_dump() if hasattr(user.profile_data, 'model_dump') else dict(user.profile_data)
            else:
                base_profile = {}

            # Inject Onboarding Style Data
            if getattr(user, "custom_system_instruction", None):
                base_profile["custom_instruction"] = user.custom_system_instruction
            if getattr(user, "style_profile", None):
                base_profile["style_profile"] = user.style_profile

            # Build checkpoint data for state restoration
            checkpoint_data = {}
            if checkpoint and session_active:
                checkpoint_data = {
                    "current_state": checkpoint.current_stage,
                    "lead_score": checkpoint.lead_score,
                    "lead_data": checkpoint.lead_data or {},
                    "buying_signals": checkpoint.buying_signals or [],
                    "objection_history": checkpoint.objection_history or [],
                    "qualification_answers": checkpoint.qualification_answers or {},
                    "turn_count": checkpoint.turn_count or 0,
                    "close_strategy": checkpoint.close_strategy,
                }
            elif checkpoint and not session_active:
                state_repo.deactivate(tenant_uuid, user.id)

            initial_state = create_initial_state(
                user_id=str(user.id),
                tenant_id=str(tenant_id) if tenant_id else str(uuid.uuid4()),
                tenant_config=tenant_config,
                history=history,
                user_profile={**base_profile, **incoming.metadata},
                session_active=session_active,
                active_enrollment=active_enrollment,
                active_product=active_product_dict,
                last_intent=last_intent,
                agent_identity=agent_identity,
                customer_profile_id=customer.id,
                channel_type=channel_type,
                **checkpoint_data,
            )

            if launch_stage:
                initial_state["launch_stage"] = launch_stage

            # Sanitize user input
            sanitized_text = incoming.text
            try:
                from src.modules.sales_agent.infrastructure.external.safety_service import SafetyLayerService
                safety = SafetyLayerService()
                sanitized_text, was_modified = await safety.sanitize_content(incoming.text)
                if was_modified:
                    logger.warning("user_input_sanitized", original_preview=incoming.text[:50])
            except Exception as e:
                logger.warning("safety_sanitization_failed", error=str(e))
                sanitized_text = incoming.text

            # Add the current user message to state["messages"] so LLM nodes can read it
            initial_state["messages"] = [{"role": "user", "content": sanitized_text}]

            # ── Closer Studio: inject resume_objective as operator instruction ──
            if checkpoint and checkpoint.resume_objective:
                initial_state["messages"].insert(0, {
                    "role": "system",
                    "content": f"[INSTRUCCION DEL OPERADOR] {checkpoint.resume_objective}",
                })
                # One-shot: clear after injection
                checkpoint.resume_objective = None
                db.flush()

            # 3.5 Semantic Intent Detection + Signal Accumulation
            try:
                detected_intent, intent_score, updated_signals = SemanticRouter.detect_and_accumulate(
                    incoming.text,
                    existing_signals=initial_state.get("buying_signals", []),
                    tenant_id=tenant_uuid,
                )
                if detected_intent:
                    initial_state["detected_intent"] = detected_intent
                    initial_state["buying_signals"] = updated_signals
                    logger.debug(f"Semantic intent: {detected_intent} (score={intent_score:.2f})")
            except Exception as e:
                logger.warning(f"Semantic router failed, continuing without intent: {e}")

            # Invoke Agent (with typing polling every 3s)
            async def _keep_typing():
                while True:
                    await asyncio.sleep(3)
                    try:
                        await channel_adapter.set_typing_status(incoming.user_id)
                    except Exception:
                        pass

            typing_task = asyncio.create_task(_keep_typing())
            try:
                result = await agent_app.ainvoke(initial_state)
            finally:
                typing_task.cancel()

            # Save state checkpoint after graph execution
            if tenant_uuid and user:
                try:
                    state_repo.save_checkpoint(
                        tenant_id=tenant_uuid,
                        lead_id=user.id,
                        session_id=initial_state.get("session_id", ""),
                        customer_profile_id=customer.id,
                        channel_type=channel_type,
                        current_stage=result.get("current_state", "rapport"),
                        lead_score=result.get("lead_score", 0),
                        lead_data=result.get("lead_data", {}),
                        buying_signals=result.get("buying_signals", []),
                        objection_history=result.get("objection_history", []),
                        qualification_answers=result.get("qualification_answers", {}),
                        turn_count=result.get("turn_count", 0),
                        last_specialist=result.get("next_node"),
                        close_strategy=result.get("close_strategy"),
                    )
                    db.commit()
                except Exception as e:
                    logger.error("checkpoint_save_failed", error=str(e))
                    try:
                        db.rollback()
                    except Exception:
                        pass

            # 4. Extract Response
            last_msg = result["messages"][-1]
            bot_text = last_msg.get("content", "") if isinstance(last_msg, dict) else str(last_msg)

            # Sanitize bot output
            try:
                from src.modules.sales_agent.infrastructure.external.safety_service import SafetyLayerService
                safety = SafetyLayerService()
                bot_text, was_modified = await safety.sanitize_content(bot_text)
                if was_modified:
                    logger.warning("bot_output_sanitized", original_preview=bot_text[:50])
            except Exception as e:
                logger.warning("safety_output_sanitization_failed", error=str(e))

            # Log Assistant Message
            audit_repo.log_message(
                user_id=user.id,
                role="assistant",
                content=bot_text,
                channel=channel_type,
                tenant_id=tenant_uuid
            )
            
            # 5. Send using OutputManager (Chunks + Human Typing)
            await OutputManager.process_response(incoming.user_id, bot_text, channel_adapter, channel_type=channel_type)

            # 6. Closer Studio: emit WS event for real-time updates
            if tenant_uuid:
                try:
                    from src.modules.sales_agent.infrastructure.ws_manager import ws_manager
                    await ws_manager.emit(str(tenant_uuid), {
                        "type": "new_message",
                        "lead_id": str(user.id),
                        "role": "assistant",
                        "content": bot_text[:200],
                        "handler_mode": "ai",
                        "lead_score": result.get("lead_score", 0),
                        "funnel_stage": result.get("current_state", "rapport"),
                    })
                except Exception:
                    pass  # WS is best-effort
            
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

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Body, Query, Request
from sqlalchemy.orm import Session
from src.shared.infrastructure.db.database import get_db
from src.modules.communication.domain.channel import ChannelConnection
from src.modules.communication.domain.enums import ChannelType
from src.modules.iam.api.dependencies import get_current_tenant_id
from src.modules.integration.infrastructure.channels.whatsapp import WhatsAppChannel
from src.core.config import settings
from src.modules.communication.application.orchestrators.chat import ChatOrchestrator
import structlog
import uuid
import asyncio
import traceback

router = APIRouter(tags=["WhatsApp"])
logger = structlog.get_logger()
orchestrator = ChatOrchestrator()

# --- Webhooks ---

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

# --- Endpoints ---

@router.get("/whatsapp/status")
async def get_whatsapp_status(
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant_id)
):
    """
    Checks the connection status of the WhatsApp instance for this tenant.
    Returns status for both Evolution (QR) and Meta (Cloud) providers.
    """
    
    # --- 1. EVOLUTION API (QR) STATUS ---
    evolution_status = {"status": "disconnected", "profile": None}
    
    # Check DB for Evolution
    evo_conn = db.query(ChannelConnection).filter(
        ChannelConnection.tenant_id == uuid.UUID(tenant_id),
        ChannelConnection.channel_type == ChannelType.WHATSAPP
    ).first()

    if evo_conn and evo_conn.is_active:
        # Check actual status via Provider
        channel = WhatsAppChannel(tenant_id)
        status_data = await channel.check_status()
        
        if status_data.get("exists"):
            state = status_data.get("state")
            if state == "open":
                # Logic to auto-heal metadata if missing in DB but present in Provider
                current_metadata = evo_conn.config.get("metadata", {})
                provider_instance = status_data.get("data", {}).get("instance", {})
                
                # If we have provider data but no local metadata, update it
                if not current_metadata and provider_instance:
                    from sqlalchemy.orm.attributes import flag_modified
                    
                    # Extract info (Evolution V1/V2 variations)
                    owner_jid = provider_instance.get("ownerJid") or provider_instance.get("number")
                    profile_name = provider_instance.get("profileName") or provider_instance.get("pushName") or "WhatsApp User"
                    
                    if owner_jid:
                        new_metadata = {
                            "first_name": profile_name,
                            "remote_jid": owner_jid,
                            "platform": "whatsapp",
                            "connected_at": "Sincronizado recientemente" # Placeholder
                        }
                        
                        # Update DB
                        config = evo_conn.config or {}
                        config["metadata"] = new_metadata
                        evo_conn.config = config
                        flag_modified(evo_conn, "config")
                        db.commit()
                        current_metadata = new_metadata

                evolution_status = {
                    "status": "connected", 
                    "profile": current_metadata
                }
            elif state == "connecting":
                evolution_status = {"status": "connecting", "profile": None}

    # --- 2. META CLOUD API STATUS ---
    meta_status = {"status": "disconnected", "profile": None}
    
    # Check DB for Meta
    meta_conn = db.query(ChannelConnection).filter(
        ChannelConnection.tenant_id == uuid.UUID(tenant_id),
        ChannelConnection.channel_type == ChannelType.WHATSAPP_CLOUD
    ).first()
    
    if meta_conn and meta_conn.is_active:
        meta_status = {
            "status": "connected",
            "profile": meta_conn.config.get("metadata", {})
        }

    return {
        "evolution": evolution_status,
        "meta": meta_status
    }

@router.post("/whatsapp/session")
async def create_whatsapp_session(
    provider: str = Body("evolution", embed=True), # 'evolution' or 'meta'
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant_id)
):
    """
    Creates a new WhatsApp instance.
    Provider: 'evolution' (QR) or 'meta' (Cloud API).
    """
    
    if provider == "meta":
        # Placeholder for Meta logic
        # In real implementation, this would save credentials from body
        return {"status": "error", "message": "Meta integration coming soon"}

    # --- EVOLUTION LOGIC ---
    channel = WhatsAppChannel(tenant_id)
    
    try:
        # 1. Check if exists first (Zombie Cleanup)
        status_data = await channel.check_status()
        
        if status_data.get("exists"):
            logger.info("whatsapp_instance_reset", tenant_id=tenant_id)
            await channel.delete_instance()
            await asyncio.sleep(5) # Wait for cleanup

        # 2. Create Instance
        token = str(uuid.uuid4())
        resp = await channel.create_instance(token)
        
        if resp.get("status") != 201:
             logger.error("whatsapp_create_rejected", status=resp.get("status"), body=resp.get("text"))
             raise HTTPException(status_code=500, detail=f"Failed to create instance: {resp.get('text')}")

        # Wait for Evolution to initialize worker
        await asyncio.sleep(2)

        # 3. Configure Webhook
        webhook_url = f"{settings.API_URL}/api/v1/whatsapp/webhook/{tenant_id}"
        webhook_resp = await channel.configure_webhook(webhook_url)
        
        if webhook_resp.get("status") not in [200, 201]:
            logger.warning("whatsapp_webhook_config_failed", tenant_id=tenant_id, status=webhook_resp.get("status"))

        # 4. Save to DB
        connection = db.query(ChannelConnection).filter(
            ChannelConnection.tenant_id == uuid.UUID(tenant_id),
            ChannelConnection.channel_type == ChannelType.WHATSAPP
        ).first()

        if not connection:
            connection = ChannelConnection(
                tenant_id=uuid.UUID(tenant_id),
                channel_type=ChannelType.WHATSAPP,
                credentials={"instance": tenant_id, "token": token},
                config={},
                is_active=True
            )
            db.add(connection)
            db.commit()

        return {"status": "created", "instance": tenant_id}

    except Exception as e:
        logger.error("whatsapp_create_session_failed", error=str(e), traceback=traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/whatsapp/qr")
async def get_whatsapp_qr(
    tenant_id: str = Depends(get_current_tenant_id)
):
    """
    Retrieves the QR code via Provider (Evolution only).
    """
    channel = WhatsAppChannel(tenant_id)
    
    try:
        resp = await channel.get_qr()
        
        if resp.get("status") == 200:
            data = resp.get("data", {})
            
            # Normalize response (Provider might have already normalized it partially)
            qr_code = data.get("base64") or data.get("code") or data.get("qrcode")
            
            # Check for nested object
            if not qr_code and isinstance(data.get("qrcode"), dict):
                 qr_code = data.get("qrcode", {}).get("base64")

            if qr_code:
                return {"code": qr_code}
            
            # Pass through other states (like count: 0)
            return data 
        else:
             if resp.get("status") == 404:
                 raise HTTPException(status_code=404, detail="Instance not found. Create session first.")
             raise HTTPException(status_code=500, detail=f"Evolution Error: {resp.get('text')}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/whatsapp/session")
async def delete_whatsapp_session(
    provider: str = "evolution", # Query param
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant_id)
):
    """
    Logs out and deletes the instance via Provider.
    """
    if provider == "meta":
        # Remove Meta from DB
        db.query(ChannelConnection).filter(
            ChannelConnection.tenant_id == uuid.UUID(tenant_id),
            ChannelConnection.channel_type == ChannelType.WHATSAPP_CLOUD
        ).delete()
        db.commit()
        return {"status": "deleted"}

    # --- EVOLUTION LOGIC ---
    channel = WhatsAppChannel(tenant_id)
    
    try:
        await channel.logout()
        await channel.delete_instance()
        
        # Remove from DB
        db.query(ChannelConnection).filter(
            ChannelConnection.tenant_id == uuid.UUID(tenant_id),
            ChannelConnection.channel_type == ChannelType.WHATSAPP
        ).delete()
        db.commit()
        
        return {"status": "deleted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/whatsapp/webhook/{tenant_id}")
async def handle_whatsapp_webhook(
    tenant_id: str,
    payload: dict = Body(...),
    background_tasks: BackgroundTasks = None
):
    """
    Receives webhooks from Evolution API.
    """
    # Basic check - Evolution V1/V2 send "type" or "event"
    # We let the orchestrator/adapter handle normalization
    
    from src.modules.communication.application.orchestrators.chat import ChatOrchestrator
    
    # Instantiate orchestrator
    orchestrator = ChatOrchestrator()
    
    # Create adapter (Context)
    adapter = WhatsAppChannel(tenant_id=tenant_id)
    
    # The adapter's normalize_payload will be called inside orchestrator
    # We pass the raw payload
    if background_tasks:
        background_tasks.add_task(orchestrator._handle_incoming_webhook, adapter, payload, None, tenant_id)
    else:
         await orchestrator._handle_incoming_webhook(adapter, payload, background_tasks, tenant_id)
    
    return {"status": "ok"}

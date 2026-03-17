from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Body, Query, Request
from sqlalchemy.orm import Session
from src.core.database import get_db
from src.modules.connections.domain.enums import ChannelType
from src.modules.connections.infrastructure.repositories import ChannelConnectionRepository
from src.modules.iam.api.dependencies import get_current_tenant_id
from src.modules.connections.infrastructure.channels.whatsapp import WhatsAppChannel
from src.core.config import settings
from src.modules.sales_agent.application.orchestrator.chat import ChatOrchestrator
import structlog
import uuid
import asyncio
import traceback

router = APIRouter(tags=["WhatsApp"])
logger = structlog.get_logger()
orchestrator = ChatOrchestrator()


def _get_repo(db: Session = Depends(get_db)) -> ChannelConnectionRepository:
    return ChannelConnectionRepository(db)


# --- Webhooks ---

@router.get("/webhooks/whatsapp")
async def verify_whatsapp_webhook(
    mode: str = Query(alias="hub.mode"),
    token: str = Query(alias="hub.verify_token"),
    challenge: str = Query(alias="hub.challenge"),
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
    tenant_id: str = Depends(get_current_tenant_id),
    repo: ChannelConnectionRepository = Depends(_get_repo),
):
    tenant_uuid = uuid.UUID(tenant_id)

    # --- 1. EVOLUTION API (QR) STATUS ---
    evolution_status = {"status": "disconnected", "profile": None}

    evo_conn = repo.get_active(tenant_uuid, ChannelType.WHATSAPP)

    if evo_conn:
        channel = WhatsAppChannel(tenant_id)
        status_data = await channel.check_status()

        if status_data.get("exists"):
            state = status_data.get("state")
            if state == "open":
                current_metadata = evo_conn.config.get("metadata", {})
                provider_instance = status_data.get("data", {}).get("instance", {})

                if not current_metadata and provider_instance:
                    owner_jid = provider_instance.get("ownerJid") or provider_instance.get("number")
                    profile_name = (
                        provider_instance.get("profileName")
                        or provider_instance.get("pushName")
                        or "WhatsApp User"
                    )

                    if owner_jid:
                        new_metadata = {
                            "first_name": profile_name,
                            "remote_jid": owner_jid,
                            "platform": "whatsapp",
                            "connected_at": "Sincronizado recientemente",
                        }
                        repo.update_config(evo_conn, {"metadata": new_metadata})
                        current_metadata = new_metadata

                evolution_status = {"status": "connected", "profile": current_metadata}
            elif state == "connecting":
                evolution_status = {"status": "connecting", "profile": None}

    # --- 2. META CLOUD API STATUS ---
    meta_status = {"status": "disconnected", "profile": None}

    meta_conn = repo.get_active(tenant_uuid, ChannelType.WHATSAPP_CLOUD)

    if meta_conn:
        meta_status = {
            "status": "connected",
            "profile": meta_conn.config.get("metadata", {}),
        }

    return {"evolution": evolution_status, "meta": meta_status}


@router.post("/whatsapp/session")
async def create_whatsapp_session(
    provider: str = Body("evolution", embed=True),
    tenant_id: str = Depends(get_current_tenant_id),
    repo: ChannelConnectionRepository = Depends(_get_repo),
):
    if provider == "meta":
        return {"status": "error", "message": "Meta integration coming soon"}

    channel = WhatsAppChannel(tenant_id)

    try:
        status_data = await channel.check_status()

        if status_data.get("exists"):
            logger.info("whatsapp_instance_reset", tenant_id=tenant_id)
            await channel.delete_instance()
            await asyncio.sleep(5)

        token = str(uuid.uuid4())
        resp = await channel.create_instance(token)

        if resp.get("status") != 201:
            logger.error("whatsapp_create_rejected", status=resp.get("status"), body=resp.get("text"))
            raise HTTPException(status_code=500, detail=f"Failed to create instance: {resp.get('text')}")

        await asyncio.sleep(2)

        webhook_url = f"{settings.API_URL}/api/v1/whatsapp/webhook/{tenant_id}"
        webhook_resp = await channel.configure_webhook(webhook_url)

        if webhook_resp.get("status") not in [200, 201]:
            logger.warning("whatsapp_webhook_config_failed", tenant_id=tenant_id, status=webhook_resp.get("status"))

        repo.upsert(
            tenant_id=uuid.UUID(tenant_id),
            channel_type=ChannelType.WHATSAPP,
            credentials={"instance": tenant_id, "token": token},
            config={},
        )

        return {"status": "created", "instance": tenant_id}

    except HTTPException:
        raise
    except Exception as e:
        logger.error("whatsapp_create_session_failed", error=str(e), traceback=traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/whatsapp/qr")
async def get_whatsapp_qr(
    tenant_id: str = Depends(get_current_tenant_id),
):
    channel = WhatsAppChannel(tenant_id)

    try:
        resp = await channel.get_qr()

        if resp.get("status") == 200:
            data = resp.get("data", {})
            qr_code = data.get("base64") or data.get("code") or data.get("qrcode")

            if not qr_code and isinstance(data.get("qrcode"), dict):
                qr_code = data.get("qrcode", {}).get("base64")

            if qr_code:
                return {"code": qr_code}

            return data
        else:
            if resp.get("status") == 404:
                raise HTTPException(status_code=404, detail="Instance not found. Create session first.")
            raise HTTPException(status_code=500, detail=f"Evolution Error: {resp.get('text')}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/whatsapp/session")
async def delete_whatsapp_session(
    provider: str = "evolution",
    tenant_id: str = Depends(get_current_tenant_id),
    repo: ChannelConnectionRepository = Depends(_get_repo),
):
    tenant_uuid = uuid.UUID(tenant_id)

    if provider == "meta":
        connection = repo.get_by_tenant_and_type(tenant_uuid, ChannelType.WHATSAPP_CLOUD)
        if connection:
            repo.deactivate(connection)
        return {"status": "deleted"}

    channel = WhatsAppChannel(tenant_id)

    try:
        await channel.logout()
        await channel.delete_instance()

        connection = repo.get_by_tenant_and_type(tenant_uuid, ChannelType.WHATSAPP)
        if connection:
            repo.deactivate(connection)

        return {"status": "deleted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/whatsapp/webhook/{tenant_id}")
async def handle_whatsapp_webhook(
    tenant_id: str,
    payload: dict = Body(...),
    background_tasks: BackgroundTasks = None,
):
    from src.modules.sales_agent.application.orchestrator.chat import ChatOrchestrator

    orch = ChatOrchestrator()
    adapter = WhatsAppChannel(tenant_id=tenant_id)

    if background_tasks:
        background_tasks.add_task(orch._handle_incoming_webhook, adapter, payload, None, tenant_id)
    else:
        await orch._handle_incoming_webhook(adapter, payload, background_tasks, tenant_id)

    return {"status": "ok"}

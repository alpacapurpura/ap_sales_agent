from fastapi import APIRouter, Depends, HTTPException, Body, Query, Request
from sqlalchemy.orm import Session
from typing import Optional
import structlog
import os
from pydantic import BaseModel

from src.core.database import get_db
from src.core.context import set_tenant_id
from src.modules.iam.api.dependencies import get_current_user
from src.modules.iam.domain.user import User
from src.modules.sales_agent.infrastructure.models.channel_model import ChannelConnectionModel
from src.modules.connections.infrastructure.channels.meta import MetaAdapter
from src.modules.connections.infrastructure.channels.instagram import InstagramChannel
from src.modules.sales_agent.application.orchestrator.chat import ChatOrchestrator
from src.modules.connections.api.dto.meta import MetaStatusResponse
from src.modules.connections.api.dependencies.webhook_security import verify_meta_signature

router = APIRouter(tags=["meta"])
logger = structlog.get_logger()
orchestrator = ChatOrchestrator()

# --- Endpoints ---

@router.get("/webhook")
async def verify_webhook(
    mode: str = Query(..., alias="hub.mode"),
    token: str = Query(..., alias="hub.verify_token"),
    challenge: str = Query(..., alias="hub.challenge")
):
    """
    Meta Webhook Verification.
    """
    # TODO: Move to env var or tenant config
    VERIFY_TOKEN = os.getenv("META_VERIFY_TOKEN", "visionarias_secret_token")
    
    if mode == "subscribe" and token == VERIFY_TOKEN:
        return int(challenge)
    
    raise HTTPException(status_code=403, detail="Verification failed")

@router.post("/webhook")
async def webhook_event(
    payload: dict = Body(...),
    verified: bool = Depends(verify_meta_signature),
    db: Session = Depends(get_db)
):
    """
    Handle incoming Meta Webhooks (Instagram/Messenger).
    """
    try:
        # 1. Identify Tenant by Instagram Account ID
        # The payload structure: object='instagram', entry=[{id: 'ACCOUNT_ID', ...}]
        entry = payload.get("entry", [])[0]
        account_id = entry.get("id") 
    except (IndexError, AttributeError):
        # Could be a different event type or malformed
        return {"status": "ignored", "reason": "invalid_payload"}

    # Find connection with this account_id
    # Scanning all meta connections to find the one with matching user_id/account_id
    # Optimization: Add index on config->>'user_id' or dedicated column
    connections = db.query(ChannelConnectionModel).filter(
        ChannelConnectionModel.channel_type.in_(['meta', 'instagram']),
        ChannelConnectionModel.is_active.is_(True)
    ).all()
    
    connection = None
    for conn in connections:
        if conn.config.get("user_id") == account_id:
            connection = conn
            break
            
    if not connection:
        logger.warning("meta_webhook_unknown_account", account_id=account_id)
        return {"status": "ignored", "reason": "unknown_account"}

    # Set Context for the Orchestrator
    set_tenant_id(connection.tenant_id)
    
    # 2. Initialize Channel
    channel = InstagramChannel(
        client_config=connection.config,
        credentials_data=connection.credentials
    )
    
    # 3. Normalize Payload
    incoming = channel.normalize_payload(payload)
    if not incoming:
        return {"status": "ignored", "reason": "normalization_failed"}
        
    # 4. Process Flow
    try:
        await orchestrator.process_chat_flow(channel, incoming)
    except Exception as e:
        logger.error("meta_webhook_process_error", error=str(e))
        # Don't fail the webhook response, or Meta will retry indefinitely
        
    return {"status": "processed"}

@router.get("/auth-url")
async def get_auth_url(
    redirect_uri: Optional[str] = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """
    Get the Meta OAuth2 authorization URL.
    Uses global environment variables for Client ID.
    """
    if not redirect_uri:
         raise HTTPException(status_code=400, detail="Redirect URI is required")

    adapter = MetaAdapter()
    url, state = adapter.get_authorization_url(redirect_uri)
    return {"url": url, "state": state}

@router.post("/callback")
async def oauth_callback(
    code: str = Body(..., embed=True),
    redirect_uri: str = Body(..., embed=True),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """
    Exchange the authorization code for tokens and save connection.
    """
    adapter = MetaAdapter()

    try:
        creds_data = await adapter.exchange_code(code, redirect_uri)
    except Exception as e:
        logger.error("meta_oauth_exchange_failed", error=str(e))
        raise HTTPException(status_code=400, detail="Error de autenticación con Meta")

    # Get profile to identify
    try:
        adapter_with_token = MetaAdapter(access_token=creds_data.get("access_token"))
        profile = await adapter_with_token.get_user_profile()
        user_id = profile.get('id')
        name = profile.get('name')
        if not user_id:
            raise ValueError("User ID not found in profile")
    except Exception as e:
        logger.error("failed_to_get_meta_profile", error=str(e))
        raise HTTPException(status_code=400, detail="No se pudo obtener el perfil de Meta.")

    # Save or Update connection
    connection = db.query(ChannelConnectionModel).filter(
        ChannelConnectionModel.tenant_id == user.tenant_id,
        ChannelConnectionModel.channel_type == 'meta'
    ).first()

    new_config = {"user_id": user_id, "name": name}

    if connection:
        current_config = dict(connection.config) if connection.config else {}
        current_config.update(new_config)
        connection.config = current_config
        connection.credentials = creds_data
        connection.is_active = True
    else:
        connection = ChannelConnectionModel(
            tenant_id=user.tenant_id,
            channel_type='meta',
            config=new_config,
            credentials=creds_data,
            is_active=True
        )
        db.add(connection)
    
    db.commit()
    return {"status": "connected", "profile": profile}

@router.get("/status", response_model=MetaStatusResponse)
async def get_status(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """
    Check if Meta is connected.
    """
    connection = db.query(ChannelConnectionModel).filter(
        ChannelConnectionModel.tenant_id == user.tenant_id,
        ChannelConnectionModel.channel_type == 'meta',
        ChannelConnectionModel.is_active.is_(True)
    ).first()
    
    if not connection:
        return MetaStatusResponse(is_connected=False)
        
    return MetaStatusResponse(
        is_connected=True, 
        name=connection.config.get("name"),
        account_id=connection.config.get("user_id")
    )

@router.delete("/disconnect")
async def disconnect(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """
    Disconnect Meta.
    """
    connection = db.query(ChannelConnectionModel).filter(
        ChannelConnectionModel.tenant_id == user.tenant_id,
        ChannelConnectionModel.channel_type == 'meta'
    ).first()
    
    if connection:
        db.delete(connection)
        db.commit()
        
    return {"status": "disconnected"}

@router.post("/test")
async def test_connection(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """
    Test Meta connection by fetching profile.
    """
    connection = db.query(ChannelConnectionModel).filter(
        ChannelConnectionModel.tenant_id == user.tenant_id,
        ChannelConnectionModel.channel_type == 'meta',
        ChannelConnectionModel.is_active.is_(True)
    ).first()
    
    if not connection or not connection.credentials:
        raise HTTPException(status_code=400, detail="Meta no conectado")
        
    try:
        access_token = connection.credentials.get("access_token")
        if not access_token:
             raise ValueError("Token de acceso no encontrado")

        adapter = MetaAdapter(access_token=access_token)
        profile = await adapter.get_user_profile()
        return {"status": "ok", "message": "Conexión exitosa", "data": profile}
    except Exception as e:
        logger.error("meta_test_failed", error=str(e))
        return {"status": "error", "message": str(e)}

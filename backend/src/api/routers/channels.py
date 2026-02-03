from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel
import httpx
from typing import Optional, Dict, Any
import structlog

from src.services.database import get_db
from src.api.dependencies import get_current_user
from src.services.db.models.user import User
from src.services.db.models.channel_connection import ChannelConnection, ChannelType
from src.config import settings

router = APIRouter(prefix="/channels", tags=["channels"])
logger = structlog.get_logger()

# --- Schemas ---
class TelegramConnectRequest(BaseModel):
    token: str

class ChannelStatusResponse(BaseModel):
    is_connected: bool
    bot_name: Optional[str] = None
    username: Optional[str] = None
    config: Dict[str, Any] = {}

class TelegramConfigRequest(BaseModel):
    config: Dict[str, Any]

# --- Endpoints ---

@router.get("/telegram", response_model=ChannelStatusResponse)
async def get_telegram_status(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """
    Get current Telegram connection status for the tenant.
    """
    connection = db.query(ChannelConnection).filter(
        ChannelConnection.tenant_id == user.tenant_id,
        ChannelConnection.channel_type == ChannelType.TELEGRAM,
        ChannelConnection.is_active.is_(True)
    ).first()

    if not connection:
        return ChannelStatusResponse(is_connected=False)

    metadata = connection.config.get("metadata", {})
    return ChannelStatusResponse(
        is_connected=True,
        bot_name=metadata.get("first_name"),
        username=metadata.get("username"),
        config=connection.config
    )

@router.post("/telegram/connect")
async def connect_telegram(
    payload: TelegramConnectRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """
    Connect a Telegram Bot to the tenant.
    Validates token, sets webhook, and saves to DB.
    """
    token = payload.token.strip()
    
    # 1. Validate Token with Telegram
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(f"https://api.telegram.org/bot{token}/getMe", timeout=10.0)
            if resp.status_code != 200:
                logger.warning("invalid_telegram_token", status_code=resp.status_code, body=resp.text)
                raise HTTPException(status_code=400, detail="Token de Telegram inválido. Verifique e intente nuevamente.")
            bot_info = resp.json().get("result", {})
        except httpx.RequestError as e:
            logger.error("telegram_connection_error", error=str(e))
            raise HTTPException(status_code=503, detail=f"Error conectando con Telegram: {str(e)}")

    # 2. Set Webhook
    # Force use of API_DOMAIN if available, otherwise construct from DOMAIN_NAME
    # NOTE: Telegram requires a publicly accessible HTTPS URL.
    # We must ensure we are not sending a .local domain if it is configured that way by mistake.
    
    final_domain = None
    
    if settings.API_DOMAIN and "local" not in settings.API_DOMAIN:
         final_domain = settings.API_DOMAIN
    else:
         # Fallback to the main domain which we know is tunneled
         final_domain = settings.DOMAIN_NAME

    # Ensure protocol
    if final_domain.startswith("http"):
         base_url = final_domain
    else:
         base_url = f"https://{final_domain}"

    webhook_url = f"{base_url}/api/v1/webhooks/telegram/{user.tenant_id}"
    logger.info("setting_telegram_webhook", webhook_url=webhook_url)
    
    async with httpx.AsyncClient() as client:
        try:
            # Delete old webhook first to be safe
            await client.get(f"https://api.telegram.org/bot{token}/deleteWebhook")
            
            # Set new webhook
            webhook_resp = await client.post(
                f"https://api.telegram.org/bot{token}/setWebhook",
                json={"url": webhook_url}
            )
            
            if webhook_resp.status_code != 200:
                logger.error("failed_to_set_webhook", status_code=webhook_resp.status_code, response=webhook_resp.text)
                error_detail = "No se pudo configurar el Webhook en Telegram."
                try:
                    error_json = webhook_resp.json()
                    if error_json.get("description"):
                        error_detail = f"Telegram Error: {error_json.get('description')}"
                except Exception:
                    pass
                raise HTTPException(status_code=500, detail=error_detail)
            
            logger.info("webhook_set_success", response=webhook_resp.json())
                
        except httpx.RequestError as e:
            logger.error("webhook_network_error", error=str(e))
            raise HTTPException(status_code=503, detail=f"Error configurando Webhook: {str(e)}")

    # 3. Save to DB
    # Check if exists
    connection = db.query(ChannelConnection).filter(
        ChannelConnection.tenant_id == user.tenant_id,
        ChannelConnection.channel_type == ChannelType.TELEGRAM
    ).first()

    metadata = {
        "id": bot_info.get("id"),
        "first_name": bot_info.get("first_name"),
        "username": bot_info.get("username"),
    }

    if connection:
        connection.credentials = {"token": token}
        connection.config["metadata"] = metadata
        connection.is_active = True
    else:
        connection = ChannelConnection(
            tenant_id=user.tenant_id,
            channel_type=ChannelType.TELEGRAM,
            credentials={"token": token},
            config={"metadata": metadata},
            is_active=True
        )
        db.add(connection)
    
    db.commit()
    db.refresh(connection)

    return {"status": "connected", "bot": metadata}

@router.post("/telegram/test")
async def test_telegram_connection(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """
    Test the current Telegram connection.
    """
    connection = db.query(ChannelConnection).filter(
        ChannelConnection.tenant_id == user.tenant_id,
        ChannelConnection.channel_type == ChannelType.TELEGRAM,
        ChannelConnection.is_active.is_(True)
    ).first()

    if not connection:
        raise HTTPException(status_code=404, detail="No hay conexión de Telegram activa.")

    token = connection.credentials.get("token")
    if not token:
        raise HTTPException(status_code=500, detail="Credenciales corruptas.")

    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(f"https://api.telegram.org/bot{token}/getMe", timeout=5.0)
            if resp.status_code == 200:
                return {"status": "ok", "message": "Conexión exitosa", "data": resp.json()}
            else:
                return {"status": "error", "message": "El token parece inválido o expirado."}
        except Exception as e:
            return {"status": "error", "message": f"Error de red: {str(e)}"}

@router.delete("/telegram")
async def disconnect_telegram(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """
    Disconnect Telegram: Delete Webhook and deactivate in DB.
    """
    connection = db.query(ChannelConnection).filter(
        ChannelConnection.tenant_id == user.tenant_id,
        ChannelConnection.channel_type == ChannelType.TELEGRAM
    ).first()

    if not connection or not connection.is_active:
        raise HTTPException(status_code=404, detail="No hay conexión activa para desconectar.")

    token = connection.credentials.get("token")
    if token:
        # Try to remove webhook, but don't fail if it fails (maybe token is already invalid)
        async with httpx.AsyncClient() as client:
            try:
                await client.get(f"https://api.telegram.org/bot{token}/deleteWebhook")
            except Exception as e:
                logger.warning(f"Failed to delete webhook during disconnect: {e}")

    # Soft delete (or hard delete? User said "eliminar", usually soft delete or just remove credentials)
    # Let's delete the record to be clean as per "eliminar la conexión"
    db.delete(connection)
    db.commit()

    return {"status": "disconnected"}

import httpx
import structlog
from sqlalchemy.orm import Session
from uuid import UUID
from typing import Dict, Any

from src.modules.communication.domain.channel_connection import ChannelConnection, ChannelType
from src.config import settings

logger = structlog.get_logger()

class TelegramService:
    def __init__(self, db: Session):
        self.db = db

    def get_status(self, tenant_id: UUID) -> Dict[str, Any]:
        """
        Get current Telegram connection status for the tenant.
        """
        connection = self.db.query(ChannelConnection).filter(
            ChannelConnection.tenant_id == tenant_id,
            ChannelConnection.channel_type == ChannelType.TELEGRAM,
            ChannelConnection.is_active.is_(True)
        ).first()

        if not connection:
            return {"is_connected": False}

        metadata = connection.config.get("metadata", {})
        return {
            "is_connected": True,
            "bot_name": metadata.get("first_name"),
            "username": metadata.get("username"),
            "config": connection.config
        }

    async def connect(self, tenant_id: UUID, token: str) -> Dict[str, Any]:
        """
        Connect a Telegram Bot to the tenant.
        Validates token, sets webhook, and saves to DB.
        """
        token = token.strip()
        
        # 1. Validate Token with Telegram
        async with httpx.AsyncClient() as client:
            try:
                resp = await client.get(f"https://api.telegram.org/bot{token}/getMe", timeout=10.0)
                if resp.status_code != 200:
                    logger.warning("invalid_telegram_token", status_code=resp.status_code, body=resp.text)
                    raise ValueError("Token de Telegram inválido. Verifique e intente nuevamente.")
                bot_info = resp.json().get("result", {})
            except httpx.RequestError as e:
                logger.error("telegram_connection_error", error=str(e))
                raise RuntimeError(f"Error conectando con Telegram: {str(e)}")

        # 2. Set Webhook
        final_domain = None
        
        if settings.API_DOMAIN and "local" not in settings.API_DOMAIN:
             final_domain = settings.API_DOMAIN
        else:
             final_domain = settings.DOMAIN_NAME

        if final_domain.startswith("http"):
             base_url = final_domain
        else:
             base_url = f"https://{final_domain}"

        webhook_url = f"{base_url}/api/v1/webhooks/telegram/{tenant_id}"
        logger.info("setting_telegram_webhook", webhook_url=webhook_url)
        
        async with httpx.AsyncClient() as client:
            try:
                # Delete old webhook first
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
                    except Exception as e:
                        logger.warning("failed_to_parse_telegram_error", error=str(e))
                    raise RuntimeError(error_detail)
                
                logger.info("webhook_set_success", response=webhook_resp.json())
                    
            except httpx.RequestError as e:
                logger.error("webhook_network_error", error=str(e))
                raise RuntimeError(f"Error configurando Webhook: {str(e)}")

        # 3. Save to DB
        connection = self.db.query(ChannelConnection).filter(
            ChannelConnection.tenant_id == tenant_id,
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
                tenant_id=tenant_id,
                channel_type=ChannelType.TELEGRAM,
                credentials={"token": token},
                config={"metadata": metadata},
                is_active=True
            )
            self.db.add(connection)
        
        self.db.commit()
        self.db.refresh(connection)

        return {"status": "connected", "bot": metadata}

    async def test_connection(self, tenant_id: UUID) -> Dict[str, Any]:
        """
        Test the current Telegram connection.
        """
        connection = self.db.query(ChannelConnection).filter(
            ChannelConnection.tenant_id == tenant_id,
            ChannelConnection.channel_type == ChannelType.TELEGRAM,
            ChannelConnection.is_active.is_(True)
        ).first()

        if not connection:
            raise ValueError("No hay conexión de Telegram activa.")

        token = connection.credentials.get("token")
        if not token:
            raise RuntimeError("Credenciales corruptas.")

        async with httpx.AsyncClient() as client:
            try:
                resp = await client.get(f"https://api.telegram.org/bot{token}/getMe", timeout=5.0)
                if resp.status_code == 200:
                    return {"status": "ok", "message": "Conexión exitosa", "data": resp.json()}
                else:
                    return {"status": "error", "message": "El token parece inválido o expirado."}
            except Exception as e:
                return {"status": "error", "message": f"Error de red: {str(e)}"}

    async def disconnect(self, tenant_id: UUID) -> Dict[str, Any]:
        """
        Disconnect Telegram: Delete Webhook and deactivate in DB.
        """
        connection = self.db.query(ChannelConnection).filter(
            ChannelConnection.tenant_id == tenant_id,
            ChannelConnection.channel_type == ChannelType.TELEGRAM
        ).first()

        if not connection or not connection.is_active:
            raise ValueError("No hay conexión activa para desconectar.")

        token = connection.credentials.get("token")
        if token:
            async with httpx.AsyncClient() as client:
                try:
                    await client.get(f"https://api.telegram.org/bot{token}/deleteWebhook")
                except Exception as e:
                    logger.warning(f"Failed to delete webhook during disconnect: {e}")

        self.db.delete(connection)
        self.db.commit()

        return {"status": "disconnected"}

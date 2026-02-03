from typing import Dict, Any, Optional
import httpx
import structlog
from src.core.domain.schema import IncomingMessage, OutgoingMessage
from .interface import WhatsAppProvider

logger = structlog.get_logger()

class EvolutionApiV1(WhatsAppProvider):
    """
    Strategy for Evolution API v1.x (Stable for WSL2/Dev).
    """

    def normalize_payload(self, payload: Dict[str, Any]) -> Optional[IncomingMessage]:
        # V1 Webhook Payload
        # Usually: { "data": { "key": {...}, "message": {...} }, "sender": ... }
        # Matches current implementation
        data = payload.get("data", {})
        key = data.get("key", {})
        message = data.get("message", {})
        
        # Check if it's a text message
        conversation = message.get("conversation") or \
                       message.get("extendedTextMessage", {}).get("text")
        
        if not conversation:
            return None
            
        # Ignore messages from self
        if key.get("fromMe"):
            return None
            
        remote_jid = key.get("remoteJid") # e.g., 573001234567@s.whatsapp.net
        if not remote_jid:
            return None
            
        user_id = remote_jid.split("@")[0] # Just the number
        push_name = data.get("pushName", "User")
        
        metadata = {
            "first_name": push_name,
            "source": "whatsapp",
            "remote_jid": remote_jid
        }
        
        return IncomingMessage(
            user_id=user_id,
            text=conversation,
            channel_type="whatsapp",
            metadata=metadata
        )

    async def send_message(self, message: OutgoingMessage) -> Dict[str, Any]:
        url = f"{self.base_url}/message/sendText/{self.tenant_id}"
        
        remote_jid = message.user_id
        if "@" not in remote_jid:
            remote_jid = f"{remote_jid}@s.whatsapp.net"
            
        payload = {
            "number": remote_jid,
            "text": message.text,
            "linkPreview": False
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(url, json=payload, headers=self.headers, timeout=10.0)
                if response.status_code not in [200, 201]:
                    logger.error("whatsapp_v1_send_failed", status=response.status_code, body=response.text)
                    return {"error": f"Evolution API V1 Error: {response.status_code}"}
                return response.json()
            except Exception as e:
                logger.error("whatsapp_v1_network_error", error=str(e))
                raise e

    async def set_typing_status(self, user_id: str) -> None:
        url = f"{self.base_url}/chat/sendPresence/{self.tenant_id}"
        remote_jid = user_id
        if "@" not in remote_jid:
            remote_jid = f"{remote_jid}@s.whatsapp.net"
            
        payload = {
            "number": remote_jid,
            "presence": "composing",
            "delay": 1200
        }
        async with httpx.AsyncClient() as client:
            try:
                await client.post(url, json=payload, headers=self.headers, timeout=5.0)
            except Exception:
                pass

    # Management
    async def create_instance(self, token: str) -> Dict[str, Any]:
        url = f"{self.base_url}/instance/create"
        payload = {
            "instanceName": self.tenant_id,
            "token": token,
            "qrcode": True,
            # No "integration" field for V1
            "reject_call": False,
            "groupsIgnore": True,
            "alwaysOnline": False,
            "readMessages": False,
            "readStatus": False
        }
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(url, json=payload, headers=self.headers)
            return {"status": resp.status_code, "data": resp.json() if resp.text else {}, "text": resp.text}

    async def delete_instance(self) -> Dict[str, Any]:
        url = f"{self.base_url}/instance/delete/{self.tenant_id}"
        async with httpx.AsyncClient() as client:
            resp = await client.delete(url, headers=self.headers)
            return {"status": resp.status_code}

    async def check_status(self) -> Dict[str, Any]:
        url = f"{self.base_url}/instance/connectionState/{self.tenant_id}"
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, headers=self.headers, timeout=5.0)
            if resp.status_code == 200:
                data = resp.json()
                # V1: { "instance": { "state": "open" ... } }
                state = data.get("instance", {}).get("state", "close")
                return {"exists": True, "state": state, "data": data}
            elif resp.status_code == 404:
                return {"exists": False, "state": "disconnected"}
            return {"exists": True, "state": "error", "error": resp.text}

    async def get_qr(self) -> Dict[str, Any]:
        url = f"{self.base_url}/instance/connect/{self.tenant_id}"
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, headers=self.headers)
            if resp.status_code == 200:
                data = resp.json()
                # V1: { "base64": "..." } or { "code": "..." }
                return {"status": 200, "data": data}
            return {"status": resp.status_code, "text": resp.text}

    async def configure_webhook(self, webhook_url: str) -> Dict[str, Any]:
        # V1 Webhook Config
        url = f"{self.base_url}/webhook/set/{self.tenant_id}"
        payload = {
            "enabled": True,
            "url": webhook_url,
            "webhookByEvents": True,
            "events": ["MESSAGES_UPSERT", "CONNECTION_UPDATE"]
        }
        async with httpx.AsyncClient() as client:
            resp = await client.post(url, json=payload, headers=self.headers)
            return {"status": resp.status_code, "text": resp.text}

    async def logout(self) -> Dict[str, Any]:
        url = f"{self.base_url}/instance/logout/{self.tenant_id}"
        async with httpx.AsyncClient() as client:
            resp = await client.delete(url, headers=self.headers)
            return {"status": resp.status_code}

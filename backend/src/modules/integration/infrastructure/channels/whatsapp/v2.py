from typing import Dict, Any, Optional
import httpx
from src.shared.domain.messages import IncomingMessage, OutgoingMessage
from .base import BaseEvolutionApi

class EvolutionApiV2(BaseEvolutionApi):
    """
    Strategy for Evolution API v2.x (Production).
    """

    def normalize_payload(self, payload: Dict[str, Any]) -> Optional[IncomingMessage]:
        # Reuse base logic and add version metadata
        message = super().normalize_payload(payload)
        if message:
            message.metadata["version"] = "v2"
        return message

    async def create_instance(self, token: str) -> Dict[str, Any]:
        url = f"{self.base_url}/instance/create"
        payload = {
            "instanceName": self.tenant_id,
            "token": token,
            "qrcode": True,
            "integration": "WHATSAPP-BAILEYS", # Required for V2
            "reject_call": False,
            "groupsIgnore": True,
            "alwaysOnline": False,
            "readMessages": False,
            "readStatus": False
        }
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(url, json=payload, headers=self.headers)
            return {"status": resp.status_code, "data": resp.json() if resp.text else {}, "text": resp.text}

    async def configure_webhook(self, webhook_url: str) -> Dict[str, Any]:
        # V2 Webhook Config - Nested Structure
        url = f"{self.base_url}/webhook/set/{self.tenant_id}"
        payload = {
            "webhook": {
                "enabled": True,
                "url": webhook_url,
                "webhookByEvents": True,
                "events": ["MESSAGES_UPSERT", "CONNECTION_UPDATE"]
            }
        }
        async with httpx.AsyncClient() as client:
            resp = await client.post(url, json=payload, headers=self.headers)
            return {"status": resp.status_code, "text": resp.text}

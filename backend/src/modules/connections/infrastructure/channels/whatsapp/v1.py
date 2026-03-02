from typing import Dict, Any
import httpx
from .base import BaseEvolutionApi

class EvolutionApiV1(BaseEvolutionApi):
    """
    Strategy for Evolution API v1.x (Stable for WSL2/Dev).
    """

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

"""Base channel adapter."""

import contextlib
from typing import Any

import httpx
import structlog
from luana_core_platform.domain.messages import IncomingMessage, OutgoingMessage

from .interface import WhatsAppProvider

logger = structlog.get_logger()


class BaseEvolutionApi(WhatsAppProvider):
    """Base strategy for Evolution API (Common logic for V1 and V2)."""

    def _normalize_jid(self, user_id: str) -> str:
        """Ensure JID has the correct suffix."""
        if "@" not in user_id:
            return f"{user_id}@s.whatsapp.net"
        return user_id

    def normalize_payload(self, payload: dict[str, Any]) -> IncomingMessage | None:
        """Normalize payload with common logic.

        Extracts message text, sender info, and metadata.
        """
        data = payload.get("data", {})
        key = data.get("key", {})
        message = data.get("message", {})

        # Check for text content
        conversation = message.get("conversation") or message.get(
            "extendedTextMessage",
            {},
        ).get("text")

        if not conversation:
            return None

        # Ignore messages from self
        if key.get("fromMe"):
            return None

        remote_jid = key.get("remoteJid")
        if not remote_jid:
            return None

        user_id = remote_jid.split("@")[0]
        push_name = data.get("pushName", "User")

        metadata = {
            "first_name": push_name,
            "source": "whatsapp",
            "remote_jid": remote_jid,
        }

        return IncomingMessage(
            user_id=user_id,
            text=conversation,
            channel_type="whatsapp",
            metadata=metadata,
        )

    async def send_message(self, message: OutgoingMessage) -> dict[str, Any]:
        """Send message."""
        url = f"{self.base_url}/message/sendText/{self.tenant_id}"

        remote_jid = self._normalize_jid(message.user_id)

        payload = {"number": remote_jid, "text": message.text, "linkPreview": False}

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    url,
                    json=payload,
                    headers=self.headers,
                    timeout=10.0,
                )
                if response.status_code not in [200, 201]:
                    # Use class name in log to distinguish V1/V2
                    logger.error(
                        "whatsapp_send_failed",
                        provider=self.__class__.__name__.lower(),
                        status=response.status_code,
                        body=response.text,
                    )
                    return {"error": f"Evolution API Error: {response.status_code}"}
                return response.json()
            except Exception as e:
                logger.exception(
                    "whatsapp_network_error",
                    provider=self.__class__.__name__.lower(),
                    error=str(e),
                )
                raise

    async def set_typing_status(self, user_id: str) -> None:
        """Set typing status."""
        url = f"{self.base_url}/chat/sendPresence/{self.tenant_id}"
        remote_jid = self._normalize_jid(user_id)

        payload = {"number": remote_jid, "presence": "composing", "delay": 1200}
        async with httpx.AsyncClient() as client:
            with contextlib.suppress(Exception):
                await client.post(url, json=payload, headers=self.headers, timeout=5.0)

    async def delete_instance(self) -> dict[str, Any]:
        """Delete instance."""
        url = f"{self.base_url}/instance/delete/{self.tenant_id}"
        async with httpx.AsyncClient() as client:
            resp = await client.delete(url, headers=self.headers)
            return {"status": resp.status_code}

    async def logout(self) -> dict[str, Any]:
        """Logout."""
        url = f"{self.base_url}/instance/logout/{self.tenant_id}"
        async with httpx.AsyncClient() as client:
            resp = await client.delete(url, headers=self.headers)
            return {"status": resp.status_code}

    async def check_status(self) -> dict[str, Any]:
        """Check status."""
        url = f"{self.base_url}/instance/connectionState/{self.tenant_id}"
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, headers=self.headers, timeout=5.0)
            if resp.status_code == 200:
                data = resp.json()
                state = data.get("instance", {}).get("state", "close")
                return {"exists": True, "state": state, "data": data}
            if resp.status_code == 404:
                return {"exists": False, "state": "disconnected"}
            return {"exists": True, "state": "error", "error": resp.text}

    async def get_qr(self) -> dict[str, Any]:
        """Retrieve qr."""
        url = f"{self.base_url}/instance/connect/{self.tenant_id}"
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, headers=self.headers)
            if resp.status_code == 200:
                return {"status": 200, "data": resp.json()}
            return {"status": resp.status_code, "text": resp.text}

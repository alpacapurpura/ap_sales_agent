from typing import Dict, Any, List, Tuple

import httpx

from .base import BaseConnector


class ManyChatConnector(BaseConnector):
    """Conector para verificar conexion y operar con ManyChat API."""

    @staticmethod
    async def verify_connection(api_key: str) -> Tuple[bool, Dict[str, Any]]:
        """Verifica si el Token es valido haciendo una llamada a /fb/page/getInfo."""
        url = "https://api.manychat.com/fb/page/getInfo"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=headers)

                if response.status_code == 200:
                    data = response.json()
                    if data.get("status") == "success":
                        return True, data.get("data", {})
                    else:
                        return False, {
                            "error": f"API Error: {data.get('message', 'Unknown error')}"
                        }
                else:
                    return False, {
                        "error": f"Status: {response.status_code}, Body: {response.text}"
                    }
        except Exception as e:
            return False, {"error": str(e)}

    @staticmethod
    async def get_subscriber(
        api_key: str, subscriber_id: str
    ) -> Tuple[bool, Dict[str, Any]]:
        """Fetch full subscriber profile by ManyChat ID."""
        url = f"https://api.manychat.com/fb/subscriber/getInfo?subscriber_id={subscriber_id}"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Accept": "application/json",
        }
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=headers, timeout=10.0)
                if response.status_code == 200:
                    data = response.json()
                    if data.get("status") == "success":
                        return True, data.get("data", {})
                return False, {"error": f"Status: {response.status_code}"}
        except Exception as e:
            return False, {"error": str(e)}

    @staticmethod
    async def find_subscriber_by_email(
        api_key: str, email: str
    ) -> Tuple[bool, Dict[str, Any]]:
        """Find subscriber by email via system field search."""
        url = "https://api.manychat.com/fb/subscriber/findBySystemField"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Accept": "application/json",
        }
        params = {"field": "email", "value": email}
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    url, headers=headers, params=params, timeout=10.0
                )
                if response.status_code == 200:
                    data = response.json()
                    if data.get("status") == "success":
                        return True, data.get("data", [])
                return False, {"error": f"Status: {response.status_code}"}
        except Exception as e:
            return False, {"error": str(e)}

    @staticmethod
    async def get_tags(api_key: str) -> Tuple[bool, List[Dict[str, Any]]]:
        """List all bot tags."""
        url = "https://api.manychat.com/fb/page/getTags"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Accept": "application/json",
        }
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=headers, timeout=10.0)
                if response.status_code == 200:
                    data = response.json()
                    if data.get("status") == "success":
                        return True, data.get("data", [])
                return False, []
        except Exception:
            return False, []

    @staticmethod
    async def get_custom_fields(api_key: str) -> Tuple[bool, List[Dict[str, Any]]]:
        """List all custom fields."""
        url = "https://api.manychat.com/fb/page/getCustomFields"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Accept": "application/json",
        }
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=headers, timeout=10.0)
                if response.status_code == 200:
                    data = response.json()
                    if data.get("status") == "success":
                        return True, data.get("data", [])
                return False, []
        except Exception:
            return False, []

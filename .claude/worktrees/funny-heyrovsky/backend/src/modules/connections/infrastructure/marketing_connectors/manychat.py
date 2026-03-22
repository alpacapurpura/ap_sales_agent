from typing import Dict, Any, Tuple
import httpx
from .base import BaseConnector

class ManyChatConnector(BaseConnector):
    """
    Conector para verificar conexión con ManyChat.
    """

    @staticmethod
    async def verify_connection(api_key: str) -> Tuple[bool, Dict[str, Any]]:
        """
        Verifica si el Token es válido haciendo una llamada a /fb/page/getInfo.
        """
        url = "https://api.manychat.com/fb/page/getInfo"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=headers)
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("status") == "success":
                         return True, data.get("data", {})
                    else:
                         return False, {"error": f"API Error: {data.get('message', 'Unknown error')}"}
                else:
                    return False, {"error": f"Status: {response.status_code}, Body: {response.text}"}
        except Exception as e:
            return False, {"error": str(e)}

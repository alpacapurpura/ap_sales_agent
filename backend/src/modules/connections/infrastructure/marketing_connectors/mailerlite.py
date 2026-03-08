from typing import List, Dict, Any, Tuple
import httpx
from .base import BaseConnector

class MailerliteConnector(BaseConnector):
    """
    Conector para sincronizar datos con MailerLite.
    """

    @staticmethod
    async def verify_connection(api_key: str) -> Tuple[bool, Dict[str, Any]]:
        """
        Verifica si la API Key es válida haciendo una llamada a /api/account.
        """
        url = "https://connect.mailerlite.com/api/account"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=headers)
                
                if response.status_code == 200:
                    return True, response.json()
                else:
                    return False, {"error": f"Status: {response.status_code}, Body: {response.text}"}
        except Exception as e:
            return False, {"error": str(e)}
    
    def sync_contacts(self, tenant_id: str) -> List[Dict[str, Any]]:
        # TODO: Implementar lógica real de MailerLite para obtener suscriptores
        print(f"Sincronizando contactos de MailerLite para tenant {tenant_id}")
        return []

    def sync_events(self, tenant_id: str) -> List[Dict[str, Any]]:
        # TODO: Implementar lógica real de MailerLite para obtener eventos (aperturas, clics, etc.)
        print(f"Sincronizando eventos de MailerLite para tenant {tenant_id}")
        return []

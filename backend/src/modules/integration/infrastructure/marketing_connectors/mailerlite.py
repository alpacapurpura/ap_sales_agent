from typing import List, Dict, Any
from .base import BaseConnector

class MailerliteConnector(BaseConnector):
    """
    Conector para sincronizar datos con MailerLite.
    """
    
    def sync_contacts(self, tenant_id: str) -> List[Dict[str, Any]]:
        # TODO: Implementar lógica real de MailerLite para obtener suscriptores
        print(f"Sincronizando contactos de MailerLite para tenant {tenant_id}")
        return []

    def sync_events(self, tenant_id: str) -> List[Dict[str, Any]]:
        # TODO: Implementar lógica real de MailerLite para obtener eventos (aperturas, clics, etc.)
        print(f"Sincronizando eventos de MailerLite para tenant {tenant_id}")
        return []

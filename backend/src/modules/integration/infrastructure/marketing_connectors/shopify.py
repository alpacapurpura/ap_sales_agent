from typing import List, Dict, Any
from .base import BaseConnector

class ShopifyConnector(BaseConnector):
    """
    Conector para sincronizar datos con Shopify.
    """
    
    def sync_contacts(self, tenant_id: str) -> List[Dict[str, Any]]:
        # TODO: Implementar lógica real de Shopify para obtener clientes
        print(f"Sincronizando contactos de Shopify para tenant {tenant_id}")
        return []

    def sync_events(self, tenant_id: str) -> List[Dict[str, Any]]:
        # TODO: Implementar lógica real de Shopify para obtener eventos (órdenes, carritos abandonados, etc.)
        print(f"Sincronizando eventos de Shopify para tenant {tenant_id}")
        return []

from abc import ABC, abstractmethod
from typing import Any


class BaseConnector(ABC):
    """
    Clase base abstracta para conectores de marketing.
    Define la interfaz para sincronizar contactos y eventos.
    """

    @abstractmethod
    def sync_contacts(self, tenant_id: str) -> list[dict[str, Any]]:
        """
        Sincroniza contactos desde la fuente externa.
        Debe devolver una lista de diccionarios con la información del contacto.
        """

    @abstractmethod
    def sync_events(self, tenant_id: str) -> list[dict[str, Any]]:
        """
        Sincroniza eventos desde la fuente externa.
        Debe devolver una lista de diccionarios con la información del evento.
        """

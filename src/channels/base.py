from abc import ABC, abstractmethod
from typing import Any, Optional
from src.core.schema import IncomingMessage, OutgoingMessage

class BaseChannel(ABC):
    """
    Clase abstracta que define el contrato para cualquier canal de comunicación.
    """
    
    @abstractmethod
    def normalize_payload(self, request: Any) -> Optional[IncomingMessage]:
        """
        Convierte el payload específico del canal a un IncomingMessage unificado.
        Retorna None si el payload no es un mensaje de texto válido (ej. status update).
        """
        pass

    @abstractmethod
    async def send_message(self, message: OutgoingMessage) -> None:
        """
        Envía una respuesta al canal específico.
        """
        pass

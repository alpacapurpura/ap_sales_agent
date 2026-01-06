from pydantic import BaseModel, Field
from typing import Optional, Any, Dict, Literal

class IncomingMessage(BaseModel):
    """
    Modelo unificado para mensajes entrantes de cualquier canal.
    Normaliza la entrada antes de que llegue al Agente.
    """
    user_id: str = Field(..., description="Identificador único del usuario en el canal origen")
    text: str = Field(..., description="Contenido textual del mensaje")
    channel_type: Literal["telegram", "whatsapp", "manychat", "web"] = Field(..., description="Canal de origen")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Datos extra del canal (nombre, teléfono, etc.)")

class OutgoingMessage(BaseModel):
    """
    Modelo unificado para respuestas del Agente.
    Los adaptadores convertirán esto al formato específico del canal.
    """
    user_id: str
    text: str
    message_type: Literal["text", "template", "image"] = "text"
    metadata: Dict[str, Any] = Field(default_factory=dict)

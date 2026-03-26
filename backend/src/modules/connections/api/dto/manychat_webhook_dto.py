"""DTOs for ManyChat webhook event ingestion."""
from typing import Optional, Dict

from pydantic import BaseModel


class ManyChatWebhookPayload(BaseModel):
    """Payload que ManyChat envia via External Request.

    Se configura en cada flow de ManyChat para enviar estos campos.
    """

    event_type: str
    subscriber_id: str
    channel: str = "instagram"

    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    ig_username: Optional[str] = None

    tag_name: Optional[str] = None
    flow_ns: Optional[str] = None
    flow_name: Optional[str] = None
    custom_field_name: Optional[str] = None
    custom_field_value: Optional[str] = None

    custom_fields: Optional[Dict[str, str]] = None
    webhook_secret: Optional[str] = None

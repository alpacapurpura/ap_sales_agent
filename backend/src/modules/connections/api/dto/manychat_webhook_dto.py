"""DTOs for ManyChat webhook event ingestion."""

from pydantic import BaseModel


class ManyChatWebhookPayload(BaseModel):
    """Payload que ManyChat envia via External Request.

    Se configura en cada flow de ManyChat para enviar estos campos.
    """

    event_type: str
    subscriber_id: str
    channel: str = "instagram"

    first_name: str | None = None
    last_name: str | None = None
    email: str | None = None
    phone: str | None = None
    ig_username: str | None = None

    tag_name: str | None = None
    flow_ns: str | None = None
    flow_name: str | None = None
    custom_field_name: str | None = None
    custom_field_value: str | None = None

    custom_fields: dict[str, str] | None = None
    webhook_secret: str | None = None

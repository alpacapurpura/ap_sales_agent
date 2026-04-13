import uuid
from typing import Annotated

import structlog
from fastapi import APIRouter, Body, Depends, Header, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.core.context import set_tenant_id
from src.core.database import get_db
from src.modules.connections.infrastructure.channels.webhook import WebhookAdapter
from src.modules.iam.domain.tenant import Tenant
from src.modules.sales_agent.application.orchestrator.chat import ChatOrchestrator
from src.shared.domain.messages import IncomingMessage

router = APIRouter()
logger = structlog.get_logger()
orchestrator = ChatOrchestrator()


def get_tenant_by_secret(
    x_webhook_secret: str = Header(..., alias="X-Webhook-Secret"),
    db: Session = Depends(get_db),
) -> Tenant:
    """
    Validates the Webhook Secret and sets the Tenant Context.
    """
    tenant = db.execute(select(Tenant).where(Tenant.webhook_secret == x_webhook_secret)).scalars().first()
    if not tenant:
        # Security: Generic error or specific? Specific is fine for API.
        raise HTTPException(status_code=401, detail="Invalid Webhook Secret")

    if not tenant.is_active:
        raise HTTPException(status_code=403, detail="Tenant is inactive")

    # Set Context
    set_tenant_id(tenant.id)
    structlog.contextvars.bind_contextvars(tenant_id=str(tenant.id))

    return tenant


@router.post("/chat")
async def webhook_chat(
    payload: Annotated[dict, Body()],
    tenant: Annotated[Tenant, Depends(get_tenant_by_secret)],
):
    """
    Generic Webhook Endpoint for AI Agent.

    Payload:
    {
        "user_id": "external_123",
        "message": "Hello",
        "metadata": { ... }
    }

    Returns:
    {
        "response": "Hello! How can I help?",
        "metadata": { ... }
    }
    """
    user_id = payload.get("user_id")
    message_text = payload.get("message")
    metadata = payload.get("metadata", {})

    if not user_id or not message_text:
        raise HTTPException(status_code=400, detail="Missing user_id or message")

    # Construct IncomingMessage
    # Channel type is 'api' to distinguish from other channels
    incoming = IncomingMessage(
        user_id=str(user_id),
        text=str(message_text),
        channel_type="api",
        metadata=metadata,
    )

    # Create Adapter
    adapter = WebhookAdapter()

    try:
        # Process Flow
        # We await this, which waits for the full flow (including typing simulation)
        # For API, we might want to disable typing simulation or reduce it?
        # But 'process_chat_flow' uses 'OutputManager' which has hardcoded delays.
        # Ideally, we should pass a flag to disable delays for API,
        # but for now we accept the "human-like" delay as a feature.
        await orchestrator.process_chat_flow(adapter, incoming)

        # Collect responses
        full_response = "\n\n".join(adapter.responses)

        return {
            "response": full_response,
            "metadata": {
                "agent_id": str(tenant.id),
                "timestamp": str(uuid.uuid4()),  # Just a dummy
            },
        }

    except Exception as e:
        logger.exception("webhook_chat_error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e)) from e

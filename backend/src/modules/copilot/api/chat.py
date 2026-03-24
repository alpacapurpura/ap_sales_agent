"""SSE streaming chat endpoint for the Copilot agent."""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.modules.copilot.api.dto import CopilotChatRequest
from src.modules.copilot.application.orchestrator.chat import CopilotOrchestrator
from src.modules.iam.api.dependencies import get_current_user, get_tenant_context
from src.modules.iam.domain.user import User

router = APIRouter()


@router.post("/chat")
async def copilot_chat(
    request: CopilotChatRequest,
    current_user: User = Depends(get_current_user),
    tenant_id: Optional[UUID] = Depends(get_tenant_context),
    db: Session = Depends(get_db),
):
    """
    Stream a copilot response via Server-Sent Events.

    The client should consume this as an SSE stream. Each event has:
    - event: text_chunk | tool_start | tool_result | status | done | error
    - data: JSON payload
    """
    if not tenant_id:
        raise HTTPException(status_code=401, detail="Tenant ID required")
    if not current_user.tenant_id:
        raise HTTPException(status_code=400, detail="User not associated with a tenant")

    orchestrator = CopilotOrchestrator(db)

    return StreamingResponse(
        orchestrator.stream_chat(
            user_id=current_user.id,
            tenant_id=tenant_id,
            message=request.message,
            conversation_id=request.conversation_id,
            context=request.context,
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )

"""SSE streaming chat endpoint for the Copilot agent."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from luana_core_copilot.api.dto import CopilotChatRequest
from luana_core_copilot.application.orchestrator.chat import CopilotOrchestrator
from luana_core_iam.api.dependencies import get_current_user, get_tenant_context
from luana_core_iam.domain.user import User
from luana_core_platform.core.context import set_user_id
from luana_core_platform.core.database import get_db
from luana_core_platform.core.rate_limit import check_rate_limit
from sqlalchemy.orm import Session

router = APIRouter()


@router.post("/chat")
async def copilot_chat(
    request: CopilotChatRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    tenant_id: Annotated[UUID | None, Depends(get_tenant_context)],
    db: Annotated[Session, Depends(get_db)],
) -> StreamingResponse:
    """Stream a copilot response via Server-Sent Events.

    The client should consume this as an SSE stream. Each frame has:
    - event: ``message_start`` | ``message_end`` |
             ``block_start`` | ``block_delta`` | ``block_end`` | ``block_append`` |
             ``tool_start`` | ``tool_result`` | ``ui_action`` |
             ``status`` | ``done`` | ``error``
    - data: JSON payload (shape depends on event — see ``SSEEvent`` DTO).
    """
    if not tenant_id:
        raise HTTPException(status_code=401, detail="Tenant ID required")
    if not current_user.tenant_id:
        raise HTTPException(status_code=400, detail="User not associated with a tenant")
    if not request.message.strip() and not request.blocks:
        raise HTTPException(status_code=422, detail="Message or attachments required")

    # Rate limit: 30 messages per minute per user
    check_rate_limit(user_id=str(current_user.id), scope="copilot-chat")

    set_user_id(current_user.id)

    orchestrator = CopilotOrchestrator(db)

    return StreamingResponse(
        orchestrator.stream_chat(
            user_id=current_user.id,
            tenant_id=tenant_id,
            message=request.message,
            conversation_id=request.conversation_id,
            context=request.context,
            blocks=request.blocks,
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )

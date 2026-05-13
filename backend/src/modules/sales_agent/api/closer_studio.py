"""Closer Studio API — conversation supervision and control for the business owner."""

from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from luana_core_iam.api.dependencies import get_current_user
from luana_core_iam.domain.user import User
from luana_core_platform.core.database import get_db
from luana_core_sales_agent.api.dto.closer_studio import (
    CloserKPIs,
    ConversationDetail,
    ConversationListResponse,
    DiagnoseResponse,
    FrozenConversation,
    NudgeRequest,
    NudgeResponse,
    ReactivateRequest,
    ReactivateResponse,
    ResumeRequest,
    ResumeResponse,
    SendMessageRequest,
    SendMessageResponse,
    StopRequest,
    StopResponse,
)
from luana_core_sales_agent.application.services.closer_studio_service import (
    CloserStudioService,
)
from sqlalchemy import select
from sqlalchemy.orm import Session

router = APIRouter()


# ── List ────────────────────────────────────────────────────────────────────


@router.get("/conversations")
def list_conversations(
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    temperature: Annotated[str | None, Query()] = None,
    handler_mode: Annotated[str | None, Query()] = None,
    channel: Annotated[str | None, Query()] = None,
    search: Annotated[str | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> ConversationListResponse:
    """List conversations."""
    svc = CloserStudioService(db)
    conversations, total = svc.list_conversations(
        tenant_id=user.tenant_id,
        temperature=temperature,
        handler_mode=handler_mode,
        channel=channel,
        search=search,
        limit=limit,
        offset=offset,
    )
    return ConversationListResponse(conversations=conversations, total=total)


# ── Detail ──────────────────────────────────────────────────────────────────


@router.get("/conversations/{lead_id}")
def get_conversation(
    lead_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    message_limit: Annotated[int, Query(ge=1, le=200)] = 50,
    before: Annotated[datetime | None, Query()] = None,
) -> ConversationDetail:
    """Retrieve conversation."""
    svc = CloserStudioService(db)
    detail = svc.get_conversation_detail(
        tenant_id=user.tenant_id,
        lead_id=lead_id,
        message_limit=message_limit,
        before=before,
    )
    if not detail:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return ConversationDetail(**detail)


# ── STOP ────────────────────────────────────────────────────────────────────


@router.post("/conversations/{lead_id}/stop")
async def stop_ai(
    lead_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    body: StopRequest = None,
) -> StopResponse:
    """Stop ai."""
    svc = CloserStudioService(db)
    result = svc.stop_ai(user.tenant_id, lead_id, user.id)
    if not result:
        raise HTTPException(status_code=404, detail="Conversation not found")
    db.commit()

    try:
        from luana_core_sales_agent.infrastructure.ws_manager import ws_manager

        await ws_manager.emit(
            str(user.tenant_id),
            {
                "type": "handler_changed",
                "lead_id": str(lead_id),
                "handler_mode": "human",
            },
        )
    except Exception:  # noqa: BLE001 — agent resilience
        pass

    return StopResponse(**result)


# ── RESUME ──────────────────────────────────────────────────────────────────


@router.post("/conversations/{lead_id}/resume")
async def resume_ai(
    lead_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    body: ResumeRequest = ResumeRequest(),
) -> ResumeResponse:
    """Resume ai."""
    svc = CloserStudioService(db)
    result = svc.resume_ai(user.tenant_id, lead_id, objective=body.objective)
    if not result:
        raise HTTPException(status_code=404, detail="Conversation not found")
    db.commit()

    try:
        from luana_core_sales_agent.infrastructure.ws_manager import ws_manager

        await ws_manager.emit(
            str(user.tenant_id),
            {"type": "handler_changed", "lead_id": str(lead_id), "handler_mode": "ai"},
        )
    except Exception:  # noqa: BLE001 — agent resilience
        pass

    return ResumeResponse(**result)


# ── Send Message ────────────────────────────────────────────────────────────


@router.post("/conversations/{lead_id}/messages")
async def send_message(
    lead_id: UUID,
    body: SendMessageRequest,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> SendMessageResponse:
    """Send message."""
    svc = CloserStudioService(db)
    result = svc.send_message(
        tenant_id=user.tenant_id,
        lead_id=lead_id,
        content=body.content,
        mode=body.mode,
    )
    if not result:
        raise HTTPException(status_code=404, detail="Conversation not found")

    if body.mode == "direct":
        from luana_core_platform.infrastructure.models.crm import LeadModel
        from luana_core_sales_agent.application.services.channel_resolver import (
            ChannelResolver,
        )

        lead = db.execute(select(LeadModel).where(LeadModel.id == lead_id)).scalars().first()
        if lead:
            resolver = ChannelResolver(db)
            sent = await resolver.send_to_lead(user.tenant_id, lead, body.content)
            result["sent_to_channel"] = sent

    db.commit()
    return SendMessageResponse(**result)


# ── Nudge ───────────────────────────────────────────────────────────────────


@router.post("/conversations/{lead_id}/nudge")
def nudge(
    lead_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    body: NudgeRequest = NudgeRequest(),
) -> NudgeResponse:
    """Nudge."""
    # For now, nudge stores as instruction for AI to generate proactive message
    svc = CloserStudioService(db)
    nudge_instruction = body.context or "Send a proactive follow-up message to re-engage this lead."
    result = svc.send_message(
        tenant_id=user.tenant_id,
        lead_id=lead_id,
        content=nudge_instruction,
        mode="instruction",
    )
    if not result:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Resume AI so it processes the instruction
    svc.resume_ai(user.tenant_id, lead_id, objective=nudge_instruction)
    db.commit()

    return NudgeResponse(
        message_id=result["message_id"],
        content=nudge_instruction,
        sent_to_channel=False,
    )


# ── Reactivate Frozen ──────────────────────────────────────────────────────


@router.post("/conversations/{lead_id}/reactivate")
def reactivate(
    lead_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    body: ReactivateRequest = ReactivateRequest(),
) -> ReactivateResponse:
    """Reactivate."""
    svc = CloserStudioService(db)
    result = svc.reactivate(user.tenant_id, lead_id, objective=body.objective)
    if not result:
        raise HTTPException(status_code=404, detail="Conversation not found")
    db.commit()
    return ReactivateResponse(**result)


# ── Diagnose ────────────────────────────────────────────────────────────────


@router.post("/conversations/{lead_id}/diagnose")
async def diagnose(
    lead_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> DiagnoseResponse:
    """Diagnose."""
    svc = CloserStudioService(db)
    result = await svc.diagnose(user.tenant_id, lead_id)
    if not result:
        raise HTTPException(status_code=404, detail="Conversation not found")
    db.commit()
    return DiagnoseResponse(**result)


# ── Frozen ──────────────────────────────────────────────────────────────────


@router.get("/frozen")
def list_frozen(
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> list[FrozenConversation]:
    """List frozen."""
    svc = CloserStudioService(db)
    return [FrozenConversation(**f) for f in svc.list_frozen(user.tenant_id)]


# ── KPIs ────────────────────────────────────────────────────────────────────


@router.get("/kpis")
def get_kpis(
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> CloserKPIs:
    """Retrieve kpis."""
    svc = CloserStudioService(db)
    return CloserKPIs(**svc.get_kpis(user.tenant_id))

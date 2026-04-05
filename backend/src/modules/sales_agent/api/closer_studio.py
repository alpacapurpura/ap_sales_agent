"""Closer Studio API — conversation supervision and control for the business owner."""

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.modules.iam.api.dependencies import get_current_user
from src.modules.iam.domain.user import User
from src.modules.sales_agent.api.dto.closer_studio import (
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
from src.modules.sales_agent.application.services.closer_studio_service import (
    CloserStudioService,
)

router = APIRouter()


# ── List ────────────────────────────────────────────────────────────────────


@router.get("/conversations", response_model=ConversationListResponse)
def list_conversations(
    temperature: str | None = Query(None),
    handler_mode: str | None = Query(None),
    channel: str | None = Query(None),
    search: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
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


@router.get("/conversations/{lead_id}", response_model=ConversationDetail)
def get_conversation(
    lead_id: UUID,
    message_limit: int = Query(50, ge=1, le=200),
    before: datetime | None = Query(None),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
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


@router.post("/conversations/{lead_id}/stop", response_model=StopResponse)
def stop_ai(
    lead_id: UUID,
    body: StopRequest = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    svc = CloserStudioService(db)
    result = svc.stop_ai(user.tenant_id, lead_id, user.id)
    if not result:
        raise HTTPException(status_code=404, detail="Conversation not found")
    db.commit()
    return StopResponse(**result)


# ── RESUME ──────────────────────────────────────────────────────────────────


@router.post("/conversations/{lead_id}/resume", response_model=ResumeResponse)
def resume_ai(
    lead_id: UUID,
    body: ResumeRequest = ResumeRequest(),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    svc = CloserStudioService(db)
    result = svc.resume_ai(user.tenant_id, lead_id, objective=body.objective)
    if not result:
        raise HTTPException(status_code=404, detail="Conversation not found")
    db.commit()
    return ResumeResponse(**result)


# ── Send Message ────────────────────────────────────────────────────────────


@router.post("/conversations/{lead_id}/messages", response_model=SendMessageResponse)
async def send_message(
    lead_id: UUID,
    body: SendMessageRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
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
        from src.modules.crm.infrastructure.models.lead_model import LeadModel
        from src.modules.sales_agent.application.services.channel_resolver import (
            ChannelResolver,
        )

        lead = db.query(LeadModel).filter(LeadModel.id == lead_id).first()
        if lead:
            resolver = ChannelResolver(db)
            sent = await resolver.send_to_lead(user.tenant_id, lead, body.content)
            result["sent_to_channel"] = sent

    db.commit()
    return SendMessageResponse(**result)


# ── Nudge ───────────────────────────────────────────────────────────────────


@router.post("/conversations/{lead_id}/nudge", response_model=NudgeResponse)
def nudge(
    lead_id: UUID,
    body: NudgeRequest = NudgeRequest(),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    # For now, nudge stores as instruction for AI to generate proactive message
    svc = CloserStudioService(db)
    nudge_instruction = (
        body.context or "Send a proactive follow-up message to re-engage this lead."
    )
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


@router.post("/conversations/{lead_id}/reactivate", response_model=ReactivateResponse)
def reactivate(
    lead_id: UUID,
    body: ReactivateRequest = ReactivateRequest(),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    svc = CloserStudioService(db)
    result = svc.reactivate(user.tenant_id, lead_id, objective=body.objective)
    if not result:
        raise HTTPException(status_code=404, detail="Conversation not found")
    db.commit()
    return ReactivateResponse(**result)


# ── Diagnose ────────────────────────────────────────────────────────────────


@router.post("/conversations/{lead_id}/diagnose", response_model=DiagnoseResponse)
async def diagnose(
    lead_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    svc = CloserStudioService(db)
    result = await svc.diagnose(user.tenant_id, lead_id)
    if not result:
        raise HTTPException(status_code=404, detail="Conversation not found")
    db.commit()
    return DiagnoseResponse(**result)


# ── Frozen ──────────────────────────────────────────────────────────────────


@router.get("/frozen", response_model=list[FrozenConversation])
def list_frozen(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    svc = CloserStudioService(db)
    return [FrozenConversation(**f) for f in svc.list_frozen(user.tenant_id)]


# ── KPIs ────────────────────────────────────────────────────────────────────


@router.get("/kpis", response_model=CloserKPIs)
def get_kpis(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    svc = CloserStudioService(db)
    return CloserKPIs(**svc.get_kpis(user.tenant_id))

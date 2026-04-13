"""Audit API endpoints."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.modules.crm.infrastructure.models.lead_model import LeadModel
from src.modules.iam.api.dependencies import get_current_user
from src.modules.iam.domain.user import User
from src.modules.sales_agent.api.dto.audit import (
    AuditLeadDetail,
    AuditLeadListItem,
    AuditLeadSummary,
    ClearHistoryResponse,
    LLMLogDetail,
    LLMLogSummary,
    TimelineEvent,
    TraceDetail,
)
from src.modules.sales_agent.infrastructure.memory.audit_repository import (
    AuditRepository,
)
from src.modules.sales_agent.infrastructure.models.message_model import MessageModel

router = APIRouter()


@router.get("/leads")
def list_audit_leads(
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> list[AuditLeadListItem]:
    """List recent active leads with their last activity timestamp."""
    repo = AuditRepository(db)

    try:
        rows = repo.get_recent_users(user.tenant_id, limit=30)
    except Exception:  # noqa: BLE001 — agent resilience
        # Fallback: if agent_traces table is empty or has issues,
        # return leads that have messages instead
        subq = (
            select(
                MessageModel.user_id,
                func.max(MessageModel.created_at).label("last_activity"),
            )
            .where(MessageModel.tenant_id == user.tenant_id)
            .group_by(MessageModel.user_id)
            .subquery()
        )
        rows = db.execute(
            select(LeadModel, subq.c.last_activity)
            .join(subq, LeadModel.id == subq.c.lead_id)
            .order_by(subq.c.last_activity.desc())
            .limit(30),
        ).all()

    result = []
    for lead, last_activity in rows:
        result.append(
            AuditLeadListItem(
                lead=AuditLeadSummary(
                    id=str(lead.id),
                    full_name=_lead_name(lead),
                    telegram_id=lead.telegram_id,
                    whatsapp_id=lead.whatsapp_id,
                    created_at=lead.created_at.isoformat() if lead.created_at else None,
                ),
                last_activity=last_activity.isoformat() if last_activity else None,
            ),
        )
    return result


@router.get("/leads/{lead_id}")
def get_lead_details(
    lead_id: str,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> AuditLeadDetail:
    """Get full lead profile details."""
    lead = (
        db.execute(
            select(LeadModel).where(
                LeadModel.id == UUID(lead_id),
                LeadModel.tenant_id == user.tenant_id,
            ),
        )
        .scalars()
        .first()
    )

    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    return AuditLeadDetail(
        id=str(lead.id),
        full_name=_lead_name(lead),
        telegram_id=lead.telegram_id,
        whatsapp_id=lead.whatsapp_id,
        instagram_id=lead.instagram_id,
        tiktok_id=lead.tiktok_id,
        profile_data=lead.profile_data or {},
        created_at=lead.created_at.isoformat() if lead.created_at else None,
        updated_at=lead.updated_at.isoformat() if lead.updated_at else None,
    )


@router.get("/leads/{lead_id}/timeline")
def get_lead_timeline(
    lead_id: str,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> list[TimelineEvent]:
    """Get combined message + trace timeline for a lead."""
    # Verify lead belongs to tenant
    lead = (
        db.execute(
            select(LeadModel).where(
                LeadModel.id == UUID(lead_id),
                LeadModel.tenant_id == user.tenant_id,
            ),
        )
        .scalars()
        .first()
    )
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    repo = AuditRepository(db)
    timeline = repo.get_full_timeline(lead_id, str(user.tenant_id))

    result = []
    for event in timeline:
        created_at_val = event.get("created_at")
        item = TimelineEvent(
            type=event["type"],
            id=event["id"],
            created_at=created_at_val.isoformat() if created_at_val else None,
            timestamp=created_at_val.timestamp() if created_at_val else 0,
        )
        if event["type"] == "message":
            item.role = event.get("role")
            item.content = event.get("content")
        elif event["type"] == "trace":
            item.node_name = event.get("node")
            item.execution_time_ms = event.get("execution_time")
            raw_summary = event.get("llm_summary")
            if raw_summary:
                item.llm_summary = LLMLogSummary(**raw_summary)
        result.append(item)

    return result


@router.delete("/leads/{lead_id}/history")
def clear_lead_history(
    lead_id: str,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> ClearHistoryResponse:
    """Clear all traces for a lead."""
    lead = (
        db.execute(
            select(LeadModel).where(
                LeadModel.id == UUID(lead_id),
                LeadModel.tenant_id == user.tenant_id,
            ),
        )
        .scalars()
        .first()
    )
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    repo = AuditRepository(db)
    repo.clear_user_history(lead_id, str(user.tenant_id))
    return ClearHistoryResponse(status="ok")


@router.get("/traces/{trace_id}")
def get_trace_details(
    trace_id: str,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> TraceDetail:
    """Get detailed trace with LLM logs."""
    repo = AuditRepository(db)
    details = repo.get_trace_details(trace_id, str(user.tenant_id))
    if not details:
        raise HTTPException(status_code=404, detail="Trace not found")

    trace = details["trace"]
    created_at_val = trace["created_at"]
    return TraceDetail(
        id=trace["id"],
        node_name=trace["node"],
        input_state=trace["input"],
        output_state=trace["output"],
        execution_time_ms=trace["execution_time"],
        created_at=created_at_val.isoformat() if hasattr(created_at_val, "isoformat") else created_at_val,
        llm_logs=[
            LLMLogDetail(
                id=log["id"],
                model=log["model"],
                prompt_template=log.get("prompt_template", "unknown"),
                prompt_rendered=log["prompt"],
                response_text=log["response"],
                tokens_input=log["tokens"]["in"],
                tokens_output=log["tokens"]["out"],
                metadata=log["metadata"],
            )
            for log in details["llm_logs"]
        ],
    )


def _lead_name(lead: LeadModel) -> str:
    """Extract a display name from lead profile_data or fallback."""
    if lead.profile_data and isinstance(lead.profile_data, dict):
        first = lead.profile_data.get("first_name", "")
        last = lead.profile_data.get("last_name", "")
        name = f"{first} {last}".strip()
        if name:
            return name
    return lead.telegram_id or lead.whatsapp_id or str(lead.id)[:8]

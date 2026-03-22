from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID

from src.core.database import get_db
from src.modules.iam.api.dependencies import get_current_user
from src.modules.iam.domain.user import User
from src.modules.sales_agent.infrastructure.memory.audit_repository import AuditRepository
from src.modules.crm.infrastructure.models.lead_model import LeadModel

router = APIRouter()


@router.get("/leads")
def list_audit_leads(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """List recent active leads with their last activity timestamp."""
    repo = AuditRepository(db)

    try:
        rows = repo.get_recent_users(user.tenant_id, limit=30)
    except Exception:
        # Fallback: if agent_traces table is empty or has issues,
        # return leads that have messages instead
        from src.modules.sales_agent.infrastructure.models.message_model import MessageModel
        from sqlalchemy import func

        subq = (
            db.query(
                MessageModel.user_id,
                func.max(MessageModel.created_at).label("last_activity"),
            )
            .filter(MessageModel.tenant_id == user.tenant_id)
            .group_by(MessageModel.user_id)
            .subquery()
        )
        rows = (
            db.query(LeadModel, subq.c.last_activity)
            .join(subq, LeadModel.id == subq.c.lead_id)
            .order_by(subq.c.last_activity.desc())
            .limit(30)
            .all()
        )

    result = []
    for lead, last_activity in rows:
        result.append({
            "lead": {
                "id": str(lead.id),
                "full_name": _lead_name(lead),
                "telegram_id": lead.telegram_id,
                "whatsapp_id": lead.whatsapp_id,
                "created_at": lead.created_at.isoformat() if lead.created_at else None,
            },
            "last_activity": last_activity.isoformat() if last_activity else None,
        })
    return result


@router.get("/leads/{lead_id}")
def get_lead_details(
    lead_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get full lead profile details."""
    lead = db.query(LeadModel).filter(
        LeadModel.id == UUID(lead_id),
        LeadModel.tenant_id == user.tenant_id,
    ).first()

    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    return {
        "id": str(lead.id),
        "full_name": _lead_name(lead),
        "email": None,
        "phone": None,
        "telegram_id": lead.telegram_id,
        "whatsapp_id": lead.whatsapp_id,
        "instagram_id": lead.instagram_id,
        "tiktok_id": lead.tiktok_id,
        "profile_data": lead.profile_data or {},
        "created_at": lead.created_at.isoformat() if lead.created_at else None,
        "updated_at": lead.updated_at.isoformat() if lead.updated_at else None,
    }


@router.get("/leads/{lead_id}/timeline")
def get_lead_timeline(
    lead_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get combined message + trace timeline for a lead."""
    # Verify lead belongs to tenant
    lead = db.query(LeadModel).filter(
        LeadModel.id == UUID(lead_id),
        LeadModel.tenant_id == user.tenant_id,
    ).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    repo = AuditRepository(db)
    timeline = repo.get_full_timeline(lead_id, str(user.tenant_id))

    # Map to frontend expected format
    result = []
    for event in timeline:
        item = {
            "type": event["type"],
            "id": event["id"],
            "created_at": event["created_at"].isoformat() if event.get("created_at") else None,
            "timestamp": event["created_at"].timestamp() if event.get("created_at") else 0,
        }
        if event["type"] == "message":
            item["role"] = event.get("role")
            item["content"] = event.get("content")
        elif event["type"] == "trace":
            item["node_name"] = event.get("node")
            item["execution_time_ms"] = event.get("execution_time")
            item["llm_summary"] = event.get("llm_summary")
        result.append(item)

    return result


@router.delete("/leads/{lead_id}/history")
def clear_lead_history(
    lead_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Clear all traces for a lead."""
    lead = db.query(LeadModel).filter(
        LeadModel.id == UUID(lead_id),
        LeadModel.tenant_id == user.tenant_id,
    ).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    repo = AuditRepository(db)
    repo.clear_user_history(lead_id, str(user.tenant_id))
    return {"status": "ok"}


@router.get("/traces/{trace_id}")
def get_trace_details(
    trace_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get detailed trace with LLM logs."""
    repo = AuditRepository(db)
    details = repo.get_trace_details(trace_id, str(user.tenant_id))
    if not details:
        raise HTTPException(status_code=404, detail="Trace not found")

    # Flatten to match frontend TraceDetail contract
    trace = details["trace"]
    return {
        "id": trace["id"],
        "node_name": trace["node"],
        "input_state": trace["input"],
        "output_state": trace["output"],
        "execution_time_ms": trace["execution_time"],
        "created_at": trace["created_at"].isoformat() if hasattr(trace["created_at"], "isoformat") else trace["created_at"],
        "llm_logs": [
            {
                "id": log["id"],
                "model": log["model"],
                "prompt_template": log.get("prompt_template", "unknown"),
                "prompt_rendered": log["prompt"],
                "response_text": log["response"],
                "tokens_input": log["tokens"]["in"],
                "tokens_output": log["tokens"]["out"],
                "metadata": log["metadata"],
            }
            for log in details["llm_logs"]
        ],
    }


def _lead_name(lead: LeadModel) -> str:
    """Extract a display name from lead profile_data or fallback."""
    if lead.profile_data and isinstance(lead.profile_data, dict):
        first = lead.profile_data.get("first_name", "")
        last = lead.profile_data.get("last_name", "")
        name = f"{first} {last}".strip()
        if name:
            return name
    return lead.telegram_id or lead.whatsapp_id or str(lead.id)[:8]

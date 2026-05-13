"""Cron worker: appointment reminder + postcheck cadence (S8).

Runs every 15 minutes. Three reminder kinds, one worker (cohesion —
they share the iteration over ``scheduled_meetings`` + the brand-voice
LLM call + the channel send path):

* **T-24h** — confirms attendance the day before. Idempotent via
  ``reminder_24h_sent_at`` stamp.
* **T-1h**  — last-mile heads-up. Idempotent via ``reminder_1h_sent_at``.
* **T+1h postcheck** — opens follow-up after the meeting (or asks to
  reschedule if the lead missed). Idempotent via ``postcheck_sent_at``.

Brand voice is **inherited automatically** because the system prompt
already injects ``personality_profile.system_instruction`` in slot 5
(S7). The Jinja template here only generates the **user instruction**
piece — the LLM speaks the tenant's voice without per-tenant template
forks.

Coupling discipline:

* Reads/writes JSONB only via ``MeetingStateService``.
* Sends only via ``ChannelResolver`` (re-used from ``follow_up_engine``).
* LLM via ``LLMFactory`` + ``LLM_ROLE_BY_SITE['appointment_reminder_*']``.
* No direct ``BookingLink`` / ``Appointment`` writes — those belong to
  the verify cron + scheduler endpoints.
"""

# [SALES-AGENT-S8-CRON]  # noqa: ERA001

from __future__ import annotations

import contextlib
import datetime as dt
from typing import TYPE_CHECKING
from zoneinfo import ZoneInfo

import structlog
from luana_core_llm.factory import LLMFactory
from luana_core_sales_agent.application.services.channel_resolver import (
    ChannelResolver,
)
from luana_core_sales_agent.application.services.meeting_state_service import (
    MeetingEntry,
    MeetingEntryStatus,
    MeetingStateService,
)
from luana_core_sales_agent.domain.model_tier import LLM_ROLE_BY_SITE
from luana_core_sales_agent.infrastructure.memory.audit_repository import (
    AuditRepository,
)
from luana_core_sales_agent.infrastructure.models.agent_state_checkpoint_model import (
    AgentStateCheckpointModel,
)
from luana_core_sales_agent.infrastructure.prompts.base import prompt_loader
from sqlalchemy import select

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

logger = structlog.get_logger()


# Window each reminder fires within. ±15 min mirrors the cron cadence.
_REMINDER_WINDOW = dt.timedelta(minutes=15)
# Postcheck fires from T+30min..T+3h to give the meeting time to wrap.
_POSTCHECK_MIN_OFFSET = dt.timedelta(minutes=30)
_POSTCHECK_MAX_OFFSET = dt.timedelta(hours=3)


async def run_appointment_reminders(ctx: dict) -> None:
    """Send T-24h / T-1h / T+1h messages for upcoming meetings."""
    db_factory = ctx["db_factory"]
    db = db_factory()

    sent_24h = sent_1h = sent_postcheck = 0

    try:
        now = dt.datetime.now(dt.UTC)

        stmt = select(AgentStateCheckpointModel).where(
            AgentStateCheckpointModel.is_active.is_(True),
            AgentStateCheckpointModel.deleted_at.is_(None),
            AgentStateCheckpointModel.frozen_at.is_(None),
            AgentStateCheckpointModel.handler_mode == "ai",
            AgentStateCheckpointModel.scheduled_meetings.isnot(None),
        )
        checkpoints = db.execute(stmt).scalars().all()

        for cp in checkpoints:
            try:
                stats = await _process_checkpoint(db, cp, now)
                sent_24h += stats[0]
                sent_1h += stats[1]
                sent_postcheck += stats[2]
            except Exception as exc:
                logger.exception(
                    "appointment_reminder_checkpoint_failed",
                    lead_id=str(cp.lead_id),
                    error=str(exc),
                )
                continue

        db.commit()
        logger.info(
            "appointment_reminders_complete",
            t24h=sent_24h,
            t1h=sent_1h,
            postcheck=sent_postcheck,
        )
    except Exception as exc:
        logger.exception("appointment_reminders_failed", error=str(exc))
        with contextlib.suppress(Exception):
            db.rollback()
    finally:
        db.close()


async def _process_checkpoint(
    db: Session,
    cp: AgentStateCheckpointModel,
    now: dt.datetime,
) -> tuple[int, int, int]:
    """Return (sent_24h, sent_1h, sent_postcheck) deltas for a checkpoint."""
    state_service = MeetingStateService(db)
    entries = state_service.list_for_lead(cp.tenant_id, cp.lead_id)
    if not entries:
        return 0, 0, 0

    sent_24h = sent_1h = sent_postcheck = 0
    for entry in entries:
        if entry.scheduled_at is None:
            continue
        # T-24h
        if (
            not entry.reminder_24h_sent_at
            and _within(entry.scheduled_at - dt.timedelta(hours=24), now)
            and await _fire(db, cp, entry, "24h", state_service)
        ):
            sent_24h += 1
        # T-1h
        if (
            not entry.reminder_1h_sent_at
            and _within(entry.scheduled_at - dt.timedelta(hours=1), now)
            and await _fire(db, cp, entry, "1h", state_service)
        ):
            sent_1h += 1
        # T+postcheck (only after meeting has had a chance to wrap)
        if not entry.postcheck_sent_at:
            offset = now - entry.scheduled_at
            if _POSTCHECK_MIN_OFFSET <= offset <= _POSTCHECK_MAX_OFFSET and await _fire(
                db,
                cp,
                entry,
                "postcheck",
                state_service,
            ):
                sent_postcheck += 1

    return sent_24h, sent_1h, sent_postcheck


def _within(target: dt.datetime, now: dt.datetime) -> bool:
    """True if ``now`` is within ±_REMINDER_WINDOW of ``target``."""
    return abs((now - target).total_seconds()) <= _REMINDER_WINDOW.total_seconds()


async def _fire(
    db: Session,
    cp: AgentStateCheckpointModel,
    entry: MeetingEntry,
    kind: str,
    state_service: MeetingStateService,
) -> bool:
    """Render brand-voiced message + send + stamp.

    Returns True if a message went out. Failure paths log + return False
    so the cron continues with other entries.
    """
    text = _render_reminder(cp, entry, kind)
    if not text:
        logger.warning(
            "appointment_reminder_empty",
            lead_id=str(cp.lead_id),
            tracking_id=entry.tracking_id,
            kind=kind,
        )
        return False

    sent = await _send_and_log(db, cp, entry, text, kind)
    if not sent:
        return False

    state_service.mark_reminder_sent(
        cp.tenant_id,
        cp.lead_id,
        entry.tracking_id,
        reminder_kind=kind,
    )
    return True


def _render_reminder(
    cp: AgentStateCheckpointModel,
    entry: MeetingEntry,
    kind: str,
) -> str:
    """Build the LLM user prompt + invoke. Brand voice from system slot 5."""
    template_name = {
        "24h": "appointment_reminder_t24h",
        "1h": "appointment_reminder_t1h",
        "postcheck": "appointment_postcheck",
    }[kind]

    lead_data = cp.lead_data or {}
    lead_name = lead_data.get("lead_name") or lead_data.get("name") or ""
    offer_name = lead_data.get("active_product_name") or ""
    scheduled_at_local = _format_local(entry.scheduled_at, lead_data.get("tenant_timezone", "UTC"))
    meeting_link = lead_data.get("meeting_link") or ""

    prompt = prompt_loader.render(
        template_name,
        lead_name=lead_name,
        scheduled_at_local=scheduled_at_local,
        offer_name=offer_name,
        event_title=entry.event_slug.replace("-", " "),
        channel_type=cp.channel_type,
        meeting_link=meeting_link,
        was_attended=(entry.status == MeetingEntryStatus.COMPLETED),
    )

    role = LLM_ROLE_BY_SITE[f"appointment_reminder_{kind}" if kind != "postcheck" else "appointment_postcheck"]

    return (
        LLMFactory.get_service()
        .generate_response(
            messages=[],
            system_prompt=prompt,
            model_type=role,
            temperature=0.5,
            max_output_tokens=160,
            metadata={
                "prompt_template": template_name,
                "tenant_id": str(cp.tenant_id),
                "prompt_cache_key": str(cp.tenant_id),
            },
        )
        .strip()
    )


def _format_local(value: dt.datetime, tz_name: str) -> str:
    """Render ``value`` in tenant TZ as ``DD/MM/YYYY HH:MM``."""
    try:
        tz = ZoneInfo(tz_name)
    except (KeyError, ValueError):
        tz = ZoneInfo("UTC")
    aware = value if value.tzinfo else value.replace(tzinfo=dt.UTC)
    return aware.astimezone(tz).strftime("%d/%m/%Y %H:%M")


async def _send_and_log(
    db: Session,
    cp: AgentStateCheckpointModel,
    entry: MeetingEntry,
    text: str,
    kind: str,
) -> bool:
    """Send via ChannelResolver + persist audit row. Best-effort."""
    from luana_core_platform.links.ports.crm_repos import get_lead_metrics_repository

    lead_repo = get_lead_metrics_repository(db)
    lead = lead_repo.get_active_lead_by_id(cp.lead_id)
    if lead is None:
        return False

    resolver = ChannelResolver(db)
    sent = await resolver.send_to_lead(
        tenant_id=cp.tenant_id,
        lead=lead,
        text=text,
        preferred_channel=cp.channel_type,
    )
    if not sent:
        logger.warning(
            "appointment_reminder_channel_unavailable",
            lead_id=str(cp.lead_id),
            kind=kind,
            channel=cp.channel_type,
        )
        return False

    AuditRepository(db).log_message(
        user_id=cp.lead_id,
        role="assistant",
        content=text,
        channel=cp.channel_type,
        tenant_id=cp.tenant_id,
        metadata={
            "source": "appointment_reminder",
            "reminder_kind": kind,
            "tracking_id": entry.tracking_id,
        },
    )
    return True


__all__ = ["run_appointment_reminders"]

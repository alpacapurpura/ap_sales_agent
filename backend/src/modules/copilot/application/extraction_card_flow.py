"""Extraction card flow — event subscribers + card emitters in one place.

Unified handler for extraction domain events published by brand/offer workers
(and by ``extract_from_doc`` running inline). Subscribes at app/worker startup
and renders:

- ``navigation`` pills per completed section.
- A final ``extraction_summary`` card per completed job.

Idempotency: each emission is guarded by a Redis SET key
``extract_card:{job_id}:{kind}:{slug}`` (TTL 24h) so worker retries are safe.

Previously split across:
  - ``application/subscribers/extraction_events.py`` (thin subscriber wrapper)
  - ``application/emitters/extraction_card_emitter.py`` (card building)

Merged here because the two files were coupled 1:1 and the indirection added
no value. Reintroduce a ``subscribers/``/``emitters/`` split when a second
card-emission feature lands with a different emitter life-cycle.
"""

from __future__ import annotations

from uuid import UUID, uuid4

import structlog

from src.modules.copilot.infrastructure.repositories.conversation_repository import (
    ConversationRepository,
)
from src.shared.domain.events import DomainEvent, EventBus

logger = structlog.get_logger(__name__)


# ── Card emitters ─────────────────────────────────────────────────────────────


def emit_section_complete_pill(
    *,
    db: object,
    tenant_id: UUID,
    conversation_id: UUID,
    job_id: str,
    section_slug: str,
    section_label: str,
    fields_count: int,
    module: str,
    trace_recorder: object | None = None,
) -> None:
    """Insert a navigation pill for a completed section.

    Idempotent: duplicate calls with same job_id + section_slug are no-ops.
    Pill label: ``✓ {section_label} lista · {fields_count} campos``.
    Route: ``/{module}-studio/{section_slug}``.
    """
    from src.core.database import redis_client

    idempotency_key = f"extract_card:{job_id}:nav:{section_slug}"
    if redis_client:
        if redis_client.get(idempotency_key):
            logger.debug(
                "nav_pill_duplicate_skipped",
                job_id=job_id,
                section_slug=section_slug,
            )
            return
        redis_client.setex(idempotency_key, 86400, "1")

    page_label = f"✓ {section_label} lista · {fields_count} campos"
    module_slug = f"{module}-studio" if not module.endswith("-studio") else module
    # Leave the ``{tenantId}`` placeholder literal — the FE navigator substitutes
    # it at click-time from the current route. Hardcoding the tenant UUID here
    # would bake stale state into persisted cards if the user ever switches
    # tenants; shipping a path without the tenant segment sends the user to a
    # not-found page because every studio route requires ``[tenantId]``.
    route = f"/{{tenantId}}/{module_slug}/{section_slug}"

    # ``type`` must match the UIAction enum the frontend navigator switch-cases
    # on (see frontend/.../use-copilot-navigator.ts). Emitting "navigation_card"
    # here silently no-ops the click. Stay on "navigate".
    nav_payload = {
        "type": "navigate",
        "route": route,
        "page_label": page_label,
        "section_id": section_slug,
    }

    message = _build_card_message(card_kind="navigation", payload=nav_payload)

    try:
        conv_repo = ConversationRepository(db)
        conv_repo.append_messages(conversation_id, tenant_id, [message])
        logger.info(
            "extraction_nav_pill_emitted",
            job_id=job_id,
            section_slug=section_slug,
            conversation_id=str(conversation_id),
        )
        # Record observability trace so card_emitted rows appear in
        # copilot_trace_event (previously 0 rows for navigation cards).
        if trace_recorder is not None:
            trace_recorder.record(
                event_type="card_emitted",
                name="navigation",
                data={
                    "card_kind": "navigation",
                    "source_tool": "extract_from_url",
                    "job_id": job_id,
                    "conversation_id": str(conversation_id),
                    "section_slug": section_slug,
                    "fields_count": fields_count,
                },
            )
    except Exception:  # noqa: BLE001 — card emission must not fail the job
        logger.warning(
            "nav_pill_emit_failed",
            exc_info=True,
            job_id=job_id,
            section_slug=section_slug,
        )


def emit_extraction_summary_card(
    *,
    db: object,
    tenant_id: UUID,
    conversation_id: UUID,
    job_id: str,
    source_ref: str,
    duration_seconds: int,
    filled_fields: list[str],
    filled_fields_by_section: dict[str, list[str]],
    sections_completed: list[str],
    primary_cta_route: str | None = None,
    trace_recorder: object | None = None,
) -> None:
    """Insert an extraction_summary card into the conversation.

    Idempotent: duplicate calls with same job_id are no-ops. The frontend
    resolves section labels from its canonical catalog, so ``coverage_by_section``
    emits slug names and the UI translates.
    """
    from src.core.database import redis_client

    idempotency_key = f"extract_card:{job_id}:summary"
    if redis_client:
        if redis_client.get(idempotency_key):
            logger.debug("summary_card_duplicate_skipped", job_id=job_id)
            return
        redis_client.setex(idempotency_key, 86400, "1")

    coverage_by_section = [
        {
            "slug": slug,
            "label": slug,  # frontend resolves Spanish label from catalog
            "filled": len(filled_fields_by_section.get(slug, [])),
            "total": len(filled_fields_by_section.get(slug, [])),
        }
        for slug in sections_completed
    ]

    module_from_cta: str | None = None
    if primary_cta_route:
        if "/brand-studio" in primary_cta_route:
            module_from_cta = "brand"
        elif "/offer-studio" in primary_cta_route:
            module_from_cta = "offer"

    # ``{tenantId}`` placeholder (same convention as nav pills) — FE navigator
    # replaces at click-time. Never bake a concrete tenant UUID here.
    default_cta = f"/{{tenantId}}/brand-studio/{sections_completed[0]}" if sections_completed else None
    summary_payload = {
        "type": "extraction_summary",
        "source_ref": source_ref,
        "module": module_from_cta,
        "duration_seconds": duration_seconds,
        "total_fields": len(filled_fields),
        "total_sections": len(sections_completed),
        "coverage_by_section": coverage_by_section,
        "strong_assumptions_count": 0,
        "open_questions_count": 0,
        "primary_cta_route": primary_cta_route or default_cta,
    }

    message = _build_card_message(
        card_kind="extraction_summary",
        payload=summary_payload,
    )

    try:
        conv_repo = ConversationRepository(db)
        conv_repo.append_messages(conversation_id, tenant_id, [message])
        logger.info(
            "extraction_summary_card_emitted",
            job_id=job_id,
            total_fields=len(filled_fields),
            total_sections=len(sections_completed),
            conversation_id=str(conversation_id),
        )
        # Record observability trace so card_emitted rows appear in
        # copilot_trace_event (previously 0 rows for extraction_summary cards).
        if trace_recorder is not None:
            trace_recorder.record(
                event_type="card_emitted",
                name="extraction_summary",
                data={
                    "card_kind": "extraction_summary",
                    "source_tool": "extract_from_url",
                    "job_id": job_id,
                    "conversation_id": str(conversation_id),
                    "total_fields": len(filled_fields),
                    "total_sections": len(sections_completed),
                },
            )
    except Exception:  # noqa: BLE001 — card emission must not fail the job
        logger.warning("summary_card_emit_failed", exc_info=True, job_id=job_id)


def _build_card_message(*, card_kind: str, payload: dict) -> dict:
    """Build a persisted assistant message dict containing a CardBlock (v2 shape)."""
    from src.shared.domain.datetime_utils import utc_now

    block_id = str(uuid4())
    message_id = str(uuid4())
    now = utc_now().isoformat()

    return {
        "id": message_id,
        "role": "assistant",
        "content": "",
        "blocks": [
            {
                "type": "card",
                "id": block_id,
                "card_kind": card_kind,
                "payload": payload,
            }
        ],
        "status": "sent",
        "created_at": now,
    }


# ── Event subscribers ─────────────────────────────────────────────────────────


def handle_section_completed(event: DomainEvent) -> None:
    """Handle extraction_section_completed: insert navigation pill."""
    conversation_id_raw: str | None = event.payload.get("conversation_id")
    if not conversation_id_raw:
        return

    try:
        from src.core.database import SessionLocal
        from src.modules.copilot.application.observability import trace_recorder as tr_mod

        # Build a recorder scoped to this event (no active turn — uses None turn_id).
        # The subscriber runs outside any /copilot/chat turn so we create an
        # independent recorder to capture the card_emitted event.
        recorder = tr_mod.start(
            tenant_id=UUID(str(event.tenant_id)),
            conversation_id=UUID(conversation_id_raw),
        )

        db = SessionLocal()
        try:
            emit_section_complete_pill(
                db=db,
                tenant_id=UUID(str(event.tenant_id)),
                conversation_id=UUID(conversation_id_raw),
                job_id=str(event.payload.get("job_id", "")),
                section_slug=str(event.payload.get("section_slug", "")),
                section_label=str(event.payload.get("section_label", "")),
                fields_count=int(event.payload.get("fields_count", 0)),
                module=str(event.payload.get("module", "brand")),
                trace_recorder=recorder,
            )
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()
    except Exception:
        logger.exception(
            "extraction_section_handler_failed",
            tenant_id=str(event.tenant_id),
            job_id=event.payload.get("job_id"),
            section_slug=event.payload.get("section_slug"),
        )


def handle_job_completed(event: DomainEvent) -> None:
    """Handle extraction_job_completed: insert extraction_summary card + clear active job state."""
    conversation_id_raw: str | None = event.payload.get("conversation_id")
    if not conversation_id_raw:
        return

    try:
        from src.core.database import SessionLocal
        from src.modules.copilot.application.extraction.active_job_persistence import (
            write_active_job,
        )
        from src.modules.copilot.application.observability import trace_recorder as tr_mod

        recorder = tr_mod.start(
            tenant_id=UUID(str(event.tenant_id)),
            conversation_id=UUID(conversation_id_raw),
        )

        db = SessionLocal()
        try:
            emit_extraction_summary_card(
                db=db,
                tenant_id=UUID(str(event.tenant_id)),
                conversation_id=UUID(conversation_id_raw),
                job_id=str(event.payload.get("job_id", "")),
                source_ref=str(event.payload.get("source_ref", "")),
                duration_seconds=int(event.payload.get("duration_seconds", 0)),
                filled_fields=list(event.payload.get("filled_fields", [])),
                filled_fields_by_section=dict(event.payload.get("filled_fields_by_section", {})),
                sections_completed=list(event.payload.get("sections_completed", [])),
                primary_cta_route=event.payload.get("primary_cta_route"),
                trace_recorder=recorder,
            )
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

        # Clear the active_extraction_job flag so guided resumes question flow
        # on the paused block. Done after card emission so a failure here does
        # not block the UX feedback.
        try:
            write_active_job(conversation_id_raw, None)
        except Exception:  # noqa: BLE001 — best-effort cleanup
            logger.warning(
                "active_extraction_job_clear_failed",
                conversation_id=conversation_id_raw,
                job_id=event.payload.get("job_id"),
            )
    except Exception:
        logger.exception(
            "extraction_job_handler_failed",
            tenant_id=str(event.tenant_id),
            job_id=event.payload.get("job_id"),
            module=event.payload.get("module"),
        )


def register_extraction_event_handlers() -> None:
    """Register subscribers. Idempotent — safe from multiple startup paths."""
    already_section = handle_section_completed in EventBus._handlers.get(
        "extraction_section_completed",
        [],
    )
    already_job = handle_job_completed in EventBus._handlers.get(
        "extraction_job_completed",
        [],
    )

    if not already_section:
        EventBus.subscribe("extraction_section_completed", handle_section_completed)
    if not already_job:
        EventBus.subscribe("extraction_job_completed", handle_job_completed)

    if not already_section or not already_job:
        logger.info(
            "copilot_extraction_event_handlers_registered",
            events=["extraction_section_completed", "extraction_job_completed"],
        )


__all__ = [
    "emit_extraction_summary_card",
    "emit_section_complete_pill",
    "handle_job_completed",
    "handle_section_completed",
    "register_extraction_event_handlers",
]

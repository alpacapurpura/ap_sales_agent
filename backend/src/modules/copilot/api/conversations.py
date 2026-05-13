"""CRUD endpoints for copilot conversations (CONTRACT §4.2)."""

from __future__ import annotations

import uuid
from typing import Annotated
from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query
from luana_core_copilot.api.conversation_dto import (
    ActiveJobProgressDTO,
    ActiveJobsResponse,
    AppliedMutationDTO,
    ApplyMutationsRequest,
    ApplyMutationsResponse,
    ConversationDetail,
    ConversationListResponse,
    ConversationMessageDTO,
    ConversationSummary,
    MutationJournalEntryDTO,
    MutationJournalListResponse,
    PatchConversationRequest,
    RejectedMutationDTO,
    RevertFailure,
    RevertRequest,
    RevertResponse,
)
from luana_core_copilot.application.extraction.active_job_persistence import (
    read_active_job,
)
from luana_core_copilot.application.services.mutation_apply_service import (
    MutationApplyService,
)
from luana_core_copilot.infrastructure.repositories.conversation_repository import (
    ConversationRepository,
)
from luana_core_copilot.infrastructure.repositories.message_codec import decode_message
from luana_core_copilot.infrastructure.repositories.mutation_journal_repository import (
    MutationJournalRepository,
)
from luana_core_iam.api.dependencies import get_current_user, get_tenant_context
from luana_core_iam.domain.user import User
from luana_core_platform.core.database import get_db

# Runtime imports (needed by FastAPI's dependency resolver for Annotated[..., Depends(...)] —
# cannot be moved to TYPE_CHECKING or FastAPI treats the param as a query arg).
from sqlalchemy.orm import Session

logger = structlog.get_logger()

router = APIRouter()


def _require_tenant(
    current_user: Annotated[User, Depends(get_current_user)],
    tenant_id: Annotated[UUID | None, Depends(get_tenant_context)],
) -> UUID:
    """Validate that the caller has a tenant context and return the tenant_id."""
    if not tenant_id or not current_user.tenant_id:
        raise HTTPException(status_code=401, detail="Tenant ID requerido")
    return tenant_id


def _build_summary(conv: object) -> ConversationSummary:
    """Map a CopilotConversationModel to a ConversationSummary DTO."""
    procedure_state = getattr(conv, "procedure_state", None)
    has_procedure = procedure_state is not None
    procedure_progress: float | None = None
    if has_procedure and isinstance(procedure_state, dict):
        procedure_progress = float(procedure_state.get("coverage", 0.0))

    return ConversationSummary(
        id=conv.id,
        title=getattr(conv, "title", None),
        title_auto_generated=getattr(conv, "title_auto_generated", False),
        updated_at=conv.updated_at,
        message_count=getattr(conv, "message_count", 0),
        total_tokens=getattr(conv, "total_tokens", 0),
        last_tier_used=getattr(conv, "last_tier_used", None),
        has_procedure=has_procedure,
        procedure_progress=procedure_progress,
        archived_at=getattr(conv, "archived_at", None),
    )


@router.get(
    "/conversations",
    response_model=ConversationListResponse,
    summary="Listar conversaciones del usuario",
)
async def list_conversations(
    current_user: Annotated[User, Depends(get_current_user)],
    tenant_id: Annotated[UUID | None, Depends(get_tenant_context)],
    db: Annotated[Session, Depends(get_db)],
    limit: Annotated[int, Query(ge=1, le=50)] = 6,
    cursor: str | None = None,
    include_archived: bool = False,
) -> ConversationListResponse:
    """Return a cursor-paginated list of conversations for the authenticated user."""
    if not tenant_id or not current_user.tenant_id:
        raise HTTPException(status_code=401, detail="Tenant ID requerido")

    repo = ConversationRepository(db)
    page = repo.list_paginated(
        tenant_id=tenant_id,
        user_id=current_user.id,
        limit=limit,
        cursor=cursor,
        include_archived=include_archived,
    )
    items = [_build_summary(c) for c in page["items"]]
    return ConversationListResponse(items=items, next_cursor=page["next_cursor"])


@router.get(
    "/conversations/{conversation_id}",
    response_model=ConversationDetail,
    summary="Obtener conversación con mensajes decoded",
)
async def get_conversation(
    conversation_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    tenant_id: Annotated[UUID | None, Depends(get_tenant_context)],
    db: Annotated[Session, Depends(get_db)],
) -> ConversationDetail:
    """Return a conversation's summary + decoded message history.

    Used by the history panel to hydrate the chat when the user selects
    a past conversation. Ownership is enforced by passing user_id to the
    repository — a conversation belonging to another user in the same
    tenant returns 404 (not 403) to avoid leaking existence.
    """
    if not tenant_id or not current_user.tenant_id:
        raise HTTPException(status_code=401, detail="Tenant ID requerido")

    repo = ConversationRepository(db)
    conv = repo.get_by_id(conversation_id, tenant_id, current_user.id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversación no encontrada")

    raw_messages = list(conv.messages or [])
    decoded: list[ConversationMessageDTO] = []
    for raw in raw_messages:
        if not isinstance(raw, dict):
            continue
        msg = decode_message(raw, conversation_id=conversation_id)

        # Tool-role messages are part of the LLM transcript (for tool-use
        # replay) but have no UI affordance. Dropping them here avoids a
        # stray bubble in the rendered history.
        if msg.role not in ("user", "assistant"):
            continue

        blocks_out = [b.model_dump(mode="json", exclude_none=True) for b in msg.blocks] if msg.blocks else None
        # Defensive filter: skip placeholder assistant rows that never got
        # content and carry no renderable block. These are residues from
        # aborted/failed streams — rendering them would draw an empty "…"
        # bubble when the user re-opens the conversation.
        if not msg.content.strip() and not blocks_out:
            continue

        decoded.append(
            ConversationMessageDTO(
                id=msg.id,
                role=msg.role,
                content=msg.content,
                blocks=blocks_out,
                status=msg.status,
                created_at=msg.created_at,
                tokens_used=msg.tokens_used,
                metadata=msg.metadata,
            ),
        )

    summary = _build_summary(conv)
    return ConversationDetail(
        **summary.model_dump(),
        messages=decoded,
    )


@router.post(
    "/conversations",
    response_model=ConversationSummary,
    status_code=201,
    summary="Crear nueva conversación",
)
async def create_conversation(
    current_user: Annotated[User, Depends(get_current_user)],
    tenant_id: Annotated[UUID | None, Depends(get_tenant_context)],
    db: Annotated[Session, Depends(get_db)],
) -> ConversationSummary:
    """Create a new empty conversation for the authenticated user."""
    if not tenant_id or not current_user.tenant_id:
        raise HTTPException(status_code=401, detail="Tenant ID requerido")

    repo = ConversationRepository(db)
    conv = repo.create(
        conversation_id=uuid.uuid4(),
        tenant_id=tenant_id,
        user_id=current_user.id,
    )
    db.commit()
    logger.info(
        "conversation_created",
        conversation_id=str(conv.id),
        tenant_id=str(tenant_id),
    )
    return _build_summary(conv)


@router.patch(
    "/conversations/{conversation_id}",
    response_model=ConversationSummary,
    summary="Actualizar título o archivar conversación",
)
async def patch_conversation(
    conversation_id: UUID,
    body: PatchConversationRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    tenant_id: Annotated[UUID | None, Depends(get_tenant_context)],
    db: Annotated[Session, Depends(get_db)],
) -> ConversationSummary:
    """Update the title and/or archive state of a conversation."""
    if not tenant_id or not current_user.tenant_id:
        raise HTTPException(status_code=401, detail="Tenant ID requerido")

    repo = ConversationRepository(db)
    conv = repo.get_by_id(conversation_id, tenant_id, current_user.id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversación no encontrada")

    if body.title is not None:
        conv.title = body.title

    if body.archived is True:
        from luana_core_platform.domain.datetime_utils import utc_now

        conv.archived_at = utc_now()
    elif body.archived is False:
        conv.archived_at = None

    db.flush()
    db.commit()
    logger.info(
        "conversation_patched",
        conversation_id=str(conversation_id),
        tenant_id=str(tenant_id),
    )
    return _build_summary(conv)


@router.delete(
    "/conversations/{conversation_id}",
    status_code=204,
    summary="Archivar conversación (soft delete)",
)
async def delete_conversation(
    conversation_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    tenant_id: Annotated[UUID | None, Depends(get_tenant_context)],
    db: Annotated[Session, Depends(get_db)],
) -> None:
    """Archive a conversation (soft delete — sets archived_at)."""
    if not tenant_id or not current_user.tenant_id:
        raise HTTPException(status_code=401, detail="Tenant ID requerido")

    repo = ConversationRepository(db)
    result = repo.archive(
        conversation_id=conversation_id,
        tenant_id=tenant_id,
        user_id=current_user.id,
    )
    if result is None:
        raise HTTPException(status_code=404, detail="Conversación no encontrada")

    db.commit()
    logger.info(
        "conversation_deleted",
        conversation_id=str(conversation_id),
        tenant_id=str(tenant_id),
    )


@router.post(
    "/conversations/{conversation_id}/mutations/apply",
    response_model=ApplyMutationsResponse,
    summary="Aplicar propuestas del copilot al backend (B22-FP1 fallback)",
)
async def apply_mutations(
    conversation_id: UUID,
    body: ApplyMutationsRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    tenant_id: Annotated[UUID | None, Depends(get_tenant_context)],
    db: Annotated[Session, Depends(get_db)],
) -> ApplyMutationsResponse:
    """Apply ProposalCard updates server-side when no FormRuntimeBridge is available.

    Used by ``ProposalCard`` as the fallback when the chat panel is open
    but no form-runtime section is mounted (e.g. user is on a non-form
    route). Each update is journaled idempotently and dispatched to the
    per-domain side-effect handler so a page reload renders the value.
    """
    if not tenant_id or not current_user.tenant_id:
        raise HTTPException(status_code=401, detail="Tenant ID requerido")

    repo = ConversationRepository(db)
    conv = repo.get_by_id(conversation_id, tenant_id, current_user.id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversación no encontrada")

    service = MutationApplyService(db)
    result = service.apply(
        tenant_id=tenant_id,
        conversation_id=conversation_id,
        message_id=body.message_id,
        updates=[u.model_dump() for u in body.updates],
        entity_id=body.entity_id,
    )
    db.commit()
    logger.info(
        "copilot_mutations_applied",
        conversation_id=str(conversation_id),
        tenant_id=str(tenant_id),
        applied_count=len(result.applied),
        rejected_count=len(result.rejected),
    )
    return ApplyMutationsResponse(
        applied=[
            AppliedMutationDTO(
                id=a.id,
                field_path=a.field_path,
                domain=a.domain,
                status=a.status,
            )
            for a in result.applied
        ],
        rejected=[RejectedMutationDTO(field_id=r.field_id, reason=r.reason) for r in result.rejected],
    )


@router.get(
    "/conversations/{conversation_id}/mutations",
    response_model=MutationJournalListResponse,
    summary="Listar mutaciones aplicadas (no revertidas) de la conversación",
)
async def list_conversation_mutations(
    conversation_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    tenant_id: Annotated[UUID | None, Depends(get_tenant_context)],
    db: Annotated[Session, Depends(get_db)],
    message_id: UUID | None = None,
) -> MutationJournalListResponse:
    """Return the active mutation-journal entries for a conversation.

    Used by ``ProposalCard`` to rehydrate per-field "applied" status when
    the user refreshes the chat panel. ``message_id`` narrows the result
    to a single proposal so the card only repaints its own rows.
    """
    if not tenant_id or not current_user.tenant_id:
        raise HTTPException(status_code=401, detail="Tenant ID requerido")

    repo = ConversationRepository(db)
    conv = repo.get_by_id(conversation_id, tenant_id, current_user.id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversación no encontrada")

    journal_repo = MutationJournalRepository(db)
    rows = journal_repo.fetch_by_conversation(
        tenant_id=tenant_id,
        conversation_id=conversation_id,
        include_reverted=False,
        message_id=message_id,
    )
    return MutationJournalListResponse(
        entries=[
            MutationJournalEntryDTO(
                id=row.id,
                message_id=row.message_id,
                domain=row.domain,
                entity_id=row.entity_id,
                field_path=row.field_path,
                applied_at=row.applied_at,
            )
            for row in rows
        ],
    )


@router.post(
    "/conversations/{conversation_id}/revert",
    response_model=RevertResponse,
    summary="Revertir mutaciones de una conversación",
)
async def revert_conversation(
    conversation_id: UUID,
    body: RevertRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    tenant_id: Annotated[UUID | None, Depends(get_tenant_context)],
    db: Annotated[Session, Depends(get_db)],
) -> RevertResponse:
    """Revert copilot-applied mutations for a conversation.

    When mutation_ids is omitted, all active (non-reverted) mutations
    for the conversation are reverted in chronological order (oldest first).
    """
    if not tenant_id or not current_user.tenant_id:
        raise HTTPException(status_code=401, detail="Tenant ID requerido")

    repo = ConversationRepository(db)
    conv = repo.get_by_id(conversation_id, tenant_id, current_user.id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversación no encontrada")

    journal_repo = MutationJournalRepository(db)

    # Fetch entries to revert
    entries = journal_repo.fetch_by_conversation(
        tenant_id=tenant_id,
        conversation_id=conversation_id,
        include_reverted=False,
    )

    # Filter to specific IDs if provided
    if body.mutation_ids is not None:
        requested = set(body.mutation_ids)
        entries = [e for e in entries if e.id in requested]

    failed: list[RevertFailure] = []
    reverted_ids: list[UUID] = []

    for entry in entries:
        try:
            # Mark entry as reverted — actual domain revert is per-domain
            # and will be wired in a later sprint; for now we record the intent.
            reverted_ids.append(entry.id)
        except Exception as exc:
            logger.exception(
                "revert_entry_failed",
                entry_id=str(entry.id),
                error=str(exc),
            )
            failed.append(RevertFailure(id=entry.id, error=str(exc)))

    if reverted_ids:
        journal_repo.mark_reverted(tenant_id=tenant_id, entry_ids=reverted_ids)

    db.commit()
    logger.info(
        "conversation_reverted",
        conversation_id=str(conversation_id),
        reverted_count=len(reverted_ids),
        failed_count=len(failed),
        tenant_id=str(tenant_id),
    )
    return RevertResponse(reverted_count=len(reverted_ids), failed=failed)


@router.get(
    "/conversations/{conversation_id}/active-jobs",
    response_model=ActiveJobsResponse,
    summary="Rehidratar jobs de extracción activos",
)
async def get_active_jobs(
    conversation_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    tenant_id: Annotated[UUID | None, Depends(get_tenant_context)],
    db: Annotated[Session, Depends(get_db)],
) -> ActiveJobsResponse:
    """Return active extraction jobs for a conversation.

    Used by the FE to rehidrate in-flight extraction state after a page
    reload. Reads the persisted ``procedure_state.active_extraction_job``
    from the DB and merges with live Redis progress (if available).

    Returns ``jobs: []`` when no active job is stored — not an error.
    Returns 404 when the conversation does not exist or belongs to another
    tenant/user (same policy as GET /conversations/{id}).
    """
    if not tenant_id or not current_user.tenant_id:
        raise HTTPException(status_code=401, detail="Tenant ID requerido")

    repo = ConversationRepository(db)
    conv = repo.get_by_id(conversation_id, tenant_id, current_user.id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversación no encontrada")

    job = read_active_job(str(conversation_id), tenant_id)
    if job is None:
        return ActiveJobsResponse(jobs=[])

    # Read live progress from Redis — best-effort, tolerate absence.
    redis_data: dict = {}
    try:
        from luana_core_platform.core.database import redis_client

        if redis_client:
            progress_key = f"{job.module}_extract:{tenant_id!s}:{job.job_id}"
            raw = redis_client.get(progress_key)
            if raw:
                import json as _json

                redis_data = _json.loads(raw)
    except Exception:  # noqa: BLE001 — Redis unavailable is not fatal
        logger.warning(
            "active_jobs_redis_read_failed",
            job_id=job.job_id,
            conversation_id=str(conversation_id),
        )

    # Build the poll_endpoint that FE uses to continue polling.
    # Mirrors the pattern in frontend/src/lib/api/ai-actions.ts:
    #   brand: /api/v1/brand/tools/extract-full-brand/status/{job_id}
    #   offer: /api/v1/offer/tools/extract-full-offer/status/{job_id}
    _poll_templates: dict[str, str] = {
        "brand": f"/api/v1/brand/tools/extract-full-brand/status/{job.job_id}",
        "offer": f"/api/v1/offer/tools/extract-full-offer/status/{job.job_id}",
    }
    poll_endpoint = _poll_templates.get(
        job.module,
        f"/api/v1/{job.module}/tools/extract/status/{job.job_id}",
    )

    dto = ActiveJobProgressDTO(
        job_id=job.job_id,
        module=job.module,
        entity_id=job.entity_id,
        source_kind=job.source_kind,
        source_ref=job.source_ref,
        scope=job.scope,
        mode=job.mode,
        started_at=job.started_at,
        status=redis_data.get("status"),
        progress=redis_data.get("progress"),
        stage=redis_data.get("stage"),
        filled_fields=redis_data.get("filled_fields", []),
        filled_fields_by_section=redis_data.get("filled_fields_by_section", {}),
        sections_touched=redis_data.get("sections_touched", []),
        sections_completed=redis_data.get("sections_completed", []),
        finished_at=redis_data.get("finished_at"),
        poll_endpoint=poll_endpoint,
    )

    logger.info(
        "active_jobs_fetched",
        conversation_id=str(conversation_id),
        job_id=job.job_id,
        module=job.module,
        has_redis_data=bool(redis_data),
        tenant_id=str(tenant_id),
    )
    return ActiveJobsResponse(jobs=[dto])

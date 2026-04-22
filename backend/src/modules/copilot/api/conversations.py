"""CRUD endpoints for copilot conversations (CONTRACT §4.2)."""

from __future__ import annotations

import uuid
from typing import Annotated
from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query

# Runtime imports (needed by FastAPI's dependency resolver for Annotated[..., Depends(...)] —
# cannot be moved to TYPE_CHECKING or FastAPI treats the param as a query arg).
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.modules.copilot.api.conversation_dto import (
    ConversationDetail,
    ConversationListResponse,
    ConversationMessageDTO,
    ConversationSummary,
    PatchConversationRequest,
    RevertFailure,
    RevertRequest,
    RevertResponse,
)
from src.modules.copilot.infrastructure.repositories.conversation_repository import (
    ConversationRepository,
)
from src.modules.copilot.infrastructure.repositories.message_codec import decode_message
from src.modules.copilot.infrastructure.repositories.mutation_journal_repository import (
    MutationJournalRepository,
)
from src.modules.iam.api.dependencies import get_current_user, get_tenant_context
from src.modules.iam.domain.user import User

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
        from src.shared.domain.datetime_utils import utc_now

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

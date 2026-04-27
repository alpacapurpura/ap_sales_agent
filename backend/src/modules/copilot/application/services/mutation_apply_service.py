"""MutationApplyService — apply copilot ProposalCard updates server-side (B22-FP1).

Used by ``POST /api/v1/copilot/conversations/{id}/mutations/apply`` when the
``ProposalCard`` cannot route updates through ``FormRuntimeBridge``
(no section mounted, copilot panel open over a non-form route, etc).

Pipeline per update:

1. Resolve owning ``domain`` from the editable-fields catalog. Updates
   pointing to a path the copilot does not own are rejected and surfaced
   to the FE so the user sees an explicit error.
2. Idempotent journal upsert keyed on
   ``(tenant_id, conversation_id, message_id, field_path)`` — backed by
   the partial unique index added in migration 074.
3. Dispatch the actual side-effect to the per-domain handler so the
   underlying aggregate (e.g. ``BrandSettings``) is updated and the
   user's next page reload renders the new value.

Per-domain side-effect handlers register through
:func:`register_apply_handler`. ``brand`` is wired by default; ``offer``
and ``buyer_persona`` are tracked as Sub-FP1.1 deferred work — for now
those domains journal the change but skip side-effect (handler returns
False) so the FE still gets honest feedback (status=``applied`` for the
journal, but no aggregate write happened).
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any
from uuid import UUID

import structlog

from src.modules.copilot.infrastructure.repositories.mutation_journal_repository import (
    MutationJournalRepository,
)
from src.shared.links.ports.editable_fields import (
    get_paths_for,
    get_registered_domains,
)

logger = structlog.get_logger()


@dataclass(frozen=True, slots=True)
class AppliedMutation:
    """A single applied mutation row, exposed to the FE."""

    id: UUID
    field_path: str
    domain: str
    status: str  # "applied" | "existing"


@dataclass(frozen=True, slots=True)
class RejectedMutation:
    """A single update that the apply pipeline refused to persist."""

    field_id: str
    reason: str


@dataclass(frozen=True, slots=True)
class ApplyResult:
    """Aggregate result of one apply call."""

    applied: list[AppliedMutation]
    rejected: list[RejectedMutation]


# ── Per-domain side-effect dispatcher ────────────────────────────────────
# Handler signature: (db, tenant_id, field_path, new_value) -> bool
# Returns True when the aggregate was actually written, False otherwise.

ApplyHandler = Callable[[Any, UUID, str, Any], bool]
_HANDLERS: dict[str, ApplyHandler] = {}


def register_apply_handler(domain: str, handler: ApplyHandler) -> None:
    """Register the side-effect handler for ``domain``.

    Idempotent — re-registering replaces the previous handler. Tests use
    this to swap in stubs without touching the real repos.
    """
    _HANDLERS[domain] = handler


def get_apply_handler(domain: str) -> ApplyHandler | None:
    """Return the registered handler for ``domain`` or ``None``."""
    return _HANDLERS.get(domain)


# ── Domain resolver ──────────────────────────────────────────────────────


def _resolve_domain(field_id: str) -> str | None:
    """Mirror of ``application/tools/mutations.py::_guess_domain``.

    Walks every registered editable-fields catalog deterministically and
    returns the first domain whose paths contain ``field_id``. Returns
    ``None`` when no domain owns the path — surfacing the rejection to
    the FE rather than writing an orphan journal row.
    """
    for domain in get_registered_domains():
        if field_id in get_paths_for(domain):
            return domain
    return None


# ── Service ──────────────────────────────────────────────────────────────


class MutationApplyService:
    """Apply ProposalCard updates: journal write + per-domain side-effect.

    Caller scope: one service instance per request. The FastAPI route
    constructs it with the active ``Session`` and forwards the validated
    request body. Commit happens in the route after the service returns.
    """

    def __init__(self, db: Any) -> None:  # noqa: ANN401  # Session/AsyncSession opaque
        """Initialize with a database session."""
        self.db = db
        self.journal = MutationJournalRepository(db)

    def apply(
        self,
        *,
        tenant_id: UUID,
        conversation_id: UUID,
        message_id: UUID,
        updates: list[dict[str, Any]],
    ) -> ApplyResult:
        """Apply each update and return a structured result.

        Each ``update`` dict must include ``field_id`` and ``new_value``.
        ``reason`` is optional and ignored by the apply pipeline (the FE
        already shows it inside ProposalCard for the user).
        """
        applied: list[AppliedMutation] = []
        rejected: list[RejectedMutation] = []

        for u in updates:
            field_id = u.get("field_id")
            new_value = u.get("new_value")
            if not field_id or new_value is None:
                rejected.append(
                    RejectedMutation(
                        field_id=str(field_id or ""),
                        reason="Faltan campos obligatorios: field_id y new_value.",
                    ),
                )
                continue

            domain = _resolve_domain(str(field_id))
            if domain is None:
                rejected.append(
                    RejectedMutation(
                        field_id=str(field_id),
                        reason=(f"'{field_id}' no está en el catálogo editable. Revisa el field_id propuesto."),
                    ),
                )
                continue

            row, status = self.journal.upsert_idempotent(
                tenant_id=tenant_id,
                conversation_id=conversation_id,
                message_id=message_id,
                domain=domain,
                entity_id=None,
                field_path=str(field_id),
                old_value=None,
                new_value=new_value,
            )

            handler = get_apply_handler(domain)
            if handler is not None and status == "applied":
                try:
                    handler(self.db, tenant_id, str(field_id), new_value)
                except Exception as exc:
                    logger.exception(
                        "mutation_apply_handler_failed",
                        domain=domain,
                        field_path=str(field_id),
                        tenant_id=str(tenant_id),
                        error=str(exc),
                    )
                    rejected.append(
                        RejectedMutation(
                            field_id=str(field_id),
                            reason=f"Falló al aplicar el cambio: {exc}",
                        ),
                    )
                    continue
            else:
                logger.info(
                    "mutation_apply_no_handler",
                    domain=domain,
                    field_path=str(field_id),
                    status=status,
                    tenant_id=str(tenant_id),
                )

            applied.append(
                AppliedMutation(
                    id=row.id,
                    field_path=str(field_id),
                    domain=domain,
                    status=status,
                ),
            )

        logger.info(
            "mutation_apply_completed",
            tenant_id=str(tenant_id),
            conversation_id=str(conversation_id),
            applied_count=len(applied),
            rejected_count=len(rejected),
        )
        return ApplyResult(applied=applied, rejected=rejected)

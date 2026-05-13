"""Copilot conversation ``DataAccessProvider`` — F5 internal accessor.

Own-module accessor (no provider discovery): the dispatcher in ``ask_tenant_data``
registers an instance directly so user questions like "cuántas conversaciones
tuve esta semana" resolve against the copilot's own ``copilot_conversations``
table without going through cross-module imports.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from luana_core_copilot.domain.ports import DataQueryPlan, DataQueryResult

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping
    from uuid import UUID

    from sqlalchemy.orm import Session


def _default_db_factory() -> Session:
    from luana_core_platform.core.database import SessionLocal

    return SessionLocal()


class ConversationDataAccessProvider:
    """Read-only accessor for copilot conversation counts."""

    SUPPORTED_KINDS = frozenset({"conversation_count"})

    def __init__(
        self,
        db_factory: Callable[[], Session] | None = None,
    ) -> None:
        """Optional ``db_factory`` lets tests inject a fixture session."""
        self._db_factory = db_factory or _default_db_factory

    def supports(self, kind: str) -> bool:
        """Return ``True`` if this accessor handles plans with the given kind."""
        return kind in self.SUPPORTED_KINDS

    async def execute(
        self,
        *,
        tenant_id: UUID,
        plan: DataQueryPlan,
        context: Mapping[str, Any] | None = None,
    ) -> DataQueryResult:
        """Run the conversation_count plan against the copilot's own store."""
        if not self.supports(plan.kind):
            msg = (
                f"ConversationDataAccessProvider does not support kind {plan.kind!r}. "
                f"Expected one of {sorted(self.SUPPORTED_KINDS)}."
            )
            raise ValueError(msg)

        since = plan.filters.get("since")
        until = plan.filters.get("until")
        if since is None or until is None:
            msg = "conversation_count requires both 'since' and 'until' in filters"
            raise ValueError(msg)

        from luana_core_copilot.infrastructure.repositories.conversation_repository import (
            ConversationRepository,
        )

        ctx = dict(context or {})
        db = ctx.get("db")
        owns_session = db is None
        if db is None:
            db = self._db_factory()
        try:
            repo = ConversationRepository(db)
            count = repo.count_window(
                tenant_id=tenant_id,
                since=since,
                until=until,
                include_archived=bool(plan.filters.get("include_archived", False)),
            )
            return DataQueryResult(
                rows=[],
                metadata={
                    "count": count,
                    "kind": "conversation_count",
                    "since": since.isoformat() if hasattr(since, "isoformat") else str(since),
                    "until": until.isoformat() if hasattr(until, "isoformat") else str(until),
                },
            )
        finally:
            if owns_session:
                db.close()

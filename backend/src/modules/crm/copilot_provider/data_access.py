"""CRM ``DataAccessProvider`` — F5 ``ask_tenant_data`` integration.

Wraps :class:`LeadRepository.count_inbound` behind the ``DataAccessProvider``
port. Returns counts (no rows) so the copilot synthesizer can answer "cuántas
personas escribieron esta semana"-class questions without leaking PII.

[COPILOT-PROVIDER-PATTERN]
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


class CrmDataAccessProvider:
    """Read-only data accessor for the CRM module."""

    SUPPORTED_KINDS = frozenset({"lead_count"})

    def __init__(
        self,
        db_factory: Callable[[], Session] | None = None,
    ) -> None:
        """Optional ``db_factory`` lets tests inject a fixture session."""
        self._db_factory = db_factory or _default_db_factory

    def supports(self, kind: str) -> bool:
        return kind in self.SUPPORTED_KINDS

    async def execute(
        self,
        *,
        tenant_id: UUID,
        plan: DataQueryPlan,
        context: Mapping[str, Any] | None = None,
    ) -> DataQueryResult:
        if not self.supports(plan.kind):
            msg = (
                f"CrmDataAccessProvider does not support kind {plan.kind!r}. "
                f"Expected one of {sorted(self.SUPPORTED_KINDS)}."
            )
            raise ValueError(msg)

        since = plan.filters.get("since")
        until = plan.filters.get("until")
        if since is None or until is None:
            msg = "lead_count requires both 'since' and 'until' in filters"
            raise ValueError(msg)

        from luana_core_crm.infrastructure.repositories.lead_repository import (
            LeadRepository,
        )

        ctx = dict(context or {})
        db = ctx.get("db")
        owns_session = db is None
        if db is None:
            db = self._db_factory()
        try:
            repo = LeadRepository(db)
            channel = plan.filters.get("channel")
            count = repo.count_inbound(
                tenant_id=tenant_id,
                since=since,
                until=until,
                channel=channel,
            )
            metadata: dict[str, Any] = {
                "count": count,
                "kind": "lead_count",
                "since": since.isoformat() if hasattr(since, "isoformat") else str(since),
                "until": until.isoformat() if hasattr(until, "isoformat") else str(until),
            }
            if channel:
                metadata["channel"] = channel
            return DataQueryResult(rows=[], metadata=metadata)
        finally:
            if owns_session:
                db.close()

"""SQLAlchemy 2.0 async repository for ``llm_role_binding``.

PI-2 S4 PR-1 db-registry-admin-ui.

Per ``backend-ddd.md`` rules:
- ``select(Model).where(...)`` — never ``session.query()``.
- All queries filter ``tenant_id`` (NULL means global default — explicit).
- Async ``AsyncSession``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any
from uuid import UUID, uuid4

import structlog
from luana_core_llm.domain.role_binding import LLMRoleBinding
from luana_core_llm.infrastructure.audit_model import LLMConfigAuditModel
from luana_core_llm.infrastructure.role_binding_model import LLMRoleBindingModel
from luana_core_platform.core.enums import AIProvider, ModelRole
from luana_core_platform.domain.datetime_utils import utc_now
from sqlalchemy import select, update

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()


class BindingNotFoundError(Exception):
    """Raised when activate/deactivate target binding does not exist."""


class SqlAlchemyLLMRoleBindingRepository:
    """SA 2.0 async repo for LLM role bindings + co-located audit writes."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize repo with active SA AsyncSession."""
        self._session = session

    @staticmethod
    def _to_domain(row: LLMRoleBindingModel) -> LLMRoleBinding:
        return LLMRoleBinding(
            id=row.id,
            role=ModelRole(row.role),
            provider=AIProvider(row.provider),
            model=row.model,
            is_active=row.is_active,
            tenant_id=row.tenant_id,
            config=row.config or {},
            eval_score=row.eval_score,
            notes=row.notes,
            created_at=row.created_at,
            created_by=row.created_by,
            activated_at=row.activated_at,
            deactivated_at=row.deactivated_at,
        )

    async def find_active_global(self, role: ModelRole) -> LLMRoleBinding | None:
        """Return active global binding for role (tenant_id IS NULL)."""
        stmt = select(LLMRoleBindingModel).where(
            LLMRoleBindingModel.role == role.value,
            LLMRoleBindingModel.tenant_id.is_(None),
            LLMRoleBindingModel.is_active.is_(True),
        )
        result = await self._session.execute(stmt)
        row = result.scalar_one_or_none()
        return self._to_domain(row) if row else None

    async def list_by_role(self, role: ModelRole) -> list[LLMRoleBinding]:
        """Return all bindings (active + inactive) for role."""
        stmt = (
            select(LLMRoleBindingModel)
            .where(LLMRoleBindingModel.role == role.value)
            .order_by(LLMRoleBindingModel.created_at.desc())
        )
        result = await self._session.execute(stmt)
        return [self._to_domain(r) for r in result.scalars().all()]

    async def list_all(self) -> list[LLMRoleBinding]:
        """Return all bindings ordered by role + created_at desc."""
        stmt = select(LLMRoleBindingModel).order_by(
            LLMRoleBindingModel.role,
            LLMRoleBindingModel.created_at.desc(),
        )
        result = await self._session.execute(stmt)
        return [self._to_domain(r) for r in result.scalars().all()]

    async def find_by_id(self, binding_id: UUID) -> LLMRoleBinding | None:
        """Return binding by primary key UUID, or None if not found."""
        stmt = select(LLMRoleBindingModel).where(LLMRoleBindingModel.id == binding_id)
        result = await self._session.execute(stmt)
        row = result.scalar_one_or_none()
        return self._to_domain(row) if row else None

    async def create(
        self,
        *,
        role: ModelRole,
        provider: AIProvider,
        model: str,
        config: dict[str, Any] | None = None,
        eval_score: float | None = None,
        notes: str | None = None,
        actor: str = "system",
    ) -> LLMRoleBinding:
        """Insert new INACTIVE binding row + audit entry."""
        row = LLMRoleBindingModel(
            id=uuid4(),
            role=role.value,
            provider=provider.value,
            model=model,
            is_active=False,
            tenant_id=None,
            config=config or {},
            eval_score=eval_score,  # type: ignore[arg-type]
            notes=notes,
            created_at=utc_now(),
            created_by=actor,
        )
        self._session.add(row)
        await self._session.flush()
        await self._write_audit(
            actor=actor,
            action="create",
            role=role.value,
            tenant_id=None,
            before=None,
            after={"provider": provider.value, "model": model, "is_active": False},
            reason=None,
        )
        await self._session.commit()
        return self._to_domain(row)

    async def activate(self, binding_id: UUID, *, actor: str, reason: str | None = None) -> LLMRoleBinding:
        """Atomic: deactivate prior active for same role + activate target."""
        target = await self.find_by_id(binding_id)
        if target is None:
            raise BindingNotFoundError(str(binding_id))

        prior = await self.find_active_global(target.role)

        now = utc_now()
        if prior is not None and prior.id != binding_id:
            await self._session.execute(
                update(LLMRoleBindingModel)
                .where(LLMRoleBindingModel.id == prior.id)
                .values(is_active=False, deactivated_at=now)
            )
            await self._write_audit(
                actor=actor,
                action="deactivate",
                role=prior.role.value,
                tenant_id=None,
                before={"provider": prior.provider.value, "model": prior.model, "is_active": True},
                after={"provider": prior.provider.value, "model": prior.model, "is_active": False},
                reason=reason or f"Replaced by binding {binding_id}",
            )

        await self._session.execute(
            update(LLMRoleBindingModel)
            .where(LLMRoleBindingModel.id == binding_id)
            .values(is_active=True, activated_at=now)
        )
        await self._write_audit(
            actor=actor,
            action="activate",
            role=target.role.value,
            tenant_id=None,
            before={"provider": target.provider.value, "model": target.model, "is_active": False},
            after={"provider": target.provider.value, "model": target.model, "is_active": True},
            reason=reason,
        )
        await self._session.commit()

        # Re-read to capture activated_at + is_active=True.
        refreshed = await self.find_by_id(binding_id)
        assert refreshed is not None  # noqa: S101
        return refreshed

    async def deactivate(self, binding_id: UUID, *, actor: str, reason: str | None = None) -> None:
        """Soft-deactivate single binding + audit. Idempotent."""
        target = await self.find_by_id(binding_id)
        if target is None:
            raise BindingNotFoundError(str(binding_id))
        if not target.is_active:
            return  # idempotent — already deactivated

        await self._session.execute(
            update(LLMRoleBindingModel)
            .where(LLMRoleBindingModel.id == binding_id)
            .values(is_active=False, deactivated_at=utc_now())
        )
        await self._write_audit(
            actor=actor,
            action="deactivate",
            role=target.role.value,
            tenant_id=None,
            before={"provider": target.provider.value, "model": target.model, "is_active": True},
            after={"provider": target.provider.value, "model": target.model, "is_active": False},
            reason=reason,
        )
        await self._session.commit()

    async def list_audit(self, limit: int = 50) -> list[dict[str, Any]]:
        """Return recent audit rows for admin UI display."""
        stmt = select(LLMConfigAuditModel).order_by(LLMConfigAuditModel.created_at.desc()).limit(limit)
        result = await self._session.execute(stmt)
        return [
            {
                "actor": r.actor,
                "action": r.action,
                "role": r.role,
                "tenant_id": str(r.tenant_id) if r.tenant_id else None,
                "before": r.before,
                "after": r.after,
                "reason": r.reason,
                "created_at": r.created_at.isoformat(),
            }
            for r in result.scalars().all()
        ]

    async def _write_audit(
        self,
        *,
        actor: str,
        action: str,
        role: str,
        tenant_id: UUID | None,
        before: dict[str, Any] | None,
        after: dict[str, Any] | None,
        reason: str | None,
    ) -> None:
        """Append-only audit row write. Best-effort warning if commit fails."""
        try:
            row = LLMConfigAuditModel(
                id=uuid4(),
                actor=actor,
                action=action,
                role=role,
                tenant_id=tenant_id,
                before=before,
                after=after,
                reason=reason,
                created_at=utc_now(),
            )
            self._session.add(row)
        except Exception as exc:  # noqa: BLE001 — best-effort audit write
            logger.warning(
                "llm_config_audit_write_failed",
                action=action,
                role=role,
                error=str(exc),
            )


__all__ = ["BindingNotFoundError", "SqlAlchemyLLMRoleBindingRepository"]

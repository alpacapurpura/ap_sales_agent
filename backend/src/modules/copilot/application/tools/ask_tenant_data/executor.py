"""Executor stage for ``ask_tenant_data``.

Picks the first :class:`DataAccessProvider` that ``supports(plan.kind)`` and
delegates. Iteration order is the caller's: the tool wires
``[ConversationDataAccessProvider, *discovered_module_providers]`` so the
copilot's own data takes precedence over module-supplied accessors when there
is a kind collision (none today, but the invariant is cheap to enforce).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Sequence

    from src.modules.copilot.domain.ports import (
        DataAccessProvider,
        DataQueryPlan,
        DataQueryResult,
    )


class NoAccessorError(RuntimeError):
    """Raised when no registered accessor supports the plan's kind."""


async def execute_plan(
    *,
    plan: DataQueryPlan,
    tenant_id: Any,  # noqa: ANN401 — UUID-or-string; opaque to dispatcher
    accessors: Sequence[DataAccessProvider],
    db: Any | None = None,  # noqa: ANN401 — opaque (SQLA Session, test stub, …)
) -> DataQueryResult:
    """Dispatch ``plan`` to the first accessor that supports its kind."""
    context: dict[str, Any] | None = None
    if db is not None:
        context = {"db": db}

    for accessor in accessors:
        if accessor.supports(plan.kind):
            return await accessor.execute(
                tenant_id=tenant_id,
                plan=plan,
                context=context,
            )

    msg = (
        f"No DataAccessProvider supports kind {plan.kind!r}. "
        f"Registered accessors: "
        f"{[type(a).__name__ for a in accessors]}"
    )
    raise NoAccessorError(msg)


__all__ = ("NoAccessorError", "execute_plan")

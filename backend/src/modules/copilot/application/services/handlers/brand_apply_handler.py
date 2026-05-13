"""Brand domain side-effect handler for ``MutationApplyService`` (B22-FP1).

Goes through ``shared/links/ports/brand.py::BrandFieldApplyPort`` so the
copilot module never imports brand internals directly — the F1 ratchet
``test_no_new_copilot_module_imports`` stays clean.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import structlog
from luana_core_platform.links.ports.brand import create_brand_field_apply_port

if TYPE_CHECKING:
    from uuid import UUID

logger = structlog.get_logger()


def apply_brand_field(
    db: Any,  # noqa: ANN401  # Session/AsyncSession opaque
    tenant_id: UUID,
    field_path: str,
    new_value: Any,  # noqa: ANN401
) -> bool:
    """Persist ``new_value`` at ``field_path`` via ``BrandFieldApplyPort``.

    Returns ``True`` when the write happened. Raises on validation /
    persistence failures so the caller can mark the proposal rejected.
    """
    port = create_brand_field_apply_port(db)
    port.apply_field(
        tenant_id=tenant_id,
        field_path=field_path,
        new_value=new_value,
    )
    logger.debug(
        "copilot_brand_handler_done",
        tenant_id=str(tenant_id),
        field_path=field_path,
    )
    return True


def register_brand_handler() -> None:
    """Register ``apply_brand_field`` as the brand handler.

    Idempotent — re-registering replaces the previous handler. Wired by
    the copilot services package init so any caller that touches the
    apply service gets the handler for free.
    """
    from luana_core_copilot.application.services.mutation_apply_service import (
        register_apply_handler,
    )

    register_apply_handler("brand", apply_brand_field)

"""Per-domain side-effect handlers for ``MutationApplyService`` (B22-FP1)."""

from __future__ import annotations

from luana_core_copilot.application.services.handlers.brand_apply_handler import (
    apply_brand_field,
    register_brand_handler,
)

__all__ = ["apply_brand_field", "register_brand_handler"]

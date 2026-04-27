"""Copilot services package.

Importing this package wires the per-domain ``MutationApplyService``
side-effect handlers (B22-FP1). Wiring lives here — not at the orchestrator
or app entrypoint — so any caller that touches copilot services (the
``/mutations/apply`` route, tests, the chat orchestrator) gets the
handlers registered before they look them up.
"""

from src.modules.copilot.application.services.handlers.brand_apply_handler import (
    register_brand_handler,
)

register_brand_handler()

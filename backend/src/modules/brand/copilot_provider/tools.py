"""Brand-domain copilot tools.

F1 keeps this empty: brand-specific tools today are exposed via the generic
``module_data`` mutation/awareness path (legacy ``MODULE_TOOLS``,
``MUTATION_TOOLS``, ``AWARENESS_TOOLS``). When a brand-specific tool ships
(e.g. ``regen_brand_voice``, ``audit_brand_consistency``), it lives here.

The ``ToolProvider.tool_groups()`` mapping is what the registry consumes —
returning an empty mapping signals "module has no domain-specific tools yet"
without breaking the discovery contract.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence


class BrandToolProvider:
    """Brand-domain tool surface (currently empty — populated in later fases)."""

    def tool_groups(self) -> Mapping[str, Sequence[Any]]:
        return {}

    def tools(self) -> Sequence[Any]:
        return ()

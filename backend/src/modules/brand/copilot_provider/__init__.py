"""Brand module — copilot provider entry point.

Exposes ``provider`` so ``copilot.application.discovery`` can wire the brand
module's tools, module-data accessors, summary and per-route context fragment
without ``copilot/`` importing the brand package directly.

[COPILOT-PROVIDER-PATTERN]: see ``docs/domains/copilot/redesign-2026-04/02-architecture-target.md §2``.
"""

from __future__ import annotations

from src.modules.brand.copilot_provider.provider import BrandCopilotProvider

provider: BrandCopilotProvider = BrandCopilotProvider()

__all__ = ("BrandCopilotProvider", "provider")

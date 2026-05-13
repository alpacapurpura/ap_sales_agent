"""Brand ``CopilotProvider`` — root implementation.

Glues the four sub-ports (tools, workflows, summary, context injector) and
the static ``ModuleData`` record into a single object discoverable via the
``src.modules.brand.copilot_provider:provider`` convention.
"""

from __future__ import annotations

from luana_core_brand_studio.copilot_provider.context_inject import BrandContextInjector
from luana_core_brand_studio.copilot_provider.module_data import build_brand_module_data
from luana_core_brand_studio.copilot_provider.summary import BrandSummaryProvider
from luana_core_brand_studio.copilot_provider.tools import BrandToolProvider
from luana_core_brand_studio.copilot_provider.workflows import BrandWorkflowProvider
from luana_core_copilot.domain.ports import (
    BaseCopilotProvider,
    ContextInjector,
    ModuleData,
    SummaryProvider,
    ToolProvider,
    WorkflowProvider,
)


class BrandCopilotProvider(BaseCopilotProvider):
    """Brand module provider — see ``docs/domains/copilot/redesign-2026-04``."""

    @property
    def module_id(self) -> str:
        return "brand"

    @property
    def label(self) -> str:
        return "Brand Studio"

    def module_data(self) -> ModuleData | None:
        return build_brand_module_data()

    def tool_provider(self) -> ToolProvider | None:
        return BrandToolProvider()

    def workflow_provider(self) -> WorkflowProvider | None:
        return BrandWorkflowProvider()

    def summary_provider(self) -> SummaryProvider | None:
        return BrandSummaryProvider()

    def context_injector(self) -> ContextInjector | None:
        return BrandContextInjector()

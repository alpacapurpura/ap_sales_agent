"""F6 — workflow registry aggregator.

Iterates the discovered ``CopilotProvider`` registry and flattens every
provider's ``WorkflowProvider.workflows()`` into a single
``{workflow_id: Workflow}`` dict. Mirrors the F1 ``_collect_*`` aggregators —
no business-module imports, per-provider failures are isolated.

[COPILOT-WORKFLOW-F6]
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

if TYPE_CHECKING:
    from collections.abc import Mapping

    from luana_core_copilot.domain.ports import CopilotProvider
    from luana_core_copilot.domain.workflow import Workflow

logger = structlog.get_logger(__name__)


class WorkflowRegistryError(RuntimeError):
    """Raised when registry invariants are violated (duplicate ids, …)."""


def collect_workflows(
    providers: Mapping[str, CopilotProvider],
) -> dict[str, Workflow]:
    """Aggregate every provider's workflows into one ``{id: Workflow}`` dict.

    Failures from a single provider's ``workflow_provider()`` accessor are
    logged and the provider is skipped — matches the F1 discovery isolation
    contract: a broken plugin must not take siblings down.
    """
    registry: dict[str, Workflow] = {}

    for module_id, provider in providers.items():
        try:
            wf_provider = provider.workflow_provider()
        except Exception as exc:
            logger.exception(
                "copilot.workflow.provider_accessor_failed",
                module_id=module_id,
                error=str(exc),
            )
            continue

        if wf_provider is None:
            continue

        try:
            workflows = list(wf_provider.workflows())
        except Exception as exc:
            logger.exception(
                "copilot.workflow.workflows_call_failed",
                module_id=module_id,
                error=str(exc),
            )
            continue

        for wf in workflows:
            if wf.id in registry:
                msg = (
                    f"Duplicate workflow id {wf.id!r}: registered twice — first provider, second provider {module_id!r}"
                )
                raise WorkflowRegistryError(msg)
            registry[wf.id] = wf

    return registry

"""F6 — declarative ``Workflow`` engine + registry.

Hosts the deterministic Python state-machine executor (``engine.py``) and the
provider-discovery aggregator (``registry.py``). The package is intentionally
agnostic: it imports nothing from business modules — providers register their
own workflows via ``WorkflowProvider.workflows()`` and the registry collects
them at boot.

[COPILOT-WORKFLOW-F6]
"""

from luana_core_copilot.application.workflows.engine import (
    WorkflowEngine,
    WorkflowExecutionError,
)
from luana_core_copilot.application.workflows.registry import (
    WorkflowRegistryError,
    collect_workflows,
)

__all__ = (
    "WorkflowEngine",
    "WorkflowExecutionError",
    "WorkflowRegistryError",
    "collect_workflows",
)

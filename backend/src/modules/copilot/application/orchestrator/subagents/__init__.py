"""Sub-agents spawned by the deep agent harness via the built-in ``task`` tool.

F2 shipped the dummy ``audit_inspector`` (plumbing only). F4 added the real
``url_analyzer`` (URL contextual scratchpad). F5 adds ``data_query``
(``ask_tenant_data`` subgraph).
"""

from src.modules.copilot.application.orchestrator.subagents.audit_inspector import (
    AUDIT_INSPECTOR_SUBAGENT,
)
from src.modules.copilot.application.orchestrator.subagents.data_query import (
    DATA_QUERY_SUBAGENT,
)
from src.modules.copilot.application.orchestrator.subagents.url_analyzer import (
    URL_ANALYZER_SUBAGENT,
)

__all__ = [
    "AUDIT_INSPECTOR_SUBAGENT",
    "DATA_QUERY_SUBAGENT",
    "URL_ANALYZER_SUBAGENT",
]

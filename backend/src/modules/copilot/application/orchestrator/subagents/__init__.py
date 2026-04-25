"""Sub-agents spawned by the deep agent harness via the built-in ``task`` tool.

F2 shipped the dummy ``audit_inspector`` (plumbing only). F4 adds the
real ``url_analyzer`` (URL contextual scratchpad). F5 will add
``data_query``.
"""

from src.modules.copilot.application.orchestrator.subagents.audit_inspector import (
    AUDIT_INSPECTOR_SUBAGENT,
)
from src.modules.copilot.application.orchestrator.subagents.url_analyzer import (
    URL_ANALYZER_SUBAGENT,
)

__all__ = ["AUDIT_INSPECTOR_SUBAGENT", "URL_ANALYZER_SUBAGENT"]

"""Sub-agents spawned by the deep agent harness via the built-in ``task`` tool.

F2 ships a dummy ``audit_inspector`` for plumbing only. F4 and F5 replace
it with real ``url_analyzer`` / ``data_query`` subagents.
"""

from src.modules.copilot.application.orchestrator.subagents.audit_inspector import (
    AUDIT_INSPECTOR_SUBAGENT,
)

__all__ = ["AUDIT_INSPECTOR_SUBAGENT"]

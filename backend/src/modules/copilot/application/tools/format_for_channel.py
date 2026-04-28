"""F7 — ``format_for_channel`` transversal tool (back-compat shim → S5 shared).

Post-S5 (2026-04-28) la implementación canónica vive en
``src/shared/agent_observability/channels/format_for_channel.py``. Este
módulo re-exporta el ``@tool`` decorado y la función pure-Python para no
romper consumers (`copilot/application/tools/registry.py`,
`copilot/application/orchestrator/output_sanitizer.py`).

# [COPILOT-CHANNEL-FORMATTER-F7] -> docs/domains/copilot/redesign-2026-04/phases/F7-channel-formatter.md
# [SALES-AGENT-CHANNEL-REGISTRY-S5] -> docs/domains/sales-agent/redesign-2026-04/phases/S5-channel-registry.md
"""

from __future__ import annotations

from src.shared.agent_observability.channels.format_for_channel import (
    format_for_channel,
    format_for_channel_impl,
)

__all__ = ("format_for_channel", "format_for_channel_impl")

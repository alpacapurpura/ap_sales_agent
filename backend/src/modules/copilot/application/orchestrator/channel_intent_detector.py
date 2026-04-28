"""FP2 — channel intent detection (back-compat shim → S5 shared SSoT).

Post-S5 (2026-04-28) la implementación canónica vive en
``src/shared/agent_observability/channels/intent_detector.py``. Este módulo
re-exporta los símbolos públicos para mantener consumers
(`output_sanitizer.py`, `chat.py`).

# [COPILOT-CHANNEL-FORMATTER-F7]
# [SALES-AGENT-CHANNEL-REGISTRY-S5]
"""

from __future__ import annotations

from src.shared.agent_observability.channels.intent_detector import (
    ChannelIntent,
    detect_channel_in_user_msg,
    detect_channel_intent,
)

__all__ = (
    "ChannelIntent",
    "detect_channel_in_user_msg",
    "detect_channel_intent",
)

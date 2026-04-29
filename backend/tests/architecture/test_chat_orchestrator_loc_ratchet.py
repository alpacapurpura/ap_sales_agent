"""Architectural fitness: ChatOrchestrator LOC ratchet (S11B Definition of Done).

After the Strangler Fig decomposition, ``chat.py`` should stay under
~400 LOC — anything larger means a new responsibility has crept into the
facade and should be carved out into a dedicated collaborator
(:class:`AuditEmitter`, :class:`IdentityResolver`,
:class:`ConversationPipeline`, or a new sibling).

Threshold is shrink-only: lower it when a sibling absorbs more.

# [SALES-AGENT-CHAT-LOC-RATCHET-S11B] -> docs/domains/sales-agent/redesign-2026-04/phases/
# S11-shared-lift-orchestrator-decomp.md
"""

from __future__ import annotations

from pathlib import Path

CHAT_PY = (
    Path(__file__).resolve().parents[2] / "src" / "modules" / "sales_agent" / "application" / "orchestrator" / "chat.py"
)

# Frozen at S11B close (2026-04-28). Shrink-only — bumping requires
# explicit decision in the commit message.
CHAT_LOC_CEILING: int = 400


def test_chat_orchestrator_under_loc_ceiling() -> None:
    """``chat.py`` stays a thin facade. Ceiling 400 LOC (S11B DoD §8)."""
    assert CHAT_PY.exists(), f"chat.py not found at {CHAT_PY}"
    line_count = sum(1 for _ in CHAT_PY.read_text(encoding="utf-8").splitlines())
    assert line_count <= CHAT_LOC_CEILING, (
        f"chat.py has {line_count} LOC (ceiling {CHAT_LOC_CEILING}). "
        "Strangler Fig: extract a new collaborator instead of growing the facade. "
        "If the new shape is intentional, lower the ceiling — never raise it."
    )

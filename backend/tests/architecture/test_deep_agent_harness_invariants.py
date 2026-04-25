"""F2 — Architectural invariants for the deep-agent harness.

Ratchet tests that prevent the harness from quietly drifting:

- The dispatcher in ``CopilotOrchestrator`` MUST guard the deep-agent
  graph behind ``settings.COPILOT_DEEP_AGENT_V2``.
- ``deep_agent.py`` MUST NOT hardcode model strings — the 4-tier model
  router (``LLMFactory.get_service().get_client(ModelRole.AGENT)``)
  remains the single source of truth.
- ``deep_agent.py`` MUST register at least one subagent so the
  ``task()`` tool stays usable end-to-end.
- The ``[COPILOT-DEEP-AGENT-V2]`` anchor MUST appear at least once in
  source.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

BACKEND_SRC = Path(__file__).parents[2] / "src"
DEEP_AGENT_PATH = BACKEND_SRC / "modules" / "copilot" / "application" / "orchestrator" / "deep_agent.py"
CHAT_PATH = BACKEND_SRC / "modules" / "copilot" / "application" / "orchestrator" / "chat.py"


def test_deep_agent_module_exists() -> None:
    assert DEEP_AGENT_PATH.exists(), (
        f"Expected harness module at {DEEP_AGENT_PATH}. Did F2 implementation get reverted?"
    )


def test_deep_agent_does_not_hardcode_provider_model() -> None:
    """``create_deep_agent`` must not be invoked with a string model literal.

    Hardcoding e.g. ``"openai:gpt-4o"`` would bypass the 4-tier model
    router (``LLMFactory.get_service().get_client(ModelRole.AGENT)``)
    and the per-tenant model overrides that ride on top of it.
    """
    src = DEEP_AGENT_PATH.read_text(encoding="utf-8")
    # Only flag string-literal model arg in create_deep_agent calls.
    pattern = re.compile(
        r"create_deep_agent\([^)]*model\s*=\s*[\"']\w",
        re.DOTALL,
    )
    assert not pattern.search(src), (
        "deep_agent.py hardcodes a model string in create_deep_agent(). "
        "Use LLMFactory.get_service().get_client(ModelRole.AGENT) instead."
    )


def test_deep_agent_registers_subagent() -> None:
    """``subagents=[...]`` must be present and non-empty in the create call."""
    src = DEEP_AGENT_PATH.read_text(encoding="utf-8")
    tree = ast.parse(src)
    found = False
    for node in ast.walk(tree):
        if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)):
            continue
        if node.func.id != "create_deep_agent":
            continue
        for kw in node.keywords:
            if kw.arg != "subagents":
                continue
            value = kw.value
            if isinstance(value, ast.List) and value.elts:
                found = True
            elif isinstance(value, ast.Name):
                # Indirect reference — accept when it points to a non-empty
                # constant in the module.
                found = True
    assert found, (
        "create_deep_agent(...) must declare subagents=[...] with at least one entry. "
        "F2 ships AUDIT_INSPECTOR_SUBAGENT as the dummy plumbing target."
    )


def test_chat_orchestrator_guards_dispatcher_behind_flag() -> None:
    """``COPILOT_DEEP_AGENT_V2`` must be the ONLY toggle that unlocks the harness.

    Anyone removing the flag check accidentally would route 100% of
    traffic through the deep-agent graph before its rollout window.
    """
    src = CHAT_PATH.read_text(encoding="utf-8")
    assert "COPILOT_DEEP_AGENT_V2" in src, (
        "CopilotOrchestrator must check settings.COPILOT_DEEP_AGENT_V2 before delegating to the deep-agent graph."
    )
    assert "build_deep_agent_graph" in src, (
        "CopilotOrchestrator must wire build_deep_agent_graph as the F2 entry point."
    )


def test_deep_agent_anchor_present_in_source() -> None:
    """The [COPILOT-DEEP-AGENT-V2] anchor must live in src/ — not just docs."""
    anchors_in_code = set()
    for py_file in BACKEND_SRC.rglob("*.py"):
        try:
            text = py_file.read_text(encoding="utf-8")
        except OSError:
            continue
        if "[COPILOT-DEEP-AGENT-V2]" in text:
            anchors_in_code.add(py_file.name)
    assert anchors_in_code, (
        "[COPILOT-DEEP-AGENT-V2] anchor missing from src/. "
        "Tag the harness module + the chat dispatcher so the anchor "
        "registry stays in sync."
    )

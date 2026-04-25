"""F5 — invariants for the ``data_query`` subagent + pipeline.

These are not unit tests of behaviour (covered by ``tests/modules/copilot/
test_ask_tenant_data_*``); they enforce structural rules so a refactor cannot
silently widen the subagent's permissions.
"""

from __future__ import annotations

import ast
from pathlib import Path

from src.modules.copilot.application.orchestrator.subagents import (
    DATA_QUERY_SUBAGENT,
)
from src.modules.copilot.application.tools.ask_tenant_data import ask_tenant_data
from src.modules.copilot.application.tools.registry import (
    ALWAYS_AVAILABLE_GROUPS,
    TOOL_GROUPS,
)

PIPELINE_DIR = Path(__file__).parents[2] / "src" / "modules" / "copilot" / "application" / "tools" / "ask_tenant_data"


def test_subagent_has_only_ask_tenant_data_tool() -> None:
    """No mutations / extraction tools may leak into the subagent's toolset."""
    tools = DATA_QUERY_SUBAGENT.get("tools")
    assert tools is not None, "DATA_QUERY_SUBAGENT must declare tools= explicitly"
    names = [t.name for t in tools]
    assert names == ["ask_tenant_data"]


def test_subagent_has_required_typeddict_fields() -> None:
    assert DATA_QUERY_SUBAGENT["name"] == "data_query"
    assert "description" in DATA_QUERY_SUBAGENT
    assert "system_prompt" in DATA_QUERY_SUBAGENT
    # Ensure prompt is non-trivial — guards against accidental wipe.
    assert len(DATA_QUERY_SUBAGENT["system_prompt"]) > 200


def test_data_query_group_registered_in_tool_groups() -> None:
    assert "data_query" in TOOL_GROUPS
    group = TOOL_GROUPS["data_query"]
    names = [t.name for t in group]
    assert "ask_tenant_data" in names


def test_data_query_group_in_always_available() -> None:
    """A user can ask Q&A from any screen — group must bind on every route."""
    assert "data_query" in ALWAYS_AVAILABLE_GROUPS


def test_ask_tenant_data_callable() -> None:
    assert ask_tenant_data is not None
    assert hasattr(ask_tenant_data, "name")
    assert ask_tenant_data.name == "ask_tenant_data"


def _imports_in(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    out: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            out.add(node.module)
    return out


def test_pipeline_does_not_import_mutation_tools() -> None:
    """The deterministic pipeline must NOT import any mutation surface."""
    forbidden = (
        "src.modules.copilot.application.tools.mutations",
        "src.modules.copilot.application.tools.extraction_tools",
    )
    for py in PIPELINE_DIR.glob("*.py"):
        imports = _imports_in(py)
        for f in forbidden:
            assert f not in imports, f"{py.name} unexpectedly imports {f}"


def test_pipeline_does_not_import_other_module_repos() -> None:
    """Cross-module repo imports stay behind the DataAccessProvider port.

    Pipeline files may import ``src.modules.copilot...`` (own module) but
    NOT ``src.modules.{offer,crm,brand,...}`` directly — that would bump
    the cross-module ratchet without going through the port.
    """
    for py in PIPELINE_DIR.glob("*.py"):
        imports = _imports_in(py)
        for module_path in imports:
            if module_path.startswith("src.modules.") and not module_path.startswith(
                "src.modules.copilot",
            ):
                msg = (
                    f"{py.name} imports {module_path} directly. Cross-module reads must go through DataAccessProvider."
                )
                raise AssertionError(msg)

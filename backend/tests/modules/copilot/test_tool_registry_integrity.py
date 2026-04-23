"""Arch test: TOOL_GROUPS must not silently override tools with the same name.

Prior behavior: registry deduped via `if t.name not in seen` → the second
occurrence of a tool name was dropped silently. That hid bugs such as two
groups both exporting a tool called `clarify` with divergent behavior.

Contract: every tool name is unique across *all* groups, except when the
same tool **object** is intentionally re-exported (e.g. clarify lives in
SHARED_TOOLS and is re-exported in INTERVIEW_TOOLS via shim). Different
objects with the same name must raise.
"""

from __future__ import annotations

import pytest


def _iter_named_tools():
    from src.modules.copilot.application.tools.registry import TOOL_GROUPS

    for group_name, tools in TOOL_GROUPS.items():
        for t in tools:
            yield group_name, t.name, id(t), t


class TestToolRegistryIntegrity:
    def test_no_divergent_name_collisions(self) -> None:
        """Two *different* tool objects sharing a name is a bug."""
        seen: dict[str, tuple[str, int]] = {}
        collisions: list[str] = []
        for group_name, name, obj_id, _tool in _iter_named_tools():
            prior = seen.get(name)
            if prior is not None and prior[1] != obj_id:
                collisions.append(
                    f"{name!r}: in {prior[0]!r} (id={prior[1]}) and {group_name!r} (id={obj_id})",
                )
            else:
                seen.setdefault(name, (group_name, obj_id))
        assert not collisions, "Tool name collisions with divergent objects:\n" + "\n".join(
            collisions,
        )

    def test_register_tool_groups_enforces_uniqueness(self) -> None:
        """`register_tool_groups` raises on divergent same-name collisions."""
        from langchain_core.tools import tool as lc_tool

        from src.modules.copilot.application.tools.registry import (
            ToolNameCollisionError,
            _register_tool_groups,
        )

        @lc_tool
        def my_tool_a(x: str) -> str:
            """Placeholder."""
            return x

        @lc_tool
        def my_tool_b(x: str) -> str:  # pragma: no cover — would execute only if bound
            """Placeholder."""
            return x

        # Same name, different objects → must raise.
        my_tool_b.name = my_tool_a.name  # force collision
        with pytest.raises(ToolNameCollisionError):
            _register_tool_groups({"g1": [my_tool_a], "g2": [my_tool_b]})

    def test_register_tool_groups_allows_reexport(self) -> None:
        """Re-exporting the *same* tool object across groups is fine."""
        from langchain_core.tools import tool as lc_tool

        from src.modules.copilot.application.tools.registry import (
            _register_tool_groups,
        )

        @lc_tool
        def reexported(x: str) -> str:
            """Placeholder."""
            return x

        # Same object under two groups — must not raise.
        _register_tool_groups({"g1": [reexported], "g2": [reexported]})

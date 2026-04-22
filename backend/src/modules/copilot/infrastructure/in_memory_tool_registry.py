"""InMemoryToolRegistry — dict-backed ToolRegistry implementation.

See CONTRACT §18.3.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.modules.copilot.domain.tools.tool_descriptor import (
        ToolCategory,
        ToolDescriptor,
    )


class InMemoryToolRegistry:
    """Dict-backed plugin tool registry."""

    def __init__(self) -> None:
        """Start empty."""
        self._tools: dict[str, ToolDescriptor] = {}

    def register(self, descriptor: ToolDescriptor) -> None:
        """Register a tool. Raises on duplicate name."""
        if descriptor.name in self._tools:
            msg = f"duplicate tool name: {descriptor.name}"
            raise ValueError(msg)
        self._tools[descriptor.name] = descriptor

    def get(self, name: str) -> ToolDescriptor | None:
        """Return descriptor by name or None."""
        return self._tools.get(name)

    def all(self) -> list[ToolDescriptor]:
        """Return every registered descriptor."""
        return list(self._tools.values())

    def by_category(self, category: ToolCategory) -> list[ToolDescriptor]:
        """Return descriptors filtered by category."""
        return [t for t in self._tools.values() if t.category == category]

    def for_route(self, route: str | None) -> list[ToolDescriptor]:
        """Return tools bound to ``route`` (prefix match) or route-agnostic tools."""
        matches: list[ToolDescriptor] = []
        for tool in self._tools.values():
            if not tool.routes:
                matches.append(tool)
                continue
            if route is None:
                continue
            if any(route.startswith(prefix) for prefix in tool.routes):
                matches.append(tool)
        return matches

    def for_procedure(self, procedure_id: str) -> list[ToolDescriptor]:
        """Return tools attached to ``procedure_id``."""
        return [t for t in self._tools.values() if procedure_id in t.procedure_ids]

    def for_skill(self, skill_name: str) -> list[ToolDescriptor]:
        """Return tools attached to ``skill_name``."""
        return [t for t in self._tools.values() if skill_name in t.skill_names]

    def clear(self) -> None:
        """Reset — used in tests. Not part of the Protocol surface."""
        self._tools.clear()

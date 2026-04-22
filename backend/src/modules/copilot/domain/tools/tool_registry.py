"""ToolRegistry — protocol for the plugin tool registry.

See CONTRACT §18.3.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from src.modules.copilot.domain.tools.tool_descriptor import (
        ToolCategory,
        ToolDescriptor,
    )


@runtime_checkable
class ToolRegistry(Protocol):
    """Port for the plugin tool registry."""

    def register(self, descriptor: ToolDescriptor) -> None:
        """Register a tool descriptor. Raises on duplicate name."""
        ...

    def get(self, name: str) -> ToolDescriptor | None:
        """Return the tool descriptor by name (or None if absent)."""
        ...

    def all(self) -> list[ToolDescriptor]:
        """Return all registered tools."""
        ...

    def by_category(self, category: ToolCategory) -> list[ToolDescriptor]:
        """Return tools filtered by category."""
        ...

    def for_route(self, route: str | None) -> list[ToolDescriptor]:
        """Return tools bound to the given route prefix (or any-route tools)."""
        ...

    def for_procedure(self, procedure_id: str) -> list[ToolDescriptor]:
        """Return tools attached to a specific procedure."""
        ...

    def for_skill(self, skill_name: str) -> list[ToolDescriptor]:
        """Return tools available only when the given skill is active."""
        ...

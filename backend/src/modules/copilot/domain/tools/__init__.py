"""Copilot tool plugin domain types (descriptors + registry protocol)."""

from src.modules.copilot.domain.tools.tool_descriptor import (
    ToolCategory,
    ToolDescriptor,
)
from src.modules.copilot.domain.tools.tool_registry import ToolRegistry

__all__ = ["ToolCategory", "ToolDescriptor", "ToolRegistry"]

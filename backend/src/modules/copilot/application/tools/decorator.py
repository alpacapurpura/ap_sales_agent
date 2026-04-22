"""@copilot_tool decorator — register tools as ToolDescriptor plugins at import time.

See CONTRACT §18.2.

Usage::

    @copilot_tool(
        name="navigate_to_page",
        description="Navigate the user to a page in the app.",
        category="builtin",
        routes=("brand-studio", "offer-studio"),
        ui_action_types=("navigate",),
    )
    @tool  # langchain
    def navigate_to_page(keyword: str) -> str:
        ...

Import the module once at boot and the tool self-registers in
``GLOBAL_TOOL_REGISTRY``.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import TypeVar

from src.modules.copilot.domain.tools.tool_descriptor import (
    ToolCategory,
    ToolDescriptor,
)
from src.modules.copilot.infrastructure.in_memory_tool_registry import (
    InMemoryToolRegistry,
)

F = TypeVar("F", bound=Callable[..., object])

# Process-global registry populated at import time. Re-exported from
# ``application/tools/__init__.py`` for consumers.
GLOBAL_TOOL_REGISTRY = InMemoryToolRegistry()


def copilot_tool(
    *,
    name: str,
    description: str,
    category: ToolCategory = "builtin",
    routes: tuple[str, ...] = (),
    required_scopes: tuple[str, ...] = (),
    procedure_ids: tuple[str, ...] = (),
    skill_names: tuple[str, ...] = (),
    provider: str | None = None,
    dangerous: bool = False,
    ui_action_types: tuple[str, ...] = (),
) -> Callable[[F], F]:
    """Register a function as a copilot tool plugin.

    The decorator does NOT wrap the underlying function — it only builds a
    :class:`ToolDescriptor` and registers it in :data:`GLOBAL_TOOL_REGISTRY`.
    Intended to be combined with LangChain's ``@tool`` decorator, which
    should be applied **closer to the function** (lower in the stack) so
    this decorator sees the already-wrapped LangChain tool object::

        @copilot_tool(name="foo", description="…", category="builtin")
        @tool
        def foo(arg: str) -> str: ...
    """

    def _decorator(func: F) -> F:
        descriptor = ToolDescriptor(
            name=name,
            description=description,
            category=category,
            routes=routes,
            required_scopes=required_scopes,
            procedure_ids=procedure_ids,
            skill_names=skill_names,
            provider=provider,
            dangerous=dangerous,
            ui_action_types=ui_action_types,
            handler=func,
        )
        GLOBAL_TOOL_REGISTRY.register(descriptor)
        return func

    return _decorator

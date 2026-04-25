"""Port interfaces for the copilot domain.

All are Protocol classes — pure Python, no concrete imports from
infrastructure or api layers.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable
from uuid import UUID

from src.modules.copilot.domain.model_tier import ModelTier
from src.modules.copilot.domain.procedure_state import ProcedureState

if TYPE_CHECKING:
    from collections.abc import AsyncIterator, Sequence

# ── LLM provider ────────────────────────────────────────────────────────────


@dataclass(frozen=True, slots=True)
class LLMMessage:
    """A single message in an LLM conversation."""

    role: str
    content: str
    name: str | None = None
    tool_call_id: str | None = None


@dataclass(frozen=True, slots=True)
class LLMEvent:
    """One chunk of a streamed LLM response.

    ``kind`` is one of: "text" | "tool_start" | "tool_result" | "usage" |
    "done" | "error". ``data`` is kind-specific and JSON-serializable.
    """

    kind: str
    data: dict[str, Any]


@runtime_checkable
class LLMProvider(Protocol):
    """Abstraction over LLM API (OpenAI, Anthropic, etc.)."""

    async def complete(
        self,
        *,
        tier: ModelTier,
        messages: list[LLMMessage],
        tools: list[dict[str, Any]] | None = None,
        stream: bool = True,
    ) -> AsyncIterator[LLMEvent]:
        """Stream LLM completion events for the given tier and messages."""
        ...


# ── Conversation store ───────────────────────────────────────────────────────


@dataclass(frozen=True, slots=True)
class ConversationPage:
    """Cursor-paginated conversation list."""

    items: list[ConversationSummaryVO]
    next_cursor: str | None


@dataclass(frozen=True, slots=True)
class ConversationSummaryVO:
    """Value object representing one row in the conversation history list."""

    id: UUID
    title: str | None
    updated_at: Any
    message_count: int
    total_tokens: int
    last_tier_used: ModelTier | None
    has_procedure: bool
    procedure_progress: float | None
    title_auto_generated: bool
    archived_at: Any | None


@runtime_checkable
class ConversationStore(Protocol):
    """Port for accessing and mutating conversations."""

    async def list(
        self,
        *,
        tenant_id: UUID,
        user_id: UUID,
        limit: int = 6,
        cursor: str | None = None,
        include_archived: bool = False,
    ) -> ConversationPage:
        """Return a cursor-paginated page of conversations for the user."""
        ...

    async def get(
        self,
        *,
        tenant_id: UUID,
        user_id: UUID,
        conversation_id: UUID,
    ) -> ConversationSummaryVO | None:
        """Fetch one conversation summary (or None if missing)."""
        ...

    async def create(
        self,
        *,
        tenant_id: UUID,
        user_id: UUID,
        title: str | None = None,
    ) -> ConversationSummaryVO:
        """Create a new empty conversation and return its summary."""
        ...

    async def append(
        self,
        *,
        tenant_id: UUID,
        conversation_id: UUID,
        message: LLMMessage,
        tier_used: ModelTier,
        tokens_added: int,
    ) -> None:
        """Append a message to the conversation and update aggregate counters."""
        ...

    async def update_summary(
        self,
        *,
        tenant_id: UUID,
        conversation_id: UUID,
        summary: str,
    ) -> None:
        """Persist a new rolling summary for the conversation."""
        ...

    async def update_title(
        self,
        *,
        tenant_id: UUID,
        conversation_id: UUID,
        title: str,
        auto_generated: bool,
    ) -> ConversationSummaryVO:
        """Persist a new title for the conversation."""
        ...

    async def archive(
        self,
        *,
        tenant_id: UUID,
        user_id: UUID,
        conversation_id: UUID,
    ) -> ConversationSummaryVO:
        """Soft-delete the conversation and return its updated summary."""
        ...

    async def update_procedure_state(
        self,
        *,
        tenant_id: UUID,
        conversation_id: UUID,
        procedure_state: ProcedureState | None,
    ) -> None:
        """Persist the procedure state attached to the conversation."""
        ...


# ── Tool registry ────────────────────────────────────────────────────────────


@dataclass(frozen=True, slots=True)
class CopilotContext:
    """Runtime context passed from the frontend to tool selection."""

    current_route: str | None
    selected_fields: list[dict[str, str]]
    form_data: dict[str, Any]
    locale: str
    procedure_state: ProcedureState | None = None


@runtime_checkable
class ToolRegistry(Protocol):
    """Port for selecting tools based on current context."""

    def get_tools_for_context(self, ctx: CopilotContext) -> list[Any]:
        """Return the ordered list of tools available for the given context."""
        ...


# ── Identity provider ────────────────────────────────────────────────────────


@dataclass(frozen=True, slots=True)
class UserPrincipal:
    """Authenticated user identity."""

    user_id: UUID
    tenant_id: UUID


@runtime_checkable
class IdentityProvider(Protocol):
    """Port for resolving the current authenticated user."""

    async def current_user(self) -> UserPrincipal:
        """Return the authenticated user principal."""
        ...

    async def tenant_id_for(self, user_id: UUID) -> UUID:
        """Resolve the tenant id for the given user id."""
        ...


# ── Module providers (F1 — provider pattern) ────────────────────────────────
#
# Each business module (brand, offer, landing, analytics, crm, connections, …)
# exposes a ``CopilotProvider`` so the copilot can absorb its tools, workflows,
# living summary and per-route system-prompt fragments without importing the
# module directly. Discovery (``application/discovery.py``) wires providers at
# startup; refactor of any module's copilot surface stays inside the module.


@dataclass(frozen=True, slots=True)
class ModuleData:
    """Static metadata + read-side accessors a module exposes to the copilot.

    Replaces the inline ``ModuleDescriptor`` that lived in
    ``copilot/domain/module_registry.py``: the field shape is preserved so the
    legacy registry can be derived from providers without changes downstream.
    """

    module_id: str
    label: str
    description: str
    route_prefix: str
    model_class: type | None = None
    repo_factory: Callable[..., Any] | None = None
    read_fn: Callable[..., Any] | None = None
    keywords: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class ProviderRoute:
    """Declares which tool groups a provider participates in for a route.

    The discovery layer aggregates ``ProviderRoute`` entries across all
    providers to build the runtime ``ROUTE_TOOL_MAP``. Multiple providers may
    contribute to the same route prefix (groups merged in declaration order).
    """

    prefix: str
    groups: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ProviderHealth:
    """Health snapshot for one provider — surfaced in admin and Sentry."""

    module_id: str
    last_error: str | None = None
    last_loaded_at: Any = None  # ISO-8601 string or datetime; opaque to ports

    @property
    def healthy(self) -> bool:
        """``True`` when the provider loaded without error."""
        return self.last_error is None


# F6 — full Workflow declarative model lives in ``domain/workflow.py``. Ports
# re-exports it so existing imports (``from src.modules.copilot.domain.ports
# import Workflow``) keep working without a churn touch in every provider.
from src.modules.copilot.domain.workflow import Workflow as Workflow  # noqa: PLC0414, TC001


@runtime_checkable
class ToolProvider(Protocol):
    """Tools the module contributes to the copilot, grouped by category.

    ``tool_groups()`` returns a mapping ``{group_name: [BaseTool, ...]}`` and
    feeds the existing ``TOOL_GROUPS`` registry. ``tools()`` is a flat alias
    used by tests and the admin overview.
    """

    def tool_groups(self) -> Mapping[str, Sequence[Any]]:
        """Return named tool groups exposed by this module."""
        ...

    def tools(self) -> Sequence[Any]:
        """Return the flat tool list (deduplicated by ``tool.name``)."""
        ...


@runtime_checkable
class WorkflowProvider(Protocol):
    """Declarative multi-step flows (F6 wires this end-to-end)."""

    def workflows(self) -> Sequence[Workflow]:
        """Return workflows registered by this module."""
        ...


@runtime_checkable
class SummaryProvider(Protocol):
    """Living summary injected into the system prompt (F3 powers brand)."""

    async def summary(self, *, tenant_id: UUID) -> str | None:
        """Return the latest module summary for ``tenant_id`` or ``None``."""
        ...


@runtime_checkable
class ContextInjector(Protocol):
    """Per-route system prompt fragment supplied by the module."""

    async def inject_for(
        self,
        *,
        target_route: str,
        tenant_id: UUID,
    ) -> str | None:
        """Return a system-prompt fragment for ``target_route`` or ``None``."""
        ...


# ── DataAccessProvider (F5 — ask_tenant_data subgraph) ─────────────────────────


@dataclass(frozen=True, slots=True)
class DataQueryPlan:
    """Structured query the ask_tenant_data pipeline dispatches to providers.

    ``kind`` matches the intent classifier output (``offer_lookup``,
    ``lead_count``, ``conversation_count``…). ``filters`` is provider-specific
    payload (e.g. ``{"name_query": "...", "status": "active", "since": ...}``).
    """

    kind: str
    filters: Mapping[str, Any] = field(default_factory=dict)
    limit: int = 20


@dataclass(frozen=True, slots=True)
class DataQueryResult:
    """Result returned by a ``DataAccessProvider`` execution.

    ``rows`` carry the records the synthesizer formats; ``metadata`` carries
    aggregate counters / state flags consumed by the state_check stage.
    """

    rows: list[dict[str, Any]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@runtime_checkable
class DataAccessProvider(Protocol):
    """Read-only data accessor a module exposes to the ask_tenant_data tool.

    Each provider declares which ``kind`` values it handles via ``supports``;
    the pipeline dispatches a ``DataQueryPlan`` to the first provider that
    accepts it. This keeps cross-module reads going through the provider port
    (no direct repo imports from ``copilot/`` — preserves the ratchet) and
    enforces tenant isolation at one place per provider.

    The optional ``context`` mapping carries request-scoped collaborators (e.g.
    an open SQLAlchemy ``Session`` under the key ``"db"``). Providers fall back
    to opening their own session when ``context`` is empty so unit tests can
    inject a fixture session without coupling production code to a global.
    """

    def supports(self, kind: str) -> bool:
        """Return ``True`` if this provider handles plans with the given kind."""
        ...

    async def execute(
        self,
        *,
        tenant_id: UUID,
        plan: DataQueryPlan,
        context: Mapping[str, Any] | None = None,
    ) -> DataQueryResult:
        """Run the plan against the module's read side and return the result."""
        ...


@runtime_checkable
class CopilotProvider(Protocol):
    """Root provider every module implements to plug into the copilot.

    Discovery loads providers from two sources (in this order):
      1. Convention scan of ``src.modules.{name}.copilot_provider`` (in-repo).
      2. ``importlib.metadata`` entry points in group
         ``nicolify.copilot_providers`` (external plugins).

    All sub-port accessors return ``None`` when the module does not expose
    that capability (e.g. ``analytics`` has no ``summary_provider`` yet).
    """

    @property
    def module_id(self) -> str:
        """Stable id used as registry key (``brand``, ``offer``, …)."""
        ...

    @property
    def label(self) -> str:
        """Human-readable label shown in admin + system prompts."""
        ...

    def module_data(self) -> ModuleData | None:
        """Return module metadata or ``None`` if the module isn't introspectable."""
        ...

    def routes(self) -> Sequence[ProviderRoute]:
        """Return the routes this provider participates in."""
        ...

    def tool_provider(self) -> ToolProvider | None:
        """Return the module's tool provider or ``None``."""
        ...

    def workflow_provider(self) -> WorkflowProvider | None:
        """Return the module's workflow provider or ``None`` (F6+)."""
        ...

    def summary_provider(self) -> SummaryProvider | None:
        """Return the module's summary provider or ``None`` (F3+)."""
        ...

    def context_injector(self) -> ContextInjector | None:
        """Return the module's context injector or ``None`` (F3+)."""
        ...

    def data_access(self) -> DataAccessProvider | None:
        """Return the module's data access provider or ``None`` (F5+)."""
        ...


class BaseCopilotProvider:
    """Convenience base class implementing safe ``CopilotProvider`` defaults.

    Every sub-port returns ``None``; ``routes()`` returns an empty tuple. A
    concrete provider only overrides what it actually exposes — typically
    ``module_id``, ``label`` and ``module_data()``. Subclasses still satisfy
    the structural ``CopilotProvider`` Protocol; the class is a contract
    helper, not a runtime requirement.
    """

    @property
    def module_id(self) -> str:
        """Stable id used as registry key. Subclasses MUST override."""
        msg = "Concrete CopilotProvider must override module_id"
        raise NotImplementedError(msg)

    @property
    def label(self) -> str:
        """Human-readable label. Subclasses MUST override."""
        msg = "Concrete CopilotProvider must override label"
        raise NotImplementedError(msg)

    def module_data(self) -> ModuleData | None:
        """Return ``None`` by default — modules without introspectable shape."""
        return None

    def routes(self) -> Sequence[ProviderRoute]:
        """Return an empty tuple by default — modules with no own routes."""
        return ()

    def tool_provider(self) -> ToolProvider | None:
        """Return ``None`` by default — module exposes no domain-specific tools."""
        return None

    def workflow_provider(self) -> WorkflowProvider | None:
        """Return ``None`` by default — module declares no workflows yet (F6)."""
        return None

    def summary_provider(self) -> SummaryProvider | None:
        """Return ``None`` by default — module produces no living summary (F3)."""
        return None

    def context_injector(self) -> ContextInjector | None:
        """Return ``None`` by default — module injects no system-prompt fragment."""
        return None

    def data_access(self) -> DataAccessProvider | None:
        """Return ``None`` by default — module exposes no data_access port (F5)."""
        return None

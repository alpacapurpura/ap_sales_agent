"""F1 — Provider pattern ports contract tests.

Validates the public Protocol surface that every module must satisfy to plug
into the copilot. These tests pin the contract so adding a new sub-port
(or breaking an existing one) is caught before discovery wires anything live.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

import pytest

from src.modules.copilot.domain.ports import (
    ContextInjector,
    CopilotProvider,
    ModuleData,
    ProviderHealth,
    ProviderRoute,
    SummaryProvider,
    ToolProvider,
    Workflow,
    WorkflowProvider,
)

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence


# ── Stubs ──────────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class _StubTool:
    name: str
    description: str = ""


class _StubToolProvider:
    def tool_groups(self) -> Mapping[str, Sequence[object]]:
        return {"brand_section": [_StubTool(name="get_brand")]}

    def tools(self) -> Sequence[object]:
        return [_StubTool(name="get_brand")]


class _StubWorkflowProvider:
    def workflows(self) -> Sequence[Workflow]:
        return ()


class _StubSummaryProvider:
    async def summary(self, *, tenant_id: UUID) -> str | None:
        _ = tenant_id
        return None


class _StubContextInjector:
    async def inject_for(self, *, target_route: str, tenant_id: UUID) -> str | None:
        _ = (target_route, tenant_id)
        return None


class _StubProvider:
    @property
    def module_id(self) -> str:
        return "stub"

    @property
    def label(self) -> str:
        return "Stub Module"

    def module_data(self) -> ModuleData | None:
        return ModuleData(
            module_id="stub",
            label="Stub Module",
            description="A stub for tests",
            route_prefix="stub-studio",
        )

    def routes(self) -> Sequence[ProviderRoute]:
        return (ProviderRoute(prefix="stub-studio", groups=("brand_section",)),)

    def tool_provider(self) -> ToolProvider | None:
        return _StubToolProvider()

    def workflow_provider(self) -> WorkflowProvider | None:
        return _StubWorkflowProvider()

    def summary_provider(self) -> SummaryProvider | None:
        return _StubSummaryProvider()

    def context_injector(self) -> ContextInjector | None:
        return _StubContextInjector()

    def data_access(self) -> object | None:
        # F5 — protocol acquired ``data_access()``; ``None`` keeps the stub
        # opt-out of the ``ask_tenant_data`` dispatcher.
        return None


# ── Protocol compliance ────────────────────────────────────────────────────


class TestProtocolCompliance:
    def test_tool_provider_protocol(self) -> None:
        assert isinstance(_StubToolProvider(), ToolProvider)

    def test_workflow_provider_protocol(self) -> None:
        assert isinstance(_StubWorkflowProvider(), WorkflowProvider)

    def test_summary_provider_protocol(self) -> None:
        assert isinstance(_StubSummaryProvider(), SummaryProvider)

    def test_context_injector_protocol(self) -> None:
        assert isinstance(_StubContextInjector(), ContextInjector)

    def test_root_provider_protocol(self) -> None:
        assert isinstance(_StubProvider(), CopilotProvider)


class TestProviderShape:
    def test_module_id_is_str(self) -> None:
        provider = _StubProvider()
        assert isinstance(provider.module_id, str)
        assert provider.module_id != ""

    def test_label_is_str(self) -> None:
        provider = _StubProvider()
        assert isinstance(provider.label, str)
        assert provider.label != ""

    def test_module_data_returns_typed_record(self) -> None:
        provider = _StubProvider()
        data = provider.module_data()
        assert data is not None
        assert data.module_id == provider.module_id
        assert data.route_prefix
        assert data.label

    def test_routes_returns_sequence_of_provider_route(self) -> None:
        provider = _StubProvider()
        routes = provider.routes()
        assert len(routes) >= 1
        for route in routes:
            assert isinstance(route, ProviderRoute)
            assert route.prefix
            assert isinstance(route.groups, tuple)

    def test_sub_ports_optional_return_none_or_protocol(self) -> None:
        provider = _StubProvider()
        # All sub-port accessors must return either None or a Protocol-compliant object.
        for attr, proto in (
            ("tool_provider", ToolProvider),
            ("workflow_provider", WorkflowProvider),
            ("summary_provider", SummaryProvider),
            ("context_injector", ContextInjector),
        ):
            sub = getattr(provider, attr)()
            assert sub is None or isinstance(sub, proto), f"{attr} broke contract"


class TestModuleDataInvariants:
    def test_module_data_is_frozen(self) -> None:
        data = ModuleData(
            module_id="brand",
            label="Brand Studio",
            description="...",
            route_prefix="brand-studio",
        )
        with pytest.raises((AttributeError, TypeError)):
            data.module_id = "other"  # type: ignore[misc]

    def test_module_data_keywords_default_empty(self) -> None:
        data = ModuleData(
            module_id="brand",
            label="Brand Studio",
            description="...",
            route_prefix="brand-studio",
        )
        assert data.keywords == ()


class TestProviderRouteInvariants:
    def test_route_prefix_is_lowercase(self) -> None:
        route = ProviderRoute(prefix="brand-studio", groups=("brand_section",))
        assert route.prefix == route.prefix.lower()

    def test_groups_is_tuple(self) -> None:
        route = ProviderRoute(prefix="x", groups=("a", "b"))
        assert isinstance(route.groups, tuple)


class TestProviderHealth:
    def test_health_defaults_healthy(self) -> None:
        health = ProviderHealth(module_id="brand")
        assert health.healthy
        assert health.last_error is None

    def test_health_unhealthy_when_error_set(self) -> None:
        health = ProviderHealth(module_id="brand", last_error="boom")
        assert not health.healthy


@pytest.mark.asyncio
class TestSummaryProviderAsync:
    async def test_summary_returns_optional_str(self) -> None:
        sp = _StubSummaryProvider()
        result = await sp.summary(tenant_id=uuid4())
        assert result is None or isinstance(result, str)


@pytest.mark.asyncio
class TestContextInjectorAsync:
    async def test_inject_for_returns_optional_str(self) -> None:
        ci = _StubContextInjector()
        result = await ci.inject_for(target_route="brand-studio", tenant_id=uuid4())
        assert result is None or isinstance(result, str)

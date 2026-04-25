"""F6 — workflow registry aggregator.

``_collect_workflows(providers)`` mirrors the F1 ``_collect_*`` aggregators —
iterates discovered providers, calls their ``WorkflowProvider.workflows()``,
flattens to a single ``{workflow_id: Workflow}`` dict, raises on duplicate ids.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from pydantic import BaseModel

if TYPE_CHECKING:
    from collections.abc import Sequence

from src.modules.copilot.application.workflows.registry import (
    WorkflowRegistryError,
    collect_workflows,
)
from src.modules.copilot.domain.ports import (
    BaseCopilotProvider,
    ContextInjector,
    DataAccessProvider,
    ModuleData,
    SummaryProvider,
    ToolProvider,
    WorkflowProvider,
)
from src.modules.copilot.domain.workflow import (
    Workflow,
    WorkflowNode,
    WorkflowTrigger,
)

if TYPE_CHECKING:
    from src.modules.copilot.domain.ports import CopilotProvider


class _State(BaseModel):
    pass


def _wf(workflow_id: str, *, domain: str = "demo") -> Workflow:
    return Workflow(
        id=workflow_id,
        domain=domain,
        description_es="x",
        trigger=WorkflowTrigger.USER_INTENT,
        nodes=(WorkflowNode(id="only", handler_ref="src.x:y"),),
        state_schema=_State,
        ui_progress_kind="plan_card",
    )


class _StubWorkflowProvider:
    def __init__(self, workflows: Sequence[Workflow]) -> None:
        self._workflows = tuple(workflows)

    def workflows(self) -> Sequence[Workflow]:
        return self._workflows


class _StubProvider(BaseCopilotProvider):
    def __init__(self, module_id_value: str, workflows_value: Sequence[Workflow]) -> None:
        self._module_id = module_id_value
        self._workflows = workflows_value

    @property
    def module_id(self) -> str:
        return self._module_id

    @property
    def label(self) -> str:
        return self._module_id.title()

    def module_data(self) -> ModuleData | None:
        return ModuleData(
            module_id=self._module_id,
            label=self.label,
            description="stub",
            route_prefix=f"{self._module_id}-studio",
        )

    def workflow_provider(self) -> WorkflowProvider | None:
        return _StubWorkflowProvider(self._workflows)

    def tool_provider(self) -> ToolProvider | None:
        return None

    def summary_provider(self) -> SummaryProvider | None:
        return None

    def context_injector(self) -> ContextInjector | None:
        return None

    def data_access(self) -> DataAccessProvider | None:
        return None


class TestCollectWorkflows:
    def test_empty_registry_returns_empty(self) -> None:
        assert collect_workflows({}) == {}

    def test_collects_single_provider(self) -> None:
        providers: dict[str, CopilotProvider] = {
            "brand": _StubProvider("brand", (_wf("setup_brand"),)),
        }
        result = collect_workflows(providers)
        assert "setup_brand" in result
        assert result["setup_brand"].domain == "demo"

    def test_collects_multiple_providers(self) -> None:
        providers: dict[str, CopilotProvider] = {
            "brand": _StubProvider("brand", (_wf("setup_brand"),)),
            "offer": _StubProvider("offer", (_wf("design_offer_from_url"),)),
        }
        result = collect_workflows(providers)
        assert set(result) == {"setup_brand", "design_offer_from_url"}

    def test_provider_without_workflow_provider_skipped(self) -> None:
        class _NoWfProvider(BaseCopilotProvider):
            @property
            def module_id(self) -> str:
                return "x"

            @property
            def label(self) -> str:
                return "X"

            def workflow_provider(self) -> WorkflowProvider | None:
                return None

        providers: dict[str, CopilotProvider] = {"x": _NoWfProvider()}
        assert collect_workflows(providers) == {}

    def test_duplicate_workflow_id_raises(self) -> None:
        providers: dict[str, CopilotProvider] = {
            "brand": _StubProvider("brand", (_wf("dup"),)),
            "offer": _StubProvider("offer", (_wf("dup"),)),
        }
        with pytest.raises(WorkflowRegistryError, match=r"(?i)duplicate"):
            collect_workflows(providers)

    def test_provider_workflow_provider_failure_logged_not_raised(self) -> None:
        class _BoomProvider(BaseCopilotProvider):
            @property
            def module_id(self) -> str:
                return "boom"

            @property
            def label(self) -> str:
                return "Boom"

            def workflow_provider(self) -> WorkflowProvider | None:
                msg = "intentional"
                raise RuntimeError(msg)

        providers: dict[str, CopilotProvider] = {"boom": _BoomProvider()}
        # One provider blowing up MUST NOT take down the rest of the registry.
        # Mirrors how F1 discovery isolates per-provider failures.
        result = collect_workflows(providers)
        assert result == {}


class TestRealProviderIntegration:
    """Integration with real brand + offer providers (after pilots wired)."""

    def test_brand_provider_returns_workflow(self) -> None:
        from src.modules.brand.copilot_provider import provider as brand_provider

        wf_provider = brand_provider.workflow_provider()
        assert wf_provider is not None
        workflows = list(wf_provider.workflows())
        assert len(workflows) >= 1
        ids = {wf.id for wf in workflows}
        assert "setup_brand_minimal" in ids

    def test_offer_provider_returns_workflow(self) -> None:
        from src.modules.offer.copilot_provider import provider as offer_provider

        wf_provider = offer_provider.workflow_provider()
        assert wf_provider is not None
        workflows = list(wf_provider.workflows())
        assert len(workflows) >= 1
        ids = {wf.id for wf in workflows}
        assert "design_offer_from_url" in ids

    def test_brand_workflow_node_handlers_resolvable(self) -> None:
        """Every brand workflow node handler_ref must import successfully."""
        import importlib

        from src.modules.brand.copilot_provider import provider as brand_provider

        wf_provider = brand_provider.workflow_provider()
        assert wf_provider is not None
        for wf in wf_provider.workflows():
            for node in wf.nodes:
                module_path, _, attr = node.handler_ref.partition(":")
                mod = importlib.import_module(module_path)
                assert hasattr(mod, attr), f"{wf.id}/{node.id}: {node.handler_ref} missing"

    def test_offer_workflow_node_handlers_resolvable(self) -> None:
        import importlib

        from src.modules.offer.copilot_provider import provider as offer_provider

        wf_provider = offer_provider.workflow_provider()
        assert wf_provider is not None
        for wf in wf_provider.workflows():
            for node in wf.nodes:
                module_path, _, attr = node.handler_ref.partition(":")
                mod = importlib.import_module(module_path)
                assert hasattr(mod, attr), f"{wf.id}/{node.id}: {node.handler_ref} missing"

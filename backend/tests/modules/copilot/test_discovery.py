"""F1 — Provider discovery tests.

Validates that ``copilot.application.discovery`` builds the provider registry
from two sources:
  1. Convention scan: ``src.modules.{name}.copilot_provider``.
  2. Entry points: ``nicolify.copilot_providers`` group.

Convention takes precedence over entry points so internal modules cannot be
shadowed by an installed plugin with the same ``module_id``.
"""

from __future__ import annotations

import importlib
import sys
from collections.abc import Mapping
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any
from unittest.mock import patch

import pytest

from src.modules.copilot.application import discovery as discovery_mod
from src.modules.copilot.domain.ports import (
    CopilotProvider,
    ModuleData,
    ProviderHealth,
    ProviderRoute,
)

if TYPE_CHECKING:
    from collections.abc import Sequence

# ── Stub providers ─────────────────────────────────────────────────────────


@dataclass(frozen=True)
class _FakeProvider:
    _module_id: str
    _label: str = "Fake"

    @property
    def module_id(self) -> str:
        return self._module_id

    @property
    def label(self) -> str:
        return self._label

    def module_data(self) -> ModuleData | None:
        return ModuleData(
            module_id=self._module_id,
            label=self._label,
            description="...",
            route_prefix=f"{self._module_id}-studio",
        )

    def routes(self) -> Sequence[ProviderRoute]:
        return (ProviderRoute(prefix=f"{self._module_id}-studio", groups=()),)

    def tool_provider(self) -> Any:
        return None

    def workflow_provider(self) -> Any:
        return None

    def summary_provider(self) -> Any:
        return None

    def context_injector(self) -> Any:
        return None


@pytest.fixture(autouse=True)
def _reset_discovery_cache() -> None:
    discovery_mod.reset_discovery()


# ── Convention scan ────────────────────────────────────────────────────────


class TestConventionScan:
    def test_picks_up_in_repo_providers(self) -> None:
        # Real in-repo modules expose `copilot_provider/__init__.py` with `provider`.
        # After F1 migration, brand + offer + at least one shim must be discoverable.
        registry = discovery_mod.discover_providers()
        assert "brand" in registry, "brand provider must be registered after F1"

    def test_returns_protocol_compliant_objects(self) -> None:
        registry = discovery_mod.discover_providers()
        for module_id, provider in registry.items():
            assert isinstance(provider, CopilotProvider), f"{module_id} broke contract"

    def test_module_id_matches_registry_key(self) -> None:
        registry = discovery_mod.discover_providers()
        for module_id, provider in registry.items():
            assert provider.module_id == module_id


# ── Entry points scan ──────────────────────────────────────────────────────


class TestEntryPointsScan:
    def test_entry_points_can_extend_registry(self) -> None:
        """An external plugin via entry_points appears alongside in-repo providers."""
        external = _FakeProvider(_module_id="external_plugin")

        class _FakeEP:
            name = "external_plugin"

            def load(self) -> _FakeProvider:
                return external

        with patch.object(discovery_mod, "_scan_entry_points", return_value={"external_plugin": external}):
            discovery_mod.reset_discovery()
            registry = discovery_mod.discover_providers()
            assert "external_plugin" in registry

    def test_convention_wins_on_collision(self) -> None:
        """If both scans return the same module_id, convention wins."""
        convention_p = _FakeProvider(_module_id="brand", _label="ConventionBrand")
        entry_p = _FakeProvider(_module_id="brand", _label="EntryPointBrand")

        with (
            patch.object(discovery_mod, "_scan_convention", return_value={"brand": convention_p}),
            patch.object(discovery_mod, "_scan_entry_points", return_value={"brand": entry_p}),
        ):
            discovery_mod.reset_discovery()
            registry = discovery_mod.discover_providers()
            assert registry["brand"].label == "ConventionBrand"


# ── Cache + reset ───────────────────────────────────────────────────────────


class TestCacheBehavior:
    def test_discover_is_cached(self) -> None:
        first = discovery_mod.discover_providers()
        second = discovery_mod.discover_providers()
        assert first is second  # singleton via lru_cache

    def test_reset_clears_cache(self) -> None:
        first = discovery_mod.discover_providers()
        discovery_mod.reset_discovery()
        second = discovery_mod.discover_providers()
        # After reset both calls return equivalent dicts but new instances
        assert first == second


# ── Health check ────────────────────────────────────────────────────────────


class TestHealth:
    def test_health_returns_one_entry_per_provider(self) -> None:
        registry = discovery_mod.discover_providers()
        report = discovery_mod.health()
        assert set(report.keys()) == set(registry.keys())

    def test_health_marks_provider_healthy_by_default(self) -> None:
        report = discovery_mod.health()
        for module_id, status in report.items():
            assert isinstance(status, ProviderHealth)
            assert status.module_id == module_id
            # In-repo providers must be healthy on first load.
            assert status.healthy, f"{module_id} unhealthy: {status.last_error}"


# ── Discovery is the only source of truth (no feature flag) ────────────────


class TestNoFeatureFlag:
    def test_discovery_module_does_not_expose_legacy_flag(self) -> None:
        """F1 retired ``COPILOT_DISCOVERY_V2`` — the legacy fallback is gone."""

        assert not hasattr(discovery_mod, "discovery_enabled"), (
            "discovery_enabled() reintroduces a runtime fallback path. F1 closed "
            "this door — to roll back providers, revert the commit instead."
        )

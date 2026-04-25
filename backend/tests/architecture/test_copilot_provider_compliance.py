"""F1 — Architectural fitness: provider pattern compliance.

Three invariants every fase must respect after F1:

1. Every ``src/modules/{name}/copilot_provider/__init__.py`` exports a
   top-level ``provider`` attribute that satisfies the ``CopilotProvider``
   Protocol.
2. Discovery wires every provider correctly (``module_id`` matches the
   registry key, ``module_data`` is consistent).
3. Every module listed in the runtime ``MODULE_REGISTRY`` (i.e. every module
   the copilot can introspect by name) has a ``copilot_provider/`` directory.

Fitness tests live next to ``test_no_new_copilot_module_imports.py`` so the
ratchet and the structural invariants stay in the same review surface.
"""

from __future__ import annotations

from pathlib import Path

from src.modules.copilot.application.discovery import (
    discover_providers,
    health,
    reset_discovery,
)
from src.modules.copilot.domain.module_registry import (
    get_module_registry,
    reset_module_registry_cache,
)
from src.modules.copilot.domain.ports import CopilotProvider

_MODULES_BASE = Path(__file__).resolve().parents[2] / "src" / "modules"


def setup_function() -> None:
    """Reset cached singletons so each test sees a fresh discovery."""

    reset_discovery()
    reset_module_registry_cache()


def test_every_in_repo_provider_satisfies_protocol() -> None:
    """Every discovered provider object satisfies ``CopilotProvider`` Protocol."""

    registry = discover_providers()
    assert registry, "Discovery must surface at least one in-repo provider after F1."
    for module_id, provider in registry.items():
        assert isinstance(provider, CopilotProvider), (
            f"Provider for {module_id!r} does not satisfy CopilotProvider Protocol."
        )


def test_provider_module_id_matches_registry_key() -> None:
    """A provider must self-identify using the same id discovery keyed it under."""

    for module_id, provider in discover_providers().items():
        assert provider.module_id == module_id, (
            f"module_id mismatch: registry key={module_id!r} provider={provider.module_id!r}"
        )


def test_module_registry_built_only_from_providers() -> None:
    """``MODULE_REGISTRY`` must mirror discovered providers' ``module_data()``."""

    descriptors = get_module_registry()
    providers = discover_providers()
    for module_id, descriptor in descriptors.items():
        provider = providers.get(module_id)
        assert provider is not None, f"Descriptor {module_id!r} has no provider."
        data = provider.module_data()
        assert data is not None
        assert descriptor.label == data.label
        assert descriptor.description == data.description
        assert descriptor.route_prefix == data.route_prefix


def test_all_registered_modules_have_copilot_provider_dir() -> None:
    """Every module surfaced through ``MODULE_REGISTRY`` ships a ``copilot_provider/``."""

    for module_id in get_module_registry():
        provider_dir = _MODULES_BASE / module_id / "copilot_provider"
        assert provider_dir.is_dir(), f"{module_id!r} must expose {provider_dir.as_posix()}/."
        init_file = provider_dir / "__init__.py"
        assert init_file.is_file(), f"{module_id!r} provider missing __init__.py."


def test_brand_provider_is_deep_migrated() -> None:
    """F1 pilot: brand provider owns its ``module_data`` builder.

    Verifies the brand-specific lazy loaders left ``copilot/`` and now live in
    ``backend/src/modules/brand/copilot_provider/module_data.py``.
    """

    brand_module_data = _MODULES_BASE / "brand" / "copilot_provider" / "module_data.py"
    assert brand_module_data.is_file(), "Brand provider must own its module_data builder after F1 pilot migration."
    text = brand_module_data.read_text(encoding="utf-8")
    assert "BrandRepository" in text
    assert "BrandSettings" in text
    assert "build_brand_module_data" in text


def test_health_check_reports_healthy_after_load() -> None:
    """Boot-time health: every provider returns healthy after discovery."""

    snapshot = health()
    assert snapshot, "health() must surface at least one provider after F1."
    for module_id, status in snapshot.items():
        assert status.healthy, f"{module_id!r} provider unhealthy: {status.last_error}"

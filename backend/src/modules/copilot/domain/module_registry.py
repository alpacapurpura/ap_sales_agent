"""Module Registry — Single source of truth for modules the copilot can introspect.

[COPILOT-PROVIDER-PATTERN]: as of F1 (April 2026) this registry is fully
provider-driven. Each business module exposes a ``CopilotProvider`` via
``src.modules.{name}.copilot_provider`` and discovery imports them at runtime
without ``copilot/`` referencing the module directly. The legacy hardcoded
``MODULE_REGISTRY`` was retired alongside its lazy loaders — discovery is
the single source of truth.

Each ``ModuleDescriptor`` declares HOW to read a module's data and model
class. The copilot never hardcodes field names; it uses ``model_class`` for
Pydantic introspection and the ``repo_factory`` / ``read_fn`` callables for
data access. Both come from the providing module's ``ModuleData`` record.
"""

from __future__ import annotations

import functools
from collections.abc import Callable
from dataclasses import dataclass, field

from pydantic import BaseModel


@dataclass
class ModuleDescriptor:
    """Metadata describing a module the copilot can read."""

    module_id: str  # "brand", "offer", etc.
    label: str  # "Brand Studio"
    description: str  # Short description for system prompt
    route_prefix: str  # Route segment for matching (e.g. "brand-settings")

    # Optional Pydantic model — enables automatic introspection of sections/fields.
    # Not all modules have a single root model (e.g. analytics uses SQL queries).
    model_class: type[BaseModel] | None = None

    # Factory: (db_session) -> repository_instance
    repo_factory: Callable | None = None

    # Read function: (repo, tenant_id) -> data (model instance or dict/list)
    read_fn: Callable | None = None

    # Extra keywords for fuzzy matching
    keywords: list[str] = field(default_factory=list)


def _build_from_providers() -> dict[str, ModuleDescriptor]:
    """Derive the registry from discovered ``CopilotProvider`` plugins.

    Each provider's ``module_data()`` is converted into the legacy
    ``ModuleDescriptor`` shape so consumers (mutation tools, awareness tools,
    schema introspection) keep their current interface. Providers that do not
    expose introspectable shape (``module_data() is None``) are skipped — the
    provider is still discoverable for tools/workflows but not addressable by
    name through the registry.
    """
    # Local import keeps domain layer free of application-layer dependencies
    # at module-load time and matches the lazy-loader pattern this module
    # used pre-F1.
    from luana_core_copilot.application.discovery import discover_providers

    registry: dict[str, ModuleDescriptor] = {}
    for module_id, provider in discover_providers().items():
        data = provider.module_data()
        if data is None:
            continue
        registry[module_id] = ModuleDescriptor(
            module_id=data.module_id,
            label=data.label,
            description=data.description,
            route_prefix=data.route_prefix,
            model_class=data.model_class,
            repo_factory=data.repo_factory,
            read_fn=data.read_fn,
            keywords=list(data.keywords),
        )
    return registry


@functools.lru_cache(maxsize=1)
def get_module_registry() -> dict[str, ModuleDescriptor]:
    """Return the module registry, building it on first access."""
    return _build_from_providers()


def reset_module_registry_cache() -> None:
    """Clear the singleton — test/admin helper."""
    get_module_registry.cache_clear()

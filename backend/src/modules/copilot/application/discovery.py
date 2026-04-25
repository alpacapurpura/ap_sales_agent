"""F1 — Provider discovery for the copilot.

Builds the runtime ``CopilotProvider`` registry from two sources, in priority
order:

1. **Convention scan** of ``src.modules.{name}.copilot_provider``. Each
   in-repo module that wants to plug into the copilot exports a top-level
   ``provider`` attribute satisfying ``CopilotProvider``.
2. **Entry points** in the ``nicolify.copilot_providers`` group. Lets external
   packages distribute providers via ``pyproject.toml`` without touching this
   repo. Convention wins on collision so internal modules can't be shadowed.

Discovery is **lazy + cached**: ``discover_providers()`` is a singleton; tests
call ``reset_discovery()`` to reload. Discovery is the single source of truth
for module metadata and tool aggregation — there is no ``COPILOT_DISCOVERY``
feature flag. If a provider fails to load it is logged via structlog/Sentry
and skipped, but the registry continues to serve all healthy siblings. To
roll back, revert the commit; runtime fallback through legacy hardcoded
imports was retired alongside this fase.
"""

from __future__ import annotations

import importlib
import importlib.metadata
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path

import structlog

from src.modules.copilot.domain.ports import CopilotProvider, ProviderHealth

_LOGGER = structlog.get_logger(__name__)

_ENTRY_POINT_GROUP = "nicolify.copilot_providers"
_CONVENTION_PACKAGE = "src.modules"
_PROVIDER_SUBMODULE = "copilot_provider"
_PROVIDER_ATTR = "provider"

# Modules to skip during convention scan: copilot itself + common shared dirs.
_CONVENTION_SKIP: frozenset[str] = frozenset({"copilot"})


class ProviderDiscoveryError(RuntimeError):
    """Raised when the discovery layer cannot satisfy minimum invariants."""


def _scan_convention() -> dict[str, CopilotProvider]:
    """Walk ``src.modules.*.copilot_provider`` and import each provider.

    Filesystem-based scan (not ``pkgutil``) so namespace packages without an
    ``__init__.py`` (e.g. ``assets``, ``connections``, ``sales_agent``) are
    discovered alongside regular packages. Failures (missing submodule, import
    error, malformed export) are logged but never raise — the caller gets a
    partial registry and Sentry receives the structured event so a failing
    provider is visible in admin without crashing siblings.
    """
    registry: dict[str, CopilotProvider] = {}
    try:
        pkg = importlib.import_module(_CONVENTION_PACKAGE)
    except ModuleNotFoundError:
        _LOGGER.exception("copilot.discovery.convention_root_missing", package=_CONVENTION_PACKAGE)
        return registry

    candidate_modules: set[str] = set()
    for path_entry in pkg.__path__:
        try:
            entries = sorted(Path(path_entry).iterdir())
        except (FileNotFoundError, NotADirectoryError):
            continue
        for child in entries:
            if not child.is_dir() or child.name.startswith((".", "_")):
                continue
            if (child / _PROVIDER_SUBMODULE).is_dir():
                candidate_modules.add(child.name)

    for mod_name in sorted(candidate_modules):
        if mod_name in _CONVENTION_SKIP:
            continue
        full_path = f"{_CONVENTION_PACKAGE}.{mod_name}.{_PROVIDER_SUBMODULE}"
        try:
            sub = importlib.import_module(full_path)
        except ModuleNotFoundError:
            # Module exists but has no copilot provider yet — expected.
            continue
        except Exception as exc:
            _LOGGER.exception(
                "copilot.discovery.convention_import_failed",
                module=mod_name,
                path=full_path,
                error=str(exc),
            )
            continue

        provider = getattr(sub, _PROVIDER_ATTR, None)
        if provider is None:
            _LOGGER.warning(
                "copilot.discovery.convention_attr_missing",
                module=mod_name,
                path=full_path,
                attr=_PROVIDER_ATTR,
            )
            continue
        if not isinstance(provider, CopilotProvider):
            _LOGGER.warning(
                "copilot.discovery.convention_protocol_violation",
                module=mod_name,
                path=full_path,
                provider_type=type(provider).__name__,
            )
            continue

        registry[provider.module_id] = provider

    return registry


def _scan_entry_points() -> dict[str, CopilotProvider]:
    """Discover providers via ``importlib.metadata.entry_points``.

    Tolerates the case where entry points support is absent (e.g. backend
    installed without ``pyproject.toml [project]`` block) — returns ``{}``.
    """
    registry: dict[str, CopilotProvider] = {}
    try:
        eps = importlib.metadata.entry_points(group=_ENTRY_POINT_GROUP)
    except Exception as exc:  # noqa: BLE001
        _LOGGER.warning("copilot.discovery.entry_points_unavailable", error=str(exc))
        return registry

    for ep in eps:
        try:
            provider = ep.load()
        except Exception as exc:
            _LOGGER.exception(
                "copilot.discovery.entry_point_load_failed",
                name=ep.name,
                error=str(exc),
            )
            continue
        if not isinstance(provider, CopilotProvider):
            _LOGGER.warning(
                "copilot.discovery.entry_point_protocol_violation",
                name=ep.name,
                provider_type=type(provider).__name__,
            )
            continue
        registry[provider.module_id] = provider

    return registry


@lru_cache(maxsize=1)
def discover_providers() -> dict[str, CopilotProvider]:
    """Return the merged provider registry (singleton)."""
    convention = _scan_convention()
    entry_points = _scan_entry_points()

    # Convention wins over entry points (in-repo > distributed plugins).
    merged: dict[str, CopilotProvider] = {**entry_points, **convention}

    if not merged:
        _LOGGER.error(
            "copilot.discovery.empty",
            convention_count=len(convention),
            entry_points_count=len(entry_points),
        )
    else:
        _LOGGER.info(
            "copilot.discovery.complete",
            convention=sorted(convention),
            entry_points=sorted(entry_points),
            merged=sorted(merged),
        )
    return merged


def reset_discovery() -> None:
    """Clear the discovery cache — test helper.

    Production callers do not need this: the registry is loaded once at
    process boot and any provider that fails to load is reported via
    structlog/Sentry without crashing the worker.
    """
    discover_providers.cache_clear()


def health() -> dict[str, ProviderHealth]:
    """Return a per-provider health snapshot.

    Each entry is built by exercising the provider's required surface
    (``module_id``, ``module_data()``). Failures land in ``last_error`` so
    the admin page can surface broken plugins without affecting siblings.
    """
    snapshot: dict[str, ProviderHealth] = {}
    timestamp = datetime.now(tz=timezone.utc).isoformat()
    for module_id, provider in discover_providers().items():
        try:
            _ = provider.module_id
            _ = provider.label
            _ = provider.module_data()
            _ = provider.routes()
            snapshot[module_id] = ProviderHealth(
                module_id=module_id,
                last_loaded_at=timestamp,
            )
        except Exception as exc:  # noqa: BLE001
            snapshot[module_id] = ProviderHealth(
                module_id=module_id,
                last_error=str(exc),
                last_loaded_at=timestamp,
            )
    return snapshot

"""Architectural fitness: DDD boundary enforcement.

Ratchet pattern — known violations are allowlisted. The test ensures
NO NEW cross-module imports are introduced. To fix a violation, remove
it from the allowlist and refactor the import.
"""

from tests.architecture.conftest import (
    CROSS_IMPORT_ALLOWED_SOURCES,
    CROSS_IMPORT_ALLOWED_TARGETS,
    MODULES_DIR,
    module_name_from_path,
    parse_imports,
)

# ──────────────────────────────────────────────────────────────
# KNOWN VIOLATIONS — ratchet: only remove lines, never add.
# Expected format — "source_module -> target_module | file_relative_path"
# ──────────────────────────────────────────────────────────────
KNOWN_CROSS_MODULE_IMPORTS: set[str] = {
    # ── IRREDUCIBLES — justified exceptions (9 total, DDD sessions S1-S8 complete) ──
    #
    # Rule: only remove entries when the violation is fixed. Never add new ones.
    # Each entry below has a documented reason why it cannot be eliminated.
    # api/metrics.py is the analytics composition root. It wires ConnectionPortImpl,
    # OfferReadPortImpl, and BrandReadPortImpl as FastAPI Depends() — correct DI.
    # Eliminating these would require moving wiring to shared/, which just hides it.
    "analytics -> brand | analytics/api/metrics.py",
    "analytics -> connections | analytics/api/metrics.py",
    "analytics -> offer | analytics/api/metrics.py",
    # connections/api/dependencies/__init__.py sole purpose is DI wiring:
    # it binds ChatOrchestrator as the concrete MessageHandlerPort implementation.
    # The cross-module import IS the composition — not a design smell.
    "connections -> sales_agent | connections/api/dependencies/__init__.py",
    # offer/api/ is the composition root for offer endpoints. Both files import
    # OfferCampaignsReadAdapter to surface advertising stats alongside offer KPIs.
    # This is correct orchestration at the API layer boundary.
    "offer -> advertising | offer/api/campaigns.py",
    "offer -> advertising | offer/api/counts.py",
    # copilot is explicitly allowed as an import target for any module —
    # it is an infra-like orchestrator (see .claude/rules/backend-ddd.md).
    "offer -> copilot | offer/api/offer_ai.py",
    # campaign_service.py: campaign sync must know which ad connections (Meta,
    # Google Ads) are active. The connection record IS the provider config.
    "analytics -> connections | analytics/application/services/campaign_service.py",
    # etl_service.py: ETL run queries active connections to select providers.
    # Connection credentials and config live only in the connections module —
    # no abstraction can remove this genuine data dependency.
    "analytics -> connections | analytics/application/services/etl_service.py",
}


# ──────────────────────────────────────────────────────────────
# Provider-pattern (F1, April 2026): modules implement
# ``CopilotProvider`` Protocols defined in ``copilot.domain.ports``. Importing
# the contract surface from inside ``{module}/copilot_provider/`` is the
# dependency-inversion knot — copilot owns the abstraction, modules supply
# concretions. These imports are NOT cross-module coupling.
# ──────────────────────────────────────────────────────────────
_PROVIDER_CONTRACT_IMPORTS: frozenset[str] = frozenset(
    {
        "src.modules.copilot.domain.ports",
        # F6 — workflow declarative types are part of the provider contract:
        # ``WorkflowProvider.workflows() -> Sequence[Workflow]`` requires
        # subclasses outside of copilot to import ``Workflow``,
        # ``WorkflowNode``, ``WorkflowTrigger``, ``NodeOutput`` from here. This
        # mirrors the ports.py inversion knot — copilot owns the abstraction,
        # modules supply the concretion.
        "src.modules.copilot.domain.workflow",
        # F7 — channel formatter registry. Providers that ship custom output
        # channels (e.g. a future WhatsApp business adapter that registers a
        # ``whatsapp_template`` variant) import ``ChannelFormat`` and call
        # ``register_channel`` from their package init. Same dependency-
        # inversion pattern as ports.py / workflow.py.
        "src.modules.copilot.domain.output_channels",
    }
)


def _is_provider_contract_import(py_file_parts: tuple[str, ...], imported_module: str) -> bool:
    """Return ``True`` for imports of the copilot provider contract from
    a module's ``copilot_provider/`` directory."""

    if "copilot_provider" not in py_file_parts:
        return False
    return any(
        imported_module == contract or imported_module.startswith(f"{contract}.")
        for contract in _PROVIDER_CONTRACT_IMPORTS
    )


def test_no_new_cross_module_imports():
    """No module imports from another module (except copilot, shared, core, iam).

    This is the single most important DDD constraint. Violations create
    hidden coupling that makes modules impossible to extract or test independently.
    """
    violations: list[str] = []

    for py_file in sorted(MODULES_DIR.rglob("*.py")):
        source_module = module_name_from_path(py_file)
        if source_module in CROSS_IMPORT_ALLOWED_SOURCES:
            continue

        for imp in parse_imports(py_file):
            if not imp.startswith("src.modules."):
                continue
            target_module = imp.split("src.modules.")[1].split(".")[0]

            # Same module or allowed target — OK
            if target_module == source_module:
                continue
            if target_module in CROSS_IMPORT_ALLOWED_TARGETS:
                continue
            # Provider-pattern contract import — see comment above.
            if _is_provider_contract_import(py_file.parts, imp):
                continue

            rel_path = str(py_file.relative_to(MODULES_DIR))
            violation_key = f"{source_module} -> {target_module} | {rel_path}"

            if violation_key not in KNOWN_CROSS_MODULE_IMPORTS:
                violations.append(violation_key)

    assert violations == [], (
        "NEW cross-module imports detected (DDD boundary violation).\n"
        "These imports were NOT in the allowlist.\n\n"
        "Options:\n"
        "  1. Refactor: move shared types to src/shared/ or use domain events\n"
        "  2. If truly necessary, add to KNOWN_CROSS_MODULE_IMPORTS in this file\n"
        "     (requires code review justification)\n\n"
        "Violations:\n" + "\n".join(f"  - {v}" for v in violations)
    )


def test_domain_layer_has_no_framework_imports():
    """Domain layer must be pure Python — no SQLAlchemy, FastAPI, or httpx imports.

    The domain layer defines business rules. Framework imports in domain/
    create coupling to infrastructure and make the domain untestable.
    """
    forbidden_prefixes = (
        "sqlalchemy",
        "fastapi",
        "httpx",
        "aiohttp",
        "redis",
        "qdrant_client",
        "alembic",
    )

    violations: list[str] = []

    for py_file in sorted(MODULES_DIR.rglob("*.py")):
        rel = py_file.relative_to(MODULES_DIR)
        parts = rel.parts
        # Only check files inside domain/ subdirectory
        if len(parts) < 2 or parts[1] != "domain":
            continue

        for imp in parse_imports(py_file):
            violations.extend(f"{rel}: imports {imp}" for prefix in forbidden_prefixes if imp.startswith(prefix))

    assert violations == [], (
        "Domain layer files import framework code.\n"
        "Domain must be pure Python (Pydantic, stdlib, typing only).\n\n"
        "Violations:\n" + "\n".join(f"  - {v}" for v in violations)
    )

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
    # ── DI WIRING (correct ports & adapters) ──────────────────
    # API layer imports concrete adapter for shared port via Depends().
    # Architecturally correct — composition root pattern.
    "analytics -> brand | analytics/api/metrics.py",
    "analytics -> connections | analytics/api/metrics.py",
    "analytics -> offer | analytics/api/metrics.py",
    "connections -> sales_agent | connections/api/dependencies/__init__.py",
    "offer -> advertising | offer/api/campaigns.py",
    "offer -> advertising | offer/api/counts.py",
    "offer -> copilot | offer/api/offer_ai.py",
    # ── DI WIRING (lazy factory in service) ───────────────────
    # Services create ConnectionPortImpl with isolated DB sessions
    # for parallel extraction workers.
    "analytics -> connections | analytics/application/services/campaign_service.py",
    "analytics -> connections | analytics/application/services/etl_service.py",
    # ── CRM ORM QUERIES (analytics services/engines) ──────────────
    # Still import from crm.application.services.* or crm.infrastructure.engines/*
    # (not resolved by model move — need service ports or shared kernel decision).
    "analytics -> crm | analytics/application/services/etl_service.py",
    "analytics -> crm | analytics/application/services/ig_dm_sync_service.py",
    "analytics -> crm | analytics/application/services/metrics_service.py",
    "analytics -> crm | analytics/application/services/stage_services/summary_stage.py",
    "analytics -> crm | analytics/infrastructure/engines/rfm.py",
    "analytics -> crm | analytics/infrastructure/engines/scoring.py",
    # (eliminated S5: repos + providers now use src.shared.infrastructure.models.crm)
    # ── WEBHOOK / EVENT INTEGRATION ───────────────────────────
    # (eliminated: analytics → offer/etl_service via shared/links/ports/offer)
    # (eliminated: analytics workers → crm via shared/links/ports/crm_enrichment)
    # (eliminated: connections/channel_info → analytics via shared/links/ports/analytics)
    "connections -> analytics | connections/api/marketing_webhooks.py",
    "connections -> crm | connections/api/marketing_webhooks.py",
    "connections -> offer | connections/api/marketing_webhooks.py",
    # ── OFFER ↔ CRM (product mapping backfill) ────────────────
    "offer -> crm | offer/api/product_mappings.py",
    # ── SALES AGENT ↔ CRM (runtime data access) ──────────────
    # (eliminated S5: audit.py + audit_repository.py now use shared models)
    "sales_agent -> crm | sales_agent/api/closer_studio.py",
    "sales_agent -> crm | sales_agent/application/orchestrator/chat.py",
    "sales_agent -> crm | sales_agent/application/services/closer_studio_service.py",
    "sales_agent -> crm | sales_agent/workers/follow_up_engine.py",
    # ── SALES AGENT ↔ CONNECTIONS/OFFER ───────────────────────
    # (eliminated: sales_agent → connections via shared/links/ports/channel_adapter + calendar)
    "sales_agent -> offer | sales_agent/application/services/knowledge_builder.py",
    "sales_agent -> offer | sales_agent/infrastructure/db/repositories/business_repository.py",
    # ── SCHEDULING CROSS-CUTS ─────────────────────────────────
    # (eliminated: scheduling → connections + crm via shared/links/ports/calendar + lead_resolution)
}


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

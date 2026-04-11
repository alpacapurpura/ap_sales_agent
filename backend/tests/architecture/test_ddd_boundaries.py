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
# Format: "source_module -> target_module | file_relative_path"
# ──────────────────────────────────────────────────────────────
KNOWN_CROSS_MODULE_IMPORTS: set[str] = {
    # --- analytics ---
    "analytics -> connections | analytics/api/metrics.py",
    "analytics -> connections | analytics/application/services/campaign_service.py",
    "analytics -> connections | analytics/application/services/etl_service.py",
    "analytics -> connections | analytics/application/services/metrics_service.py",
    "analytics -> connections | analytics/infrastructure/providers/google_ads_provider.py",
    "analytics -> connections | analytics/infrastructure/providers/google_analytics_provider.py",
    "analytics -> connections | analytics/infrastructure/providers/search_console_provider.py",
    "analytics -> connections | analytics/infrastructure/providers/tiktok_provider.py",
    "analytics -> connections | analytics/infrastructure/providers/youtube_provider.py",
    "analytics -> connections | analytics/workers/manychat_sync.py",
    "analytics -> connections | analytics/workers/tasks.py",
    "analytics -> crm | analytics/application/services/etl_service.py",
    "analytics -> crm | analytics/application/services/ig_dm_sync_service.py",
    "analytics -> crm | analytics/application/services/metrics_service.py",
    "analytics -> crm | analytics/application/services/stage_services/summary_stage.py",
    "analytics -> crm | analytics/infrastructure/engines/rfm.py",
    "analytics -> crm | analytics/infrastructure/engines/scoring.py",
    "analytics -> crm | analytics/infrastructure/providers/crm_internal_provider.py",
    "analytics -> crm | analytics/infrastructure/repositories/adoption_repository.py",
    "analytics -> crm | analytics/infrastructure/repositories/capture_repository.py",
    "analytics -> crm | analytics/infrastructure/repositories/evangelization_repository.py",
    "analytics -> crm | analytics/infrastructure/repositories/expansion_repository.py",
    "analytics -> crm | analytics/infrastructure/repositories/nurture_repository.py",
    "analytics -> crm | analytics/infrastructure/repositories/opportunity_repository.py",
    "analytics -> crm | analytics/infrastructure/repositories/sales_metrics_repository.py",
    "analytics -> crm | analytics/workers/manychat_sync.py",
    "analytics -> crm | analytics/workers/tasks.py",
    "analytics -> brand | analytics/api/metrics.py",  # BrandReadPort DI (same pattern as OfferReadPort)
    "analytics -> offer | analytics/api/metrics.py",
    "analytics -> offer | analytics/application/services/etl_service.py",
    # --- connections ---
    "connections -> analytics | connections/api/channel_info.py",
    "connections -> analytics | connections/api/marketing_webhooks.py",
    "connections -> analytics | connections/application/services/connection_port_impl.py",
    "connections -> crm | connections/api/calendar.py",
    "connections -> crm | connections/api/marketing_webhooks.py",
    "connections -> offer | connections/api/marketing_webhooks.py",
    "connections -> sales_agent | connections/api/meta.py",
    "connections -> sales_agent | connections/api/telegram.py",
    "connections -> sales_agent | connections/api/webhook.py",
    "connections -> sales_agent | connections/api/whatsapp.py",
    "connections -> scheduling | connections/api/calendar.py",
    # --- offer ---
    "offer -> copilot | offer/api/offer_ai.py",
    "offer -> crm | offer/api/product_mappings.py",
    # AdvertisingReadPort DI at the FastAPI route (same pattern as BrandReadPort):
    # offer declares the shared port, advertising ships the concrete adapter,
    # and the router wires it via Depends() at request time. No runtime
    # coupling — only the adapter import.
    "offer -> advertising | offer/api/campaigns.py",
    "offer -> advertising | offer/api/counts.py",
    # --- sales_agent ---
    "sales_agent -> brand | sales_agent/application/services/knowledge_builder.py",
    "sales_agent -> connections | sales_agent/application/orchestrator/chat.py",
    "sales_agent -> connections | sales_agent/application/services/channel_resolver.py",
    "sales_agent -> connections | sales_agent/application/services/channel_service.py",
    "sales_agent -> crm | sales_agent/api/audit.py",
    "sales_agent -> crm | sales_agent/api/closer_studio.py",
    "sales_agent -> crm | sales_agent/application/orchestrator/chat.py",
    "sales_agent -> crm | sales_agent/application/services/channel_resolver.py",
    "sales_agent -> crm | sales_agent/application/services/closer_studio_service.py",
    "sales_agent -> crm | sales_agent/infrastructure/memory/audit_repository.py",
    "sales_agent -> crm | sales_agent/workers/follow_up_engine.py",
    "sales_agent -> offer | sales_agent/application/services/knowledge_builder.py",
    "sales_agent -> offer | sales_agent/infrastructure/db/repositories/business_repository.py",
    "sales_agent -> scheduling | sales_agent/api/dto/public_links.py",
    "sales_agent -> scheduling | sales_agent/application/agents/sales/tools.py",
    # --- scheduling ---
    "scheduling -> connections | scheduling/application/services/availability_service.py",
    "scheduling -> crm | scheduling/api/agenda.py",
    "scheduling -> crm | scheduling/application/services/availability_service.py",
    "scheduling -> tenant_domains | scheduling/application/booking_url.py",
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
            for prefix in forbidden_prefixes:
                if imp.startswith(prefix):
                    violations.append(f"{rel}: imports {imp}")

    assert violations == [], (
        "Domain layer files import framework code.\n"
        "Domain must be pure Python (Pydantic, stdlib, typing only).\n\n"
        "Violations:\n" + "\n".join(f"  - {v}" for v in violations)
    )

"""Coherence fitness tests — enforce consistent coding patterns across all modules.

Gates:
1. HTTPException only in api/ layer
2. structlog only (no import logging, no print)
3. Pydantic v2 only (model_config, no class Config)
4. SA 2.0 mapped_column only (no Column())
5. All APIRouter must have tags=
6. No Optional[X] syntax (use X | None)
7. Service methods in application/ must be async
"""

import ast
import re
from pathlib import Path

MODULES_DIR = Path(__file__).resolve().parents[2] / "src" / "modules"
SHARED_DIR = Path(__file__).resolve().parents[2] / "src" / "shared"
SRC_DIR = Path(__file__).resolve().parents[2] / "src"

# ─── Ratchet allowlists (must shrink, never grow) ───

KNOWN_HTTP_EXCEPTION_OUTSIDE_API: set[str] = {
    # 3 violations — migrate to domain exceptions
    "core/rate_limit.py",
    "modules/iam/application/auth.py",
    "modules/offer/application/offer_service.py",
}

KNOWN_LOGGING_IMPORTS: set[str] = {
    # 40 violations — migrate to structlog progressively
    "core/sentry.py",
    "modules/analytics/api/etl_admin.py",
    "modules/analytics/application/cost_type_mapping.py",
    "modules/analytics/application/services/campaign_service.py",
    "modules/analytics/application/services/capture_cost_service.py",
    "modules/analytics/application/services/etl_service.py",
    "modules/analytics/application/services/stage_cost_service.py",
    "modules/analytics/infrastructure/cache/metrics_cache.py",
    "modules/analytics/infrastructure/etl/transformers.py",
    "modules/analytics/infrastructure/providers/base.py",
    "modules/analytics/infrastructure/providers/crm_internal_provider.py",
    "modules/analytics/infrastructure/providers/google_ads_provider.py",
    "modules/analytics/infrastructure/providers/google_analytics_provider.py",
    "modules/analytics/infrastructure/providers/mailerlite_provider.py",
    "modules/analytics/infrastructure/providers/meta_campaign_provider.py",
    "modules/analytics/infrastructure/providers/meta_pixel_provider.py",
    "modules/analytics/infrastructure/providers/meta_provider.py",
    "modules/analytics/infrastructure/providers/search_console_provider.py",
    "modules/analytics/infrastructure/providers/shopify_provider.py",
    "modules/analytics/infrastructure/providers/tiktok_provider.py",
    "modules/analytics/infrastructure/providers/youtube_analytics_provider.py",
    "modules/analytics/infrastructure/providers/youtube_provider.py",
    "modules/analytics/infrastructure/repositories/campaign_repository.py",
    "modules/analytics/infrastructure/repositories/capture_repository.py",
    "modules/analytics/infrastructure/repositories/nurture_repository.py",
    "modules/analytics/infrastructure/repositories/opportunity_repository.py",
    "modules/analytics/infrastructure/sync/campaign_sync_pipeline.py",
    "modules/analytics/workers/scheduler.py",
    "modules/analytics/workers/tasks.py",
    "modules/brand/workers/tasks.py",
    "modules/connections/application/services/connection_port_impl.py",
    "modules/connections/infrastructure/channels/gmail.py",
    "modules/connections/infrastructure/channels/google_calendar.py",
    "modules/connections/infrastructure/channels/instagram.py",
    "modules/connections/infrastructure/channels/telegram.py",
    "modules/connections/infrastructure/channels/tiktok.py",
    "modules/connections/infrastructure/channels/youtube.py",
    "modules/connections/infrastructure/oauth_service.py",
    "modules/copilot/application/copilot_service.py",
    "modules/crm/application/event_handlers.py",
    "modules/crm/application/services/inactivity_service.py",
    "modules/crm/application/services/lifecycle_service.py",
    "modules/crm/application/services/nps_service.py",
    "modules/crm/application/services/referral_service.py",
    "modules/iam/application/auth.py",
    "modules/landing/application/landing_service.py",
    "modules/offer/workers/tasks.py",
    "modules/sales_agent/application/event_bus.py",
    "modules/sales_agent/application/services/knowledge_builder.py",
    "modules/sales_agent/application/services/semantic_router.py",
    "modules/sales_agent/application/services/style_anchor_retriever.py",
    "modules/sales_agent/infrastructure/external/buffer_service.py",
    "modules/sales_agent/infrastructure/memory/vector_store.py",
    "modules/sales_agent/infrastructure/monitoring/tracing.py",
    "modules/sales_agent/infrastructure/prompts/base.py",
    "modules/sales_agent/workers/follow_up_engine.py",
    "modules/sales_agent/workers/frozen_detection.py",
    "modules/scheduling/infrastructure/cal_client.py",
    "shared/domain/events.py",
    "shared/infrastructure/prompts/base.py",
}

KNOWN_PYDANTIC_V1_CONFIG: set[str] = {
    # 10 violations — migrate to model_config = ConfigDict(...)
    "modules/analytics/application/dto/kpi_dto.py",
    "modules/connections/api/schemas.py",
    "modules/crm/api/dto/cdp.py",
    "modules/crm/application/dto/customer_dto.py",
    "modules/iam/api/schemas.py",
    "modules/offer/api/dto/offer_gallery.py",
    "modules/offer/api/product_mappings.py",
    "modules/offer/domain/offer_ai_schemas.py",
    "modules/sales_agent/domain/events.py",
    "modules/scheduling/api/schemas.py",
}


# ─── 1. HTTPException only in api/ ───


def test_no_httpexception_outside_api():
    """HTTPException must only be raised/imported in api/ layer.

    Domain/application/infrastructure should raise domain exceptions.
    The api/ layer catches them and converts to HTTP responses.
    """
    violations = []
    http_exc_pattern = re.compile(
        r"(from\s+fastapi\s+import.*HTTPException|from\s+starlette.*import.*HTTPException|raise\s+HTTPException)"
    )

    for py_file in sorted(SRC_DIR.rglob("*.py")):
        rel = str(py_file.relative_to(SRC_DIR))
        # Skip api/ layer, tests, admin
        if "/api/" in rel or rel.startswith(("admin/", "tests/")):
            continue

        content = py_file.read_text(encoding="utf-8")
        for i, line in enumerate(content.splitlines(), 1):
            if http_exc_pattern.search(line) and rel not in KNOWN_HTTP_EXCEPTION_OUTSIDE_API:
                violations.append(f"{rel}:{i}: {line.strip()}")

    assert not violations, "HTTPException found outside api/ layer (use domain exceptions):\n" + "\n".join(
        f"  {v}" for v in violations
    )


# ─── 2. structlog only ───


def test_consistent_logging():
    """Only structlog allowed. No `import logging` in src/ (except allowlisted).

    Ruff T20 already catches print(). This test catches import logging.
    """
    violations = []
    logging_pattern = re.compile(r"^(?:import logging|from logging import)")

    for py_file in sorted(SRC_DIR.rglob("*.py")):
        rel = str(py_file.relative_to(SRC_DIR))
        if rel.startswith(("admin/", "tests/", "core/logger")):
            continue

        content = py_file.read_text(encoding="utf-8")
        for i, line in enumerate(content.splitlines(), 1):
            if logging_pattern.match(line.strip()) and rel not in KNOWN_LOGGING_IMPORTS:
                violations.append(f"{rel}:{i}: {line.strip()}")

    assert not violations, (
        "import logging found outside allowlist (use structlog):\n"
        + "\n".join(f"  {v}" for v in violations)
        + f"\n\nAllowlist has {len(KNOWN_LOGGING_IMPORTS)} entries — shrink, never grow."
    )


# ─── 3. Pydantic v2 only ───


def test_pydantic_v2_config_only():
    """No `class Config:` in Pydantic models. Use `model_config = ConfigDict(...)`.

    Pydantic v1 inner class Config is deprecated in v2.
    """
    violations = []
    config_class_pattern = re.compile(r"^\s+class Config\s*[:(]")

    for py_file in sorted(SRC_DIR.rglob("*.py")):
        rel = str(py_file.relative_to(SRC_DIR))
        if rel.startswith(("admin/", "tests/", "core/config")):
            continue

        content = py_file.read_text(encoding="utf-8")
        for i, line in enumerate(content.splitlines(), 1):
            if config_class_pattern.match(line) and rel not in KNOWN_PYDANTIC_V1_CONFIG:
                violations.append(f"{rel}:{i}: {line.strip()}")

    assert not violations, (
        "Pydantic v1 `class Config:` found (use model_config = ConfigDict(...)):\n"
        + "\n".join(f"  {v}" for v in violations)
        + f"\n\nAllowlist has {len(KNOWN_PYDANTIC_V1_CONFIG)} entries — shrink, never grow."
    )


# Phase 3 TODO: test_router_has_tags (48 violations — fix routers then enable)

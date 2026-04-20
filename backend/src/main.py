"""FastAPI application entry point — mounts all module routers."""

import time
import uuid
from collections.abc import Callable

import structlog
from arq.connections import RedisSettings, create_pool
from fastapi import Depends, FastAPI, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text

# --- Bootstrap all models so SQLAlchemy mapper resolves cross-module relationships ---
import src.shared.infrastructure.model_registry  # noqa: F401
from src.core.config import settings
from src.core.database import SessionLocal, init_db, redis_client
from src.core.logger import configure_logging

# --- Sentry must init before app creation to capture startup errors ---
from src.core.sentry import init_sentry
from src.modules.advertising.api import routes as advertising_routes
from src.modules.analytics.api import campaigns as analytics_campaigns
from src.modules.analytics.api import etl_admin as analytics_etl_admin

# 9. Advertising (offer-campaign association, health check, metrics by offer)
# 10. Social Media (No API Router exposed yet)
# 11. Analytics
from src.modules.analytics.api import metrics as analytics_metrics
from src.modules.assets.api import offer_gallery as assets_offers

# 13. Assets
from src.modules.assets.api import router as assets_gallery
from src.modules.brand.api import avatars as brand_avatars
from src.modules.brand.api import buyer_personas as brand_buyer_personas
from src.modules.brand.api import extraction as brand_tools
from src.modules.brand.api import personality as brand_personality
from src.modules.brand.api import router as brand_settings

# 2. Brand
from src.modules.brand.api import style as brand_style

# 14. Commercial Calendar
from src.modules.commercial_calendar.api import events as calendar_events
from src.modules.connections.api import calendar as conn_calendar
from src.modules.connections.api import channel_info as conn_channel_info
from src.modules.connections.api import gmail as conn_gmail
from src.modules.connections.api import google_analytics as conn_google_analytics
from src.modules.connections.api import google_workspace as conn_google_workspace
from src.modules.connections.api import health as conn_health
from src.modules.connections.api import mailerlite as conn_mailerlite
from src.modules.connections.api import manychat as conn_manychat
from src.modules.connections.api import marketing_webhooks as conn_marketing
from src.modules.connections.api import meta as conn_meta
from src.modules.connections.api import shopify as conn_shopify
from src.modules.connections.api import shopify_compliance
from src.modules.connections.api import status as conn_status
from src.modules.connections.api import telegram as conn_telegram

# 12. Connections
from src.modules.connections.api import webhook as conn_webhook
from src.modules.connections.api import whatsapp as conn_whatsapp
from src.modules.connections.api import youtube as conn_youtube
from src.modules.connections.api import youtube_analytics as conn_youtube_analytics

# 6. Copilot
from src.modules.copilot.api import actions as copilot_actions
from src.modules.copilot.api import chat as copilot_chat
from src.modules.copilot.api import events as copilot_events
from src.modules.copilot.api import interview as copilot_interview
from src.modules.copilot.api import knowledge as copilot_knowledge
from src.modules.copilot.api import nudge as copilot_nudge
from src.modules.copilot.api import voice as copilot_voice
from src.modules.crm.api import cdp as crm_cdp

# 7. CRM
from src.modules.crm.api import leads as crm_leads
from src.modules.crm.api import nps as crm_nps
from src.modules.crm.api import pipeline as crm_pipeline
from src.modules.crm.api import referral as crm_referral
from src.modules.crm.api import sales as crm_sales
from src.modules.iam.api import settings as iam_settings
from src.modules.iam.api import webhooks as iam_webhooks
from src.modules.iam.api.dependencies import get_tenant_context
from src.modules.iam.api.routers import auth_router as iam_users

# --- Domain Imports (Sorted by INDEX.md) ---
# 1. IAM
from src.modules.iam.api.routers import tenant_router as iam_admin
from src.modules.iam.api.tracking import public_router as iam_tracking_public
from src.modules.iam.api.tracking import router as iam_tracking

# 4. Landing
from src.modules.landing.api import landing as landing_ai
from src.modules.landing.api import public_edition as landing_public_edition
from src.modules.landing.api import public_landing as landing_public
from src.modules.offer.api import archetypes as offer_archetypes
from src.modules.offer.api import assets as offer_assets
from src.modules.offer.api import campaigns as offer_campaigns
from src.modules.offer.api import counts as offer_counts
from src.modules.offer.api import definitions as offer_definitions
from src.modules.offer.api import formats as offer_formats
from src.modules.offer.api import knowledge as offer_knowledge
from src.modules.offer.api import landing as offer_landing
from src.modules.offer.api import launch_editions as offer_launch_editions
from src.modules.offer.api import lifecycle as offer_lifecycle
from src.modules.offer.api import offer_ai
from src.modules.offer.api import offer_extraction as offer_tools
from src.modules.offer.api import offer_ladder_hints as offer_ladder_hints_api
from src.modules.offer.api import offer_type_presets as offer_type_presets_api
from src.modules.offer.api import product_mappings as offer_product_mappings

# 3. Offer
from src.modules.offer.api import products as offer_products
from src.modules.offer.api import value_levels as offer_value_levels
from src.modules.offer.api import variant_structures as offer_variant_structures

# 5. Sales Agent
from src.modules.sales_agent.api import audit as sales_audit
from src.modules.sales_agent.api import closer_studio as sales_closer
from src.modules.sales_agent.api import enrollments as sales_enrollments
from src.modules.sales_agent.api import ws as sales_ws
from src.modules.scheduling.api import agenda as sched_agenda

# 8. Scheduling
from src.modules.scheduling.api import event_types as sched_types
from src.modules.scheduling.api import public_links as sched_public

# 15. Tenant Domains
from src.modules.tenant_domains.api import domain_router as domains_router
from src.modules.tenant_profile.api import business_types_catalog as business_types_catalog_router

# 17. Tenant Profile (new bounded context — SSoT for business_types)
from src.modules.tenant_profile.api import router as tenant_profile_router

# 16. Shared catalogs (currencies, etc.)
from src.shared.api import currencies as shared_currencies

init_sentry("api")

# --- App Initialization ---

# Configure Logging (Structlog)
configure_logging()
logger = structlog.get_logger()

app = FastAPI(title=settings.PROJECT_NAME, redirect_slashes=False)

# Mount Static Files
app.mount("/static", StaticFiles(directory="static"), name="static")

# CORS Configuration — fully driven by CORS_ORIGINS env var
origins = settings.CORS_ORIGINS
logger.info("cors_origins_configured", origins=origins)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def sentry_tenant_middleware(request: Request, call_next: Callable) -> Response:
    """Tag every Sentry event/transaction with the tenant_id from the request header."""
    import sentry_sdk

    tenant_id = request.headers.get("X-Tenant-ID")
    if tenant_id:
        sentry_sdk.set_tag("tenant_id", tenant_id)
    return await call_next(request)


@app.middleware("http")
async def logging_middleware(request: Request, call_next: Callable) -> Response:
    """Log HTTP requests with timing and correlation ID."""
    request_id = str(uuid.uuid4())
    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(request_id=request_id)

    start_time = time.perf_counter()
    logger.info(
        "http_request_started",
        method=request.method,
        path=request.url.path,
        origin=request.headers.get("origin"),
    )

    if request.method == "OPTIONS":
        response = await call_next(request)
        logger.info(
            "cors_preflight",
            origin=request.headers.get("origin"),
            allow_origin=response.headers.get("access-control-allow-origin"),
        )
        return response

    try:
        response = await call_next(request)
        process_time = time.perf_counter() - start_time
        logger.info(
            "http_request_completed",
            status_code=response.status_code,
            process_time=process_time,
        )
    except Exception as e:
        process_time = time.perf_counter() - start_time
        logger.exception(
            "http_request_failed",
            error=str(e),
            process_time=process_time,
        )
        raise

    else:
        return response


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Return 422 with structured validation error details."""
    return JSONResponse(status_code=422, content={"detail": exc.errors()})


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Capture unhandled exceptions in Sentry and return 500."""
    import sentry_sdk

    sentry_sdk.capture_exception(exc)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


@app.on_event("startup")
def on_startup() -> None:
    """Initialize database and register domain event handlers."""
    init_db()

    # Register CRM domain event handlers (EventBus wiring)
    from src.modules.crm.application.event_handlers import register_event_handlers

    register_event_handlers()


@app.on_event("startup")
async def startup_arq_pool() -> None:
    """Create shared ARQ connection pool for job dispatch."""
    try:
        app.state.arq_pool = await create_pool(
            RedisSettings.from_dsn(settings.REDIS_URL),
        )
        logger.info("arq_pool_connected", redis_url=settings.REDIS_URL)
    except Exception as exc:  # noqa: BLE001 — startup/health resilience
        logger.warning(
            "arq_pool_unavailable",
            redis_url=settings.REDIS_URL,
            error=str(exc),
            hint="Background job dispatch will be unavailable",
        )
        app.state.arq_pool = None


@app.on_event("shutdown")
async def shutdown_arq_pool() -> None:
    """Close ARQ connection pool."""
    if hasattr(app.state, "arq_pool") and app.state.arq_pool:
        await app.state.arq_pool.close()


@app.get("/health")
def health_check() -> JSONResponse:
    """Liveness probe — lightweight, used by Docker healthcheck.

    Returns 200 if the API process is alive and can reach Postgres.
    For full dependency checks use GET /health/ready.
    """
    db = SessionLocal()
    try:
        db.execute(text("SELECT 1"))
        return JSONResponse(
            content={"status": "ok", "version": settings.SENTRY_RELEASE},
        )
    except Exception:  # noqa: BLE001 — startup/health resilience
        return JSONResponse(
            content={"status": "error", "postgres": "unreachable"},
            status_code=503,
        )
    finally:
        db.close()


@app.get("/health/ready")
def readiness_check() -> JSONResponse:
    """Readiness probe — deep check of all dependencies.

    Used by external monitoring / post-deploy healthcheck job.
    """
    import httpx

    checks: dict = {"api": "ok", "version": settings.SENTRY_RELEASE}
    healthy = True

    # PostgreSQL
    db = SessionLocal()
    try:
        db.execute(text("SELECT 1"))
        checks["postgres"] = "ok"
    except Exception:  # noqa: BLE001 — startup/health resilience
        checks["postgres"] = "error"
        healthy = False
    finally:
        db.close()

    # Redis
    try:
        redis_client.ping()
        checks["redis"] = "ok"
    except Exception:  # noqa: BLE001 — startup/health resilience
        checks["redis"] = "error"
        healthy = False

    # Qdrant
    try:
        resp = httpx.get(f"{settings.QDRANT_URL}/readyz", timeout=3.0)
        checks["qdrant"] = "ok" if resp.status_code == 200 else "error"
        if resp.status_code != 200:
            healthy = False
    except Exception:  # noqa: BLE001 — startup/health resilience
        checks["qdrant"] = "error"
        healthy = False

    # Scheduler heartbeat (TTL 5 min — set by run_tick_scheduler every minute)
    # Informational only — does not block healthy status because the scheduler
    # can take up to 5 min to fire its first cron tick after a fresh deploy.
    try:
        last_tick = redis_client.get("scheduler:last_tick")
        checks["scheduler"] = "ok" if last_tick else "stale"
    except Exception:  # noqa: BLE001 — startup/health resilience
        checks["scheduler"] = "error"

    status_code = 200 if healthy else 503
    return JSONResponse(
        content={"status": "ok" if healthy else "degraded", **checks},
        status_code=status_code,
    )


@app.get("/")
def root_redirect() -> Response:
    """Redirect Shopify admin 'App opened' requests to the frontend dashboard."""
    from fastapi.responses import RedirectResponse

    return RedirectResponse(url=f"{settings.DASHBOARD_DOMAIN}/connections/shopify")


# --- Router Mounting (Organized by Domain) ---

# 1. IAM
app.include_router(
    iam_admin.router,
    prefix="/api/v1/iam/tenants",
    tags=["IAM - Tenants"],
    dependencies=[Depends(get_tenant_context)],
)
app.include_router(
    iam_users.router,
    prefix="/api/v1/iam/users",
    tags=["IAM - Users"],
)  # Global Context
app.include_router(
    iam_settings.router,
    prefix="/api/v1/iam/settings",
    tags=["IAM - Settings"],
    dependencies=[Depends(get_tenant_context)],
)
app.include_router(
    iam_tracking,
    prefix="/api/v1/iam/settings",
    tags=["IAM - Settings"],
    dependencies=[Depends(get_tenant_context)],
)
app.include_router(
    iam_tracking_public,
    prefix="/api/v1/public",
    tags=["Public - Tracking"],
)
app.include_router(
    iam_webhooks.router,
    prefix="/api/v1/iam/webhooks",
    tags=["IAM - Webhooks"],
)

# 2. Brand
app.include_router(
    brand_style.router,
    prefix="/api/v1/brand/style",
    tags=["Brand - Style"],
    dependencies=[Depends(get_tenant_context)],
)
app.include_router(
    brand_avatars.router,
    prefix="/api/v1/brand/avatars",
    tags=["Brand - Avatars"],
    dependencies=[Depends(get_tenant_context)],
)
app.include_router(
    brand_settings.router,
    prefix="/api/v1/brand/settings",
    tags=["Brand - Settings"],
    dependencies=[Depends(get_tenant_context)],
)
app.include_router(
    brand_tools.router,
    prefix="/api/v1/brand/tools",
    tags=["Brand - Tools"],
    dependencies=[Depends(get_tenant_context)],
)
app.include_router(
    brand_personality.router,
    prefix="/api/v1/brand",
    tags=["Brand - Personality"],
    dependencies=[Depends(get_tenant_context)],
)
app.include_router(
    brand_buyer_personas.router,
    prefix="/api/v1/brand/buyer-personas",
    tags=["Brand - Buyer Personas"],
    dependencies=[Depends(get_tenant_context)],
)
# 3. Offer
app.include_router(
    offer_products.router,
    prefix="/api/v1/offer/products",
    tags=["Offer - Products"],
    dependencies=[Depends(get_tenant_context)],
)
app.include_router(
    offer_ai.router,
    prefix="/api/v1/offer/ai",
    tags=["Offer - AI"],
    dependencies=[Depends(get_tenant_context)],
)
app.include_router(
    offer_definitions.router,
    prefix="/api/v1/offer/definitions",
    tags=["Offer - Definitions"],
)
app.include_router(
    offer_archetypes.router,
    prefix="/api/v1/offer/archetypes",
    tags=["Offer - Archetypes"],
)
app.include_router(
    offer_value_levels.router,
    prefix="/api/v1/offer/value-levels",
    tags=["Offer - Value Levels"],
)
app.include_router(
    offer_variant_structures.router,
    prefix="/api/v1/offer/variant-structures",
    tags=["Offer - Variant Structures"],
)
app.include_router(
    offer_formats.router,
    prefix="/api/v1/offer/formats",
    tags=["Offer - Formats"],
)
app.include_router(
    offer_ladder_hints_api.router,
    prefix="/api/v1/offer/ladder-hints",
    tags=["Offer - Ladder Hints"],
)
app.include_router(
    offer_type_presets_api.router,
    prefix="/api/v1/offer/type-presets",
    tags=["Offer - Type Presets"],
)
app.include_router(
    shared_currencies.router,
    prefix="/api/v1/shared/currencies",
    tags=["Shared - Currencies"],
)
app.include_router(
    offer_product_mappings.router,
    prefix="/api/v1/offer",
    tags=["Offer - Product Mappings"],
    dependencies=[Depends(get_tenant_context)],
)
app.include_router(
    offer_tools.router,
    prefix="/api/v1/offer/tools",
    tags=["Offer - Tools"],
    dependencies=[Depends(get_tenant_context)],
)
app.include_router(
    offer_launch_editions.router,
    prefix="/api/v1/offer/products",
    tags=["Offer - Launch Editions"],
    dependencies=[Depends(get_tenant_context)],
)
app.include_router(
    offer_lifecycle.router,
    prefix="/api/v1/offer/products",
    tags=["Offer - Lifecycle"],
    dependencies=[Depends(get_tenant_context)],
)
app.include_router(
    offer_counts.router,
    prefix="/api/v1/offer/products",
    tags=["Offer - Counts"],
    dependencies=[Depends(get_tenant_context)],
)
app.include_router(
    offer_campaigns.router,
    prefix="/api/v1/offer/products",
    tags=["Offer - Campaigns"],
    dependencies=[Depends(get_tenant_context)],
)
app.include_router(
    offer_landing.router,
    prefix="/api/v1/offer/products",
    tags=["Offer - Landing"],
    dependencies=[Depends(get_tenant_context)],
)
app.include_router(
    offer_assets.router,
    prefix="/api/v1/offer/products",
    tags=["Offer - Assets"],
    dependencies=[Depends(get_tenant_context)],
)
app.include_router(
    offer_knowledge.router,
    prefix="/api/v1/offer/products",
    tags=["Offer - Knowledge"],
    dependencies=[Depends(get_tenant_context)],
)

# 4. Landing
app.include_router(
    landing_ai.router,
    prefix="/api/v1/landings",
    tags=["Landing"],
    dependencies=[Depends(get_tenant_context)],
)
app.include_router(
    landing_public.router,
    prefix="/api/v1/public",
    tags=["Public - Landing"],
)
app.include_router(
    landing_public_edition.router,
    prefix="/api/v1/public",
    tags=["Public - Landing"],
)

# 5. Sales Agent - Audit
app.include_router(
    sales_audit.router,
    prefix="/api/v1/admin/audit",
    tags=["Sales Agent - Audit"],
    dependencies=[Depends(get_tenant_context)],
)
app.include_router(
    sales_closer.router,
    prefix="/api/v1/closer-studio",
    tags=["Closer Studio"],
    dependencies=[Depends(get_tenant_context)],
)
app.include_router(
    sales_enrollments.router,
    prefix="/api/v1/sales-agent",
    tags=["Sales Agent - Enrollments"],
    dependencies=[Depends(get_tenant_context)],
)
app.include_router(sales_ws.router, tags=["Closer Studio - WebSocket"])

# 6. Copilot
app.include_router(
    copilot_actions.router,
    prefix="/api/v1/copilot/actions",
    tags=["Copilot - Actions"],
    dependencies=[Depends(get_tenant_context)],
)
app.include_router(
    copilot_chat.router,
    prefix="/api/v1/copilot",
    tags=["Copilot - Chat"],
    dependencies=[Depends(get_tenant_context)],
)
app.include_router(
    copilot_nudge.router,
    prefix="/api/v1/copilot",
    tags=["Copilot - Nudges"],
    dependencies=[Depends(get_tenant_context)],
)
app.include_router(
    copilot_knowledge.router,
    prefix="/api/v1/copilot/knowledge",
    tags=["Copilot - Knowledge"],
    dependencies=[Depends(get_tenant_context)],
)
app.include_router(
    copilot_events.router,
    prefix="/api/v1/copilot/events",
    tags=["Copilot - Events"],
    dependencies=[Depends(get_tenant_context)],
)
app.include_router(
    copilot_interview.router,
    prefix="/api/v1/copilot/interview",
    tags=["Copilot - Interview"],
    dependencies=[Depends(get_tenant_context)],
)
app.include_router(
    copilot_voice.router,
    prefix="/api/v1/copilot/voice",
    tags=["Copilot - Voice"],
    dependencies=[Depends(get_tenant_context)],
)

# 7. CRM
app.include_router(
    crm_leads.router,
    prefix="/api/v1/crm/leads",
    tags=["CRM - Leads"],
    dependencies=[Depends(get_tenant_context)],
)
app.include_router(
    crm_cdp.router,
    prefix="/api/v1/crm/cdp",
    tags=["CRM - CDP"],
    dependencies=[Depends(get_tenant_context)],
)
app.include_router(
    crm_sales.router,
    prefix="/api/v1/crm/sales",
    tags=["CRM - Sales"],
    dependencies=[Depends(get_tenant_context)],
)
app.include_router(
    crm_pipeline.router,
    prefix="/api/v1/crm/pipeline",
    tags=["CRM - Pipeline"],
    dependencies=[Depends(get_tenant_context)],
)
app.include_router(
    crm_referral.router,
    prefix="/api/v1/crm",
    tags=["CRM - Referrals"],
    dependencies=[Depends(get_tenant_context)],
)
app.include_router(
    crm_nps.router,
    prefix="/api/v1/crm",
    tags=["CRM - NPS"],
    dependencies=[Depends(get_tenant_context)],
)

# 8. Scheduling
app.include_router(
    sched_types.router,
    prefix="/api/v1/scheduling/event-types",
    tags=["Scheduling - Event Types"],
    dependencies=[Depends(get_tenant_context)],
)
app.include_router(
    sched_agenda.router,
    prefix="/api/v1/scheduling/agenda",
    tags=["Scheduling - Agenda"],
    dependencies=[Depends(get_tenant_context)],
)
app.include_router(
    sched_public.router,
    prefix="/api/v1/scheduling/public",
    tags=["Scheduling - Public"],
)

# 11. Analytics
app.include_router(
    analytics_metrics.router,
    prefix="/api/v1/analytics",
    tags=["Analytics"],
    dependencies=[Depends(get_tenant_context)],
)
app.include_router(
    analytics_etl_admin.health_router,
    prefix="/api/v1/analytics",
    tags=["Analytics ETL"],
)
app.include_router(
    analytics_etl_admin.tenant_router,
    prefix="/api/v1/analytics",
    tags=["Analytics ETL"],
    dependencies=[Depends(get_tenant_context)],
)
app.include_router(
    analytics_campaigns.router,
    prefix="/api/v1/analytics",
    tags=["Analytics - Campaigns"],
    dependencies=[Depends(get_tenant_context)],
)

# 11b. Advertising (offer↔campaign associations, health check, metrics by offer)
app.include_router(
    advertising_routes.router,
    prefix="/api/v1",
    tags=["Advertising"],
    dependencies=[Depends(get_tenant_context)],
)

# 12. Connections
app.include_router(
    conn_calendar.router,
    prefix="/api/v1/connections/calendar",
    tags=["Connections - Calendar"],
    dependencies=[Depends(get_tenant_context)],
)
app.include_router(
    conn_gmail.router,
    prefix="/api/v1/connections/gmail",
    tags=["Connections - Gmail"],
    dependencies=[Depends(get_tenant_context)],
)
app.include_router(
    conn_whatsapp.router,
    prefix="/api/v1/connections/whatsapp",
    tags=["Connections - WhatsApp"],
)
app.include_router(
    conn_telegram.router,
    prefix="/api/v1/connections/telegram",
    tags=["Connections - Telegram"],
)
app.include_router(
    conn_webhook.router,
    prefix="/api/v1/connections/webhook",
    tags=["Connections - Webhook"],
)
app.include_router(
    conn_marketing.router,
    prefix="/api/v1/connections/marketing-webhooks",
    tags=["Connections - Marketing Webhooks"],
)
app.include_router(
    conn_shopify.router,
    prefix="/api/v1/connections/shopify",
    tags=["Connections - Shopify"],
    dependencies=[Depends(get_tenant_context)],
)
app.include_router(
    conn_shopify.public_router,
    prefix="/api/v1/connections/shopify",
    tags=["Connections - Shopify"],
)
app.include_router(
    shopify_compliance.router,
    prefix="/api/v1/connections/shopify/compliance",
    tags=["Connections - Shopify Compliance"],
)
app.include_router(
    conn_mailerlite.router,
    prefix="/api/v1/connections/mailerlite",
    tags=["Connections - MailerLite"],
    dependencies=[Depends(get_tenant_context)],
)
app.include_router(
    conn_google_analytics.router,
    prefix="/api/v1/connections/google-analytics",
    tags=["Connections - Google Analytics"],
    dependencies=[Depends(get_tenant_context)],
)
app.include_router(
    conn_meta.router,
    prefix="/api/v1/connections/meta",
    tags=["Connections - Meta"],
)
app.include_router(
    conn_manychat.router,
    prefix="/api/v1/connections/manychat",
    tags=["Connections - ManyChat"],
    dependencies=[Depends(get_tenant_context)],
)
app.include_router(
    conn_youtube.router,
    prefix="/api/v1/connections/youtube",
    tags=["Connections - YouTube"],
    dependencies=[Depends(get_tenant_context)],
)
app.include_router(
    conn_youtube_analytics.router,
    prefix="/api/v1/connections/youtube-analytics",
    tags=["Connections - YouTube Analytics"],
    dependencies=[Depends(get_tenant_context)],
)
app.include_router(
    conn_google_workspace.router,
    prefix="/api/v1/connections/google/workspace",
    tags=["Connections - Google Workspace"],
    dependencies=[Depends(get_tenant_context)],
)
app.include_router(
    conn_channel_info.router,
    prefix="/api/v1/connections/channel-info",
    tags=["Connections - Channel Info"],
    dependencies=[Depends(get_tenant_context)],
)
app.include_router(
    conn_status.router,
    prefix="/api/v1/connections",
    tags=["Connections - Status"],
    dependencies=[Depends(get_tenant_context)],
)
app.include_router(
    conn_health.router,
    prefix="/api/v1/connections",
    tags=["Connections - Health"],
    dependencies=[Depends(get_tenant_context)],
)

# 13. Assets
app.include_router(
    assets_gallery.router,
    prefix="/api/v1/assets/gallery",
    tags=["Assets - Gallery"],
    dependencies=[Depends(get_tenant_context)],
)
app.include_router(
    assets_offers.router,
    prefix="/api/v1/assets/offers",
    tags=["Assets - Offers"],
    dependencies=[Depends(get_tenant_context)],
)

# 14. Commercial Calendar
app.include_router(
    calendar_events.router,
    prefix="/api/v1/commercial-calendar",
    tags=["Commercial Calendar"],
    dependencies=[Depends(get_tenant_context)],
)

# 15. Domains
app.include_router(
    domains_router.router,
    prefix="/api/v1/domains",
    tags=["Domains"],
    dependencies=[Depends(get_tenant_context)],
)

# 17. Tenant Profile — SSoT for business_types (Sprint 2026-04-20)
app.include_router(
    tenant_profile_router.router,
    prefix="/api/v1/tenant/profile",
    tags=["Tenant Profile"],
)
app.include_router(
    business_types_catalog_router.router,
    prefix="/api/v1/catalogs/business-types",
    tags=["Catalogs - Business Types"],
)


# ── Deprecated alias for the legacy catalog URL ────────────────────────────
# CONTRACT §3.4: the endpoint moved from /brand/expert-business-types/catalog
# to /catalogs/business-types on 2026-04-20. This 301 preserves any external
# cache or SDK that hard-coded the old path. Scheduled for removal after the
# two-week deprecation window (2026-05-04).
@app.get(
    "/api/v1/brand/expert-business-types/catalog",
    include_in_schema=False,
    status_code=301,
    tags=["Deprecated"],
)
async def _legacy_expert_business_types_catalog_redirect() -> RedirectResponse:
    """Redirect (301) legacy catalog URL to the canonical tenant-profile home."""
    return RedirectResponse(
        url="/api/v1/catalogs/business-types",
        status_code=301,
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)

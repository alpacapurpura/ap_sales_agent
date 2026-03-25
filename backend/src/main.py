from fastapi import FastAPI, Request, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from src.core.config import settings
from src.core.database import init_db
from src.core.logger import configure_logging
from src.modules.iam.api.dependencies import get_tenant_context
from arq.connections import create_pool, RedisSettings
import structlog
import uuid
import time

# --- Domain Imports (Sorted by INDEX.md) ---

# 1. IAM
from src.modules.iam.api.routers import tenant_router as iam_admin, auth_router as iam_users
from src.modules.iam.api import webhooks as iam_webhooks, settings as iam_settings

# 2. Brand
from src.modules.brand.api import style as brand_style, avatars as brand_avatars
from src.modules.brand.api import router as brand_settings, extraction as brand_tools

# 3. Offer
from src.modules.offer.api import products as offer_products, offer_ai, definitions as offer_definitions, product_mappings as offer_product_mappings

# 4. Landing
from src.modules.landing.api import landing as landing_ai

# 5. Sales Agent
from src.modules.sales_agent.api import audit as sales_audit

# 6. Copilot
from src.modules.copilot.api import actions as copilot_actions
from src.modules.copilot.api import chat as copilot_chat
from src.modules.copilot.api import nudge as copilot_nudge
from src.modules.copilot.api import knowledge as copilot_knowledge
from src.modules.copilot.api import events as copilot_events

# 7. CRM
from src.modules.crm.api import leads as crm_leads, cdp as crm_cdp, sales as crm_sales, pipeline as crm_pipeline
from src.modules.crm.api import referral as crm_referral, nps as crm_nps

# 8. Scheduling
from src.modules.scheduling.api import event_types as sched_types, public_links as sched_public, agenda as sched_agenda

# 9. Advertising (No API Router exposed yet)

# 10. Social Media (No API Router exposed yet)

# 11. Analytics
from src.modules.analytics.api import metrics as analytics_metrics
from src.modules.analytics.api import etl_admin as analytics_etl_admin

# 12. Connections
from src.modules.connections.api import webhook as conn_webhook, telegram as conn_telegram, whatsapp as conn_whatsapp
from src.modules.connections.api import calendar as conn_calendar, gmail as conn_gmail, marketing_webhooks as conn_marketing, shopify as conn_shopify, mailerlite as conn_mailerlite, manychat as conn_manychat, google_analytics as conn_google_analytics, meta as conn_meta, youtube as conn_youtube, youtube_analytics as conn_youtube_analytics, google_workspace as conn_google_workspace, shopify_compliance
from src.modules.connections.api import channel_info as conn_channel_info

# 13. Assets
from src.modules.assets.api import router as assets_gallery, offer_gallery as assets_offers

# --- Bootstrap all models so SQLAlchemy mapper resolves cross-module relationships ---
import src.shared.infrastructure.model_registry  # noqa: F401

# --- App Initialization ---

# Configure Logging (Structlog)
configure_logging()
logger = structlog.get_logger()

app = FastAPI(title=settings.PROJECT_NAME)

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
async def logging_middleware(request: Request, call_next):
    request_id = str(uuid.uuid4())
    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(request_id=request_id)
    
    start_time = time.perf_counter()
    logger.info("http_request_started", method=request.method, path=request.url.path, origin=request.headers.get("origin"))
    
    if request.method == "OPTIONS":
        response = await call_next(request)
        logger.info("cors_preflight", origin=request.headers.get("origin"), allow_origin=response.headers.get("access-control-allow-origin"))
        return response

    try:
        response = await call_next(request)
        process_time = time.perf_counter() - start_time
        logger.info("http_request_completed", status_code=response.status_code, process_time=process_time)
        return response
    except Exception as e:
        process_time = time.perf_counter() - start_time
        logger.error("http_request_failed", error=str(e), process_time=process_time, exc_info=True)
        raise e

@app.on_event("startup")
def on_startup():
    init_db()

    # Register CRM domain event handlers (EventBus wiring)
    from src.modules.crm.application.event_handlers import register_event_handlers
    register_event_handlers()

@app.on_event("startup")
async def startup_arq_pool():
    """Create shared ARQ connection pool for job dispatch."""
    app.state.arq_pool = await create_pool(RedisSettings.from_dsn(settings.REDIS_URL))

@app.on_event("shutdown")
async def shutdown_arq_pool():
    """Close ARQ connection pool."""
    if hasattr(app.state, "arq_pool") and app.state.arq_pool:
        await app.state.arq_pool.close()

@app.get("/health")
def health_check():
    return {"status": "ok", "version": "1.0.0"}

# --- Router Mounting (Organized by Domain) ---

# 1. IAM
app.include_router(iam_admin.router, prefix="/api/v1/iam/tenants", tags=["IAM - Tenants"], dependencies=[Depends(get_tenant_context)])
app.include_router(iam_users.router, prefix="/api/v1/iam/users", tags=["IAM - Users"]) # Global Context
app.include_router(iam_settings.router, prefix="/api/v1/iam/settings", tags=["IAM - Settings"], dependencies=[Depends(get_tenant_context)])
app.include_router(iam_webhooks.router, prefix="/api/v1/iam/webhooks", tags=["IAM - Webhooks"])

# 2. Brand
app.include_router(brand_style.router, prefix="/api/v1/brand/style", tags=["Brand - Style"], dependencies=[Depends(get_tenant_context)])
app.include_router(brand_avatars.router, prefix="/api/v1/brand/avatars", tags=["Brand - Avatars"], dependencies=[Depends(get_tenant_context)])
app.include_router(brand_settings.router, prefix="/api/v1/brand/settings", tags=["Brand - Settings"], dependencies=[Depends(get_tenant_context)])
app.include_router(brand_tools.router, prefix="/api/v1/brand/tools", tags=["Brand - Tools"], dependencies=[Depends(get_tenant_context)])

# 3. Offer
app.include_router(offer_products.router, prefix="/api/v1/offer/products", tags=["Offer - Products"], dependencies=[Depends(get_tenant_context)])
app.include_router(offer_ai.router, prefix="/api/v1/offer/ai", tags=["Offer - AI"], dependencies=[Depends(get_tenant_context)])
app.include_router(offer_definitions.router, prefix="/api/v1/offer/definitions", tags=["Offer - Definitions"])
app.include_router(offer_product_mappings.router, prefix="/api/v1/offer", tags=["Offer - Product Mappings"], dependencies=[Depends(get_tenant_context)])

# 4. Landing
app.include_router(landing_ai.router, prefix="/api/v1/landings", tags=["Landing"], dependencies=[Depends(get_tenant_context)])

# 5. Sales Agent - Audit
app.include_router(sales_audit.router, prefix="/api/v1/admin/audit", tags=["Sales Agent - Audit"], dependencies=[Depends(get_tenant_context)])

# 6. Copilot
app.include_router(copilot_actions.router, prefix="/api/v1/copilot/actions", tags=["Copilot - Actions"], dependencies=[Depends(get_tenant_context)])
app.include_router(copilot_chat.router, prefix="/api/v1/copilot", tags=["Copilot - Chat"], dependencies=[Depends(get_tenant_context)])
app.include_router(copilot_nudge.router, prefix="/api/v1/copilot", tags=["Copilot - Nudges"], dependencies=[Depends(get_tenant_context)])
app.include_router(copilot_knowledge.router, prefix="/api/v1/copilot/knowledge", tags=["Copilot - Knowledge"], dependencies=[Depends(get_tenant_context)])
app.include_router(copilot_events.router, prefix="/api/v1/copilot/events", tags=["Copilot - Events"], dependencies=[Depends(get_tenant_context)])

# 7. CRM
app.include_router(crm_leads.router, prefix="/api/v1/crm/leads", tags=["CRM - Leads"], dependencies=[Depends(get_tenant_context)])
app.include_router(crm_cdp.router, prefix="/api/v1/crm/cdp", tags=["CRM - CDP"], dependencies=[Depends(get_tenant_context)])
app.include_router(crm_sales.router, prefix="/api/v1/crm/sales", tags=["CRM - Sales"], dependencies=[Depends(get_tenant_context)])
app.include_router(crm_pipeline.router, prefix="/api/v1/crm/pipeline", tags=["CRM - Pipeline"], dependencies=[Depends(get_tenant_context)])
app.include_router(crm_referral.router, prefix="/api/v1/crm", tags=["CRM - Referrals"], dependencies=[Depends(get_tenant_context)])
app.include_router(crm_nps.router, prefix="/api/v1/crm", tags=["CRM - NPS"], dependencies=[Depends(get_tenant_context)])

# 8. Scheduling
app.include_router(sched_types.router, prefix="/api/v1/scheduling/event-types", tags=["Scheduling - Event Types"], dependencies=[Depends(get_tenant_context)])
app.include_router(sched_agenda.router, prefix="/api/v1/scheduling/agenda", tags=["Scheduling - Agenda"], dependencies=[Depends(get_tenant_context)])
app.include_router(sched_public.router, prefix="/api/v1/scheduling/public", tags=["Scheduling - Public"])

# 11. Analytics
app.include_router(analytics_metrics.router, prefix="/api/v1/analytics", tags=["Analytics"], dependencies=[Depends(get_tenant_context)])
app.include_router(analytics_etl_admin.health_router, prefix="/api/v1/analytics", tags=["Analytics ETL"])
app.include_router(analytics_etl_admin.tenant_router, prefix="/api/v1/analytics", tags=["Analytics ETL"], dependencies=[Depends(get_tenant_context)])

# 12. Connections
app.include_router(conn_calendar.router, prefix="/api/v1/connections/calendar", tags=["Connections - Calendar"], dependencies=[Depends(get_tenant_context)])
app.include_router(conn_gmail.router, prefix="/api/v1/connections/gmail", tags=["Connections - Gmail"], dependencies=[Depends(get_tenant_context)])
app.include_router(conn_whatsapp.router, prefix="/api/v1/connections/whatsapp", tags=["Connections - WhatsApp"])
app.include_router(conn_telegram.router, prefix="/api/v1/connections/telegram", tags=["Connections - Telegram"])
app.include_router(conn_webhook.router, prefix="/api/v1/connections/webhook", tags=["Connections - Webhook"])
app.include_router(conn_marketing.router, prefix="/api/v1/connections/marketing-webhooks", tags=["Connections - Marketing Webhooks"])
app.include_router(conn_shopify.router, prefix="/api/v1/connections/shopify", tags=["Connections - Shopify"], dependencies=[Depends(get_tenant_context)])
app.include_router(conn_shopify.public_router, prefix="/api/v1/connections/shopify", tags=["Connections - Shopify"])
app.include_router(shopify_compliance.router, prefix="/api/v1/connections/shopify/compliance", tags=["Connections - Shopify Compliance"])
app.include_router(conn_mailerlite.router, prefix="/api/v1/connections/mailerlite", tags=["Connections - MailerLite"], dependencies=[Depends(get_tenant_context)])
app.include_router(conn_google_analytics.router, prefix="/api/v1/connections/google-analytics", tags=["Connections - Google Analytics"], dependencies=[Depends(get_tenant_context)])
app.include_router(conn_meta.router, prefix="/api/v1/connections/meta", tags=["Connections - Meta"])
app.include_router(conn_manychat.router, prefix="/api/v1/connections/manychat", tags=["Connections - ManyChat"], dependencies=[Depends(get_tenant_context)])
app.include_router(conn_youtube.router, prefix="/api/v1/connections/youtube", tags=["Connections - YouTube"], dependencies=[Depends(get_tenant_context)])
app.include_router(conn_youtube_analytics.router, prefix="/api/v1/connections/youtube-analytics", tags=["Connections - YouTube Analytics"], dependencies=[Depends(get_tenant_context)])
app.include_router(conn_google_workspace.router, prefix="/api/v1/connections/google/workspace", tags=["Connections - Google Workspace"], dependencies=[Depends(get_tenant_context)])
app.include_router(conn_channel_info.router, prefix="/api/v1/connections/channel-info", tags=["Connections - Channel Info"], dependencies=[Depends(get_tenant_context)])

# 13. Assets
app.include_router(assets_gallery.router, prefix="/api/v1/assets/gallery", tags=["Assets - Gallery"], dependencies=[Depends(get_tenant_context)])
app.include_router(assets_offers.router, prefix="/api/v1/assets/offers", tags=["Assets - Offers"], dependencies=[Depends(get_tenant_context)])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

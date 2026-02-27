from fastapi import FastAPI, Request, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from src.config import settings
from src.modules.iam.api.routers import tenant_router as admin, auth_router as users
from src.modules.iam.api import webhooks, settings as user_settings
from src.modules.offer.api import products, offer_ai, definitions
from src.modules.landing.api import landing as landing_ai
from src.modules.gallery.api import router as gallery, offer_gallery
from src.modules.onboarding.api import onboarding
from src.modules.communication.api import event_types, public_links
from src.modules.integration.api import webhook, telegram, whatsapp, calendar, gmail, marketing_webhooks
from src.modules.sales.api import leads
from src.modules.marketing.api import cdp, metrics
from src.modules.brand.api import router as brand_settings_router, extraction as brand_extraction_router, avatars
from src.modules.iam.api.dependencies import get_tenant_context
from src.shared.infrastructure.db.database import init_db
from src.shared.utils.logger import configure_logging
import structlog
import uuid
import time

# Configure Logging (Structlog)
configure_logging()
logger = structlog.get_logger()

app = FastAPI(title=settings.PROJECT_NAME)

# Mount Static Files
app.mount("/static", StaticFiles(directory="static"), name="static")

# CORS Configuration
# Default local development origins
default_origins = [
    "http://localhost:3000",
    "http://localhost:3001",
    "http://localhost:3002",
    "http://localhost:8501", # Streamlit Prod (Tunnel)
    "http://localhost:8502", # Streamlit Dev
    "http://127.0.0.1:3000",
]

# Combine with environment-configured origins
origins = default_origins + settings.CORS_ORIGINS

# Log configured origins for debugging
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
    
    # Bind request_id to context for all subsequent logs
    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(request_id=request_id)
    
    start_time = time.perf_counter()
    
    # Log Request
    logger.info("http_request_started", 
                      method=request.method, 
                      path=request.url.path,
                      client_ip=request.client.host if request.client else None)
    
    try:
        response = await call_next(request)
        process_time = time.perf_counter() - start_time
        
        # Log Response
        logger.info("http_request_completed",
                          status_code=response.status_code,
                          process_time=process_time)
        
        return response
    except Exception as e:
        process_time = time.perf_counter() - start_time
        logger.error("http_request_failed",
                           error=str(e),
                           process_time=process_time,
                           exc_info=True)
        raise e

@app.on_event("startup")
def on_startup():
    init_db()

# Legacy Router (Webhooks)
# app.include_router(api_router, prefix="/api/v1")

# New Routers (API-First Architecture)
app.include_router(admin.router, prefix="/api/v1/admin", tags=["Admin"], dependencies=[Depends(get_tenant_context)])
app.include_router(products.router, prefix="/api/v1/products", tags=["Products"], dependencies=[Depends(get_tenant_context)])
app.include_router(avatars.router, prefix="/api/v1/avatars", tags=["Avatars"], dependencies=[Depends(get_tenant_context)])
app.include_router(onboarding.router, prefix="/api/v1/onboarding", tags=["Onboarding"], dependencies=[Depends(get_tenant_context)])
app.include_router(user_settings.router, prefix="/api/v1/settings", tags=["Settings"], dependencies=[Depends(get_tenant_context)])
app.include_router(brand_settings_router.router, prefix="/api/v1/settings", tags=["Brand Settings"], dependencies=[Depends(get_tenant_context)])
app.include_router(users.router, prefix="/api/v1/users", tags=["Users"]) # Global User Context (no specific tenant dependency for list)
app.include_router(telegram.router, prefix="/api/v1")
app.include_router(calendar.router, prefix="/api/v1", dependencies=[Depends(get_tenant_context)])
app.include_router(gmail.router, prefix="/api/v1", dependencies=[Depends(get_tenant_context)])
app.include_router(event_types.router, prefix="/api/v1", dependencies=[Depends(get_tenant_context)])
app.include_router(whatsapp.router, prefix="/api/v1")
app.include_router(public_links.router, prefix="/api/v1/public", tags=["Public"]) # No Auth Dependency (Token based)
app.include_router(webhook.router, prefix="/api/v1/webhook", tags=["Webhook"]) # No Auth Dependency here (uses header secret)
app.include_router(definitions.router, prefix="/api/v1", tags=["Definitions"]) # Public or Auth? Maybe Auth is better but for now keep it accessible
app.include_router(leads.router, prefix="/api/v1", dependencies=[Depends(get_tenant_context)])
app.include_router(brand_extraction_router.router, prefix="/api/v1/tools", tags=["Tools"], dependencies=[Depends(get_tenant_context)])
app.include_router(gallery.router, prefix="/api/v1/gallery", tags=["Gallery"], dependencies=[Depends(get_tenant_context)])
app.include_router(offer_gallery.router, prefix="/api/v1/offers", tags=["Offer Gallery"], dependencies=[Depends(get_tenant_context)])
app.include_router(offer_ai.router, prefix="/api/v1/offers/ai", tags=["Offer AI"], dependencies=[Depends(get_tenant_context)])
app.include_router(landing_ai.router, prefix="/api/v1/offers", tags=["Landing AI"]) # Dependencies defined per route to allow public/preview access
app.include_router(cdp.router, prefix="/api/v1/cdp", tags=["Growth Studio"], dependencies=[Depends(get_tenant_context)])
app.include_router(metrics.router, prefix="/api/v1/marketing", tags=["Marketing Metrics"], dependencies=[Depends(get_tenant_context)])
app.include_router(marketing_webhooks.router, prefix="/api/v1/webhooks/cdp", tags=["Webhooks"])
app.include_router(webhooks.router, prefix="/api/v1/webhooks", tags=["Webhooks"])

@app.get("/health")
def health_check():
    return {"status": "ok", "version": "1.0.0"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

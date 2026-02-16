from fastapi import FastAPI, Request, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from src.config import settings
from src.api.routes import router as api_router
from src.api.routers import admin, products, avatars, onboarding, settings as user_settings, webhook, channels, calendar, public_links, event_types, gmail, whatsapp, definitions, leads, tools, gallery, offer_gallery, offer_ai, landing_ai
from src.api.dependencies import get_tenant_context
from src.services.database import init_db
from src.core.logging_config import configure_logging
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
    "http://localhost:8501", # Streamlit
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
app.include_router(api_router, prefix="/api/v1")

# New Routers (API-First Architecture)
app.include_router(admin.router, prefix="/api/v1/admin", tags=["Admin"], dependencies=[Depends(get_tenant_context)])
app.include_router(products.router, prefix="/api/v1/products", tags=["Products"], dependencies=[Depends(get_tenant_context)])
app.include_router(avatars.router, prefix="/api/v1/avatars", tags=["Avatars"], dependencies=[Depends(get_tenant_context)])
app.include_router(onboarding.router, prefix="/api/v1/onboarding", tags=["Onboarding"], dependencies=[Depends(get_tenant_context)])
app.include_router(user_settings.router, prefix="/api/v1/settings", tags=["Settings"], dependencies=[Depends(get_tenant_context)])
app.include_router(channels.router, prefix="/api/v1", dependencies=[Depends(get_tenant_context)])
app.include_router(calendar.router, prefix="/api/v1", dependencies=[Depends(get_tenant_context)])
app.include_router(gmail.router, prefix="/api/v1", dependencies=[Depends(get_tenant_context)])
app.include_router(event_types.router, prefix="/api/v1", dependencies=[Depends(get_tenant_context)])
app.include_router(whatsapp.router, prefix="/api/v1/whatsapp", dependencies=[Depends(get_tenant_context)])
app.include_router(public_links.router, prefix="/api/v1/public", tags=["Public"]) # No Auth Dependency (Token based)
app.include_router(webhook.router, prefix="/api/v1/webhook", tags=["Webhook"]) # No Auth Dependency here (uses header secret)
app.include_router(definitions.router, prefix="/api/v1", tags=["Definitions"]) # Public or Auth? Maybe Auth is better but for now keep it accessible
app.include_router(leads.router, prefix="/api/v1", dependencies=[Depends(get_tenant_context)])
app.include_router(tools.router, prefix="/api/v1/tools", tags=["Tools"], dependencies=[Depends(get_tenant_context)])
app.include_router(gallery.router, prefix="/api/v1/gallery", tags=["Gallery"], dependencies=[Depends(get_tenant_context)])
app.include_router(offer_gallery.router, prefix="/api/v1/offers", tags=["Offer Gallery"], dependencies=[Depends(get_tenant_context)])
app.include_router(offer_ai.router, prefix="/api/v1/offers/ai", tags=["Offer AI"], dependencies=[Depends(get_tenant_context)])
app.include_router(landing_ai.router, prefix="/api/v1/offers", tags=["Landing AI"]) # Dependencies defined per route to allow public/preview access

@app.get("/health")
def health_check():
    return {"status": "ok", "version": "1.0.0"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

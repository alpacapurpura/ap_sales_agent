from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from src.config import settings
from src.api.routes import router as api_router
from src.api.routers import knowledge, admin, products, avatars
from src.services.database import init_db
from src.core.logging_config import configure_logging
import structlog
import uuid
import time

# Configure Logging (Structlog)
configure_logging()
logger = structlog.get_logger()

app = FastAPI(title=settings.PROJECT_NAME)

# CORS Configuration
origins = [
    "http://localhost:3000",
    "http://localhost:8501", # Streamlit
    "http://127.0.0.1:3000",
    "http://salesagent.local",
    "http://salesagent.local:3000",
    "http://api.salesagent.local",
    "https://salesagent.local",
    "https://api.salesagent.local",
]

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
app.include_router(knowledge.router, prefix="/api/v1/knowledge", tags=["Knowledge"])
app.include_router(admin.router, prefix="/api/v1/admin", tags=["Admin"])
app.include_router(products.router, prefix="/api/v1/products", tags=["Products"])
app.include_router(avatars.router, prefix="/api/v1/avatars", tags=["Avatars"])

@app.get("/health")
def health_check():
    return {"status": "ok", "version": "1.0.0"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

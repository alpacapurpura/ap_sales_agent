from fastapi import APIRouter, Request, HTTPException, status, Depends
from sqlalchemy.orm import Session
import structlog
from src.core.database import get_db
# In a real scenario, we would use MessageService here to log the event or trigger a workflow
# For now keeping it simple but cleaner structure

from src.modules.connections.api.dependencies.webhook_security import verify_shopify_signature

logger = structlog.get_logger()

router = APIRouter()

@router.post("/shopify", status_code=status.HTTP_200_OK)
async def shopify_webhook(
    request: Request, 
    verified: bool = Depends(verify_shopify_signature),
    db: Session = Depends(get_db)
):
    """
    Recibe un webhook de Shopify.
    """
    try:
        payload = await request.json()
        logger.info("shopify_webhook_received", payload_keys=list(payload.keys()))
        
        # TODO: Use Communication Service or Event Bus to handle this
        # e.g. event_bus.publish(ShopifyOrderReceived(payload))
        
        return {"status": "received", "source": "shopify"}
        
    except Exception as e:
        logger.error("shopify_webhook_error", error=str(e))
        raise HTTPException(status_code=400, detail="Invalid payload")

@router.post("/mailerlite", status_code=status.HTTP_200_OK)
async def mailerlite_webhook(request: Request, db: Session = Depends(get_db)):
    """
    Recibe un webhook de MailerLite.
    """
    try:
        payload = await request.json()
        logger.info("mailerlite_webhook_received", payload_keys=list(payload.keys()))
        
        # TODO: Use Communication Service or Event Bus
        
        return {"status": "received", "source": "mailerlite"}
        
    except Exception as e:
        logger.error("mailerlite_webhook_error", error=str(e))
        raise HTTPException(status_code=400, detail="Invalid payload")

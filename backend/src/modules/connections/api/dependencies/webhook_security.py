import hmac
import hashlib
import base64
import structlog
from fastapi import Request, HTTPException, status
from src.core.config import settings

logger = structlog.get_logger()

async def verify_shopify_signature(request: Request):
    """
    Verifica la firma HMAC-SHA256 de Shopify.
    Header: X-Shopify-Hmac-Sha256
    """
    signature = request.headers.get("X-Shopify-Hmac-Sha256")
    if not signature:
        logger.warning("shopify_webhook_missing_signature")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing Shopify signature")

    if not settings.SHOPIFY_API_SECRET:
        logger.error("shopify_webhook_secret_not_configured")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Shopify secret not configured")

    body = await request.body()
    
    digest = hmac.new(
        settings.SHOPIFY_API_SECRET.encode('utf-8'),
        body,
        hashlib.sha256
    ).digest()
    
    computed_hmac = base64.b64encode(digest).decode('utf-8')

    if not hmac.compare_digest(computed_hmac, signature):
        logger.warning("shopify_webhook_invalid_signature", computed=computed_hmac, received=signature)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Shopify signature")
    
    return True

async def verify_meta_signature(request: Request):
    """
    Verifica la firma HMAC-SHA256 de Meta (Facebook/Instagram).
    Header: X-Hub-Signature-256
    Formato: sha256=<signature>
    """
    signature_header = request.headers.get("X-Hub-Signature-256")
    if not signature_header:
        logger.warning("meta_webhook_missing_signature")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing Meta signature")

    if not settings.META_APP_SECRET:
        logger.error("meta_webhook_secret_not_configured")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Meta App Secret not configured")

    if not signature_header.startswith("sha256="):
        logger.warning("meta_webhook_invalid_signature_format", header=signature_header)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid signature format")
    
    signature = signature_header.split("=")[1]
    body = await request.body()

    digest = hmac.new(
        settings.META_APP_SECRET.encode('utf-8'),
        body,
        hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(digest, signature):
        logger.warning("meta_webhook_invalid_signature", computed=digest, received=signature)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Meta signature")

    return True

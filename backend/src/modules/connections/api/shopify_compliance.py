import structlog
from fastapi import APIRouter, Depends, Request, status

from src.modules.connections.api.dependencies.webhook_security import (
    verify_shopify_signature,
)

logger = structlog.get_logger()

router = APIRouter()


@router.post("/customers/data_request", status_code=status.HTTP_200_OK)
async def customers_data_request(
    request: Request, verified: bool = Depends(verify_shopify_signature)
):
    """
    GDPR: Request customer data.
    Shopify sends this when a merchant or customer requests their data.
    """
    try:
        payload = await request.json()
        logger.info(
            "shopify_compliance_customers_data_request",
            shop_domain=payload.get("shop_domain"),
            customer=payload.get("customer"),
        )
        # TODO: Trigger data export workflow
        return {"status": "received"}
    except Exception as e:
        logger.error(
            "shopify_compliance_error", endpoint="customers_data_request", error=str(e)
        )
        # Always return 200 to Shopify to acknowledge receipt, even if processing fails
        return {"status": "error", "message": str(e)}


@router.post("/customers/redact", status_code=status.HTTP_200_OK)
async def customers_redact(
    request: Request, verified: bool = Depends(verify_shopify_signature)
):
    """
    GDPR: Erase customer data.
    Shopify sends this when a merchant or customer requests deletion.
    """
    try:
        payload = await request.json()
        logger.info(
            "shopify_compliance_customers_redact",
            shop_domain=payload.get("shop_domain"),
            customer=payload.get("customer"),
        )
        # TODO: Trigger data deletion workflow
        return {"status": "received"}
    except Exception as e:
        logger.error(
            "shopify_compliance_error", endpoint="customers_redact", error=str(e)
        )
        return {"status": "error", "message": str(e)}


@router.post("/shop/redact", status_code=status.HTTP_200_OK)
async def shop_redact(
    request: Request, verified: bool = Depends(verify_shopify_signature)
):
    """
    GDPR: Erase shop data.
    Shopify sends this when a merchant uninstalls the app and 48 hours have passed.
    """
    try:
        payload = await request.json()
        logger.info(
            "shopify_compliance_shop_redact", shop_domain=payload.get("shop_domain")
        )
        # TODO: Trigger shop data deletion workflow
        return {"status": "received"}
    except Exception as e:
        logger.error("shopify_compliance_error", endpoint="shop_redact", error=str(e))
        return {"status": "error", "message": str(e)}
